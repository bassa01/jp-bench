import pytest

from jpbench.task import TaskError, parse_task


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


def test_base_task_is_valid():
    assert parse_task(base()).id == "sample-task"


@pytest.mark.parametrize("over,msg", [
    ({"extra": 1}, "unknown keys"),
    ({"title_ja": "Sample"}, "title_ja must contain Japanese"),
    ({"instructions_ja": "Search"}, "instructions_ja must contain Japanese"),
    ({"instructions_en": "検索"}, "instructions_en must not contain Japanese"),
    ({"gold_source": "  "}, "gold_source must be non-empty"),
    ({"success": {"type": "field_match", "fields": ["a", "a"]}}, "must be unique"),
    ({"success": {"type": "set_overlap", "fields": ["a"], "min_overlap": 1.5}}, "within 0-1"),
    ({"success": {"type": "field_match", "fields": ["a"], "tolerance": -1}}, "must not be negative"),
    ({"success": {"type": "field_match", "fields": ["a"], "tolerance": 0.1}}, "only applies to numeric_tolerance"),
    ({"success": {"type": "field_match", "fields": ["a"], "state": "x"}}, "only applies to reached_state"),
])
def test_schema_rejects(over, msg):
    with pytest.raises(TaskError, match=msg):
        parse_task(base(**over))
