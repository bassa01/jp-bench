import pytest

from jpbench.normalize import normalize_date, normalize_field, normalize_number


@pytest.mark.parametrize("raw,expected", [("第三条之二", "第3条の2"), ("3条", "第3条"), ("第３条之２", "第3条の2"), ("第3条の2の3", "第3条の2の3")])
def test_article_references(raw, expected):
    assert normalize_field("law_article", raw) == expected


@pytest.mark.parametrize("raw,expected", [("令和元年法律第一号", "令和1年法律第1号"), ("法律第1号", "法律第1号")])
def test_law_numbers(raw, expected):
    assert normalize_field("law_number", raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("〒100-0012 東京千代田区一丁目", "東京都千代田区1丁目"),
    ("東京都千代田区", "東京都千代田区"),
    ("京都", "京都府"),
    ("京都市上京区", "京都市上京区"),
    ("大阪市北区", "大阪市北区"),
])
def test_addresses(raw, expected):
    assert normalize_field("address", raw) == expected


def test_approximate_numbers_and_zero_padded_dates():
    assert normalize_number("約1,000円") == 1000.0
    assert normalize_date("2027年04月01日") == "2027-04-01"
    assert normalize_date("2027年4月1日") == "2027-04-01"
