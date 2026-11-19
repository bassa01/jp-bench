"""jpbench command line: list, validate, prompt, score."""

from __future__ import annotations

import argparse
import json
import sys
from importlib.metadata import PackageNotFoundError, version as _pkg_version
from pathlib import Path

from .prompt import render_prompt
from .scoring import score_all
from .task import TaskError, load_tasks

DEFAULT_TASKS = Path(__file__).resolve().parent.parent / "tasks"


def _load(path: str | None):
    return load_tasks(Path(path) if path else DEFAULT_TASKS)


def cmd_list(args: argparse.Namespace) -> int:
    for t in _load(args.tasks):
        lock = " [stop-before-submit]" if t.stop_before_submit else ""
        print(f"{t.id:32} {t.difficulty:6} {t.category:9} {t.title_ja}{lock}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        tasks = _load(args.tasks)
    except TaskError as exc:
        print(f"invalid: {exc}", file=sys.stderr)
        return 1
    print(f"ok: {len(tasks)} tasks")
    return 0


def cmd_prompt(args: argparse.Namespace) -> int:
    tasks = {t.id: t for t in _load(args.tasks)}
    if args.task_id not in tasks:
        print(f"unknown task: {args.task_id}", file=sys.stderr)
        return 1
    print(render_prompt(tasks[args.task_id], lang=args.lang))
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    tasks = _load(args.tasks)
    preds = json.loads(Path(args.pred).read_text(encoding="utf-8"))
    golds = json.loads(Path(args.gold).read_text(encoding="utf-8"))
    results = score_all(tasks, preds, golds)
    if not results:
        print("no tasks with gold answers", file=sys.stderr)
        return 1
    for r in results:
        mark = "PASS" if r.passed else "FAIL"
        print(f"{mark} {r.task_id:32} {r.score:.2f}  {r.detail}")
    passed = sum(r.passed for r in results)
    print(f"\n{passed}/{len(results)} passed, mean score {sum(r.score for r in results) / len(results):.3f}")
    return 0


def _version() -> str:
    try:
        return _pkg_version("jpbench")
    except PackageNotFoundError:
        return "0.0.0+unknown"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jpbench", description="JP-Bench: Japanese bureaucracy tasks for browser agents")
    parser.add_argument("--tasks", help="task directory (default: bundled tasks/)")
    parser.add_argument("--version", action="version", version=f"jpbench {_version()}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list tasks").set_defaults(func=cmd_list)
    sub.add_parser("validate", help="validate task files").set_defaults(func=cmd_validate)

    p = sub.add_parser("prompt", help="render a task as an agent prompt")
    p.add_argument("task_id")
    p.add_argument("--lang", choices=["en", "ja"], default="en")
    p.set_defaults(func=cmd_prompt)

    s = sub.add_parser("score", help="score predictions against gold answers")
    s.add_argument("--pred", required=True)
    s.add_argument("--gold", required=True)
    s.set_defaults(func=cmd_score)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
