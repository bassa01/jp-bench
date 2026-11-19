import pytest

from jpbench.parse import extract_json, looks_like_refusal, strip_reasoning


def test_reasoning_block_is_stripped():
    assert strip_reasoning("<think>hmm</think>{\"a\": 1}") == '{"a": 1}'


def test_fenced_json_is_extracted():
    text = 'Here you go:\n```json\n{"name": "A"}\n```'
    assert extract_json(text) == {"name": "A"}


def test_reasoning_then_json_is_extracted():
    assert extract_json('<think>x {bad</think>{"active": true}') == {"active": True}


def test_no_json_raises():
    with pytest.raises(ValueError, match="no JSON"):
        extract_json("no answer here")


def test_refusal_detection():
    assert looks_like_refusal("申し訳ありませんが、できません")
    assert looks_like_refusal("I cannot submit that form.")
    assert not looks_like_refusal('{"name": "A"}')


def test_non_object_json_rejected():
    with pytest.raises(TypeError):
        extract_json("```json\n[1, 2]\n```")
