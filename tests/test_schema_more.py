from pathlib import Path

import pytest

from jpbench.task import Task, TaskError, load_task_ids, load_tasks, parse_task
from tests.helpers import valid_task_yaml

TASKS = Path(__file__).resolve().parent.parent / "tasks"


def test_file_name_must_equal_id(tmp_path):
    (tmp_path / "other.yaml").write_text(valid_task_yaml("a-task"), encoding="utf-8")
    with pytest.raises(TaskError, match="file name must be a-task.yaml"):
        load_tasks(tmp_path)


def test_unknown_portal_and_safety_keys_rejected():
    base = {"id": "x-task", "title_ja": "サンプル", "title_en": "S", "category": "lookup", "difficulty": "easy",
            "instructions_ja": "検索", "instructions_en": "Search.", "inputs": {}, "success": {"type": "field_match", "fields": ["a"]},
            "gold_source": "x", "portal": {"name_ja": "x", "url": "https://example.go.jp/", "operator": "x", "extra": 1},
            "safety": {"stop_before_submit": False}}
    with pytest.raises(TaskError, match="unknown portal keys"):
        parse_task(base)
    base["portal"].pop("extra")
    base["safety"]["surprise"] = True
    with pytest.raises(TaskError, match="unknown safety keys"):
        parse_task(base)


def test_nested_directories_are_loaded(tmp_path):
    sub = tmp_path / "lookup"
    sub.mkdir()
    (sub / "a-task.yaml").write_text(valid_task_yaml("a-task"), encoding="utf-8")
    assert load_task_ids(tmp_path) == ["a-task"]


def test_published_tasks_need_sources(tmp_path):
    (tmp_path / "a-task.yaml").write_text(valid_task_yaml("a-task", extra="review_status: published\n"), encoding="utf-8")
    with pytest.raises(TaskError, match="published tasks must list source_documents"):
        load_tasks(tmp_path)


def test_to_dict_and_from_dict_round_trip():
    t = next(x for x in load_tasks(TASKS) if x.id == "invoice-number-verify")
    data = t.to_dict()
    assert data["portal"]["url"] == t.portal.url and "path" not in data
    again = Task.from_dict(data)
    assert again.id == t.id and again.success.fields == t.success.fields


def test_repr_omits_instructions():
    t = next(x for x in load_tasks(TASKS) if x.id == "invoice-number-verify")
    assert "instructions" not in repr(t) and "invoice-number-verify" in repr(t)
