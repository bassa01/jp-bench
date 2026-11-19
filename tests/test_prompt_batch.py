import json
from pathlib import Path

import pytest

from jpbench.cli import main
from jpbench.examples import load_examples
from jpbench.prompt import render_prompt
from jpbench.task import TaskError, load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"


def _task(tid="invoice-number-verify"):
    return {t.id: t for t in load_tasks(TASKS)}[tid]


def test_examples_render_in_each_language(tmp_path):
    t = _task()
    ex = [{"input": {"registration_number": "T0000000000000"}, "output": {"name": "A", "registration_date": "2020-01-01", "active": True}}]
    assert "Examples:" in render_prompt(t, examples=ex)
    assert "例:" in render_prompt(t, lang="ja", examples=ex)


def test_examples_file_is_loaded_and_checked(tmp_path):
    t = _task()
    good = [{"input": {"x": 1}, "output": {"name": "A", "registration_date": "2020-01-01", "active": True}}]
    (tmp_path / f"{t.id}.yaml").write_text(
        "- input: {x: 1}\n  output: {name: A, registration_date: '2020-01-01', active: true}\n", encoding="utf-8")
    assert load_examples(t, tmp_path) == good
    (tmp_path / f"{t.id}.yaml").write_text("- input: {}\n  output: {wrong: 1}\n", encoding="utf-8")
    with pytest.raises(TaskError, match="output keys"):
        load_examples(t, tmp_path)


def test_more_than_three_examples_rejected(tmp_path):
    t = _task()
    item = "- input: {}\n  output: {name: A, registration_date: '2020-01-01', active: true}\n"
    (tmp_path / f"{t.id}.yaml").write_text(item * 4, encoding="utf-8")
    with pytest.raises(TaskError, match="at most 3"):
        load_examples(t, tmp_path)


def test_abstain_tasks_get_not_found_instruction():
    from dataclasses import replace as r

    base = _task()
    t = r(base, success=r(base.success, type="abstain", fields=["answer"]))
    assert "not_found" in render_prompt(t)


def test_diff_and_write_with_manifest(tmp_path, capsys):
    assert main(["prompt", "invoice-number-verify", "--diff"]) == 0
    assert "--- en" in capsys.readouterr().out
    out = tmp_path / "prompts"
    assert main(["prompt", "invoice-number-verify", "--write", str(out)]) == 0
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert set(manifest) == {"invoice-number-verify.en.txt", "invoice-number-verify.ja.txt"}
    import hashlib

    for name, digest in manifest.items():
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == digest
