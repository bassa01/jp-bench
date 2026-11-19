"""Run tasks through a model adapter and record one result per task."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .parse import answer_kind, extract_json
from .prompt import render_prompt
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


def run_one(adapter: Any, task: Task, gold: dict[str, Any], lang: str = "en", retries: int = 2) -> RunRecord:
    """Run one task. Adapter exceptions are retried; parse failures are not."""
    prompt = render_prompt(task, lang=lang)
    h = digest(prompt)
    error = ""
    attempts = 0
    for attempts in range(1, retries + 2):
        try:
            raw = adapter.complete(prompt)
            break
        except Exception as exc:  # noqa: BLE001 - adapter failures are recorded, never fatal to the run
            error = f"{type(exc).__name__}: {exc}"
    else:
        return RunRecord(task.id, h, "error", False, 0.0, "adapter error", "", error, attempts)
    kind = answer_kind(raw)
    if kind != "json":
        detail = {"refusal": "refused to answer", "empty": "no output", "invalid": "output is not JSON"}[kind]
        return RunRecord(task.id, h, kind, False, 0.0, detail, raw, "", attempts)
    result = score_task(task, extract_json(raw), gold)
    return RunRecord(task.id, h, "json", result.passed, result.score, result.detail, raw, "", attempts)


def run_suite(adapter: Any, tasks: list[Task], golds: dict[str, dict[str, Any]], lang: str = "en") -> list[RunRecord]:
    return [run_one(adapter, t, golds[t.id], lang=lang) for t in tasks if t.id in golds]


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
