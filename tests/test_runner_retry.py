from pathlib import Path

from jpbench.runner import ErrorAdapter, run_one
from jpbench.task import load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"
GOLD = {"name": "株式会社サンプル商事", "registration_date": "2020-01-01", "active": True}


def _task():
    return {t.id: t for t in load_tasks(TASKS)}["invoice-number-verify"]


class Flaky:
    name = "flaky"

    def __init__(self, fail_times, output):
        self.fail_times = fail_times
        self.output = output
        self.calls = 0

    def complete(self, prompt):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise TimeoutError("temporary")
        return self.output


def test_transient_error_is_retried_then_succeeds():
    rec = run_one(Flaky(1, '{"name": "x"}'), _task(), GOLD)
    assert rec.attempts == 2 and rec.answer_kind == "json"


def test_persistent_error_stops_after_retries():
    rec = run_one(ErrorAdapter("down"), _task(), GOLD, retries=2)
    assert rec.attempts == 3 and rec.answer_kind == "error" and "down" in rec.error


def test_parse_failures_are_not_retried():
    adapter = Flaky(0, "not json")
    rec = run_one(adapter, _task(), GOLD)
    assert adapter.calls == 1 and rec.answer_kind == "invalid"
