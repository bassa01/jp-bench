import json
import subprocess
import sys

import pytest

from jpbench.adapters import SubprocessAdapter
from jpbench.cost import estimate_cost, load_price_table


def test_subprocess_adapter_sends_prompt_on_stdin():
    adapter = SubprocessAdapter([sys.executable, "-c", "import sys; print(sys.stdin.read().upper())"], {sys.executable})
    assert adapter.complete("abc").strip() == "ABC"


def test_subprocess_adapter_rejects_commands_off_allowlist():
    with pytest.raises(ValueError, match="allowlist"):
        SubprocessAdapter(["rm", "-rf", "/"], {sys.executable})


def test_subprocess_adapter_empty_allowlist_refuses_everything():
    with pytest.raises(ValueError):
        SubprocessAdapter([sys.executable], set())


def test_subprocess_adapter_reports_stderr_on_failure():
    adapter = SubprocessAdapter([sys.executable, "-c", "import sys; sys.stderr.write('bad'); sys.exit(3)"], {sys.executable})
    with pytest.raises(RuntimeError, match="exit 3: bad"):
        adapter.complete("x")


def test_subprocess_adapter_timeout_raises():
    adapter = SubprocessAdapter([sys.executable, "-c", "import time; time.sleep(5)"], {sys.executable}, timeout=0.2)
    with pytest.raises(subprocess.TimeoutExpired):
        adapter.complete("x")


def test_price_table_validation_and_cost(tmp_path):
    good = tmp_path / "prices.json"
    good.write_text(json.dumps({"m": {"input_per_mtok": 1.0, "output_per_mtok": 2.0}}), encoding="utf-8")
    table = load_price_table(good)
    assert estimate_cost(table, "m", 1_000_000, 500_000) == pytest.approx(2.0)
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"m": {"input_per_mtok": -1, "output_per_mtok": 2}}), encoding="utf-8")
    with pytest.raises(ValueError, match="non-negative"):
        load_price_table(bad)


def test_unknown_model_cost_fails():
    with pytest.raises(KeyError):
        estimate_cost({}, "missing", 1, 1)
