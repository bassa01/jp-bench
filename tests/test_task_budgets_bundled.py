from pathlib import Path

import pytest

from jpbench.task import load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"
ALL = list(load_tasks(TASKS))


@pytest.mark.parametrize("task", ALL, ids=lambda t: t.id)
def test_every_bundled_task_sets_budgets(task):
    assert 1 <= task.max_steps <= 200
    assert 1 <= task.timeout_seconds <= 1800


@pytest.mark.parametrize("task", ALL, ids=lambda t: t.id)
def test_allowed_domains_include_the_portal_host(task):
    from urllib.parse import urlsplit

    host = urlsplit(task.portal.url).hostname
    assert host in task.allowed_domains
