# Contributing to JP-Bench

## Setup

```bash
pip install -e ".[dev]"
```

## Checks before opening a PR

```bash
jpbench validate   # schema and safety checks for every task file
pytest -q          # unit tests
```

## Adding a task

1. Create `tasks/<id>.yaml`. The file name must equal `id`.
2. `id` must be lowercase kebab-case (`[a-z0-9]+(-[a-z0-9]+)*`).
3. Provide both `instructions_ja` and `instructions_en`.
4. Every `form_fill` task must set `safety.stop_before_submit: true`. The validator rejects it otherwise.
5. Use fictional data for any form that could be submitted.
6. Filenames starting with `_` are skipped by the loader, so you can keep templates next to real tasks.

## Normalization changes

Add a test in `tests/` for every new normalization rule, including the notation variant it covers.
