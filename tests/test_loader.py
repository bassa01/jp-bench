from pathlib import Path

import pytest

from jpbench.task import TaskError, load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"


def test_underscore_templates_are_skipped(tmp_path):
    src = (TASKS / "invoice-number-verify.yaml").read_text(encoding="utf-8")
    (tmp_path / "invoice-number-verify.yaml").write_text(src, encoding="utf-8")
    (tmp_path / "_template.yaml").write_text("not: valid\n", encoding="utf-8")
    assert [t.id for t in load_tasks(tmp_path)] == ["invoice-number-verify"]


def test_yaml_error_names_file_and_line(tmp_path):
    (tmp_path / "broken.yaml").write_text("id: x\n  bad: [\n", encoding="utf-8")
    with pytest.raises(TaskError, match=r"broken\.yaml: YAML parse error at line"):
        load_tasks(tmp_path)


def test_non_mapping_file_rejected(tmp_path):
    (tmp_path / "list.yaml").write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(TaskError, match="top level must be a mapping"):
        load_tasks(tmp_path)
