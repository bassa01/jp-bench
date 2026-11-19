import pytest

from jpbench.parse import (
    MAX_OUTPUT_CHARS,
    ParseError,
    answer_kind,
    extract_json,
    find_refusal,
)


def test_nan_rejected():
    with pytest.raises(ParseError):
        extract_json('{"a": NaN}')


def test_duplicate_keys_rejected():
    with pytest.raises(ParseError, match="duplicate key"):
        extract_json('{"a": 1, "a": 2}')


def test_oversize_output_rejected():
    with pytest.raises(ParseError, match="limit"):
        extract_json("x" * (MAX_OUTPUT_CHARS + 1))


def test_full_width_braces_and_quotes():
    assert extract_json("\uff5b\uff02a\uff02: 1\uff5d") == {"a": 1}


def test_answer_label_is_stripped():
    assert extract_json("回答: {\"a\": 1}") == {"a": 1}


def test_parse_error_keeps_raw():
    with pytest.raises(ParseError) as exc:
        extract_json("no json here")
    assert exc.value.raw == "no json here"


def test_refusal_phrase_is_returned_case_insensitively():
    assert find_refusal("I CANNOT do that") == "I cannot"
    assert find_refusal("ok") is None


@pytest.mark.parametrize("text,kind", [
    ("", "empty"),
    ("I cannot help", "refusal"),
    ('{"a": 1}', "json"),
    ("nothing", "invalid"),
])
def test_answer_kind(text, kind):
    assert answer_kind(text) == kind
