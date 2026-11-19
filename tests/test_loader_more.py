import json
import os

import pytest

from jpbench.cli import main
from jpbench.task import TaskError, load_tasks
from tests.helpers import valid_task_yaml


def _task(dirpath, tid, extra="", suffix=None):
    """Write a task file named after its id, as the loader requires."""
    (dirpath / f"{tid}.yaml").write_text(valid_task_yaml(tid, title_suffix=suffix, extra=extra), encoding="utf-8")


def test_hidden_files_are_ignored(tmp_path):
    _task(tmp_path, "a-task")
    (tmp_path / ".scratch.yaml").write_text("not: valid\n", encoding="utf-8")
    assert [t.id for t in load_tasks(tmp_path)] == ["a-task"]


def test_bom_is_rejected(tmp_path):
    (tmp_path / "a-task.yaml").write_text("\ufeff" + valid_task_yaml("a-task"), encoding="utf-8")
    with pytest.raises(TaskError, match="byte order mark"):
        load_tasks(tmp_path)


def test_tab_indentation_names_the_line(tmp_path):
    (tmp_path / "a-task.yaml").write_text("id: a-task\n\tbad: 1\n", encoding="utf-8")
    with pytest.raises(TaskError, match="YAML parse error at line"):
        load_tasks(tmp_path)


def test_symlink_outside_directory_is_rejected(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "x-task.yaml").write_text(valid_task_yaml("x-task"), encoding="utf-8")
    d = tmp_path / "tasks"
    d.mkdir()
    os.symlink(outside / "x-task.yaml", d / "x-task.yaml")
    with pytest.raises(TaskError, match="symlink points outside"):
        load_tasks(d)


def test_version_newer_than_supported_is_rejected(tmp_path):
    _task(tmp_path, "a-task", extra="version: 2\n")
    with pytest.raises(TaskError, match="not supported"):
        load_tasks(tmp_path)


def test_deprecated_needs_replacement_and_unknown_replacement_rejected(tmp_path):
    _task(tmp_path, "a-task", extra="deprecated: true\n")
    with pytest.raises(TaskError, match="must name replaced_by"):
        load_tasks(tmp_path)
    _task(tmp_path, "a-task", extra="deprecated: true\nreplaced_by: missing\n")
    with pytest.raises(TaskError, match="not a known task"):
        load_tasks(tmp_path)


def test_replacement_cycle_is_rejected(tmp_path):
    _task(tmp_path, "a-task", extra="deprecated: true\nreplaced_by: b-task\n")
    _task(tmp_path, "b-task", extra="deprecated: true\nreplaced_by: c-task\n")
    _task(tmp_path, "c-task", extra="deprecated: true\nreplaced_by: b-task\n")
    with pytest.raises(TaskError, match="cycle"):
        load_tasks(tmp_path)


def test_duplicate_titles_are_rejected(tmp_path):
    _task(tmp_path, "a-task", suffix="same")
    _task(tmp_path, "b-task", suffix="same")
    with pytest.raises(TaskError, match="duplicates"):
        load_tasks(tmp_path)


def test_validate_json_and_breakdown(capsys):
    assert main(["validate", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["tasks"] == 5 and "lookup" in data["categories"] and "easy" in data["difficulties"]


def test_list_hides_deprecated_by_default(tmp_path, capsys):
    _task(tmp_path, "a-task")
    _task(tmp_path, "b-task", suffix="b", extra="deprecated: true\nreplaced_by: a-task\n")
    assert main(["--tasks", str(tmp_path), "list"]) == 0
    assert "b-task" not in capsys.readouterr().out
    assert main(["--tasks", str(tmp_path), "list", "--all"]) == 0
    assert "b-task" in capsys.readouterr().out
