from jpbench.cli import main


def test_show_prints_task_summary(capsys):
    assert main(["show", "invoice-number-verify"]) == 0
    out = capsys.readouterr().out
    assert "id: invoice-number-verify" in out and "difficulty: easy" in out


def test_show_unknown_task_fails(capsys):
    assert main(["show", "nope"]) == 1


def test_list_filters_by_difficulty(capsys):
    assert main(["list", "--difficulty", "hard"]) == 0
    lines = [l for l in capsys.readouterr().out.splitlines() if l.strip()]
    assert lines and all(" hard " in l for l in lines)
