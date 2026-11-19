"""Turn raw model output into a JSON answer."""

from __future__ import annotations

import json
import re
from typing import Any

MAX_OUTPUT_CHARS = 200_000

_REASONING_RE = re.compile(r"<(think|thinking|reasoning)>.*?</\1>", re.DOTALL)
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)
_LABEL_RE = re.compile(r"^\s*(?:Answer|回答)\s*[:：]\s*", re.IGNORECASE)
_FULLWIDTH_JSON = str.maketrans({"｛": "{", "｝": "}", "＂": '"', "［": "[", "］": "]"})
_REFUSAL_PATTERNS = [
    "申し訳",
    "お手伝いできません",
    "アクセスできません",
    "I can't",
    "I cannot",
    "I'm unable",
    "I am unable",
    "I don't have access",
]


class ParseError(ValueError):
    """Model output could not be turned into a JSON object. Keeps the raw text."""

    def __init__(self, message: str, raw: str) -> None:
        super().__init__(message)
        self.raw = raw


def strip_reasoning(text: str) -> str:
    """Remove <think>, <thinking> and <reasoning> blocks before parsing."""
    return _REASONING_RE.sub("", text).strip()


def _reject_constant(name: str) -> Any:
    raise ValueError(f"{name} is not allowed in JSON answers")


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate key {key!r}")
        out[key] = value
    return out


def extract_json(text: str) -> dict[str, Any]:
    """Return the first JSON object in the output, preferring a fenced block."""
    if len(text) > MAX_OUTPUT_CHARS:
        raise ParseError(f"model output is {len(text)} chars, limit is {MAX_OUTPUT_CHARS}", "")
    cleaned = _LABEL_RE.sub("", strip_reasoning(text)).translate(_FULLWIDTH_JSON)
    fenced = _FENCE_RE.search(cleaned)
    candidate = fenced.group(1) if fenced else cleaned
    if candidate.strip().startswith("["):
        raise TypeError("model output JSON is not an object")
    start, end = candidate.find("{"), candidate.rfind("}")
    if start == -1 or end < start:
        raise ParseError("no JSON object in model output", text)
    try:
        value = json.loads(
            candidate[start : end + 1],
            parse_constant=_reject_constant,
            object_pairs_hook=_no_duplicate_keys,
        )
    except json.JSONDecodeError as exc:
        raise ParseError(f"invalid JSON at char {exc.pos}: {exc.msg}", text) from exc
    except ValueError as exc:
        raise ParseError(str(exc), text) from exc
    return value


def find_refusal(text: str) -> str | None:
    """Return the refusal phrase found in the output, or None."""
    lowered = text.lower()
    for phrase in _REFUSAL_PATTERNS:
        if phrase.lower() in lowered:
            return phrase
    return None


def looks_like_refusal(text: str) -> bool:
    return find_refusal(text) is not None


def answer_kind(text: str) -> str:
    """Classify an output as refusal, empty, json, or invalid."""
    if not text.strip():
        return "empty"
    if looks_like_refusal(text):
        return "refusal"
    try:
        extract_json(text)
    except (ParseError, TypeError):
        return "invalid"
    return "json"
