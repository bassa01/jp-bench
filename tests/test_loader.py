from pathlib import Path

import pytest

from jpbench.task import TaskError, load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"


def test_underscore_templates_are_skipped(tmp_path):
    src = (TASKS / "invoice-number-verify.yaml").read_text(encoding="utf-8")
    (tmp_path / "invoice-number-verify.yaml").write_text(src, encoding="utf-8")
    (tmp_path / "_template.yaml").write_text("not: valid\n", encoding="utf-8")
    assert [t.id for t in load_tasks(tmp_path)] == ["invoice-number-verify"]
