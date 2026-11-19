"""Render a task as a prompt for a browser agent such as a Devin Bot session."""

from __future__ import annotations

import hashlib
import json

from .task import Task

_SAFETY_LINE = (
    "SAFETY: Do NOT press the final submit / 送信 / 提出 button. "
    "Stop on the confirmation screen and report the state."
)


def render_prompt(task: Task, lang: str = "en") -> str:
    instructions = task.instructions_en if lang == "en" else task.instructions_ja
    lines = [
        f"# JP-Bench task: {task.id}",
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
        lines.append(f"Answer with JSON only: {{{keys}}}")
    return "\n".join(lines)


def prompt_hash(task: Task, lang: str = "en") -> str:
    """Short stable fingerprint of the rendered prompt, stored with results for reproducibility."""
    return hashlib.sha256(render_prompt(task, lang).encode("utf-8")).hexdigest()[:16]
