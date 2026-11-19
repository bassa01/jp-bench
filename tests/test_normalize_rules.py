import pytest

from jpbench.normalize import normalize_text


@pytest.mark.parametrize("raw", ["株式\u200b会社", "株式\u200c会社", "株式\u200d会社", "株式\ufeff会社"])
def test_zero_width_characters_are_removed(raw):
    assert normalize_text(raw) == "株式会社"
