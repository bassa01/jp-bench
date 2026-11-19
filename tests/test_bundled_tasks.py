import json
from dataclasses import replace
from pathlib import Path

import pytest

from jpbench.prompt import MAX_PROMPT_CHARS, render_prompt
from jpbench.scoring import score_task
from jpbench.task import SUCCESS_TYPES, load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"
ALL = list(load_tasks(TASKS))
FORBIDDEN = ["captcha", "bypass", "paid", "purchase", "有料", "課金", "迂回", "回避"]


@pytest.mark.parametrize("task", ALL, ids=lambda t: t.id)
def test_prompt_names_every_success_field(task):
    text = render_prompt(task)
    for name in task.success.fields:
        assert f'"{name}"' in text


@pytest.mark.parametrize("task", ALL, ids=lambda t: t.id)
def test_prompt_carries_every_input_exactly(task):
    text = render_prompt(task)
    assert json.dumps(task.inputs, ensure_ascii=False, indent=2) in text


@pytest.mark.parametrize("task", ALL, ids=lambda t: t.id)
def test_prompt_is_within_length_limit_in_both_languages(task):
    assert len(render_prompt(task, "en")) <= MAX_PROMPT_CHARS
    assert len(render_prompt(task, "ja")) <= MAX_PROMPT_CHARS


@pytest.mark.parametrize("task", ALL, ids=lambda t: t.id)
def test_both_languages_are_non_empty(task):
    assert task.instructions_en.strip() and task.instructions_ja.strip()


@pytest.mark.parametrize("task", ALL, ids=lambda t: t.id)
def test_instructions_do_not_invite_bypass_or_paid_access(task):
    text = (task.instructions_en + task.instructions_ja).lower()
    assert not any(word in text for word in FORBIDDEN)


@pytest.mark.parametrize("task", ALL, ids=lambda t: t.id)
def test_form_tasks_repeat_the_safety_line(task):
    if task.stop_before_submit:
        assert "Do NOT press the final submit" in render_prompt(task)


def _case(base, kind, fields, gold, good, bad, **extra):
    t = replace(base, success=replace(base.success, type=kind, fields=fields, **extra))
    return t, gold, good, bad


def _cases():
    base = {t.id: t for t in ALL}["invoice-number-verify"]
    return {
        "field_match": _case(base, "field_match", ["name"], {"name": "A"}, {"name": "A"}, {"name": "B"}),
        "numeric_tolerance": _case(base, "numeric_tolerance", ["amount"], {"amount": 100}, {"amount": 100}, {"amount": 1}, tolerance=0.01),
        "set_overlap": _case(base, "set_overlap", ["items"], {"items": ["A", "B"]}, {"items": ["A", "B"]}, {"items": []}),
        "boolean": _case(base, "boolean", ["active"], {"active": True}, {"active": "はい"}, {"active": "いいえ"}),
        "date_range": _case(base, "date_range", ["start", "end"], {"start": "2027-04-01", "end": "無期限"}, {"start": "2027-04-01", "end": "無期限"}, {"start": "2020-01-01", "end": "無期限"}),
        "enum": _case(base, "enum", ["kind"], {"kind": "corp"}, {"kind": "株式会社"}, {"kind": "団体"}, labels={"株式会社": "corp"}),
        "multi_answer": _case(base, "multi_answer", ["address"], {"address": ["A", "B"]}, {"address": "B"}, {"address": "C"}),
        "abstain": _case(base, "abstain", ["answer"], {"answer": "not_found"}, {"answer": "not_found"}, {"answer": "X"}),
        "url_match": _case(base, "url_match", ["portal_url"], {"portal_url": "https://example.go.jp"}, {"portal_url": "HTTPS://example.go.jp/"}, {"portal_url": "https://other.example"}),
        "article_match": _case(base, "article_match", ["law_article"], {"law_article": "第3条"}, {"law_article": "第３条"}, {"law_article": "第4条"}),
        "law_number_match": _case(base, "law_number_match", ["law_number"], {"law_number": "令和1年法律第1号"}, {"law_number": "令和元年法律第一号"}, {"law_number": "令和2年法律第1号"}),
        "postal_code_match": _case(base, "postal_code_match", ["postal_code"], {"postal_code": "100-0012"}, {"postal_code": "1000012"}, {"postal_code": "100-0013"}),
        "phone_match": _case(base, "phone_match", ["phone"], {"phone": "03-1234-5678"}, {"phone": "0312345678"}, {"phone": "0312345679"}),
        "amount_yen_match": _case(base, "amount_yen_match", ["amount"], {"amount": 1000}, {"amount": "1,000円"}, {"amount": "2000"}),
    }


@pytest.mark.parametrize("kind", sorted(k for k in SUCCESS_TYPES if k != "reached_state"))
def test_every_success_type_has_passing_and_failing_sample(kind):
    t, gold, good, bad = _cases()[kind]
    assert score_task(t, good, gold).passed
    assert not score_task(t, bad, gold).passed
