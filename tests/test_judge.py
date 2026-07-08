from instructvault.judge import _parse_score


def test_parse_decimal_score() -> None:
    assert _parse_score("0.8") == 0.8


def test_parse_fraction_score() -> None:
    assert _parse_score("8/10") == 0.8


def test_parse_percent_score() -> None:
    assert _parse_score("80%") == 0.8