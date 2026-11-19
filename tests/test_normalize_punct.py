import pytest

from jpbench.normalize import normalize_text
from jpbench.scoring import TaskResult


@pytest.mark.parametrize("raw,expected", [
    ("A：B", "A:B"),
    ("A；B", "A;B"),
    ("１００％", "100%"),
    ("（テスト）", "(テスト)"),
    ("Ａ－Ｂ", "A-B"),
])
def test_full_width_punctuation_maps_to_ascii(raw, expected):
    assert normalize_text(raw) == expected


def test_task_result_to_dict():
    r = TaskResult("t", True, 1.0, "ok")
    assert r.to_dict() == {"task_id": "t", "passed": True, "score": 1.0, "detail": "ok"}
