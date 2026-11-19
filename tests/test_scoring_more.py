from pathlib import Path

import pytest

from jpbench.scoring import score_task
from jpbench.task import load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"


@pytest.fixture(scope="module")
def tasks():
    return {t.id: t for t in load_tasks(TASKS)}


def test_null_prediction_is_empty_not_the_word_none(tasks):
    t = tasks["invoice-number-verify"]
    gold = {"name": "A", "registration_date": "2020-01-01", "active": True}
    r = score_task(t, {"name": None, "registration_date": "2020-01-01", "active": True}, gold)
    assert not r.passed and "name" in r.detail


def test_set_overlap_reports_counts(tasks):
    t = tasks["jgrants-open-subsidies"]
    r = score_task(t, {"subsidy_titles": ["A", "X"]}, {"subsidy_titles": ["A", "B"]})
    assert "tp=1 fp=1 fn=1" in r.detail


def test_set_overlap_non_list_fails(tasks):
    t = tasks["jgrants-open-subsidies"]
    r = score_task(t, {"subsidy_titles": "A"}, {"subsidy_titles": ["A"]})
    assert not r.passed and "must be a list" in r.detail


def test_set_overlap_empty_gold_and_empty_prediction(tasks):
    t = tasks["jgrants-open-subsidies"]
    assert score_task(t, {"subsidy_titles": []}, {"subsidy_titles": []}).passed


def test_set_overlap_empty_prediction_scores_zero(tasks):
    t = tasks["jgrants-open-subsidies"]
    r = score_task(t, {"subsidy_titles": []}, {"subsidy_titles": ["A"]})
    assert not r.passed and r.score == 0.0


def test_numeric_detail_shows_signed_difference(tasks):
    from dataclasses import replace

    base = tasks["jgrants-open-subsidies"]
    t = replace(base, success=replace(base.success, type="numeric_tolerance", fields=["amount"], tolerance=0.01))
    r = score_task(t, {"amount": 90}, {"amount": 100})
    assert not r.passed and "amount (diff -10)" in r.detail


def test_numeric_nan_fails(tasks):
    from dataclasses import replace

    base = tasks["jgrants-open-subsidies"]
    t = replace(base, success=replace(base.success, type="numeric_tolerance", fields=["amount"], tolerance=0.1))
    assert not score_task(t, {"amount": "nan"}, {"amount": 100}).passed


def test_reached_state_names_wrong_field(tasks):
    t = tasks["egov-36kyotei-fill"]
    gold = {"employer_name": "株式会社サンプル商事", "agreement_start_date": "令和9年4月1日"}
    pred = {"state": "confirmation", "submitted": False, "entered": {"employer_name": "株式会社別", "agreement_start_date": "2027-04-01"}}
    r = score_task(t, pred, gold)
    assert not r.passed and "wrong: employer_name" in r.detail
