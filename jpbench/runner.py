"""Run tasks through a model adapter and record one result per task."""

from __future__ import annotations

import concurrent.futures
import datetime
import hashlib
import importlib.metadata
import json
import os
import platform
import random
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from .parse import answer_kind, extract_json
from .prompt import PROMPT_TEMPLATE_VERSION, render_prompt
from .scoring import score_task
from .task import Task


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


class EchoAdapter:
    """Returns the prompt itself. Useful for checking what an agent would receive."""

    name = "echo"

    def complete(self, prompt: str) -> str:
        return prompt


class ErrorAdapter:
    """Always fails. Used to test error paths."""

    name = "error"

    def __init__(self, message: str = "adapter failed") -> None:
        self.message = message

    def complete(self, prompt: str) -> str:
        raise RuntimeError(self.message)


class RecordingAdapter:
    """Wraps another adapter and keeps every prompt it was given."""

    name = "recording"

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.inner.complete(prompt)


class ReplayAdapter:
    """Replays recorded outputs keyed by prompt digest. Fails if a prompt was never recorded."""

    name = "replay"

    def __init__(self, outputs: dict[str, str]) -> None:
        self.outputs = outputs

    @classmethod
    def from_jsonl(cls, path: Path | str) -> ReplayAdapter:
        outputs: dict[str, str] = {}
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                outputs[row["prompt_hash"]] = row["output"]
        return cls(outputs)

    def complete(self, prompt: str) -> str:
        key = digest(prompt)
        if key not in self.outputs:
            raise KeyError(f"no recorded output for prompt {key}")
        return self.outputs[key]


@dataclass(frozen=True)
class RunRecord:
    task_id: str
    prompt_hash: str
    answer_kind: str
    passed: bool
    score: float
    detail: str
    raw_output: str
    error: str = ""
    attempts: int = 1
    repeat: int = 1


def _complete(adapter: Any, prompt: str, timeout: float | None) -> str:
    if timeout is None:
        return adapter.complete(prompt)
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        return pool.submit(adapter.complete, prompt).result(timeout=timeout)
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def run_one(
    adapter: Any,
    task: Task,
    gold: dict[str, Any],
    lang: str = "en",
    retries: int = 2,
    timeout: float | None = None,
    backoff: float = 0.0,
    max_total_seconds: float | None = None,
    seed: int | None = None,
) -> RunRecord:
    """Run one task. Adapter exceptions are retried with exponential backoff and seeded jitter.

    Timeouts and parse failures are never retried. `max_total_seconds` caps the time spent
    waiting and retrying for one task.
    """
    prompt = render_prompt(task, lang=lang)
    h = digest(prompt)
    rng = random.Random(seed)
    started = time.monotonic()
    error = ""
    raw = ""
    attempts = 0
    succeeded = False
    for attempts in range(1, retries + 2):
        try:
            raw = _complete(adapter, prompt, timeout)
            succeeded = True
            break
        except concurrent.futures.TimeoutError as exc:
            if timeout is not None:
                return RunRecord(task.id, h, "timeout", False, 0.0, "adapter timed out", "", f"timed out after {timeout}s", attempts)
            error = f"{type(exc).__name__}: {exc}"
        except Exception as exc:  # noqa: BLE001 - adapter failures are recorded, never fatal to the run
            error = f"{type(exc).__name__}: {exc}"
        if attempts > retries:
            break
        delay = backoff * (2 ** (attempts - 1)) * (1 + rng.uniform(0, 0.1)) if backoff else 0.0
        if max_total_seconds is not None and time.monotonic() - started + delay > max_total_seconds:
            break
        if delay:
            time.sleep(delay)
    if not succeeded:
        return RunRecord(task.id, h, "error", False, 0.0, "adapter error", "", error, attempts)
    kind = answer_kind(raw)
    if kind != "json":
        detail = {"refusal": "refused to answer", "empty": "no output", "invalid": "output is not JSON"}[kind]
        return RunRecord(task.id, h, kind, False, 0.0, detail, raw, "", attempts)
    result = score_task(task, extract_json(raw), gold)
    return RunRecord(task.id, h, "json", result.passed, result.score, result.detail, raw, "", attempts)


def run_suite(
    adapter: Any,
    tasks: list[Task],
    golds: dict[str, dict[str, Any]],
    lang: str = "en",
    fail_fast: bool = False,
    skip: set[str] | frozenset[str] = frozenset(),
    timeout: float | None = None,
    jobs: int = 1,
) -> list[RunRecord]:
    """Run tasks in order. With jobs > 1 (and not fail-fast) tasks run concurrently but results keep order."""
    chosen = [t for t in tasks if t.id in golds and t.id not in skip]
    if jobs <= 1 or fail_fast:
        records: list[RunRecord] = []
        for task in chosen:
            rec = run_one(adapter, task, golds[task.id], lang=lang, timeout=timeout)
            records.append(rec)
            if fail_fast and rec.answer_kind == "error":
                break
        return records
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        return list(pool.map(lambda t: run_one(adapter, t, golds[t.id], lang=lang, timeout=timeout), chosen))


def pass_at_k(results: dict[str, list[bool]], k: int) -> float:
    """Fraction of tasks with at least one pass in the first k attempts."""
    if not results:
        return 0.0
    return sum(any(flags[:k]) for flags in results.values()) / len(results)


def load_records(path: Path | str) -> list[dict[str, Any]]:
    """Read JSON Lines results, dropping a half-written last line instead of failing."""
    p = Path(path)
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def make_run_id(adapter_name: str, when: datetime.datetime | None = None) -> str:
    when = when or datetime.datetime.now(datetime.timezone.utc)
    return f"{when:%Y%m%dT%H%M%SZ}-{adapter_name}"


def _version() -> str:
    try:
        return importlib.metadata.version("jpbench")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0+unknown"


def write_metadata(results_path: Path | str, adapter_name: str, records: list[RunRecord], run_id: str) -> Path:
    """Metadata next to the results. Deliberately records no environment variables, so no keys."""
    meta = {
        "run_id": run_id,
        "adapter": adapter_name,
        "jpbench_version": _version(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "count": len(records),
        "prompt_hashes": sorted({r.prompt_hash for r in records}),
        "prompt_template": PROMPT_TEMPLATE_VERSION,
    }
    path = Path(f"{results_path}.meta.json")
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_results(path: Path | str, records: list[RunRecord]) -> None:
    """Write JSON Lines atomically: temp file in the same directory, then rename."""
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".results-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def tag_repeat(records: list[RunRecord], repeat: int) -> list[RunRecord]:
    """Stamp each record with the repetition it came from."""
    return [replace(r, repeat=repeat) for r in records]
