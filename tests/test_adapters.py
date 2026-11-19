from pathlib import Path

import pytest

from jpbench.adapters import FixedAdapter, run_task
from jpbench.task import load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"


def test_run_task_parses_fixed_output():
    t = {x.id: x for x in load_tasks(TASKS)}["invoice-number-verify"]
    adapter = FixedAdapter('```json\n{"name": "A", "registration_date": "2020-01-01", "active": true}\n```')
    assert run_task(adapter, t)["active"] is True


def test_run_task_rejects_non_json_output():
    t = {x.id: x for x in load_tasks(TASKS)}["invoice-number-verify"]
    with pytest.raises(ValueError):
        run_task(FixedAdapter("I cannot do that"), t)
