from pathlib import Path

from jpbench.prompt import prompt_hash
from jpbench.task import load_tasks

TASKS = Path(__file__).resolve().parent.parent / "tasks"


def test_prompt_hash_is_stable_and_language_sensitive():
    t = {x.id: x for x in load_tasks(TASKS)}["invoice-number-verify"]
    assert prompt_hash(t) == prompt_hash(t)
    assert prompt_hash(t, "en") != prompt_hash(t, "ja")
    assert len(prompt_hash(t)) == 16
