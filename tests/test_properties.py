import datetime
from dataclasses import replace
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from jpbench.normalize import normalize_date, normalize_number, normalize_text
from jpbench.scoring import score_task
from jpbench.task import load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"


@given(st.text(max_size=80))
@settings(max_examples=300)
def test_normalize_text_is_idempotent(value):
    once = normalize_text(value)
    assert normalize_text(once) == once


@given(st.floats(min_value=-1e9, max_value=1e9, allow_nan=False, allow_infinity=False))
def test_normalize_number_round_trips_plain_numbers(value):
    assert normalize_number(repr(value)) == value


@given(st.dates(min_value=datetime.date(1900, 1, 1), max_value=datetime.date(2100, 12, 31)))
def test_western_dates_normalize_to_iso(day):
    assert normalize_date(f"{day.year}/{day.month}/{day.day}") == day.isoformat()


@given(st.lists(st.text(min_size=1, max_size=8), max_size=10), st.lists(st.text(min_size=1, max_size=8), min_size=1, max_size=10))
@settings(max_examples=200)
def test_set_overlap_score_is_bounded(pred_items, gold_items):
    base = {t.id: t for t in load_tasks(TASKS)}["jgrants-open-subsidies"]
    t = replace(base, success=replace(base.success, min_overlap=0.5))
    r = score_task(t, {"subsidy_titles": pred_items}, {"subsidy_titles": gold_items})
    assert 0.0 <= r.score <= 1.0


@given(st.integers(min_value=0, max_value=10**12))
def test_perfect_numeric_answer_always_passes(amount):
    base = {t.id: t for t in load_tasks(TASKS)}["jgrants-open-subsidies"]
    t = replace(base, success=replace(base.success, type="numeric_tolerance", fields=["amount"], tolerance=0.0))
    assert score_task(t, {"amount": amount}, {"amount": amount}).passed
