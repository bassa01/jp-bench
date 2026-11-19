from hypothesis import given, settings
from hypothesis import strategies as st

from jpbench.normalize import (
    normalize_boolean,
    normalize_date,
    normalize_field,
    normalize_text,
)


def test_npo_abbreviation_and_banchi():
    assert normalize_text("(NPO)テスト") == "特定非営利活動法人テスト"
    assert normalize_field("address", "東京都千代田区1番地2") == "東京都千代田区1番2"


def test_hokkaido_is_left_alone():
    assert normalize_field("address", "北海道札幌市中央区") == "北海道札幌市中央区"


def test_mixed_separators_in_western_dates():
    assert normalize_date("2027年4/1") == "2027-04-01"


def test_boolean_answers_in_japanese_and_english():
    assert normalize_boolean("はい") == "true" and normalize_boolean("有") == "true"
    assert normalize_boolean("いいえ") == "false" and normalize_boolean(False) == "false"
    assert normalize_field("is_active_flag", "無効") == "false"


@given(st.text(max_size=60))
@settings(max_examples=200)
def test_normalize_never_raises_on_arbitrary_unicode(value):
    normalize_text(value)
    normalize_field("corporate_number", value)
    normalize_field("address", value)
    normalize_field("titles_list", [value])
