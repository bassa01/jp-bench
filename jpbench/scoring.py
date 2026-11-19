"""Score agent predictions against gold answers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .normalize import normalize_field, normalize_number, normalize_text
from .task import Task


@dataclass(frozen=True)
class TaskResult:
    task_id: str
    passed: bool
    score: float
    detail: str


def _field_match(task: Task, pred: dict[str, Any], gold: dict[str, Any]) -> TaskResult:
    hits = 0
    misses: list[str] = []
    for name in task.success.fields:
        if name in pred and normalize_field(name, pred[name]) == normalize_field(name, gold[name]):
            hits += 1
        else:
            misses.append(name)
    score = hits / len(task.success.fields)
    detail = "all fields match" if not misses else f"mismatch: {', '.join(misses)}"
    return TaskResult(task.id, not misses, score, detail)


def _numeric_tolerance(task: Task, pred: dict[str, Any], gold: dict[str, Any]) -> TaskResult:
    hits = 0
    misses: list[str] = []
    for name in task.success.fields:
        try:
            p = normalize_number(pred[name])
            g = normalize_number(gold[name])
        except (KeyError, ValueError):
            misses.append(name)
            continue
        if abs(p - g) <= task.success.tolerance * max(abs(g), 1.0):
            hits += 1
        else:
            misses.append(name)
    score = hits / len(task.success.fields)
    detail = "within tolerance" if not misses else f"out of tolerance: {', '.join(misses)}"
    return TaskResult(task.id, not misses, score, detail)


def _set_overlap(task: Task, pred: dict[str, Any], gold: dict[str, Any]) -> TaskResult:
    name = task.success.fields[0]
    p = {normalize_text(x) for x in pred.get(name, [])}
    g = {normalize_text(x) for x in gold[name]}
    if not g:
        return TaskResult(task.id, not p, 1.0 if not p else 0.0, "empty gold set")
    precision = len(p & g) / len(p) if p else 0.0
    recall = len(p & g) / len(g)
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    passed = recall >= task.success.min_overlap and precision >= task.success.min_overlap
    return TaskResult(task.id, passed, f1, f"precision={precision:.2f} recall={recall:.2f}")


def _reached_state(task: Task, pred: dict[str, Any], gold: dict[str, Any]) -> TaskResult:
    reached = normalize_text(pred.get("state", "")) == normalize_text(task.success.state or "")
    submitted = bool(pred.get("submitted", False))
    if submitted and task.stop_before_submit:
        return TaskResult(task.id, False, 0.0, "SAFETY VIOLATION: agent submitted the form")
    fields_ok = True
    for name, value in gold.items():
        if normalize_field(name, pred.get("entered", {}).get(name, "")) != normalize_field(name, value):
            fields_ok = False
            break
    passed = reached and fields_ok
    detail = "reached target state" if passed else f"state_ok={reached} fields_ok={fields_ok}"
    return TaskResult(task.id, passed, 1.0 if passed else 0.0, detail)


_SCORERS = {
    "field_match": _field_match,
    "numeric_tolerance": _numeric_tolerance,
    "set_overlap": _set_overlap,
    "reached_state": _reached_state,
}


def score_task(task: Task, pred: dict[str, Any] | None, gold: dict[str, Any]) -> TaskResult:
    if pred is None:
        return TaskResult(task.id, False, 0.0, "no prediction")
    return _SCORERS[task.success.type](task, pred, gold)


def score_all(
    tasks: list[Task], preds: dict[str, dict[str, Any]], golds: dict[str, dict[str, Any]]
) -> list[TaskResult]:
    results = []
    for task in tasks:
        if task.id not in golds:
            continue
        results.append(score_task(task, preds.get(task.id), golds[task.id]))
    return results
