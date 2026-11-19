from dataclasses import replace
from pathlib import Path

import pytest

from jpbench.scoring import score_task
from jpbench.task import TaskError, load_tasks, parse_task

TASKS = Path(__file__).resolve().parent.parent / "tasks"


@pytest.fixture(scope="module")
def tasks():
    return {t.id: t for t in load_tasks(TASKS)}


def _kind(base, kind, fields, **extra):
    return replace(base, success=replace(base.success, type=kind, fields=fields, **extra))


def test_all_or_nothing_field_match(tasks):
    t = _kind(tasks["invoice-number-verify"], "field_match", ["name", "active"], partial_credit=False)
    r = score_task(t, {"name": "A", "active": False}, {"name": "A", "active": True})
    assert r.score == 0.0 and not r.passed


def test_absolute_tolerance_at_zero_gold(tasks):
    t = _kind(tasks["jgrants-open-subsidies"], "numeric_tolerance", ["amount"], tolerance=0.5, tolerance_mode="absolute")
    assert score_task(t, {"amount": 0.4}, {"amount": 0}).passed
    assert not score_task(t, {"amount": 0.6}, {"amount": 0}).passed


def test_relative_tolerance_is_the_default(tasks):
    t = _kind(tasks["jgrants-open-subsidies"], "numeric_tolerance", ["amount"], tolerance=0.1)
    assert score_task(t, {"amount": 105}, {"amount": 100}).passed


def test_set_overlap_duplicates_do_not_count_twice(tasks):
    t = tasks["jgrants-open-subsidies"]
    assert score_task(t, {"subsidy_titles": ["A", "A"]}, {"subsidy_titles": ["A"]}).passed


def test_submitted_string_false_is_not_a_submission(tasks):
    t = tasks["egov-36kyotei-fill"]
    gold = {"employer_name": "株式会社サンプル商事"}
    pred = {"state": "confirmation", "submitted": "false", "entered": dict(gold)}
    assert score_task(t, pred, gold).passed


def test_safety_violation_wins_over_other_failures(tasks):
    t = tasks["egov-36kyotei-fill"]
    pred = {"state": "wrong", "submitted": True, "entered": {}}
    r = score_task(t, pred, {"employer_name": "株式会社サンプル商事"})
    assert r.score == 0.0 and "SAFETY VIOLATION" in r.detail


@pytest.mark.parametrize("kind,field,pred_value,gold_value", [
    ("url_match", "portal_url", "HTTPS://example.go.jp/", "https://example.go.jp"),
    ("article_match", "law_article", "第３条", "第3条"),
    ("law_number_match", "law_number", "令和元年法律第一号", "令和1年法律第1号"),
    ("postal_code_match", "postal_code", "〒1000012", "100-0012"),
    ("phone_match", "phone", "03-1234-5678", "0312345678"),
])
def test_new_normalized_match_types_use_field_rules(tasks, kind, field, pred_value, gold_value):
    t = _kind(tasks["invoice-number-verify"], kind, [field])
    assert score_task(t, {field: pred_value}, {field: gold_value}).passed


def test_amount_yen_match_compares_numbers(tasks):
    t = _kind(tasks["jgrants-open-subsidies"], "amount_yen_match", ["amount"])
    assert score_task(t, {"amount": "1,000万円"}, {"amount": 10000000}).passed


def test_bad_tolerance_mode_is_rejected():
    raw = {
        "id": "x-task", "title_ja": "サンプル", "title_en": "Sample",
        "portal": {"name_ja": "x", "url": "https://example.go.jp/", "operator": "x"},
        "category": "lookup", "difficulty": "easy", "instructions_ja": "検索", "instructions_en": "Search.",
        "inputs": {}, "success": {"type": "numeric_tolerance", "fields": ["a"], "tolerance_mode": "fuzzy"},
        "safety": {"stop_before_submit": False}, "gold_source": "example",
    }
    with pytest.raises(TaskError, match="tolerance_mode"):
        parse_task(raw)
