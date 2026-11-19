import pytest

from jpbench.normalize import (
    normalize_field,
    normalize_number,
    normalize_text,
    normalize_url,
)


@pytest.mark.parametrize("raw,expected", [("1万円", 10000.0), ("2億円", 2e8), ("¥1,000", 1000.0), ("無料", 0.0)])
def test_number_scales_and_free(raw, expected):
    assert normalize_number(raw) == expected


@pytest.mark.parametrize("raw", ["nan", "inf"])
def test_non_finite_numbers_rejected(raw):
    with pytest.raises(ValueError):
        normalize_number(raw)


def test_middle_dot_variants_unify():
    assert normalize_text("A･B·C") == "A・B・C"


def test_corporate_number_digits_only():
    assert normalize_field("corporate_number", "１２３４-５６７８ 9012 3") == "1234567890123"


def test_invoice_number_canonical_form():
    assert normalize_field("invoice_number", " t0000000000000 ") == "T0000000000000"
    assert normalize_field("invoice_number", "T12A") == "T12A"


def test_utm_removed_and_query_sorted():
    assert normalize_url("https://example.go.jp/a?utm_source=x&b=2&a=1") == "https://example.go.jp/a?a=1&b=2"


def test_http_go_jp_becomes_https_and_www_and_port_removed():
    assert normalize_url("http://www.example.go.jp:443/") == "https://example.go.jp"


def test_percent_encoded_path_decoded():
    assert normalize_url("https://example.go.jp/%E6%9D%B1%E4%BA%AC") == "https://example.go.jp/東京"


def test_list_normalized_sorted_and_deduped():
    assert normalize_field("titles_list", ["Ａ", "A", "", "B"]) == "A|B"
