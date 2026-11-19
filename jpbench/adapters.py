"""Model adapter interface. Real adapters call a model API; FixedAdapter is offline."""

from __future__ import annotations

from typing import Any, Protocol

from .parse import extract_json
from .prompt import render_prompt
from .task import Task


class ModelAdapter(Protocol):
    name: str

    def complete(self, prompt: str) -> str:
        """Return the raw text output for a prompt."""
        ...


class FixedAdapter:
    """Returns the same canned output every time. Used for dry runs and tests."""

    name = "fixed"

    def __init__(self, output: str) -> None:
        self.output = output

    def complete(self, prompt: str) -> str:
        return self.output


def run_task(adapter: ModelAdapter, task: Task, lang: str = "en") -> dict[str, Any]:
    """Render the task, call the adapter, and parse its JSON answer."""
    return extract_json(adapter.complete(render_prompt(task, lang=lang)))
