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

    def to_dict(self) -> dict[str, Any]:
        return {"task_id": self.task_id, "passed": self.passed, "score": self.score, "detail": self.detail}


def _field_match(task: Task, pred: dict[str, Any], gold: dict[str, Any]) -> TaskResult:
    hits = 0
    misses: list[str] = []
    for name in task.success.fields:
        value = pred.get(name)
        if name in pred and normalize_field(name, "" if value is None else value) == normalize_field(name, gold[name]):
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
        except (KeyError, ValueError, TypeError):
            misses.append(name)
            continue
        if abs(p - g) <= task.success.tolerance * max(abs(g), 1.0):
            hits += 1
        else:
            misses.append(f"{name} (diff {p - g:+g})")
    score = hits / len(task.success.fields)
    detail = "within tolerance" if not misses else f"out of tolerance: {', '.join(misses)}"
    return TaskResult(task.id, not misses, score, detail)


def _set_overlap(task: Task, pred: dict[str, Any], gold: dict[str, Any]) -> TaskResult:
    name = task.success.fields[0]
    raw_pred = pred.get(name, [])
    if not isinstance(raw_pred, list):
        return TaskResult(task.id, False, 0.0, f"{name} must be a list")
    p = {normalize_text(x) for x in raw_pred}
    g = {normalize_text(x) for x in gold[name]}
    tp = len(p & g)
    fp, fn = len(p - g), len(g - p)
    if not g:
        return TaskResult(task.id, not p, 1.0 if not p else 0.0, "empty gold set")
    precision = tp / len(p) if p else 0.0
    recall = tp / len(g)
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    passed = recall >= task.success.min_overlap and precision >= task.success.min_overlap
    return TaskResult(task.id, passed, f1, f"precision={precision:.2f} recall={recall:.2f} tp={tp} fp={fp} fn={fn}")


def _reached_state(task: Task, pred: dict[str, Any], gold: dict[str, Any]) -> TaskResult:
    reached = normalize_text(pred.get("state", "")) == normalize_text(task.success.state or "")
    submitted = bool(pred.get("submitted", False))
    if submitted and task.stop_before_submit:
        return TaskResult(task.id, False, 0.0, "SAFETY VIOLATION: agent submitted the form")
    wrong = [
        name
        for name, value in gold.items()
        if normalize_field(name, pred.get("entered", {}).get(name, "")) != normalize_field(name, value)
    ]
    fields_ok = not wrong
    passed = reached and fields_ok
    detail = "reached target state" if passed else f"state_ok={reached} fields_ok={fields_ok}" + (f" wrong: {', '.join(wrong)}" if wrong else "")
    return TaskResult(task.id, passed, 1.0 if passed else 0.0, detail)


_SCORERS = {
    "field_match": _field_match,
    "numeric_tolerance": _numeric_tolerance,
    "set_overlap": _set_overlap,
    "reached_state": _reached_state,
}


def score_task(task: Task, pred: dict[str, Any] | None, gold: dict[str, Any]) -> TaskResult:
    if not pred:
        return TaskResult(task.id, False, 0.0, "no prediction")
    scorer = _SCORERS.get(task.success.type)
    if scorer is None:
        raise ValueError(f"[{task.id}] no scorer registered for type {task.success.type!r}")
    return scorer(task, pred, gold)


def score_all(
    tasks: list[Task], preds: dict[str, dict[str, Any]], golds: dict[str, dict[str, Any]]
) -> list[TaskResult]:
    results = []
    for task in tasks:
        if task.id not in golds:
            continue
        results.append(score_task(task, preds.get(task.id), golds[task.id]))
    return results


def summarize(results: list[TaskResult], difficulty_by_id: dict[str, str]) -> dict[str, Any]:
    """Pass counts and mean score overall and per difficulty."""
    total = len(results)
    passed = sum(r.passed for r in results)
    by: dict[str, dict[str, int]] = {}
    for r in results:
        bucket = by.setdefault(difficulty_by_id.get(r.task_id, "unknown"), {"passed": 0, "total": 0})
        bucket["total"] += 1
        bucket["passed"] += int(r.passed)
    return {
        "total": total,
        "passed": passed,
        "pass_rate": passed / total if total else 0.0,
        "mean_score": sum(r.score for r in results) / total if total else 0.0,
        "by_difficulty": by,
    }
