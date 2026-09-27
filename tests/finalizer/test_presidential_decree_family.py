from links_detector.finalizer import LinksFinalizer
from links_detector.models import LawLink
from links_detector.utils.test_text_builder import TestTextBuilder


DUPLICATE_TITLE = "О структуре федеральных органов исполнительной власти"


def test_presidential_decree_family_variants_from_source_aliases() -> None:
    text = TestTextBuilder.build(
        [
            "ст. 10 Указа Президента Российской Федерации №240",
            "ст. 11 Указа Президента России №25",
            "ст. 12 Указа Президента РФ №1126",
            "ст. 13 Указа Президента №1110",
            "ст. 14 Указа №840",
            "Согласно ст. 15 Указу Президента РФ №613 от 22.07.2024",
            "В соответствии со ст. 16 Указом Президента РФ №73 от 27.01.2024",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=543, article="10"),
        LawLink(law_id=546, article="11"),
        LawLink(law_id=547, article="12"),
        LawLink(law_id=548, article="13"),
        LawLink(law_id=550, article="14"),
        LawLink(law_id=557, article="15"),
        LawLink(law_id=563, article="16"),
    )


def test_presidential_decree_duplicate_number_is_disambiguated_by_date() -> None:
    text = TestTextBuilder.build(
        [
            "ст. 20 Указа Президента РФ №490 от 22.07.2022",
            "ст. 21 Указа Президента РФ №490 от 24.08.2021",
            "ст. 22 Указа Президента РФ №490 от 10.10.2019",
            "ст. 23 Указа Президента РФ №490 от 06.04.2004",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=619, article="20"),
        LawLink(law_id=655, article="21"),
        LawLink(law_id=711, article="22"),
        LawLink(law_id=922, article="23"),
    )


def test_presidential_decree_duplicate_number_without_date_is_ambiguous() -> None:
    text = TestTextBuilder.build(
        [
            "ст. 30 Указа Президента РФ №490",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.links == ()
    assert len(result.ambiguous) == 1
    assert {
        (link.law_id, link.article)
        for link in result.ambiguous[0].candidates
    } == {
        (619, "30"),
        (655, "30"),
        (711, "30"),
        (922, "30"),
    }


def test_presidential_decree_unique_titles_resolve_without_number() -> None:
    text = TestTextBuilder.build(
        [
            "ст. 40 Указа Президента «О временном порядке учета некоторых ценных бумаг»",
            "ст. 41 Указа «О развитии искусственного интеллекта в Российской Федерации»",
            "ст. 42 «Об утверждении Положения об Администрации Президента Российской Федерации»",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=550, article="40"),
        LawLink(law_id=711, article="41"),
        LawLink(law_id=922, article="42"),
    )


def test_presidential_decree_duplicate_title_is_ambiguous() -> None:
    text = TestTextBuilder.build(
        [
            f"ст. 50 «{DUPLICATE_TITLE}»",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.links == ()
    assert len(result.ambiguous) == 1
    assert {
        (link.law_id, link.article)
        for link in result.ambiguous[0].candidates
    } == {
        (561, "50"),
        (702, "50"),
        (740, "50"),
        (834, "50"),
    }


def test_presidential_decree_number_disambiguates_duplicate_title() -> None:
    text = TestTextBuilder.build(
        [
            f"ст. 51 Указа Президента РФ №326 «{DUPLICATE_TITLE}»",
            f"ст. 52 Указа Президента РФ №21 «{DUPLICATE_TITLE}»",
            f"ст. 53 Указа Президента РФ №215 «{DUPLICATE_TITLE}»",
            f"ст. 54 Указа Президента РФ №636 «{DUPLICATE_TITLE}»",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=561, article="51"),
        LawLink(law_id=702, article="52"),
        LawLink(law_id=740, article="53"),
        LawLink(law_id=834, article="54"),
    )
