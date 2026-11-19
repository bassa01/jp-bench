import json

from jpbench.cli import main
from jpbench.scoring import TaskResult, summarize


def test_summarize_by_difficulty():
    results = [TaskResult("a", True, 1.0, ""), TaskResult("b", False, 0.5, "")]
    s = summarize(results, {"a": "easy", "b": "hard"})
    assert s["passed"] == 1 and s["total"] == 2 and s["pass_rate"] == 0.5
    assert s["by_difficulty"]["hard"] == {"passed": 0, "total": 1}


def test_report_outputs_markdown(tmp_path, capsys):
    pred = tmp_path / "pred.json"
    gold = tmp_path / "gold.json"
    pred.write_text(json.dumps({"invoice-number-verify": {"name": "A", "registration_date": "2020-01-01", "active": True}}), encoding="utf-8")
    gold.write_text(json.dumps({"invoice-number-verify": {"name": "A", "registration_date": "2020-01-01", "active": True}}), encoding="utf-8")
    assert main(["report", "--pred", str(pred), "--gold", str(gold)]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# JP-Bench report")
    assert "| invoice-number-verify | PASS |" in out
