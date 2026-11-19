"""Task schema, loading and validation for JP-Bench."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CATEGORIES = {"lookup", "extract", "search", "form_fill", "download"}
DIFFICULTIES = {"easy", "medium", "hard"}
_ID_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SUCCESS_TYPES = {"field_match", "numeric_tolerance", "set_overlap", "reached_state"}

REQUIRED_KEYS = {
    "id",
    "title_ja",
    "title_en",
    "portal",
    "category",
    "difficulty",
    "instructions_ja",
    "instructions_en",
    "inputs",
    "success",
    "safety",
}


class TaskError(ValueError):
    """Raised when a task file does not satisfy the schema."""


@dataclass(frozen=True)
class Portal:
    name_ja: str
    url: str
    operator: str


@dataclass(frozen=True)
class Success:
    type: str
    fields: list[str] = field(default_factory=list)
    tolerance: float = 0.0
    min_overlap: float = 1.0
    state: str | None = None


@dataclass(frozen=True)
class Task:
    id: str
    title_ja: str
    title_en: str
    portal: Portal
    category: str
    difficulty: str
    instructions_ja: str
    instructions_en: str
    inputs: dict[str, Any]
    success: Success
    stop_before_submit: bool
    auth_required: bool
    gold_source: str
    path: Path | None = None


def _require(cond: bool, task_id: str, msg: str) -> None:
    if not cond:
        raise TaskError(f"[{task_id}] {msg}")


def parse_task(raw: dict[str, Any], path: Path | None = None) -> Task:
    task_id = str(raw.get("id", path.stem if path else "?"))
    _require(bool(_ID_RE.fullmatch(task_id)), task_id, "id must be lowercase kebab-case")
    missing = REQUIRED_KEYS - raw.keys()
    _require(not missing, task_id, f"missing keys: {sorted(missing)}")

    if path is not None:
        _require(path.stem == task_id, task_id, f"file name must be {task_id}.yaml")

    portal = raw["portal"]
    _require(isinstance(portal, dict), task_id, "portal must be a mapping")
    url = str(portal.get("url", ""))
    _require(url.startswith("https://"), task_id, "portal.url must be https")

    _require(raw["category"] in CATEGORIES, task_id, f"category must be one of {sorted(CATEGORIES)}")
    _require(raw["difficulty"] in DIFFICULTIES, task_id, f"difficulty must be one of {sorted(DIFFICULTIES)}")

    succ = raw["success"]
    _require(isinstance(succ, dict), task_id, "success must be a mapping")
    stype = succ.get("type")
    _require(stype in SUCCESS_TYPES, task_id, f"success.type must be one of {sorted(SUCCESS_TYPES)}")
    if stype in {"field_match", "numeric_tolerance", "set_overlap"}:
        _require(bool(succ.get("fields")), task_id, f"success.fields required for {stype}")
    if stype == "reached_state":
        _require(bool(succ.get("state")), task_id, "success.state required for reached_state")

    safety = raw["safety"]
    _require(isinstance(safety, dict), task_id, "safety must be a mapping")
    stop = bool(safety.get("stop_before_submit", False))
    if raw["category"] == "form_fill":
        _require(stop, task_id, "form_fill tasks must set safety.stop_before_submit: true")

    return Task(
        id=task_id,
        title_ja=raw["title_ja"],
        title_en=raw["title_en"],
        portal=Portal(name_ja=portal["name_ja"], url=url, operator=portal["operator"]),
        category=raw["category"],
        difficulty=raw["difficulty"],
        instructions_ja=raw["instructions_ja"].strip(),
        instructions_en=raw["instructions_en"].strip(),
        inputs=dict(raw["inputs"] or {}),
        success=Success(
            type=stype,
            fields=list(succ.get("fields", [])),
            tolerance=float(succ.get("tolerance", 0.0)),
            min_overlap=float(succ.get("min_overlap", 1.0)),
            state=succ.get("state"),
        ),
        stop_before_submit=stop,
        auth_required=bool(safety.get("auth_required", False)),
        gold_source=str(raw.get("gold_source", "")),
        path=path,
    )


def load_tasks(directory: Path | str) -> list[Task]:
    directory = Path(directory)
    tasks: list[Task] = []
    seen: set[str] = set()
    for path in sorted(directory.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        with path.open(encoding="utf-8") as fh:
            try:
                raw = yaml.safe_load(fh)
            except yaml.YAMLError as exc:
                mark = getattr(exc, "problem_mark", None)
                where = f" at line {mark.line + 1}" if mark is not None else ""
                raise TaskError(f"{path.name}: YAML parse error{where}") from exc
        if not isinstance(raw, dict):
            raise TaskError(f"{path.name}: top level must be a mapping")
        task = parse_task(raw, path)
        _require(task.id not in seen, task.id, "duplicate task id")
        seen.add(task.id)
        tasks.append(task)
    return tasks
