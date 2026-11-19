import json
from dataclasses import replace
from pathlib import Path

from jpbench.cli import main
from jpbench.runner import ErrorAdapter, pass_at_k, run_suite
from jpbench.task import load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"
GOLD = {"name": "株式会社サンプル商事", "registration_date": "2020-01-01", "active": True}


class Slow:
    name = "slow"

    def complete(self, prompt):
        import time

        time.sleep(0.01)
        return "{}"


def _twenty():
    base = next(t for t in load_tasks(TASKS) if t.id == "invoice-number-verify")
    tasks = [replace(base, id=f"t-{i:02d}") for i in range(20)]
    golds = {t.id: GOLD for t in tasks}
    return tasks, golds


def test_concurrent_run_keeps_order_and_matches_sequential():
    tasks, golds = _twenty()
    seq = [r.task_id for r in run_suite(Slow(), tasks, golds, jobs=1)]
    par = [r.task_id for r in run_suite(Slow(), tasks, golds, jobs=4)]
    assert seq == par == [t.id for t in tasks]


def test_concurrent_run_handles_failures_per_task():
    tasks, golds = _twenty()
    recs = run_suite(ErrorAdapter("down"), tasks, golds, jobs=3)
    assert len(recs) == 20 and all(r.answer_kind == "error" for r in recs)


def test_pass_at_k_over_repeats():
    assert pass_at_k({"a": [False, True, False]}, 1) == 0.0
    assert pass_at_k({"a": [False, True, False]}, 3) == 1.0


def test_cli_repeat_reports_pass_at_k(tmp_path, capsys):
    gold = tmp_path / "gold.json"
    gold.write_text(json.dumps({"invoice-number-verify": GOLD}, ensure_ascii=False), encoding="utf-8")
    rec = tmp_path / "rec.jsonl"
    from jpbench.prompt import render_prompt
    from jpbench.runner import digest

    base = next(t for t in load_tasks(TASKS) if t.id == "invoice-number-verify")
    rec.write_text(json.dumps({"prompt_hash": digest(render_prompt(base)), "output": json.dumps(GOLD, ensure_ascii=False)}) + "\n", encoding="utf-8")
    out = tmp_path / "out.jsonl"
    code = main(["run", "--adapter", "replay", "--replay", str(rec), "--gold", str(gold), "--out", str(out), "--repeat", "2", "--quiet", "--jobs", "2"])
    assert code == 0
    assert "pass@1 1.000  pass@2 1.000" in capsys.readouterr().out
    assert len(out.read_text(encoding="utf-8").splitlines()) == 2
