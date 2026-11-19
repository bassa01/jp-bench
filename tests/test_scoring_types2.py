from dataclasses import replace
from pathlib import Path

import pytest

from jpbench.scoring import score_task
from jpbench.task import load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"


@pytest.fixture(scope="module")
def base():
    return {t.id: t for t in load_tasks(TASKS)}["invoice-number-verify"]


def _as(base, kind, fields, **extra):
    return replace(base, success=replace(base.success, type=kind, fields=fields, **extra))


def test_date_range_open_ended(base):
    t = _as(base, "date_range", ["start_date", "end_date"])
    gold = {"start_date": "令和9年4月1日", "end_date": "無期限"}
    assert score_task(t, {"start_date": "2027-04-01", "end_date": "無期限"}, gold).passed
    assert score_task(t, {"start_date": "2027-04-01", "end_date": "2028-03-31"}, gold).score == 0.5


def test_enum_maps_labels_and_rejects_unknown(base):
    from dataclasses import replace as r

    t = _as(base, "enum", ["kind"], labels={"株式会社": "corp", "個人": "person"})
    assert score_task(t, {"kind": "株式会社"}, {"kind": "corp"}).passed
    bad = score_task(t, {"kind": "団体"}, {"kind": "corp"})
    assert not bad.passed and "valid: 個人, 株式会社" in bad.detail
    assert r is not None


def test_multi_answer_records_matched_option(base):
    t = _as(base, "multi_answer", ["address"])
    r = score_task(t, {"address": "東京都千代田区"}, {"address": ["東京都千代田区", "千代田区"]})
    assert r.passed and "matched option: 東京都千代田区" in r.detail


def test_abstain_rewards_not_found_and_penalises_invention(base):
    t = _as(base, "abstain", ["answer"])
    assert score_task(t, {"answer": "not_found"}, {"answer": "not_found"}).passed
    invented = score_task(t, {"answer": "東京都"}, {"answer": "not_found"})
    assert not invented.passed and "invented" in invented.detail
