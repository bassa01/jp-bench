"""Render a task as a prompt for a browser agent such as a Devin Bot session."""

from __future__ import annotations

import hashlib
import json

from .task import Task

MAX_PROMPT_CHARS = 8000
PROMPT_TEMPLATE_VERSION = "1"

_SAFETY_LINE = (
    "SAFETY: Do NOT press the final submit / 送信 / 提出 button. "
    "Stop on the confirmation screen and report the state."
)


def render_prompt(task: Task, lang: str = "en") -> str:
    instructions = task.instructions_en if lang == "en" else task.instructions_ja
    lines = [
        f"# JP-Bench task: {task.id}",
        f"Template: jpbench-prompt/{PROMPT_TEMPLATE_VERSION}",
        f"Portal: {task.portal.name_ja} ({task.portal.url}), operated by {task.portal.operator}",
        "",
        instructions,
        "",
        "Inputs:",
        json.dumps(task.inputs, ensure_ascii=False, indent=2),
        "",
    ]
    if task.stop_before_submit:
        lines += [_SAFETY_LINE, ""]
    if task.success.type == "reached_state":
        lines.append(
            'Answer with JSON: {"state": "<screen you stopped on>", '
            '"submitted": false, "entered": {<field>: <value>}}'
        )
    else:
        keys = ", ".join(f'"{f}": ...' for f in task.success.fields)
        lines.append(f"Answer with JSON only (no text before or after the object): {{{keys}}}")
    text = "\n".join(line.rstrip() for line in "\n".join(lines).split("\n"))
    return text


def prompt_hash(task: Task, lang: str = "en") -> str:
    """Short stable fingerprint of the rendered prompt, stored with results for reproducibility."""
    return hashlib.sha256(render_prompt(task, lang).encode("utf-8")).hexdigest()[:16]


def check_prompt_length(text: str, limit: int = MAX_PROMPT_CHARS) -> str:
    """Refuse to hand a truncated or oversized prompt to a model."""
    if len(text) > limit:
        raise ValueError(f"prompt is {len(text)} chars, limit is {limit}")
    return text
