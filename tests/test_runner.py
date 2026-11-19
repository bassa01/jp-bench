import json
from pathlib import Path

import pytest

from jpbench.prompt import render_prompt
from jpbench.runner import (
    EchoAdapter,
    ErrorAdapter,
    RecordingAdapter,
    ReplayAdapter,
    digest,
    run_suite,
    write_results,
)
from jpbench.task import load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"
GOLD = {"name": "株式会社サンプル商事", "registration_date": "2020-01-01", "active": True}
ANSWER = json.dumps(GOLD, ensure_ascii=False)


@pytest.fixture(scope="module")
def task():
    return {t.id: t for t in load_tasks(TASKS)}["invoice-number-verify"]


class FixedOutput:
    name = "fixed"

    def __init__(self, output):
        self.output = output

    def complete(self, prompt):
        return self.output


def test_suite_scores_a_correct_answer(task):
    recs = run_suite(FixedOutput(ANSWER), [task], {task.id: GOLD})
    assert recs[0].passed and recs[0].answer_kind == "json" and recs[0].prompt_hash


def test_refusal_and_invalid_are_recorded_not_raised(task):
    recs = run_suite(FixedOutput("I cannot help"), [task], {task.id: GOLD})
    assert recs[0].answer_kind == "refusal" and not recs[0].passed
    recs = run_suite(FixedOutput("not json"), [task], {task.id: GOLD})
    assert recs[0].answer_kind == "invalid" and recs[0].raw_output == "not json"


def test_adapter_error_continues_the_run(task):
    recs = run_suite(ErrorAdapter("boom"), [task, task], {task.id: GOLD})
    assert len(recs) == 2 and all(r.answer_kind == "error" for r in recs)
    assert "boom" in recs[0].error


def test_echo_adapter_returns_the_prompt(task):
    recs = run_suite(EchoAdapter(), [task], {task.id: GOLD})
    assert recs[0].raw_output == render_prompt(task)


def test_recording_adapter_keeps_prompts(task):
    rec = RecordingAdapter(FixedOutput(ANSWER))
    run_suite(rec, [task], {task.id: GOLD})
    assert rec.prompts == [render_prompt(task)]


def test_replay_matches_recorded_outputs(task, tmp_path):
    original = run_suite(FixedOutput(ANSWER), [task], {task.id: GOLD})
    path = tmp_path / "rec.jsonl"
    path.write_text(json.dumps({"prompt_hash": original[0].prompt_hash, "output": ANSWER}) + "\n", encoding="utf-8")
    replayed = run_suite(ReplayAdapter.from_jsonl(path), [task], {task.id: GOLD})
    assert replayed[0].passed == original[0].passed and replayed[0].score == original[0].score


def test_replay_fails_on_missing_prompt(task):
    recs = run_suite(ReplayAdapter({}), [task], {task.id: GOLD})
    assert recs[0].answer_kind == "error" and "no recorded output" in recs[0].error


def test_write_results_is_jsonl_and_atomic(task, tmp_path):
    recs = run_suite(FixedOutput(ANSWER), [task], {task.id: GOLD})
    out = tmp_path / "results.jsonl"
    write_results(out, recs)
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["task_id"] == task.id and rows[0]["prompt_hash"] == digest(render_prompt(task))
    assert not any(p.name.endswith(".tmp") for p in tmp_path.iterdir())
