import json
from pathlib import Path

import pytest

from jpbench.cli import main
from jpbench.parse import ParseError, extract_json
from jpbench.prompt import render_prompt
from jpbench.task import load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"


def _task(tid="invoice-number-verify"):
    return {t.id: t for t in load_tasks(TASKS)}[tid]


def test_template_version_in_header():
    assert "Template: jpbench-prompt/1" in render_prompt(_task())


def test_json_only_instruction_is_explicit():
    assert "no text before or after the object" in render_prompt(_task())


def test_no_trailing_whitespace_and_lf_only():
    text = render_prompt(_task())
    assert all(line == line.rstrip() for line in text.split("\n")) and "\r" not in text


def test_render_is_byte_stable():
    assert render_prompt(_task()) == render_prompt(_task())


def test_japanese_rendering_uses_japanese_instructions():
    ja = render_prompt(_task(), lang="ja")
    assert "登録番号" in ja


def test_braces_in_inputs_survive_rendering():
    from dataclasses import replace

    t = replace(_task(), inputs={"note": "{x} and }{"})
    assert '"note": "{x} and }{"' in render_prompt(t)


def test_prompt_json_command(capsys):
    assert main(["prompt", "invoice-number-verify", "--json"]) == 0
    row = json.loads(capsys.readouterr().out)
    assert row["task_id"] == "invoice-number-verify" and len(row["hash"]) == 16 and row["prompt"]


def test_trailing_explanation_after_object_is_ignored():
    assert extract_json('{"a": 1} Explanation: this is why') == {"a": 1}


def test_parse_error_reports_character_position():
    with pytest.raises(ParseError, match="char"):
        extract_json('{"a": 1,}')
