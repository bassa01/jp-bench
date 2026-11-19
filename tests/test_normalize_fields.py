import pytest

from jpbench.normalize import normalize_field, normalize_url


@pytest.mark.parametrize("raw,expected", [
    ("HTTPS://Example.go.jp/a/#top", "https://example.go.jp/a"),
    ("https://example.go.jp/a/", "https://example.go.jp/a"),
])
def test_url_normalization(raw, expected):
    assert normalize_url(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("第３条之２", "第3条の2"),
    ("第 3 条", "第3条"),
])
def test_article_reference_normalization(raw, expected):
    assert normalize_field("law_article", raw) == expected


def test_url_field_uses_url_rule():
    assert normalize_field("portal_url", "HTTPS://Example.go.jp/") == "https://example.go.jp"
