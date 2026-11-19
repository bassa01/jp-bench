"""Score agent predictions against gold answers."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from .normalize import normalize_date, normalize_field, normalize_number, normalize_text
from .task import Task


@dataclass(frozen=True)
class TaskResult:
    task_id: str
    passed: bool
    score: float
    detail: str
    field_results: dict[str, bool] = field(default_factory=dict)
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"task_id": self.task_id, "passed": self.passed, "score": self.score, "detail": self.detail}


def _field_match(task: Task, pred: dict[str, Any], gold: dict[str, Any]) -> TaskResult:
    hits = 0
    misses: list[str] = []
    per_field: dict[str, bool] = {}
    for name in task.success.fields:
        value = pred.get(name)
        ok = name in pred and normalize_field(name, "" if value is None else value) == normalize_field(name, gold[name])
        per_field[name] = ok
        if ok:
            hits += 1
        else:
            misses.append(name)
    score = hits / len(task.success.fields)
    detail = "all fields match" if not misses else f"mismatch: {', '.join(misses)}"
    return TaskResult(task.id, not misses, score, detail, field_results=per_field)


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


_TRUE_WORDS = {"true", "yes", "はい", "有", "有効", "あり"}
_FALSE_WORDS = {"false", "no", "いいえ", "無", "無効", "なし"}


def _to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = normalize_text("" if value is None else value).lower()
    if text in {normalize_text(w).lower() for w in _TRUE_WORDS}:
        return True
    if text in {normalize_text(w).lower() for w in _FALSE_WORDS}:
        return False
    return None


def _boolean(task: Task, pred: dict[str, Any], gold: dict[str, Any]) -> TaskResult:
    name = task.success.fields[0]
    got = _to_bool(pred.get(name))
    want = _to_bool(gold[name])
    passed = got is not None and got == want
    detail = "boolean matches" if passed else f"expected {want}, got {pred.get(name)!r}"
    return TaskResult(task.id, passed, 1.0 if passed else 0.0, detail)


NOT_FOUND = "not_found"
OPEN_ENDED = "無期限"


def _date_range(task: Task, pred: dict[str, Any], gold: dict[str, Any]) -> TaskResult:
    hits = 0
    misses: list[str] = []
    for name in task.success.fields:
        got = "" if pred.get(name) is None else pred.get(name)
        want = gold[name]
        if normalize_text(want) == normalize_text(OPEN_ENDED):
            ok = normalize_text(got) == normalize_text(OPEN_ENDED)
        else:
            try:
                ok = normalize_date(got) == normalize_date(want)
            except (ValueError, TypeError):
                ok = False
        if ok:
            hits += 1
        else:
            misses.append(name)
    score = hits / len(task.success.fields)
    detail = "all dates match" if not misses else f"mismatch: {', '.join(misses)}"
    return TaskResult(task.id, not misses, score, detail)


def _enum(task: Task, pred: dict[str, Any], gold: dict[str, Any]) -> TaskResult:
    name = task.success.fields[0]
    labels = {normalize_text(k): normalize_text(v) for k, v in task.success.labels.items()}
    raw = pred.get(name)
    code = labels.get(normalize_text("" if raw is None else raw))
    if code is None:
        valid = ", ".join(sorted(task.success.labels))
        return TaskResult(task.id, False, 0.0, f"unknown label {raw!r}; valid: {valid}")
    passed = code == normalize_text(gold[name])
    return TaskResult(task.id, passed, 1.0 if passed else 0.0, "label matches" if passed else f"code {code} is wrong")


def _multi_answer(task: Task, pred: dict[str, Any], gold: dict[str, Any]) -> TaskResult:
    name = task.success.fields[0]
    options = gold[name] if isinstance(gold[name], list) else [gold[name]]
    got = normalize_text("" if pred.get(name) is None else pred.get(name))
    for option in options:
        if got == normalize_text(option):
            return TaskResult(task.id, True, 1.0, f"matched option: {option}")
    return TaskResult(task.id, False, 0.0, "no acceptable option matched")


def _abstain(task: Task, pred: dict[str, Any], gold: dict[str, Any]) -> TaskResult:
    name = task.success.fields[0]
    got = normalize_text("" if pred.get(name) is None else pred.get(name))
    if normalize_text(gold[name]) == normalize_text(NOT_FOUND):
        passed = got == normalize_text(NOT_FOUND)
        detail = "correctly abstained" if passed else "invented a value where none exists"
        return TaskResult(task.id, passed, 1.0 if passed else 0.0, detail)
    passed = got == normalize_text(gold[name])
    return TaskResult(task.id, passed, 1.0 if passed else 0.0, "value matches" if passed else "value is wrong")


_SCORERS = {
    "date_range": _date_range,
    "enum": _enum,
    "multi_answer": _multi_answer,
    "abstain": _abstain,
    "boolean": _boolean,
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


def wilson_interval(passed: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a pass rate."""
    if total == 0:
        return (0.0, 0.0)
    p = passed / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))
