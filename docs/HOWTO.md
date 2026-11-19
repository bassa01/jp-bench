# How-to guides

## Add a task
1. Create `tasks/<id>.yaml`. The file name must equal `id` (lowercase kebab-case).
2. Fill the required keys: `title_ja`, `title_en`, `portal`, `category`, `difficulty`, `instructions_ja`, `instructions_en`, `inputs`, `success`, `safety`, `gold_source`.
3. Pick a success type from `jpbench/task.py` (`SUCCESS_TYPES`). Form tasks must use `reached_state` and set `safety.stop_before_submit: true`.
4. Run `jpbench validate` and `jpbench show <id>`. Then `pytest -q`.

## Add a normalization rule
1. Add the rule to `jpbench/normalize.py`. Keep it conservative: do not fold characters that change meaning.
2. Add a test in `tests/` with the notation variant and the expected output.
3. If the rule should apply to a field, add a suffix check in `normalize_field`.

## Add a success type
1. Add the name to `SUCCESS_TYPES` and to the field-requirement list in `task.py`.
2. Write a scorer `(task, pred, gold) -> TaskResult` in `scoring.py` and register it in `_SCORERS`.
3. Add a passing and a failing sample to `tests/test_bundled_tasks.py`.

## Add a model adapter
1. Implement `complete(prompt: str) -> str`. Raise an exception on transport failure; do not return an error string.
2. Read keys from the environment only. Refuse to start without them, and never put them in an error message.
3. Use https. Plain http is allowed only for localhost.

## Run offline with replay
1. Record outputs as JSON Lines with `prompt_hash` and `output` per line.
2. `jpbench run --adapter replay --replay recorded.jsonl --gold gold.json --out results.jsonl`.
3. `jpbench report --pred preds.json --gold gold.json --format md --output report.md`.
