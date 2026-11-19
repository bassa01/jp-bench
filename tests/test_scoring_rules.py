from dataclasses import replace
from pathlib import Path

import pytest

from jpbench.scoring import score_task
from jpbench.task import load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"


@pytest.fixture(scope="module")
def tasks():
    return {t.id: t for t in load_tasks(TASKS)}


def test_unregistered_scorer_type_fails_loudly(tasks):
    t = tasks["invoice-number-verify"]
    broken = replace(t, success=replace(t.success, type="unknown_type"))
    with pytest.raises(ValueError, match="no scorer registered"):
        score_task(broken, {"name": "x"}, {"name": "x"})


def test_empty_prediction_is_not_scored(tasks):
    t = tasks["invoice-number-verify"]
    gold = {"name": "株式会社サンプル商事", "registration_date": "2020-01-01", "active": True}
    r = score_task(t, {}, gold)
    assert not r.passed and r.score == 0.0 and r.detail == "no prediction"
