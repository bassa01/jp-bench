from dataclasses import replace
from pathlib import Path

import pytest

from jpbench.browser import (
    GuardrailError,
    ScriptedBrowserAgent,
    Step,
    check_navigation,
    redact_value,
    run_guarded,
    summarize_steps,
    write_trace,
)
from jpbench.task import load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"


def _task(tid, **extra):
    """Bundled task with the guardrail fields set, since the bundled files leave them empty."""
    base = {t.id: t for t in load_tasks(TASKS)}[tid]
    return replace(base, **extra)


def _nta():
    return _task("houjin-bangou-lookup", allowed_domains=("nta.go.jp",), max_steps=5)


def test_navigation_inside_allowed_domains_is_fine():
    t = _nta()
    steps = [Step("navigate", url="https://www.houjin-bangou.nta.go.jp/")]
    assert run_guarded(ScriptedBrowserAgent(steps), t) == steps


def test_navigation_outside_allowed_domains_is_blocked():
    t = _nta()
    with pytest.raises(GuardrailError, match="outside allowed_domains"):
        run_guarded(ScriptedBrowserAgent([Step("navigate", url="https://evil.example/")]), t)


def test_suffix_lookalike_domain_is_not_allowed():
    with pytest.raises(GuardrailError):
        check_navigation("https://notnta.go.jp.evil.example/", ("nta.go.jp",))


def test_step_budget_is_enforced():
    t = _nta()
    steps = [Step("navigate", url="https://www.nta.go.jp/")] + [Step("click")] * 5
    with pytest.raises(GuardrailError, match="max_steps"):
        run_guarded(ScriptedBrowserAgent(steps), t)


def test_submit_on_form_task_is_blocked():
    t = _task("egov-36kyotei-fill", allowed_domains=("e-gov.go.jp",))
    with pytest.raises(GuardrailError, match="stop before submit"):
        run_guarded(ScriptedBrowserAgent([Step("navigate", url="https://shinsei.e-gov.go.jp/"), Step("submit")]), t)


def test_trace_is_jsonl_with_screenshot_paths_and_size_cap(tmp_path):
    steps = [Step("navigate", url="https://a.go.jp/", screenshot="s1.png"), Step("click", target="next")]
    out = tmp_path / "trace.jsonl"
    assert write_trace(out, steps) == 2
    assert out.read_text(encoding="utf-8").splitlines()[0].startswith("{")
    with pytest.raises(GuardrailError, match="cap"):
        write_trace(tmp_path / "big.jsonl", steps, max_bytes=10)


def test_personal_values_are_redacted_by_field_name():
    assert redact_value("090-1234-5678", "phone_number") == "[redacted]"
    assert redact_value("T0000000000000", "registration_number") == "T0000000000000"


def test_summary_counts_actions():
    s = summarize_steps([Step("navigate"), Step("click"), Step("click")])
    assert s == {"steps": 3, "by_action": {"click": 2, "navigate": 1}}
