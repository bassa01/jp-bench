"""Turn raw model output into a JSON answer."""

from __future__ import annotations

import json
import re
from typing import Any

_REASONING_RE = re.compile(r"<(think|thinking)>.*?</\1>", re.DOTALL)
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)
_REFUSAL_PATTERNS = [
    "申し訳",
    "お手伝いできません",
    "I can't",
    "I cannot",
    "I'm unable",
    "I am unable",
]


def strip_reasoning(text: str) -> str:
    """Remove <think>...</think> style reasoning blocks before parsing."""
    return _REASONING_RE.sub("", text).strip()


def extract_json(text: str) -> dict[str, Any]:
    """Return the first JSON object in the output, preferring a fenced block."""
    cleaned = strip_reasoning(text)
    fenced = _FENCE_RE.search(cleaned)
    candidate = fenced.group(1) if fenced else cleaned
    if candidate.strip().startswith("["):
        raise TypeError("model output JSON is not an object")
    start, end = candidate.find("{"), candidate.rfind("}")
    if start == -1 or end < start:
        raise ValueError("no JSON object in model output")
    value = json.loads(candidate[start : end + 1])
    if not isinstance(value, dict):
        raise TypeError("model output JSON is not an object")
    return value


def looks_like_refusal(text: str) -> bool:
    return any(p in text for p in _REFUSAL_PATTERNS)
