"""Normalization rules for Japanese administrative text.

Agents copy values out of government portals that mix full-width and
half-width characters, abbreviate legal-entity suffixes, and format dates
in both Western and Japanese era notation. Scoring must not punish an
agent for those differences, only for wrong values.
"""

from __future__ import annotations

import re
import unicodedata

_ENTITY_ABBREVIATIONS = {
    "(株)": "株式会社",
    "（株）": "株式会社",
    "㈱": "株式会社",
    "(有)": "有限会社",
    "（有）": "有限会社",
    "㈲": "有限会社",
    "(同)": "合同会社",
    "（同）": "合同会社",
}

_ERA_OFFSETS = {
    "令和": 2018,
    "平成": 1988,
    "昭和": 1925,
}

_SPACE_RE = re.compile(r"\s+")
_ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")
_DASH_RE = re.compile(r"[‐‑‒–—―ー−－]")
_ERA_DATE_RE = re.compile(r"(令和|平成|昭和)(元|\d+)年(\d+)月(\d+)日")
_WESTERN_DATE_RE = re.compile(r"(\d{4})[年/.\-](\d{1,2})[月/.\-](\d{1,2})日?")


def normalize_text(value: object) -> str:
    """NFKC, unify entity suffixes and dashes, drop all whitespace."""
    text = str(value)
    for short, full in _ENTITY_ABBREVIATIONS.items():
        text = text.replace(short, full)
    text = unicodedata.normalize("NFKC", text)
    text = _ZERO_WIDTH_RE.sub("", text)
    text = _DASH_RE.sub("-", text)
    text = _SPACE_RE.sub("", text)
    return text


def normalize_date(value: object) -> str:
    """Return YYYY-MM-DD for Western or Japanese-era dates, else normalized text."""
    text = unicodedata.normalize("NFKC", str(value)).strip()
    era = _ERA_DATE_RE.search(text)
    if era:
        name, year, month, day = era.groups()
        y = 1 if year == "元" else int(year)
        return f"{_ERA_OFFSETS[name] + y:04d}-{int(month):02d}-{int(day):02d}"
    western = _WESTERN_DATE_RE.search(text)
    if western:
        y, m, d = western.groups()
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
    return normalize_text(text)


def normalize_number(value: object) -> float:
    """Parse numbers written with commas, full-width digits or 円/人 suffixes."""
    text = unicodedata.normalize("NFKC", str(value))
    text = re.sub(r"[,\s円人件%]", "", text)
    return float(text)


def normalize_field(name: str, value: object) -> str:
    if name.endswith("_date") or name == "date":
        return normalize_date(value)
    return normalize_text(value)
