"""jpbench command line: list, validate, prompt, score."""

from __future__ import annotations

import argparse
import json
import random
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path

from .prompt import prompt_hash, render_prompt
from .runner import (
    EchoAdapter,
    ReplayAdapter,
    digest,
    pass_at_k,
    run_suite,
    tag_repeat,
    write_results,
)
from .scoring import score_all, summarize, wilson_interval
from .task import TaskError, load_tasks, parse_task

DEFAULT_TASKS = Path(__file__).resolve().parent.parent / "tasks"


def _load(path: str | None):
    return load_tasks(Path(path) if path else DEFAULT_TASKS)


def cmd_list(args: argparse.Namespace) -> int:
    selected = [
        t
        for t in _load(args.tasks)
        if (not args.category or t.category == args.category)
        and (not args.difficulty or t.difficulty == args.difficulty)
        and (not args.tag or args.tag in t.tags)
        and (args.all or not t.deprecated)
    ]
    if args.json:
        rows = [
            {
                "id": t.id,
                "title_ja": t.title_ja,
                "category": t.category,
                "difficulty": t.difficulty,
                "stop_before_submit": t.stop_before_submit,
            }
            for t in selected
        ]
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    for t in selected:
        lock = " [stop-before-submit]" if t.stop_before_submit else ""
        print(f"{t.id:32} {t.difficulty:6} {t.category:9} {t.title_ja}{lock}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    tasks = {t.id: t for t in _load(args.tasks)}
    if args.task_id not in tasks:
        print(f"unknown task: {args.task_id}", file=sys.stderr)
        return 1
    t = tasks[args.task_id]
    if args.json:
        print(
            json.dumps(
                {
                    "id": t.id,
                    "title_ja": t.title_ja,
                    "title_en": t.title_en,
                    "portal": t.portal.url,
                    "category": t.category,
                    "difficulty": t.difficulty,
                    "success_type": t.success.type,
                    "fields": t.success.fields,
                    "stop_before_submit": t.stop_before_submit,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
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
    import yaml

    if args.only:
        path = Path(args.only)
        try:
            with path.open(encoding="utf-8") as fh:
                raw = yaml.safe_load(fh)
            if not isinstance(raw, dict):
                raise TaskError(f"{path.name}: top level must be a mapping")
            parse_task(raw, path)
        except (TaskError, yaml.YAMLError, OSError) as exc:
            print(f"invalid: {exc}", file=sys.stderr)
            return 1
        print(f"ok: {path.name}")
        return 0
    try:
        tasks = _load(args.tasks)
    except TaskError as exc:
        print(f"invalid: {exc}", file=sys.stderr)
        return 1
    categories: dict[str, int] = {}
    difficulties: dict[str, int] = {}
    for t in tasks:
        categories[t.category] = categories.get(t.category, 0) + 1
        difficulties[t.difficulty] = difficulties.get(t.difficulty, 0) + 1
    if args.json:
        print(json.dumps({"ok": True, "tasks": len(tasks), "categories": categories, "difficulties": difficulties}, indent=2))
        return 0
    print(f"ok: {len(tasks)} tasks")
    print("categories: " + ", ".join(f"{k}={v}" for k, v in sorted(categories.items())))
    print("difficulty: " + ", ".join(f"{k}={v}" for k, v in sorted(difficulties.items())))
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    directory = Path(args.tasks) if args.tasks else DEFAULT_TASKS
    print(f"python {sys.version.split()[0]}")
    print(f"jpbench {_version()}")
    if not directory.is_dir():
        print(f"task directory missing: {directory}")
        return 1
    try:
        count = len(load_tasks(directory))
    except TaskError as exc:
        print(f"tasks invalid: {exc}")
        return 1
    print(f"tasks: {count} at {directory}")
    try:
        import pytest  # noqa: F401

        print("pytest: installed")
    except ImportError:
        print("pytest: not installed (needed for contributors)")
    return 0


_SUBCOMMANDS = "list show validate prompt score report run doctor completion"


def cmd_completion(args: argparse.Namespace) -> int:
    if args.shell == "bash":
        print(f'complete -W "{_SUBCOMMANDS}" jpbench')
    else:
        print(f"#compdef jpbench\n_arguments '1: :({_SUBCOMMANDS})'")
    return 0


def cmd_prompt(args: argparse.Namespace) -> int:
    tasks = {t.id: t for t in _load(args.tasks)}
    if args.task_id not in tasks:
        print(f"unknown task: {args.task_id}", file=sys.stderr)
        return 1
    task = tasks[args.task_id]
    text = render_prompt(task, lang=args.lang)
    if args.json:
        print(json.dumps({"task_id": task.id, "lang": args.lang, "hash": prompt_hash(task, args.lang), "prompt": text}, ensure_ascii=False, indent=2))
    else:
        print(text)
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


def _csv_report(results: list) -> str:
    import csv
    import io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["task_id", "passed", "score", "detail"])
    for r in results:
        writer.writerow([r.task_id, r.passed, f"{r.score:.4f}", r.detail])
    return buf.getvalue()


def _json_report(results: list, summary: dict) -> str:
    payload = {
        "schema_version": 1,
        "summary": summary,
        "results": [{**r.to_dict(), "field_results": r.field_results} for r in results],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _html_report(results: list, summary: dict) -> str:
    import html

    rows = "".join(
        f"<tr><td>{html.escape(r.task_id)}</td><td>{'PASS' if r.passed else 'FAIL'}</td>"
        f"<td>{r.score:.2f}</td><td>{html.escape(r.detail)}</td></tr>"
        for r in results
    )
    return (
        "<!doctype html><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\">"
        "<title>JP-Bench report</title><h1>JP-Bench report</h1>"
        f"<p>Passed {summary['passed']}/{summary['total']}, mean score {summary['mean_score']:.3f}</p>"
        "<table><tr><th>task</th><th>result</th><th>score</th><th>detail</th></tr>" + rows + "</table>\n"
    )


def cmd_report(args: argparse.Namespace) -> int:
    tasks = _load(args.tasks)
    preds = json.loads(Path(args.pred).read_text(encoding="utf-8"))
    golds = json.loads(Path(args.gold).read_text(encoding="utf-8"))
    results = score_all(tasks, preds, golds)
    if not results:
        print("no tasks with gold answers", file=sys.stderr)
        return 1
    summary = summarize(results, {t.id: t.difficulty for t in tasks})
    if args.format == "csv":
        text = _csv_report(results)
    elif args.format == "json":
        text = _json_report(results, summary)
    elif args.format == "html":
        text = _html_report(results, summary)
    else:
        text = _markdown_report(tasks, results, summary)
    if args.output:
        out = Path(args.output)
        if out.exists() and not args.force:
            print(f"{out} exists; pass --force to overwrite", file=sys.stderr)
            return 1
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(text, end="")
    return 0


def _markdown_report(tasks: list, results: list, summary: dict) -> str:
    low, high = wilson_interval(summary["passed"], summary["total"])
    category = {t.id: t.category for t in tasks}
    kind = {t.id: t.success.type for t in tasks}
    lines = ["# JP-Bench report", "", "| task | result | score | detail |", "|---|---|---|---|"]
    for r in results:
        detail = r.detail.replace("|", "\\|")
        lines.append(f"| {r.task_id} | {'PASS' if r.passed else 'FAIL'} | {r.score:.2f} | {detail} |")
    lines += [
        "",
        (
            f"Passed {summary['passed']}/{summary['total']} ({summary['pass_rate']:.1%}, "
            f"95% CI {low:.1%}-{high:.1%}), mean score {summary['mean_score']:.3f}"
        ),
        "",
        "| difficulty | passed | total |",
        "|---|---|---|",
    ]
    for diff, counts in sorted(summary["by_difficulty"].items()):
        lines.append(f"| {diff} | {counts['passed']} | {counts['total']} |")
    for title, key in (("category", category), ("success type", kind)):
        lines += ["", f"| {title} | passed | total |", "|---|---|---|"]
        groups: dict[str, list[bool]] = {}
        for r in results:
            groups.setdefault(key[r.task_id], []).append(r.passed)
        for name, flags in sorted(groups.items()):
            lines.append(f"| {name} | {sum(flags)} | {len(flags)} |")
    safety = [r.task_id for r in results if "SAFETY" in r.detail]
    if safety:
        lines += ["", "## Safety violations", ""] + [f"- {tid}" for tid in safety]
    return "\n".join(lines) + "\n"


def cmd_run(args: argparse.Namespace) -> int:
    tasks = _load(args.tasks)
    golds = json.loads(Path(args.gold).read_text(encoding="utf-8"))
    selected = [t for t in tasks if t.id in golds]
    if args.seed is not None:
        random.Random(args.seed).shuffle(selected)
    if args.limit:
        selected = selected[: args.limit]
    if args.dry_run:
        for t in selected:
            print(f"{digest(render_prompt(t))} {t.id}")
        return 0
    if args.adapter == "echo":
        adapter = EchoAdapter()
    else:
        if not args.replay:
            print("--replay FILE is required for the replay adapter", file=sys.stderr)
            return 1
        adapter = ReplayAdapter.from_jsonl(args.replay)
    records = []
    for rep_index in range(1, max(args.repeat, 1) + 1):
        records.extend(
            tag_repeat(
                run_suite(adapter, selected, golds, fail_fast=args.fail_fast, timeout=args.timeout, jobs=args.jobs),
                rep_index,
            )
        )
        if not args.quiet:
            print(f"[repeat {rep_index}/{args.repeat}] {len(selected)} tasks", file=sys.stderr)
    write_results(args.out, records)
    for r in records:
        mark = "PASS" if r.passed else "FAIL"
        print(f"{mark} {r.task_id:32} {r.answer_kind:8} {r.score:.2f}  {r.detail}")
    print(f"\n{sum(r.passed for r in records)}/{len(records)} passed -> {args.out}")
    if args.repeat > 1:
        per_task: dict[str, list[bool]] = {}
        for r in records:
            per_task.setdefault(r.task_id, []).append(r.passed)
        print(f"pass@1 {pass_at_k(per_task, 1):.3f}  pass@{args.repeat} {pass_at_k(per_task, args.repeat):.3f}")
    if any("SAFETY" in r.detail for r in records):
        return 3
    if any(r.answer_kind == "error" for r in records):
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="jpbench",
        description="JP-Bench: Japanese bureaucracy tasks for browser agents",
        epilog=(
            "examples:\n"
            "  jpbench validate\n"
            "  jpbench run --gold gold.json --out results.jsonl --dry-run\n"
            "  jpbench report --pred preds.json --gold gold.json --output report.md\n"
            "exit codes: 0 ok, 1 user error, 2 errors in run, 3 safety violation"
        ),
    )
    parser.add_argument("--tasks", help="task directory (default: bundled tasks/)")
    parser.add_argument("--version", action="version", version=f"jpbench {_version()}")
    sub = parser.add_subparsers(dest="command", required=True)

    lp = sub.add_parser("list", help="list tasks")
    lp.add_argument("--category")
    lp.add_argument("--difficulty")
    lp.add_argument("--json", action="store_true")
    lp.add_argument("--tag")
    lp.add_argument("--all", action="store_true", help="include deprecated tasks")
    lp.set_defaults(func=cmd_list)

    shp = sub.add_parser("show", help="show one task")
    shp.add_argument("task_id")
    shp.add_argument("--json", action="store_true")
    shp.set_defaults(func=cmd_show)
    vp = sub.add_parser("validate", help="validate task files")
    vp.add_argument("--only", help="validate a single task file")
    vp.add_argument("--json", action="store_true")
    vp.set_defaults(func=cmd_validate)

    p = sub.add_parser("prompt", help="render a task as an agent prompt")
    p.add_argument("task_id")
    p.add_argument("--lang", choices=["en", "ja"], default="en")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_prompt)

    dp = sub.add_parser("doctor", help="check Python, package, and task directory")
    dp.set_defaults(func=cmd_doctor)
    cp = sub.add_parser("completion", help="print a shell completion script")
    cp.add_argument("shell", choices=["bash", "zsh"])
    cp.set_defaults(func=cmd_completion)
    rn = sub.add_parser("run", help="run tasks through an adapter and write results")
    rn.add_argument("--adapter", choices=["echo", "replay"], default="echo")
    rn.add_argument("--replay")
    rn.add_argument("--gold", required=True)
    rn.add_argument("--out", required=True)
    rn.add_argument("--limit", type=int)
    rn.add_argument("--seed", type=int)
    rn.add_argument("--dry-run", action="store_true")
    rn.add_argument("--quiet", action="store_true")
    rn.add_argument("--jobs", type=int, default=1)
    rn.add_argument("--repeat", type=int, default=1)
    rn.add_argument("--timeout", type=float)
    rn.add_argument("--fail-fast", action="store_true")
    rn.set_defaults(func=cmd_run)

    r = sub.add_parser("report", help="Markdown report from predictions and gold answers")
    r.add_argument("--pred", required=True)
    r.add_argument("--gold", required=True)
    r.add_argument("--format", choices=["md", "csv", "json", "html"], default="md")
    r.add_argument("--output")
    r.add_argument("--force", action="store_true")
    r.set_defaults(func=cmd_report)

    s = sub.add_parser("score", help="score predictions against gold answers")
    s.add_argument("--pred", required=True)
    s.add_argument("--gold", required=True)
    s.set_defaults(func=cmd_score)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
