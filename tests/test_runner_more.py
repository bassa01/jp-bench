import datetime
import json
import time
from pathlib import Path

from jpbench.runner import (
    load_records,
    make_run_id,
    pass_at_k,
    run_one,
    run_suite,
    write_metadata,
    write_results,
)
from jpbench.task import load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"
GOLD = {"name": "株式会社サンプル商事", "registration_date": "2020-01-01", "active": True}


def _tasks():
    return list(load_tasks(TASKS))


class Sleepy:
    name = "sleepy"

    def complete(self, prompt):
        time.sleep(1.0)
        return "{}"


class Boom:
    name = "boom"

    def complete(self, prompt):
        raise RuntimeError("boom")


def test_timeout_is_a_timeout_record_and_not_retried():
    t = next(x for x in _tasks() if x.id == "invoice-number-verify")
    rec = run_one(Sleepy(), t, GOLD, timeout=0.05)
    assert rec.answer_kind == "timeout" and rec.attempts == 1


def test_fail_fast_stops_after_first_error():
    tasks = _tasks()
    golds = {t.id: GOLD for t in tasks}
    recs = run_suite(Boom(), tasks, golds, fail_fast=True)
    assert len(recs) == 1 and recs[0].answer_kind == "error"


def test_skip_resumes_remaining_tasks():
    tasks = _tasks()
    golds = {t.id: GOLD for t in tasks}
    done = {tasks[0].id}
    recs = run_suite(Boom(), tasks, golds, skip=done)
    assert all(r.task_id not in done for r in recs) and len(recs) == len(tasks) - 1


def test_half_written_last_line_is_dropped(tmp_path):
    p = tmp_path / "r.jsonl"
    p.write_text('{"task_id": "a"}\n{"task_id": "b", "pass', encoding="utf-8")
    assert [r["task_id"] for r in load_records(p)] == ["a"]
    assert load_records(tmp_path / "missing.jsonl") == []


def test_pass_at_k():
    results = {"a": [False, True], "b": [False, False]}
    assert pass_at_k(results, 1) == 0.0 and pass_at_k(results, 2) == 0.5
    assert pass_at_k({}, 1) == 0.0


def test_run_id_format():
    when = datetime.datetime(2026, 11, 20, 1, 2, 3, tzinfo=datetime.timezone.utc)
    assert make_run_id("replay", when) == "20261120T010203Z-replay"


def test_metadata_has_no_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-FAKE-KEY-123")
    out = tmp_path / "results.jsonl"
    rec = run_one(Boom(), _tasks()[0], GOLD)
    write_results(out, [rec])
    meta = write_metadata(out, "boom", [rec], make_run_id("boom"))
    text = meta.read_text(encoding="utf-8")
    assert "sk-test-FAKE-KEY-123" not in text
    data = json.loads(text)
    assert data["count"] == 1 and data["python"] and data["platform"] and data["prompt_hashes"]
