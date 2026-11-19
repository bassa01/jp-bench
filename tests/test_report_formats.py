import csv
import io
import json
from pathlib import Path

from jpbench.cli import _csv_report, _html_report, _json_report, _markdown_report, main
from jpbench.scoring import TaskResult, summarize
from jpbench.task import load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"
GOLD_ROW = {"name": "株式会社サンプル商事", "registration_date": "2020-01-01", "active": True}


def _results():
    return [TaskResult("invoice-number-verify", True, 1.0, "<b>wrong</b>, \"quoted\", x|y")]


def _summary(results):
    return summarize(results, {"invoice-number-verify": "easy"})


def _files(tmp_path, pred_row, gold_row, key="invoice-number-verify"):
    pred = tmp_path / "p.json"
    gold = tmp_path / "g.json"
    pred.write_text(json.dumps({key: pred_row}, ensure_ascii=False), encoding="utf-8")
    gold.write_text(json.dumps({key: gold_row}, ensure_ascii=False), encoding="utf-8")
    return str(pred), str(gold)


def test_json_report_has_schema_version(tmp_path, capsys):
    p, g = _files(tmp_path, GOLD_ROW, GOLD_ROW)
    assert main(["report", "--pred", p, "--gold", g, "--format", "json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["schema_version"] == 1 and data["summary"]["passed"] == 1
    assert data["results"][0]["field_results"]["name"] is True


def test_json_helper_keeps_detail_text():
    data = json.loads(_json_report(_results(), _summary(_results())))
    assert data["results"][0]["detail"].startswith("<b>wrong</b>")


def test_html_escapes_markup_and_has_no_scripts():
    out = _html_report(_results(), _summary(_results()))
    assert out.startswith("<!doctype html>") and "<script" not in out
    assert "&lt;b&gt;wrong&lt;/b&gt;" in out and "<b>wrong" not in out


def test_markdown_escapes_pipes_in_cells():
    tasks = list(load_tasks(TASKS))
    out = _markdown_report(tasks, _results(), _summary(_results()))
    assert "x\\|y" in out


def test_csv_quotes_commas_and_quotes():
    rows = list(csv.reader(io.StringIO(_csv_report(_results()))))
    assert rows[1][3] == '<b>wrong</b>, "quoted", x|y'


def test_no_gold_is_an_empty_run(tmp_path):
    _p, g = _files(tmp_path, GOLD_ROW, GOLD_ROW)
    empty = tmp_path / "empty_gold.json"
    empty.write_text("{}", encoding="utf-8")
    assert main(["report", "--pred", g, "--gold", str(empty)]) == 1


def test_all_pass_and_all_fail_summaries(tmp_path, capsys):
    p, g = _files(tmp_path, GOLD_ROW, GOLD_ROW)
    main(["report", "--pred", p, "--gold", g])
    assert "Passed 1/1 (100.0%" in capsys.readouterr().out
    p2, g2 = _files(tmp_path, {"name": "x"}, GOLD_ROW)
    main(["report", "--pred", p2, "--gold", g2])
    assert "Passed 0/1 (0.0%" in capsys.readouterr().out
