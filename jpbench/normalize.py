"""Normalization rules for Japanese administrative text.

Agents copy values out of government portals that mix full-width and
half-width characters, abbreviate legal-entity suffixes, and format dates
in both Western and Japanese era notation. Scoring must not punish an
agent for those differences, only for wrong values.
"""

from __future__ import annotations

import datetime
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit

_ENTITY_ABBREVIATIONS = {
    "(株)": "株式会社",
    "（株）": "株式会社",
    "㈱": "株式会社",
    "(有)": "有限会社",
    "（有）": "有限会社",
    "㈲": "有限会社",
    "(同)": "合同会社",
    "（同）": "合同会社",
    "(合名)": "合名会社",
    "（合名）": "合名会社",
    "(合資)": "合資会社",
    "（合資）": "合資会社",
    "(一社)": "一般社団法人",
    "（一社）": "一般社団法人",
    "(一財)": "一般財団法人",
    "（一財）": "一般財団法人",
}

_ERA_OFFSETS = {"令和": 2018, "平成": 1988, "昭和": 1925}
_ERA_LETTERS = {"R": "令和", "H": "平成", "S": "昭和"}
_ERA_END = {"平成": datetime.date(2019, 4, 30), "昭和": datetime.date(1989, 1, 7)}

_SPACE_RE = re.compile(r"\s+")
_DASH_RE = re.compile(r"[‐‑‒–—―ー−－]")
_ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")
_ERA_DATE_RE = re.compile(r"(令和|平成|昭和|[RHS])(元|\d+)[年.](\d+)[月.](\d+)日?")
_WESTERN_DATE_RE = re.compile(r"(\d{4})[年/.\-](\d{1,2})[月/.\-](\d{1,2})日?")
_SMALL_TO_LARGE = str.maketrans("ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮ", "あいうえおつやゆよわアイウエオツヤユヨワ")
_HIRA_KATA_VARIANTS = str.maketrans({"ゐ": "い", "ゑ": "え", "ヰ": "イ", "ヱ": "エ"})


def normalize_text(value: object) -> str:
    """NFKC, unify entity suffixes and dashes, drop all whitespace."""
    text = str(value)
    for short, full in _ENTITY_ABBREVIATIONS.items():
        text = text.replace(short, full)
    text = unicodedata.normalize("NFKC", text)
    text = _ZERO_WIDTH_RE.sub("", text)
    text = text.replace("\u301c", "~").replace("\u223c", "~")
    text = _DASH_RE.sub("-", text)
    text = _SPACE_RE.sub("", text)
    return text


def _iso(year: int, month: int, day: int, era: str | None = None) -> str:
    try:
        date = datetime.date(year, month, day)
    except ValueError as exc:
        raise ValueError(f"impossible date {year:04d}-{month:02d}-{day:02d}") from exc
    if era in _ERA_END and date > _ERA_END[era]:
        raise ValueError(f"{era} ended on {_ERA_END[era].isoformat()}, not {date.isoformat()}")
    return date.isoformat()


def normalize_date(value: object) -> str:
    """Return YYYY-MM-DD for Western or Japanese-era dates, else normalized text."""
    text = unicodedata.normalize("NFKC", str(value)).strip()
    era = _ERA_DATE_RE.search(text)
    if era:
        name, year, month, day = era.groups()
        name = _ERA_LETTERS.get(name, name)
        y = 1 if year == "元" else int(year)
        if y == 0:
            raise ValueError("era year must be 1 or later")
        return _iso(_ERA_OFFSETS[name] + y, int(month), int(day), name)
    western = _WESTERN_DATE_RE.search(text)
    if western:
        y, m, d = western.groups()
        return _iso(int(y), int(m), int(d))
    return normalize_text(text)


def normalize_number(value: object) -> float:
    """Parse numbers written with commas, full-width digits or 円/人 suffixes."""
    text = unicodedata.normalize("NFKC", str(value))
    text = re.sub(r"[,\s円人件%]", "", text)
    return float(text)


def normalize_url(value: object) -> str:
    """Lowercase scheme and host, drop fragment and trailing slash."""
    parts = urlsplit(normalize_text(value))
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, ""))


def normalize_article_ref(value: object) -> str:
    """Canonical statute reference: 第3条の2, not 第３条之２ or 第3条 の 2."""
    text = unicodedata.normalize("NFKC", str(value))
    return _SPACE_RE.sub("", text).replace("之", "の")


def normalize_postal_code(value: object) -> str:
    """NNN-NNNN with the 〒 mark and separators removed; unchanged if not 7 digits."""
    text = unicodedata.normalize("NFKC", str(value)).replace("〒", "").strip()
    digits = re.sub(r"\D", "", text)
    if len(digits) != 7:
        return normalize_text(text)
    return f"{digits[:3]}-{digits[3:]}"


def normalize_phone(value: object) -> str:
    """Digits only; +81 numbers keep the country code and drop the national trunk 0."""
    text = unicodedata.normalize("NFKC", str(value)).strip()
    if text.startswith("+81"):
        digits = re.sub(r"\D", "", text[3:])
        return "+81" + (digits.removeprefix("0"))
    return re.sub(r"\D", "", text)


def is_valid_domestic_phone(value: object) -> bool:
    """A domestic number is 10 or 11 digits starting with 0."""
    digits = normalize_phone(value)
    return digits.startswith("0") and len(digits) in (10, 11)


def fold_kana(text: str) -> str:
    """Opt-in comparison folding: small kana to large, hiragana to katakana."""
    text = text.translate(_SMALL_TO_LARGE).translate(_HIRA_KATA_VARIANTS)
    return "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in text)


def normalize_field(name: str, value: object) -> str:
    if name.endswith("_date") or name == "date":
        return normalize_date(value)
    if name.endswith("_url"):
        return normalize_url(value)
    if name.endswith("_article"):
        return normalize_article_ref(value)
    if name.endswith("postal_code"):
        return normalize_postal_code(value)
    if name.endswith("phone"):
        return normalize_phone(value)
    return normalize_text(value)
