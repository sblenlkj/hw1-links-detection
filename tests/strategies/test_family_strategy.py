import pytest

from links_detector.candidates_segmenter.strategies.family_strategy import (
    FamilyCandidateStrategy,
)
from links_detector.normalization import TextNormalizer


def families(raw: str) -> list[tuple[str, str]]:
    text = TextNormalizer().normalize(raw)
    return [
        (match.original_text, match.family)
        for match in FamilyCandidateStrategy().find(text)
    ]


@pytest.mark.parametrize(
    ("raw", "family"),
    [
        ("Федеральному закону №218-ФЗ", "federal_law"),
        ("Федеральным законом №273-ФЗ", "federal_law"),
        ("ФЗ №402-ФЗ", "federal_law"),
        ("Указу Президента №123", "presidential_decree"),
        ("Указом Президента Российской Федерации", "presidential_decree"),
        ("Указ №456", "presidential_decree"),
        ("Распоряжению Президента №426-рп", "presidential_order"),
        ("Распоряжением Президента Российской Федерации", "presidential_order"),
        ("РП №15-рп", "presidential_order"),
        ("Основами законодательства Российской Федерации", "fundamentals_of_legislation"),
        ("Основам законодательства", "fundamentals_of_legislation"),
        ("Закон №2300-1", "rf_law"),
        ("Закону №2300-1", "rf_law"),
        ("ФСБУ 5/2019", "federal_accounting_standard"),
        ("ФЕДЕРАЛЬНОМУ СТАНДАРТУ БУХГАЛТЕРСКОГО УЧЕТА", "federal_accounting_standard"),
        ("ПБУ 19/02", "accounting_regulation"),
        ("ПОЛОЖЕНИЮ ПО БУХГАЛТЕРСКОМУ УЧЕТУ", "accounting_regulation"),
        ("Гражданский кодекс Российской Федерации", "code"),
        ("Гражданскому Кодексу Российской Федерации", "code"),
        ("НК РФ", "code"),
        ("КоАП РФ", "code"),
        ("АПК", "code"),
        ("ГК РФ", "code"),
    ],
)
def test_family_variants(raw: str, family: str) -> None:
    matches = families(raw)

    assert len(matches) == 1
    assert matches[0][1] == family


def test_federal_law_and_rf_law_are_case_sensitive_families() -> None:
    assert families("Федеральный закон №1-ФЗ") == [
        ("Федеральный закон", "federal_law")
    ]
    assert families("Закон №2300-1") == [("Закон", "rf_law")]


@pytest.mark.parametrize(
    "raw",
    [
        "обычный документ",
        "федеральный закон №1-ФЗ",
        "закон №2300-1",
    ],
)
def test_family_negative_cases(raw: str) -> None:
    assert families(raw) == []


def test_family_preserves_original_offsets() -> None:
    raw = "До ссылки: КоАП РФ после."
    text = TextNormalizer().normalize(raw)
    match = next(FamilyCandidateStrategy().find(text))

    assert match.family == "code"
    assert match.original_text == "КоАП"
    assert raw[match.start:match.end] == "КоАП"
