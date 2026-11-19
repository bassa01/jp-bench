from pathlib import Path

import pytest

from jpbench.prompt import render_prompt
from jpbench.task import load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"
ALL = list(load_tasks(TASKS))


@pytest.mark.parametrize("task", ALL, ids=lambda t: t.id)
def test_english_instructions_avoid_please(task):
    assert "please" not in task.instructions_en.lower()


@pytest.mark.parametrize("task", ALL, ids=lambda t: t.id)
def test_prompt_ends_with_output_format_line(task):
    last = render_prompt(task).splitlines()[-1]
    assert last.startswith("Answer with JSON")


@pytest.mark.parametrize("task", ALL, ids=lambda t: t.id)
def test_bundled_tasks_have_source_and_dates(task):
    assert task.source_documents and task.created and task.updated
    assert task.review_status == "draft"
