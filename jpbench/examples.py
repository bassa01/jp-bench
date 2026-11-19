"""Optional few-shot examples per task, read from examples/<task-id>.yaml (never used as gold)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .task import Task, TaskError

MAX_EXAMPLES = 3


def load_examples(task: Task, directory: Path | str) -> list[dict[str, Any]]:
    path = Path(directory) / f"{task.id}.yaml"
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(raw, list):
        raise TaskError(f"[{task.id}] examples file must be a list")
    if len(raw) > MAX_EXAMPLES:
        raise TaskError(f"[{task.id}] at most {MAX_EXAMPLES} examples are allowed")
    for ex in raw:
        if not isinstance(ex, dict) or "input" not in ex or "output" not in ex:
            raise TaskError(f"[{task.id}] each example needs input and output")
        output = ex["output"]
        if not isinstance(output, dict) or set(output) != set(task.success.fields):
            raise TaskError(f"[{task.id}] example output keys must equal {sorted(task.success.fields)}")
    return raw
