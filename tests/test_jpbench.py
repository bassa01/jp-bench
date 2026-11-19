from pathlib import Path

import pytest

from jpbench.normalize import normalize_date, normalize_number, normalize_text
from jpbench.prompt import render_prompt
from jpbench.scoring import score_task
from jpbench.task import TaskError, load_tasks, parse_task

TASKS = Path(__file__).resolve().parent.parent / "tasks"


@pytest.fixture(scope="module")
def tasks():
    return {t.id: t for t in load_tasks(TASKS)}


def test_all_tasks_validate(tasks):
    assert len(tasks) >= 5


def test_form_fill_tasks_stop_before_submit(tasks):
    for t in tasks.values():
        if t.category == "form_fill":
            assert t.stop_before_submit


@pytest.mark.parametrize(
    "raw,expected",
    [("㈱サンプル商事", "株式会社サンプル商事"), ("（株）サンプル商事", "株式会社サンプル商事"), ("ＡＢＣ　１２３", "ABC123")],
)
def test_normalize_text(raw, expected):
    assert normalize_text(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [("令和9年4月1日", "2027-04-01"), ("令和元年5月1日", "2019-05-01"), ("平成31年4月30日", "2019-04-30"), ("2027/4/1", "2027-04-01")],
)
def test_normalize_date(raw, expected):
    assert normalize_date(raw) == expected


def test_normalize_number():
    assert normalize_number("１，２３４円") == 1234.0


def test_form_fill_passes_with_variant_notation(tasks):
    t = tasks["egov-36kyotei-fill"]
    gold = {"employer_name": "株式会社サンプル商事", "agreement_start_date": "令和9年4月1日"}
    pred = {
        "state": "confirmation",
        "submitted": False,
        "entered": {"employer_name": "(株)サンプル商事", "agreement_start_date": "2027-04-01"},
    }
    assert score_task(t, pred, gold).passed


def test_form_fill_submit_is_safety_violation(tasks):
    t = tasks["egov-36kyotei-fill"]
    gold = {"employer_name": "株式会社サンプル商事"}
    pred = {"state": "confirmation", "submitted": True, "entered": dict(gold)}
    result = score_task(t, pred, gold)
    assert not result.passed and "SAFETY" in result.detail


def test_set_overlap(tasks):
    t = tasks["jgrants-open-subsidies"]
    gold = {"subsidy_titles": ["A補助金", "B補助金", "C補助金", "D補助金", "E補助金"]}
    good = {"subsidy_titles": ["A補助金", "B補助金", "C補助金", "D補助金"]}
    bad = {"subsidy_titles": ["A補助金"]}
    assert score_task(t, good, gold).passed
    assert not score_task(t, bad, gold).passed


def test_field_match_partial(tasks):
    t = tasks["houjin-bangou-lookup"]
    gold = {"corporate_number": "1234567890123", "address": "東京都千代田区"}
    pred = {"corporate_number": "１２３４５６７８９０１２３", "address": "大阪府"}
    r = score_task(t, pred, gold)
    assert not r.passed and r.score == 0.5


def test_missing_prediction(tasks):
    assert not score_task(tasks["egov-law-article"], None, {"law_number": "x", "article_text": "y"}).passed


def test_validator_rejects_unsafe_form_fill():
    raw = {
        "id": "bad", "title_ja": "x", "title_en": "x",
        "portal": {"name_ja": "x", "url": "https://example.go.jp/", "operator": "x"},
        "category": "form_fill", "difficulty": "easy",
        "instructions_ja": "x", "instructions_en": "x", "inputs": {},
        "success": {"type": "reached_state", "state": "confirmation"},
        "safety": {"stop_before_submit": False},
    }
    with pytest.raises(TaskError):
        parse_task(raw)


def test_prompt_includes_safety_line(tasks):
    text = render_prompt(tasks["egov-36kyotei-fill"])
    assert "Do NOT press the final submit" in text
