# Normalization rules

Scoring compares normalized values, so an agent is not punished for notation alone. Each rule has a test in `tests/`.

## Order of steps (`normalize_text`)

1. Replace legal-entity abbreviations (`(株)`, `㈱`, `(有)`, `(NPO)`, `(一社)` and similar) with full forms.
2. NFKC (full-width to half-width, compatibility characters).
3. Remove zero-width characters.
4. Map wave dash `〜` and `∼` to `~`.
5. Map dash variants (`‐`, `－`, `―`, `ー` used as a dash, and similar) to `-`.
6. Remove all whitespace.
7. Repeat steps 2 to 6 until nothing changes, so the result is idempotent.

## Field rules (`normalize_field`, chosen by field-name suffix)

| suffix | rule |
|---|---|
| `_date`, `date` | ISO 8601. Accepts 西暦, 和暦 (令和, 平成, 昭和), R/H/S abbreviations, 元年. Rejects impossible dates and dates after an era ended. |
| `_url` | Lowercase scheme and host, https for .go.jp, no www, no :443, no `utm_` parameters, sorted query, decoded path. |
| `_article` | 第3条の2. Kanji numerals become digits; 之 becomes の; 3条 gains 第. |
| `law_number` | 令和1年法律第1号. 元年 becomes 1年; kanji 号 numbers become digits. |
| `address` | Postal mark and code removed; 丁目 numbers as digits; 番地 becomes 番; 東京, 大阪, 京都 gain 都 or 府 when they stand alone or before a ward or city, not before 都, 府, 県, 市. |
| `corporate_number` | Digits only. |
| `invoice_number` | Upper-case T and no spaces. |
| `postal_code` | NNN-NNNN. |
| `phone` | Digits only; +81 numbers keep the country code and drop the trunk 0. |
| `_list` | Each element normalized, empties dropped, duplicates removed, sorted, joined with `|`. |
| `_flag` | `true` or `false` for はい/いいえ, 有/無, 有効/無効, yes/no. |

## Numbers (`normalize_number`)

Commas, spaces, 円, ¥, 人, 件, % are removed. 万 multiplies by 10,000 and 億 by 100,000,000. 約 and およそ are ignored. 無料 is 0. NaN and infinity are rejected.

## What is deliberately not normalized

- Zero and the letter O, one and the letter l: they can change meaning in identifiers.
- Kana: hiragana and katakana are not folded by default. `fold_kana` exists as an opt-in helper for comparison only.
- Numbers with an unexplained scale (for example 100 with no unit) are not scaled.
- Ranges such as 100〜200 are not reduced to a single number.
- Gold values are never normalized into something they did not say.
