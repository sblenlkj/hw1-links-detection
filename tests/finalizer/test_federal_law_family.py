from links_detector.finalizer import LinksFinalizer
from links_detector.models import LawLink
from links_detector.utils.test_text_builder import TestTextBuilder


DUPLICATE_TITLE = 'О приостановлении действия части второй статьи 43 Закона Российской Федерации "О пенсионном обеспечении лиц, проходивших военную службу, службу в органах внутренних дел, Государственной противопожарной службе, органах по контролю за оборотом наркотических средств и психотропных веществ, учреждениях и органах уголовно-исполнительной системы, войсках национальной гвардии Российской Федерации, органах принудительного исполнения Российской Федерации, и их семей"'

NESTED_MICROFINANCE_TITLE = (
    'О защите прав и законных интересов физических лиц при осуществлении деятельности '
    'по возврату просроченной задолженности и о внесении изменений в Федеральный закон '
    '"О микрофинансовой деятельности и микрофинансовых организациях"'
)

NESTED_EDUCATION_TITLE = (
    'Об особенностях правового регулирования отношений в сфере образования в связи '
    'с принятием в Российскую Федерацию Республики Крым и образованием в составе '
    'Российской Федерации новых субъектов - Республики Крым и города федерального '
    'значения Севастополя и о внесении изменений в Федеральный закон '
    '"Об образовании в Российской Федерации"'
)


def test_federal_law_family_variants_from_source_aliases() -> None:
    text = TestTextBuilder.build(
        [
            "ст. 10 Федерального закона №419-ФЗ",
            "ст. 11 Федеральному закону №565-ФЗ",
            "ст. 12 Федеральным законом №540-ФЗ",
            "ст. 13 ФЗ №266-ФЗ",
            "Согласно ст. 14 ФЗ №207-ФЗ",
            "В соответствии со ст. 15 Федеральным законом №203-ФЗ",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=57, article="10"),
        LawLink(law_id=61, article="11"),
        LawLink(law_id=63, article="12"),
        LawLink(law_id=67, article="13"),
        LawLink(law_id=68, article="14"),
        LawLink(law_id=69, article="15"),
    )


def test_federal_law_duplicate_numbers_are_disambiguated_by_date() -> None:
    text = TestTextBuilder.build(
        [
            "ст. 20 Федерального закона №17-ФЗ от 17.02.2023",
            "ст. 21 Федерального закона №17-ФЗ от 25.02.2022",
            "ст. 22 Федерального закона №17-ФЗ от 10.01.2003",
            "ст. 23 Федерального закона №127-ФЗ от 07.06.2025",
            "ст. 24 Федерального закона №127-ФЗ от 26.10.2002",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=78, article="20"),
        LawLink(law_id=92, article="21"),
        LawLink(law_id=383, article="22"),
        LawLink(law_id=55, article="23"),
        LawLink(law_id=386, article="24"),
    )


def test_federal_law_duplicate_number_without_date_is_ambiguous() -> None:
    text = TestTextBuilder.build(
        [
            "ст. 30 Федерального закона №17-ФЗ",
            "ст. 31 Федерального закона №127-ФЗ",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.links == ()
    assert len(result.ambiguous) == 2
    assert {
        link.law_id for link in result.ambiguous[0].candidates
    } == {78, 92, 383}
    assert {
        link.law_id for link in result.ambiguous[1].candidates
    } == {55, 142, 386, 456, 488}


def test_federal_law_titles_with_nested_federal_law_quotes() -> None:
    text = TestTextBuilder.build(
        [
            f'ст. 38 «{NESTED_MICROFINANCE_TITLE}»',
            f'ст. 39 «{NESTED_EDUCATION_TITLE}»',
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=157, article="38"),
        LawLink(law_id=189, article="39"),
    )


def test_federal_law_unique_titles_resolve_without_number() -> None:
    text = TestTextBuilder.build(
        [
            "ст. 40 Федерального закона «О гражданстве Российской Федерации»",
            "ст. 41 Федерального закона «О занятости населения в Российской Федерации»",
            "ст. 42 «О железнодорожном транспорте в Российской Федерации»",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=70, article="40"),
        LawLink(law_id=61, article="41"),
        LawLink(law_id=383, article="42"),
    )


def test_federal_law_duplicate_title_is_ambiguous() -> None:
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
        (58, "50"),
        (62, "50"),
        (96, "50"),
    }


def test_federal_law_number_disambiguates_duplicate_title() -> None:
    text = TestTextBuilder.build(
        [
            f"ст. 51 Федерального закона №353-ФЗ «{DUPLICATE_TITLE}»",
            f"ст. 52 Федерального закона №547-ФЗ «{DUPLICATE_TITLE}»",
            f"ст. 53 Федерального закона №396-ФЗ «{DUPLICATE_TITLE}»",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=58, article="51"),
        LawLink(law_id=62, article="52"),
        LawLink(law_id=96, article="53"),
    )
