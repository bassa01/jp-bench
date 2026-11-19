"""Price table loading and cost estimates. Prices are per million tokens, read from a file."""

from __future__ import annotations

import json
from pathlib import Path


def load_price_table(path: Path | str) -> dict[str, dict[str, float]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("price table must be a JSON object keyed by model name")
    table: dict[str, dict[str, float]] = {}
    for model, prices in raw.items():
        if not isinstance(prices, dict):
            raise TypeError(f"{model}: prices must be an object")
        entry: dict[str, float] = {}
        for key in ("input_per_mtok", "output_per_mtok"):
            value = prices.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{model}: {key} must be a non-negative number")
            entry[key] = float(value)
        table[model] = entry
    return table


def estimate_cost(table: dict[str, dict[str, float]], model: str, input_tokens: int, output_tokens: int) -> float:
    if model not in table:
        raise KeyError(f"no price for model {model!r}")
    prices = table[model]
    return (input_tokens * prices["input_per_mtok"] + output_tokens * prices["output_per_mtok"]) / 1_000_000
