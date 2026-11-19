from pathlib import Path

import pytest

from jpbench.cli import main
from jpbench.task import TaskError, load_tasks, parse_task

TASKS = Path(__file__).resolve().parent.parent / "tasks"


def base(**over):
    raw = {
        "id": "sample-task", "title_ja": "サンプル", "title_en": "Sample",
        "portal": {"name_ja": "x", "url": "https://example.go.jp/", "operator": "x"},
        "category": "lookup", "difficulty": "easy",
        "instructions_ja": "検索する", "instructions_en": "Search.",
        "inputs": {}, "success": {"type": "field_match", "fields": ["name"]},
        "safety": {"stop_before_submit": False}, "gold_source": "example",
    }
    raw.update(over)
    return raw


def test_optional_fields_parse_and_default():
    t = parse_task(base(tags=["tax", "corporate"], review_status="reviewed", created="2026-01-01", updated="2026-02-01", owner="team", snapshot_date="2026-03-01", source_documents=["https://example.go.jp/a"]))
    assert t.tags == ("corporate", "tax") and t.review_status == "reviewed"
    assert t.created == "2026-01-01" and t.snapshot_date == "2026-03-01" and t.source_documents == ("https://example.go.jp/a",)
    d = parse_task(base())
    assert d.tags == () and d.review_status == "draft" and d.created == ""


@pytest.mark.parametrize("over,msg", [
    ({"tags": ["unknown"]}, "unknown tag"),
    ({"tags": ["tax", "tax"]}, "must be unique"),
    ({"review_status": "final"}, "review_status must be one of"),
    ({"created": "2026-13-01"}, "ISO 8601"),
    ({"created": "2026-02-01", "updated": "2026-01-01"}, "must not be earlier"),
    ({"source_documents": ["http://example.go.jp/a"]}, "https URLs"),
])
def test_optional_field_rules(over, msg):
    with pytest.raises(TaskError, match=msg):
        parse_task(base(**over))


def test_bundled_tasks_carry_tags():
    tags = {t.id: t.tags for t in load_tasks(TASKS)}
    assert "corporate" in tags["houjin-bangou-lookup"]
    assert tags["egov-law-article"] == ("legal",)


def test_list_filters_by_tag(capsys):
    assert main(["list", "--tag", "subsidy"]) == 0
    lines = [l for l in capsys.readouterr().out.splitlines() if l.strip()]
    assert len(lines) == 1 and lines[0].startswith("jgrants-open-subsidies")
