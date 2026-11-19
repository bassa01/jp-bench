from pathlib import Path

import pytest

from jpbench.task import TaskError, load_tasks, parse_task

TASKS = Path(__file__).resolve().parent.parent / "tasks"


def base(**over):
    raw = {
        "id": "sample-task", "title_ja": "サンプル", "title_en": "Sample",
        "portal": {"name_ja": "x", "url": "https://example.go.jp/a", "operator": "x"},
        "category": "lookup", "difficulty": "easy",
        "instructions_ja": "検索する", "instructions_en": "Search.",
        "inputs": {"corporate_number": "1234567890123"}, "success": {"type": "field_match", "fields": ["name"]},
        "safety": {"stop_before_submit": False}, "gold_source": "example",
    }
    raw.update(over)
    return raw


def test_budgets_and_domains_parse():
    t = parse_task(base(max_steps=20, timeout_seconds=300, allowed_domains=["example.go.jp"]))
    assert t.max_steps == 20 and t.timeout_seconds == 300 and t.allowed_domains == ("example.go.jp",)
    assert t.is_read_only and not t.is_form_fill and not t.requires_login


@pytest.mark.parametrize("over,msg", [
    ({"max_steps": 0}, "max_steps"),
    ({"timeout_seconds": 1801}, "timeout_seconds"),
    ({"allowed_domains": ["example.go.jp/a"]}, "bare host names"),
    ({"allowed_domains": ["other.go.jp"]}, "must include the portal host"),
    ({"inputs": {"x": {"nested": 1}}}, "scalar or list"),
    ({"inputs": {"phone": "090-1234-5678"}}, "mobile phone"),
    ({"auth_method": "idpw"}, "requires safety.auth_required"),
    ({"safety": {"stop_before_submit": False, "auth_required": True}}, "must declare auth_method"),
    ({"safety": {"stop_before_submit": False, "auth_required": True}, "auth_method": "magic"}, "auth_method must be one of"),
])
def test_budget_and_safety_rules(over, msg):
    with pytest.raises(TaskError, match=msg):
        parse_task(base(**over))


def test_form_fill_must_use_reached_state():
    raw = base(category="form_fill", safety={"stop_before_submit": True})
    with pytest.raises(TaskError, match="reached_state"):
        parse_task(raw)


def test_auth_tasks_parse_with_method():
    t = parse_task(base(safety={"stop_before_submit": False, "auth_required": True}, auth_method="gbizid"))
    assert t.requires_login and t.auth_method == "gbizid"


def test_bundled_tasks_still_valid():
    assert len(load_tasks(TASKS)) == 5
