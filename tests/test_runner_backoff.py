from pathlib import Path

import pytest

from jpbench.runner import ErrorAdapter, run_one
from jpbench.task import TaskError, load_tasks, parse_task

TASKS = Path(__file__).resolve().parent.parent / "tasks"
GOLD = {"name": "株式会社サンプル商事", "registration_date": "2020-01-01", "active": True}


def _task():
    return {t.id: t for t in load_tasks(TASKS)}["invoice-number-verify"]


def test_backoff_doubles_with_small_seeded_jitter(monkeypatch):
    sleeps = []
    monkeypatch.setattr("jpbench.runner.time.sleep", lambda d: sleeps.append(d))
    run_one(ErrorAdapter("x"), _task(), GOLD, retries=2, backoff=0.5, seed=7)
    assert len(sleeps) == 2
    assert 0.5 <= sleeps[0] <= 0.55 and 1.0 <= sleeps[1] <= 1.1


def test_same_seed_gives_same_delays(monkeypatch):
    first, second = [], []
    monkeypatch.setattr("jpbench.runner.time.sleep", lambda d: first.append(d))
    run_one(ErrorAdapter("x"), _task(), GOLD, retries=2, backoff=0.5, seed=3)
    monkeypatch.setattr("jpbench.runner.time.sleep", lambda d: second.append(d))
    run_one(ErrorAdapter("x"), _task(), GOLD, retries=2, backoff=0.5, seed=3)
    assert first == second


def test_total_time_cap_stops_retries_early(monkeypatch):
    monkeypatch.setattr("jpbench.runner.time.sleep", lambda d: None)
    rec = run_one(ErrorAdapter("x"), _task(), GOLD, retries=5, backoff=0.1, max_total_seconds=-1)
    assert rec.attempts == 1 and rec.answer_kind == "error"


def test_portal_must_be_a_government_domain():
    raw = {
        "id": "x-task", "title_ja": "サンプル", "title_en": "S", "category": "lookup", "difficulty": "easy",
        "instructions_ja": "検索", "instructions_en": "Search.", "inputs": {"a": "b"},
        "success": {"type": "field_match", "fields": ["a"]}, "gold_source": "x",
        "portal": {"name_ja": "x", "url": "https://example.com/", "operator": "x"}, "safety": {"stop_before_submit": False},
    }
    with pytest.raises(TaskError, match="government or public-body"):
        parse_task(raw)

