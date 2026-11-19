import json
import re
from pathlib import Path

from jpbench.cli import main

ROOT = Path(__file__).resolve().parent.parent
GOLD = {"name": "株式会社サンプル商事", "registration_date": "2020-01-01", "active": True}


def test_show_format_is_stable(capsys):
    assert main(["show", "invoice-number-verify"]) == 0
    keys = [line.split(":", 1)[0] for line in capsys.readouterr().out.splitlines()]
    assert keys == ["id", "title", "portal", "category", "difficulty", "success", "stop_before_submit"]


def test_show_prompt_and_gold_source(capsys):
    assert main(["show", "invoice-number-verify", "--prompt"]) == 0
    assert "# JP-Bench task: invoice-number-verify" in capsys.readouterr().out
    assert main(["show", "invoice-number-verify", "--gold-source"]) == 0
    assert "適格請求書発行事業者" in capsys.readouterr().out


def test_list_lines_have_stable_columns(capsys):
    assert main(["list", "--sort", "difficulty"]) == 0
    lines = [l for l in capsys.readouterr().out.splitlines() if l.strip()]
    assert len(lines) == 5 and all(re.match(r"^\S+\s+\w+\s+\w+\s+.+$", l) for l in lines)


def test_score_command_passes_a_correct_answer(tmp_path, capsys):
    pred = tmp_path / "p.json"
    gold = tmp_path / "g.json"
    row = dict(GOLD)
    pred.write_text(json.dumps({"invoice-number-verify": row}, ensure_ascii=False), encoding="utf-8")
    gold.write_text(json.dumps({"invoice-number-verify": row}, ensure_ascii=False), encoding="utf-8")
    assert main(["score", "--pred", str(pred), "--gold", str(gold)]) == 0
    assert "PASS invoice-number-verify" in capsys.readouterr().out


def test_invalid_json_names_file_and_line(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text('{\n  "a": ,\n}', encoding="utf-8")
    good = tmp_path / "g.json"
    good.write_text("{}", encoding="utf-8")
    assert main(["score", "--pred", str(bad), "--gold", str(good)]) == 1
    err = capsys.readouterr().err
    assert "bad.json" in err and "line 2" in err


def test_help_lists_exit_codes(capsys):
    try:
        main(["--help"])
    except SystemExit:
        pass
    assert "exit codes" in capsys.readouterr().out


def test_doctor_reports_writable_and_ruff(capsys):
    assert main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "results directory writable" in out and "ruff:" in out
