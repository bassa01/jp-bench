import pytest

from jpbench.normalize import (
    fold_kana,
    is_valid_domestic_phone,
    normalize_date,
    normalize_field,
    normalize_text,
)


@pytest.mark.parametrize("raw,expected", [
    ("R9.4.1", "2027-04-01"),
    ("H31.4.30", "2019-04-30"),
    ("S64.1.7", "1989-01-07"),
    ("令和元年5月1日", "2019-05-01"),
])
def test_era_abbreviations_and_gannen(raw, expected):
    assert normalize_date(raw) == expected


@pytest.mark.parametrize("raw", ["令和0年1月1日", "2027-02-30", "令和9年2月29日"])
def test_rejects_impossible_dates(raw):
    with pytest.raises(ValueError):
        normalize_date(raw)


def test_leap_day_valid_in_leap_year():
    assert normalize_date("2028-02-29") == "2028-02-29"


def test_heisei_after_end_rejected():
    with pytest.raises(ValueError, match="ended"):
        normalize_date("平成31年5月1日")


@pytest.mark.parametrize("raw,expected", [
    ("(合名)サンプル", "合名会社サンプル"),
    ("（一社）サンプル", "一般社団法人サンプル"),
    ("(一財)サンプル", "一般財団法人サンプル"),
])
def test_entity_variants(raw, expected):
    assert normalize_text(raw) == expected


def test_postal_code_format():
    assert normalize_field("postal_code", "〒１００－００１２") == "100-0012"
    assert normalize_field("postal_code", "1000012") == "100-0012"


def test_phone_normalization():
    assert normalize_field("phone", "＋81 (3) 1234-5678") == "+81312345678"
    assert normalize_field("phone", "03-1234-5678") == "0312345678"


@pytest.mark.parametrize("raw,ok", [("03-1234-5678", True), ("090-1234-5678", True), ("12345", False)])
def test_domestic_phone_validity(raw, ok):
    assert is_valid_domestic_phone(raw) is ok


def test_kana_fold_is_opt_in_helper():
    assert fold_kana("ぁカ") == "アカ"
    assert fold_kana("ゐ") == "イ"
    assert normalize_text("ぁカ") == "ぁカ"
