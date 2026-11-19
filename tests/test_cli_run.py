import json
from pathlib import Path

from jpbench.cli import main
from jpbench.prompt import render_prompt
from jpbench.runner import digest
from jpbench.task import load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"
GOLD = {"name": "株式会社サンプル商事", "registration_date": "2020-01-01", "active": True}


def _task():
    return {t.id: t for t in load_tasks(TASKS)}["invoice-number-verify"]


def _gold_file(tmp_path):
    p = tmp_path / "gold.json"
    p.write_text(json.dumps({"invoice-number-verify": GOLD}, ensure_ascii=False), encoding="utf-8")
    return p


def test_dry_run_prints_prompt_hash_and_writes_nothing(tmp_path, capsys):
    out = tmp_path / "o.jsonl"
    assert main(["run", "--gold", str(_gold_file(tmp_path)), "--out", str(out), "--dry-run"]) == 0
    assert capsys.readouterr().out.strip() == f"{digest(render_prompt(_task()))} invoice-number-verify"
    assert not out.exists()


def test_replay_run_scores_recorded_answer(tmp_path, capsys):
    rec = tmp_path / "rec.jsonl"
    row = {"prompt_hash": digest(render_prompt(_task())), "output": json.dumps(GOLD, ensure_ascii=False)}
    rec.write_text(json.dumps(row) + "\n", encoding="utf-8")
    out = tmp_path / "out.jsonl"
    code = main(["run", "--adapter", "replay", "--replay", str(rec), "--gold", str(_gold_file(tmp_path)), "--out", str(out), "--quiet"])
    assert code == 0
    assert "1/1 passed" in capsys.readouterr().out
    assert json.loads(out.read_text(encoding="utf-8").splitlines()[0])["passed"] is True


def test_replay_requires_recording_file(tmp_path):
    assert main(["run", "--adapter", "replay", "--gold", str(_gold_file(tmp_path)), "--out", str(tmp_path / "o.jsonl")]) == 1


def test_missing_recording_exits_2(tmp_path):
    rec = tmp_path / "empty.jsonl"
    rec.write_text("", encoding="utf-8")
    code = main(["run", "--adapter", "replay", "--replay", str(rec), "--gold", str(_gold_file(tmp_path)), "--out", str(tmp_path / "o.jsonl"), "--quiet"])
    assert code == 2
