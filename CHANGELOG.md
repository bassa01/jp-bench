# Changelog

All notable changes are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Contributing guide (`CONTRIBUTING.md`), security policy, code of conduct, data notice, and glossary.
- `jpbench show`, `jpbench doctor`, `jpbench completion`, `jpbench run`, and `jpbench report` subcommands.
- `--json` output for `list`, `show`, `validate`, and `prompt`; `--tag`, `--category`, `--difficulty`, `--all` filters.
- Report formats: Markdown, CSV, JSON (schema version 1), and HTML (escaped, no scripts). Wilson 95% interval and per-category and per-success-type tables.
- Success types: `boolean`, `date_range`, `enum` (with labels), `multi_answer`, `abstain`, `url_match`, `article_match`, `law_number_match`, `postal_code_match`, `phone_match`, `amount_yen_match`.
- Scoring options: `partial_credit`, `tolerance_mode` (relative or absolute), per-field results and confidence on each result.
- Task fields: `tags`, `review_status`, `created`, `updated`, `owner`, `snapshot_date`, `source_documents`, `version`, `deprecated`, `replaced_by`, `max_steps`, `timeout_seconds`, `allowed_domains`, `auth_method`.
- Runner: adapters (echo, error, recording, replay, fixed, subprocess with allowlist, OpenAI-compatible and Anthropic HTTP), retries, timeouts, fail-fast, concurrency with ordered results, repeats with pass@k, resume-safe JSONL, atomic writes, secret-free run metadata.
- Normalization: era abbreviations (R, H, S), impossible-date and era-end checks, postal codes, phone numbers, kana folding helper, corporate and invoice numbers, URL canonical form, statute references with kanji numerals, law numbers, addresses, number scales (万, 億), and list fields.
- Parsing: `ParseError` with the raw output, NaN and duplicate-key rejection, output size limit, answer kinds (json, refusal, empty, invalid), and refusal phrases.
- Prompts: template version in header, explicit JSON-only instruction, `prompt --json`, prompt hash, and length guard.
- CI: Python 3.10 to 3.13, ruff lint, coverage gate at 90%, pip cache, minimal permissions, concurrency cancel, nightly validation, Dependabot, issue and pull request templates.

### Changed
- `normalize_text` repeats NFKC and whitespace removal to a fixed point, so it is idempotent.
- Unknown keys in task files are rejected; titles must match their language; `gold_source` is required.
- Task ids must be lowercase kebab-case; `form_fill` tasks must use the `reached_state` rule.
- `null` predictions are treated as empty, not as the word "None".

### Fixed
- A `None` value in a prediction no longer compares equal to the string "None".
- Unregistered success types fail loudly instead of raising a bare `KeyError`.
- Empty predictions are reported as "no prediction".
- `submitted: "false"` (a string) is no longer read as a submission.
- Retries apply only to adapter errors, never to parse failures or timeouts.

## [0.1.0] - initial release
- Task schema, five bundled tasks, scorer with Japanese normalization, CLI, tests, and CI.
