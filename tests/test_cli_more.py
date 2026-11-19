import json
from pathlib import Path

import pytest

from jpbench.cli import main
from jpbench.scoring import wilson_interval

ROOT = Path(__file__).resolve().parent.parent
GOLD = {"name": "株式会社サンプル商事", "registration_date": "2020-01-01", "active": True}


@pytest.mark.parametrize("sub", ["list", "show", "validate", "prompt", "score", "report", "run", "doctor", "completion"])
def test_every_subcommand_help_exits_zero(sub):
    with pytest.raises(SystemExit) as exc:
        main([sub, "--help"])
    assert exc.value.code == 0


def test_completion_scripts(capsys):
    assert main(["completion", "bash"]) == 0
    assert 'complete -W "list show' in capsys.readouterr().out
    assert main(["completion", "zsh"]) == 0
    assert "#compdef jpbench" in capsys.readouterr().out


def test_doctor_reports_tasks(capsys):
    assert main(["doctor"]) == 0
    assert "tasks: 5" in capsys.readouterr().out


def test_validate_single_file(capsys):
    assert main(["validate", "--only", str(ROOT / "tasks" / "invoice-number-verify.yaml")]) == 0


def test_validate_single_bad_file(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("- a\n", encoding="utf-8")
    assert main(["validate", "--only", str(bad)]) == 1


def _report_inputs(tmp_path):
    pred = tmp_path / "p.json"
    gold = tmp_path / "g.json"
    pred.write_text(json.dumps({"invoice-number-verify": GOLD}, ensure_ascii=False), encoding="utf-8")
    gold.write_text(json.dumps({"invoice-number-verify": GOLD}, ensure_ascii=False), encoding="utf-8")
    return pred, gold


def test_report_has_category_type_and_ci(tmp_path, capsys):
    pred, gold = _report_inputs(tmp_path)
    assert main(["report", "--pred", str(pred), "--gold", str(gold)]) == 0
    out = capsys.readouterr().out
    assert "95% CI" in out and "| lookup | 1 | 1 |" in out and "| field_match | 1 | 1 |" in out


def test_report_output_refuses_overwrite_without_force(tmp_path, capsys):
    pred, gold = _report_inputs(tmp_path)
    target = tmp_path / "report.md"
    target.write_text("old", encoding="utf-8")
    assert main(["report", "--pred", str(pred), "--gold", str(gold), "--output", str(target)]) == 1
    assert main(["report", "--pred", str(pred), "--gold", str(gold), "--output", str(target), "--force"]) == 0
    assert target.read_text(encoding="utf-8").startswith("# JP-Bench report")


def test_wilson_interval_bounds():
    assert wilson_interval(0, 0) == (0.0, 0.0)
    low, high = wilson_interval(5, 5)
    assert high == 1.0 and 0.5 < low < 1.0
