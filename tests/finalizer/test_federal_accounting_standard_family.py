from links_detector.finalizer import LinksFinalizer
from links_detector.models import LawLink
from links_detector.utils.test_text_builder import TestTextBuilder


DUPLICATE_INTANGIBLE_TITLE = "НЕМАТЕРИАЛЬНЫЕ АКТИВЫ"
DUPLICATE_FIXED_ASSETS_TITLE = "ОСНОВНЫЕ СРЕДСТВА"


def test_federal_accounting_standard_unique_titles_from_source_aliases() -> None:
    text = TestTextBuilder.build(
        [
            'ст. 10 ФСБУ "БИОЛОГИЧЕСКИЕ АКТИВЫ"',
            'ст. 11 ФЕДЕРАЛЬНЫЙ СТАНДАРТ БУХГАЛТЕРСКОГО УЧЕТА "МЕТОД ДОЛЕВОГО УЧАСТИЯ"',
            'ст. 12 ФСБУ ГОСУДАРСТВЕННЫХ ФИНАНСОВ "УЧЕТ ОПЕРАЦИЙ СИСТЕМЫ КАЗНАЧЕЙСКИХ ПЛАТЕЖЕЙ"',
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=992, article="10"),
        LawLink(law_id=993, article="11"),
        LawLink(law_id=991, article="12"),
    )


def test_federal_accounting_standard_unique_title_resolves_without_family_marker() -> None:
    text = TestTextBuilder.build(
        [
            'ст. 20 "БИОЛОГИЧЕСКИЕ АКТИВЫ"',
            'ст. 21 "МЕТОД ДОЛЕВОГО УЧАСТИЯ"',
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=992, article="20"),
        LawLink(law_id=993, article="21"),
    )


def test_federal_accounting_standard_duplicate_titles_are_ambiguous() -> None:
    text = TestTextBuilder.build(
        [
            f'ст. 30 "{DUPLICATE_INTANGIBLE_TITLE}"',
            f'ст. 31 "{DUPLICATE_FIXED_ASSETS_TITLE}"',
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.links == ()
    assert len(result.ambiguous) == 2

    assert {
        (link.law_id, link.article)
        for link in result.ambiguous[0].candidates
    } == {
        (997, "30"),
        (1030, "30"),
    }

    assert {
        (link.law_id, link.article)
        for link in result.ambiguous[1].candidates
    } == {
        (1025, "31"),
        (1031, "31"),
    }


def test_federal_accounting_standard_fsbu_identifier_disambiguates_title() -> None:
    text = TestTextBuilder.build(
        [
            f'ст. 40 ФСБУ 14/2022 "{DUPLICATE_INTANGIBLE_TITLE}"',
            f'ст. 41 ФСБУ 6/2020 "{DUPLICATE_FIXED_ASSETS_TITLE}"',
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=1030, article="40"),
        LawLink(law_id=1031, article="41"),
    )
