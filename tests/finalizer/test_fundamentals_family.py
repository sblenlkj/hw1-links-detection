from links_detector.finalizer import LinksFinalizer
from links_detector.models import LawLink
from links_detector.utils.test_text_builder import TestTextBuilder


TITLE = "Основы законодательства Российской Федерации о нотариате"


def test_fundamentals_family_variants_from_source_aliases() -> None:
    text = TestTextBuilder.build(
        [
            "ст. 10 Основ законодательства Российской Федерации №4462-I",
            "ст. 11 Основ законодательства России №4462-I",
            "ст. 12 Основ законодательства РФ №4462-I",
            "ст. 13 Основ законодательства №4462-I",
            "ст. 14 Основ №4462-I",
            f"ст. 15 Основы «{TITLE}»",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=958, article="10"),
        LawLink(law_id=958, article="11"),
        LawLink(law_id=958, article="12"),
        LawLink(law_id=958, article="13"),
        LawLink(law_id=958, article="14"),
        LawLink(law_id=958, article="15"),
    )


def test_fundamentals_family_number_date_and_title_variants() -> None:
    text = TestTextBuilder.build(
        [
            f"ст. 20 Основ законодательства Российской Федерации №4462-I от 11.02.1993 «{TITLE}»",
            f"ст. 21 Основ законодательства России от 11.02.1993 «{TITLE}»",
            f"ст. 22 Основ законодательства РФ №4462-I «{TITLE}»",
            f"ст. 23 Основ №4462-I от 11.02.1993 «{TITLE}»",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=958, article="20"),
        LawLink(law_id=958, article="21"),
        LawLink(law_id=958, article="22"),
        LawLink(law_id=958, article="23"),
    )


def test_fundamentals_unique_title_resolves_without_family_marker() -> None:
    text = TestTextBuilder.build(
        [
            f"ст. 30 «{TITLE}»",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=958, article="30"),
    )
