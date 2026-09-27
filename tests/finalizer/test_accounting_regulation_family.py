from links_detector.finalizer import LinksFinalizer
from links_detector.models import LawLink
from links_detector.utils.test_text_builder import TestTextBuilder


DUPLICATE_CASH_FLOW_TITLE = "ОТЧЕТ О ДВИЖЕНИИ ДЕНЕЖНЫХ СРЕДСТВ"
DUPLICATE_RELATED_PARTIES_TITLE = "ИНФОРМАЦИЯ О СВЯЗАННЫХ СТОРОНАХ"
GENERAL_ACCOUNTING_REGULATION_TITLE = (
    "ПОЛОЖЕНИЕ ПО ВЕДЕНИЮ БУХГАЛТЕРСКОГО УЧЕТА И "
    "БУХГАЛТЕРСКОЙ ОТЧЕТНОСТИ В РОССИЙСКОЙ ФЕДЕРАЦИИ"
)


def test_accounting_regulation_pbu_identifiers_from_source_aliases() -> None:
    text = TestTextBuilder.build(
        [
            "ст. 10 ПБУ 20/03",
            "ст. 11 ПБУ 9/99",
            "ст. 12 ПБУ 19/02",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=1035, article="10"),
        LawLink(law_id=1037, article="11"),
        LawLink(law_id=1053, article="12"),
    )


def test_accounting_regulation_unique_titles_from_source_aliases() -> None:
    text = TestTextBuilder.build(
        [
            'ст. 20 ПБУ 10/99 "РАСХОДЫ ОРГАНИЗАЦИИ"',
            'ст. 21 ПОЛОЖЕНИЕ ПО БУХГАЛТЕРСКОМУ УЧЕТУ '
            'ПБУ 13/2000 "УЧЕТ ГОСУДАРСТВЕННОЙ ПОМОЩИ"',
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=1046, article="20"),
        LawLink(law_id=1048, article="21"),
    )


def test_accounting_regulation_unique_title_resolves_without_family_marker() -> None:
    text = TestTextBuilder.build(
        [
            'ст. 30 "РАСХОДЫ ОРГАНИЗАЦИИ"',
            f'ст. 31 "{GENERAL_ACCOUNTING_REGULATION_TITLE}"',
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=1046, article="30"),
        LawLink(law_id=1036, article="31"),
    )


def test_accounting_regulation_duplicate_titles_are_ambiguous() -> None:
    text = TestTextBuilder.build(
        [
            f'ст. 40 "{DUPLICATE_CASH_FLOW_TITLE}"',
            f'ст. 41 "{DUPLICATE_RELATED_PARTIES_TITLE}"',
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.links == ()
    assert len(result.ambiguous) == 2

    assert {
        (link.law_id, link.article)
        for link in result.ambiguous[0].candidates
    } == {
        (1002, "40"),
        (1038, "40"),
    }

    assert {
        (link.law_id, link.article)
        for link in result.ambiguous[1].candidates
    } == {
        (1009, "41"),
        (1043, "41"),
    }


def test_accounting_regulation_pbu_identifier_disambiguates_title() -> None:
    text = TestTextBuilder.build(
        [
            f'ст. 50 ПБУ 23/2011 "{DUPLICATE_CASH_FLOW_TITLE}"',
            f'ст. 51 ПБУ 11/2008 "{DUPLICATE_RELATED_PARTIES_TITLE}"',
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=1038, article="50"),
        LawLink(law_id=1043, article="51"),
    )
