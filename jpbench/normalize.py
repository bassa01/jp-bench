"""Normalization rules for Japanese administrative text.

Agents copy values out of government portals that mix full-width and
half-width characters, abbreviate legal-entity suffixes, and format dates
in both Western and Japanese era notation. Scoring must not punish an
agent for those differences, only for wrong values.
"""

from __future__ import annotations

import datetime
import math
import re
import unicodedata
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

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
    "・": "・",
    "･": "・",
    "·": "・",
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
    # Repeat to a fixed point: NFKC can create spaces (e.g. U+00AF) and removing spaces can
    # expose new compositions, so one pass is not idempotent.
    for _ in range(5):
        before = text
        text = unicodedata.normalize("NFKC", text)
        text = _ZERO_WIDTH_RE.sub("", text)
        text = text.replace("\u301c", "~").replace("\u223c", "~")
        text = _DASH_RE.sub("-", text)
        text = _SPACE_RE.sub("", text)
        if text == before:
            break
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
    """Parse numbers with commas, full-width digits, 円/¥ and 万/億 scales; 無料 is 0."""
    text = unicodedata.normalize("NFKC", str(value)).strip()
    text = re.sub(r"約|およそ", "", text)
    if text == "無料":
        return 0.0
    scale = 1.0
    if "億" in text:
        scale = 1e8
    elif "万" in text:
        scale = 1e4
    text = re.sub(r"[,\s円人件%¥億万]", "", text)
    number = float(text)
    if not math.isfinite(number):
        raise ValueError("number must be finite")
    return number * scale


def normalize_url(value: object) -> str:
    """Canonical URL: lowercase host, https for .go.jp, no www, no :443, no utm_ params, sorted query."""
    parts = urlsplit(normalize_text(value))
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    netloc = parts.netloc.lower()
    if host.endswith(".go.jp") and scheme == "http":
        scheme = "https"
    if scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[: -len(":443")]
    netloc = netloc.removeprefix("www.")
    path = unquote(parts.path).rstrip("/")
    pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not k.startswith("utm_")]
    return urlunsplit((scheme, netloc, path, urlencode(sorted(pairs)), ""))


def normalize_article_ref(value: object) -> str:
    """Canonical statute reference: 第3条の2, not 第３条之２ or 第3条 の 2."""
    text = unicodedata.normalize("NFKC", str(value))
    text = _SPACE_RE.sub("", text).replace("之", "の")
    text = _kanji_numerals_to_digits(text, "条")
    text = re.sub(r"の([〇一二三四五六七八九十]+)", lambda m: "の" + _kanji_or_same(m.group(1)), text)
    return re.sub(r"^(\d+)条", r"第\1条", text)


_KANJI_DIGITS = {"〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def _kanji_to_int(text: str) -> int:
    """Convert kanji numerals up to 99, such as 三十五 to 35."""
    total = 0
    current = 0
    for ch in text:
        if ch == "十":
            total += (current or 1) * 10
            current = 0
        elif ch in _KANJI_DIGITS:
            current = _KANJI_DIGITS[ch]
        else:
            raise ValueError(f"unsupported numeral {ch!r}")
    return total + current


def _kanji_or_same(text: str) -> str:
    try:
        return str(_kanji_to_int(text))
    except ValueError:
        return text


def _kanji_numerals_to_digits(text: str, suffix: str) -> str:
    """Replace kanji numerals before a suffix (条, 号, 丁目) with digits; leave unsupported forms alone."""

    def repl(match: re.Match[str]) -> str:
        try:
            return f"{_kanji_to_int(match.group(1))}{suffix}"
        except ValueError:
            return match.group(0)

    return re.sub(rf"([〇一二三四五六七八九十]+){suffix}", repl, text)


def normalize_law_number(value: object) -> str:
    """令和元年法律第一号 becomes 令和1年法律第1号."""
    text = _SPACE_RE.sub("", unicodedata.normalize("NFKC", str(value)))
    text = text.replace("元年", "1年")
    return _kanji_numerals_to_digits(text, "号")


_PREFECTURE_SHORT_FORMS = (("東京", "東京都"), ("大阪", "大阪府"), ("京都", "京都府"))


def normalize_address(value: object) -> str:
    """Strip the postal mark and code, use digits for 丁目, and add 都/府 to bare Tokyo, Osaka, Kyoto."""
    text = unicodedata.normalize("NFKC", str(value)).strip()
    text = re.sub(r"^〒?\s*\d{3}-?\d{4}\s*", "", text)
    text = _kanji_numerals_to_digits(text, "丁目")
    for short, full in _PREFECTURE_SHORT_FORMS:
        text = re.sub(rf"^{short}(?![都道府県市区町村郡])", full, text, count=1)
    return text


def normalize_corporate_number(value: object) -> str:
    """The 13 digits of a corporate number, with spaces and hyphens removed."""
    return re.sub(r"\D", "", unicodedata.normalize("NFKC", str(value)))


def normalize_invoice_number(value: object) -> str:
    """Upper-case T prefix and no spaces; a body that is not T + 13 digits stays unequal to any gold."""
    return re.sub(r"\s", "", unicodedata.normalize("NFKC", str(value))).upper()


def normalize_list(values: object) -> str:
    """Normalize each element, drop empties, dedupe, sort, and join with |."""
    items = {normalize_text(v) for v in (values or []) if normalize_text(v)}
    return "|".join(sorted(items))


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
    if name.endswith("law_number"):
        return normalize_law_number(value)
    if name.endswith("address"):
        return normalize_address(value)
    if name.endswith("corporate_number"):
        return normalize_corporate_number(value)
    if name.endswith("invoice_number"):
        return normalize_invoice_number(value)
    if name.endswith("_list"):
        return normalize_list(value)
    if name.endswith("postal_code"):
        return normalize_postal_code(value)
    if name.endswith("phone"):
        return normalize_phone(value)
    return normalize_text(value)
