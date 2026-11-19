"""jpbench command line: list, validate, prompt, score."""

from __future__ import annotations

import argparse
import json
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path

from .prompt import render_prompt
from .scoring import score_all, summarize
from .task import TaskError, load_tasks

DEFAULT_TASKS = Path(__file__).resolve().parent.parent / "tasks"


def _load(path: str | None):
    return load_tasks(Path(path) if path else DEFAULT_TASKS)


def cmd_list(args: argparse.Namespace) -> int:
    for t in _load(args.tasks):
        if args.category and t.category != args.category:
            continue
        if args.difficulty and t.difficulty != args.difficulty:
            continue
        lock = " [stop-before-submit]" if t.stop_before_submit else ""
        print(f"{t.id:32} {t.difficulty:6} {t.category:9} {t.title_ja}{lock}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    tasks = {t.id: t for t in _load(args.tasks)}
    if args.task_id not in tasks:
        print(f"unknown task: {args.task_id}", file=sys.stderr)
        return 1
    t = tasks[args.task_id]
    print(
        f"id: {t.id}\n"
        f"title: {t.title_ja} / {t.title_en}\n"
        f"portal: {t.portal.name_ja} {t.portal.url}\n"
        f"category: {t.category}\n"
        f"difficulty: {t.difficulty}\n"
        f"success: {t.success.type} [{', '.join(t.success.fields)}]\n"
        f"stop_before_submit: {t.stop_before_submit}"
    )
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


def cmd_report(args: argparse.Namespace) -> int:
    tasks = _load(args.tasks)
    preds = json.loads(Path(args.pred).read_text(encoding="utf-8"))
    golds = json.loads(Path(args.gold).read_text(encoding="utf-8"))
    results = score_all(tasks, preds, golds)
    if not results:
        print("no tasks with gold answers", file=sys.stderr)
        return 1
    summary = summarize(results, {t.id: t.difficulty for t in tasks})
    lines = ["# JP-Bench report", "", "| task | result | score | detail |", "|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r.task_id} | {'PASS' if r.passed else 'FAIL'} | {r.score:.2f} | {r.detail} |")
    lines += [
        "",
        f"Passed {summary['passed']}/{summary['total']} ({summary['pass_rate']:.1%}), "
        f"mean score {summary['mean_score']:.3f}",
        "",
        "| difficulty | passed | total |",
        "|---|---|---|",
    ]
    for diff, counts in sorted(summary["by_difficulty"].items()):
        lines.append(f"| {diff} | {counts['passed']} | {counts['total']} |")
    print("\n".join(lines))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jpbench", description="JP-Bench: Japanese bureaucracy tasks for browser agents")
    parser.add_argument("--tasks", help="task directory (default: bundled tasks/)")
    parser.add_argument("--version", action="version", version=f"jpbench {_version()}")
    sub = parser.add_subparsers(dest="command", required=True)

    lp = sub.add_parser("list", help="list tasks")
    lp.add_argument("--category")
    lp.add_argument("--difficulty")
    lp.set_defaults(func=cmd_list)

    shp = sub.add_parser("show", help="show one task")
    shp.add_argument("task_id")
    shp.set_defaults(func=cmd_show)
    sub.add_parser("validate", help="validate task files").set_defaults(func=cmd_validate)

    p = sub.add_parser("prompt", help="render a task as an agent prompt")
    p.add_argument("task_id")
    p.add_argument("--lang", choices=["en", "ja"], default="en")
    p.set_defaults(func=cmd_prompt)

    r = sub.add_parser("report", help="Markdown report from predictions and gold answers")
    r.add_argument("--pred", required=True)
    r.add_argument("--gold", required=True)
    r.set_defaults(func=cmd_report)

    s = sub.add_parser("score", help="score predictions against gold answers")
    s.add_argument("--pred", required=True)
    s.add_argument("--gold", required=True)
    s.set_defaults(func=cmd_score)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
