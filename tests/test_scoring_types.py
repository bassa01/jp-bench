from dataclasses import replace
from pathlib import Path

import pytest

from jpbench.scoring import score_task
from jpbench.task import load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"


@pytest.fixture(scope="module")
def invoice():
    return {t.id: t for t in load_tasks(TASKS)}["invoice-number-verify"]


def test_field_results_breakdown(invoice):
    gold = {"name": "A", "registration_date": "2020-01-01", "active": True}
    r = score_task(invoice, {"name": "A", "registration_date": "2021-01-01", "active": True}, gold)
    assert r.field_results == {"name": True, "registration_date": False, "active": True}
    assert r.confidence == 1.0


@pytest.mark.parametrize("answer,ok", [(True, True), ("はい", True), ("有", True), ("false", False), ("いいえ", False), ("maybe", False)])
def test_boolean_scoring(invoice, answer, ok):
    t = replace(invoice, success=replace(invoice.success, type="boolean", fields=["active"]))
    r = score_task(t, {"active": answer}, {"active": True})
    assert r.passed is ok


def test_boolean_false_gold(invoice):
    t = replace(invoice, success=replace(invoice.success, type="boolean", fields=["active"]))
    assert score_task(t, {"active": "いいえ"}, {"active": False}).passed
