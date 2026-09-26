import pytest

from links_detector.candidates_segmenter.strategies.quote_strategy import (
    QuoteCandidateStrategy,
)
from links_detector.normalization import TextNormalizer


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('Федеральный закон "О персональных данных"', "О персональных данных"),
        ("Федеральный закон «О персональных данных»", "О персональных данных"),
        ('ПБУ 19/02 "УЧЕТ ФИНАНСОВЫХ ВЛОЖЕНИЙ"', "УЧЕТ ФИНАНСОВЫХ ВЛОЖЕНИЙ"),
        ('ФСБУ "АРЕНДА"', "АРЕНДА"),
    ],
)
def test_quote_variants(raw: str, expected: str) -> None:
    text = TextNormalizer().normalize(raw)
    matches = list(QuoteCandidateStrategy().find(text))

    assert len(matches) == 1
    assert matches[0].value == expected
    assert raw[matches[0].start:matches[0].end] == matches[0].original_text


@pytest.mark.parametrize(
    "raw",
    [
        "обычная фраза без кавычек",
        '"незакрытая цитата',
        "«незакрытая цитата",
        '"первая строка\nвторая строка"',
        '"а"',
        '"12"',
        '"1.2"',
    ],
)
def test_quote_negative_cases(raw: str) -> None:
    assert list(
        QuoteCandidateStrategy().find(TextNormalizer().normalize(raw))
    ) == []
