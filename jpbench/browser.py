"""Guardrails for browser agents: recorded steps, allowed domains, step budgets, and no submission on form tasks.

A browser agent is any object with a `name` and `run(task) -> list[Step]`. The benchmark never
submits a form, and these checks stop a run that tries to.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlsplit

from .task import Task

MAX_TRACE_BYTES = 200_000
SENSITIVE_KEY_HINTS = ("phone", "tel", "email", "mail", "address", "postal", "zip", "birth", "name")


class GuardrailError(RuntimeError):
    """A browser run broke a benchmark rule."""


@dataclass(frozen=True)
class Step:
    action: str  # navigate, click, type, submit, or screenshot
    url: str = ""
    target: str = ""
    value_key: str = ""  # the name of the field typed into; never the value itself
    screenshot: str = ""


class BrowserAgent(Protocol):
    name: str

    def run(self, task: Task) -> list[Step]:
        """Drive the portal for one task and return the recorded steps."""
        ...


class ScriptedBrowserAgent:
    """Replays a fixed list of steps. Used to test guardrails without a browser."""

    name = "scripted"

    def __init__(self, steps: list[Step]) -> None:
        self.steps = list(steps)

    def run(self, task: Task) -> list[Step]:
        return list(self.steps)


def check_navigation(url: str, allowed_domains: tuple[str, ...]) -> None:
    if not allowed_domains:
        raise GuardrailError("task declares no allowed_domains")
    host = (urlsplit(url).hostname or "").lower()
    if not any(host == d or host.endswith("." + d) for d in allowed_domains):
        raise GuardrailError(f"navigation to {host!r} is outside allowed_domains")


def check_budget(steps: list[Step], max_steps: int) -> None:
    if max_steps and len(steps) > max_steps:
        raise GuardrailError(f"{len(steps)} steps exceeds max_steps {max_steps}")


def check_submission(task: Task, steps: list[Step]) -> None:
    if task.stop_before_submit and any(s.action == "submit" for s in steps):
        raise GuardrailError("form task must stop before submit")


def run_guarded(agent: BrowserAgent, task: Task) -> list[Step]:
    """Run the agent, then apply every guardrail to the steps it recorded."""
    steps = list(agent.run(task))
    for step in steps:
        if step.action == "navigate":
            check_navigation(step.url, task.allowed_domains)
    check_budget(steps, task.max_steps)
    check_submission(task, steps)
    return steps


def redact_value(value: str, key: str) -> str:
    """Hide values typed into fields that look personal, so traces never carry them."""
    return "[redacted]" if any(hint in key.lower() for hint in SENSITIVE_KEY_HINTS) else value


def write_trace(path: Path | str, steps: list[Step], max_bytes: int = MAX_TRACE_BYTES) -> int:
    lines = [json.dumps(asdict(s), ensure_ascii=False) for s in steps]
    text = "\n".join(lines) + "\n" if lines else ""
    if len(text.encode("utf-8")) > max_bytes:
        raise GuardrailError(f"trace exceeds the {max_bytes}-byte cap")
    Path(path).write_text(text, encoding="utf-8")
    return len(lines)


def summarize_steps(steps: list[Step]) -> dict[str, Any]:
    counts = Counter(s.action for s in steps)
    return {"steps": len(steps), "by_action": dict(sorted(counts.items()))}
