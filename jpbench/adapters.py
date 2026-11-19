"""Model adapter interface. Real adapters call a model API; FixedAdapter is offline."""

from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from typing import Any, Protocol
from urllib.parse import urlsplit

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


LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _checked_base(url: str) -> str:
    """https is required; plain http is allowed only for a local host (for stubs and local servers)."""
    parts = urlsplit(url)
    if parts.scheme == "https" and parts.hostname:
        return url
    if parts.scheme == "http" and parts.hostname in LOCAL_HOSTS:
        return url
    raise ValueError("base_url must be https (http is allowed only for localhost)")


def _redact(text: str, secret: str) -> str:
    return text.replace(secret, "[redacted]") if secret else text


class HTTPAdapter:
    """Base for JSON-over-HTTP model APIs. Keys come from the environment only and never appear in errors."""

    name = "http"

    def __init__(self, base_url: str, model: str, api_key: str, timeout: float = 60.0) -> None:
        self.base_url = _checked_base(base_url)
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    @classmethod
    def from_env(cls, prefix: str = "JPBENCH") -> Any:
        key = os.environ.get(f"{prefix}_API_KEY", "")
        if not key:
            raise RuntimeError(f"set {prefix}_API_KEY in the environment (keys are never read from files)")
        return cls(os.environ.get(f"{prefix}_BASE_URL", ""), os.environ.get(f"{prefix}_MODEL", ""), key)

    def _post(self, path: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        request = urllib.request.Request(
            self.base_url.rstrip("/") + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", **headers},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise RuntimeError(_redact(f"{type(exc).__name__}: {exc}", self.api_key)) from None


class OpenAICompatibleAdapter(HTTPAdapter):
    name = "openai-compatible"

    def complete(self, prompt: str) -> str:
        data = self._post(
            "/chat/completions",
            {"model": self.model, "messages": [{"role": "user", "content": prompt}]},
            {"Authorization": f"Bearer {self.api_key}"},
        )
        return str(data["choices"][0]["message"]["content"])


class AnthropicMessagesAdapter(HTTPAdapter):
    name = "anthropic-messages"

    def complete(self, prompt: str) -> str:
        data = self._post(
            "/v1/messages",
            {"model": self.model, "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]},
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
        )
        return "".join(block.get("text", "") for block in data.get("content", []))
