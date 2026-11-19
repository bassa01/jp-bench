"""Model adapter interface. Real adapters call a model API; FixedAdapter is offline."""

from __future__ import annotations

import subprocess
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


class SubprocessAdapter:
    """Runs a local command with the prompt on stdin. The command must be on an explicit allowlist."""

    name = "subprocess"

    def __init__(self, argv: list[str], allowlist: set[str], timeout: float = 30.0) -> None:
        if not argv or argv[0] not in allowlist:
            raise ValueError(f"command {argv[0] if argv else ''!r} is not on the allowlist")
        self.argv = list(argv)
        self.timeout = timeout

    def complete(self, prompt: str) -> str:
        proc = subprocess.run(
            self.argv,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=self.timeout,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"exit {proc.returncode}: {proc.stderr.strip()[:200]}")
        return proc.stdout
