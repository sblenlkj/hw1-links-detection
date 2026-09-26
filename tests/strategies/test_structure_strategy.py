import pytest

from links_detector.candidates_segmenter.strategies.structure_strategy import (
    ArticleCandidateStrategy,
    PartCandidateStrategy,
    PointCandidateStrategy,
    SubpointCandidateStrategy,
)
from links_detector.normalization import TextNormalizer


def values(strategy, raw: str) -> list[tuple[str, ...]]:
    text = TextNormalizer().normalize(raw)
    return [match.values for match in strategy.find(text)]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ст. 14", ("14",)),
        ("статьей 30.1", ("30.1",)),
        ("статьи 10", ("10",)),
        ("статью 10", ("10",)),
        ("статей 10, 11 и 12", ("10", "11", "12")),
    ],
)
def test_article_variants(raw: str, expected: tuple[str, ...]) -> None:
    assert values(ArticleCandidateStrategy(), raw) == [expected]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ч. 1", ("1",)),
        ("частью 3", ("3",)),
        ("части 2", ("2",)),
        ("частей 1, 2 и 4", ("1", "2", "4")),
        ("часть 3", ("3",)),
    ],
)
def test_part_variants(raw: str, expected: tuple[str, ...]) -> None:
    assert values(PartCandidateStrategy(), raw) == [expected]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("п. 2", ("2",)),
        ("пункта 3.345", ("3.345",)),
        ("пунктами 3.2, 4.1 и 7", ("3.2", "4.1", "7")),
        ("пунктов 1 и 2", ("1", "2")),
        ("пункта а", ("а",)),
        ("п. р", ("р",)),
        ("пунта б", ("б",)),
        ('пункта "б"', ("б",)),
        ("пункта 3.345, 23", ("3.345", "23")),
    ],
)
def test_point_variants(raw: str, expected: tuple[str, ...]) -> None:
    assert values(PointCandidateStrategy(), raw) == [expected]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("пп. 1", ("1",)),
        ("пп. 4, 5, 6 и 8", ("4", "5", "6", "8")),
        ('подпунктам "а", "б" и "в"', ("а", "б", "в")),
        ('подпунктов "а" и "б"', ("а", "б")),
        ("подпунктах а, б и с", ("а", "б", "с")),
        ("подпункту 2", ("2",)),
    ],
)
def test_subpoint_variants(raw: str, expected: tuple[str, ...]) -> None:
    assert values(SubpointCandidateStrategy(), raw) == [expected]


def test_structure_preserves_original_offsets() -> None:
    raw = "До ссылки: Ст. 30.1 после."
    text = TextNormalizer().normalize(raw)
    match = next(ArticleCandidateStrategy().find(text))

    assert match.original_text == "Ст. 30.1"
    assert raw[match.start:match.end] == match.original_text
    assert match.values == ("30.1",)


@pytest.mark.parametrize(
    ("strategy", "raw"),
    [
        (ArticleCandidateStrategy(), "статья без номера"),
        (PartCandidateStrategy(), "часть документа"),
        (PointCandidateStrategy(), "пункт договора"),
        (SubpointCandidateStrategy(), "подпункт текста"),
    ],
)
def test_structure_requires_value(strategy, raw: str) -> None:
    assert list(strategy.find(TextNormalizer().normalize(raw))) == []
