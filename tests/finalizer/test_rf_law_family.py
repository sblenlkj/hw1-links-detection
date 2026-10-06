from links_detector.finalizer import LinksFinalizer
from links_detector.models import LawLink
from links_detector.utils.test_text_builder import TestTextBuilder


def test_rf_law_family_variants_from_source_aliases() -> None:
    text = TestTextBuilder.build(
        [
            "ст. 10 Закона Российской Федерации №5663-I",
            "ст. 11 Закона России №5485-I",
            "ст. 12 Закона РФ №5473-I",
            "ст. 13 Закона №5340-I",
            "Согласно ст. 14 Закону РФ №5242-I",
            "В соответствии со ст. 15 Законом Российской Федерации №5003-I",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=959, article="10"),
        LawLink(law_id=960, article="11"),
        LawLink(law_id=961, article="12"),
        LawLink(law_id=962, article="13"),
        LawLink(law_id=963, article="14"),
        LawLink(law_id=964, article="15"),
    )


def test_rf_law_number_date_and_title_variants() -> None:
    text = TestTextBuilder.build(
        [
            'ст. 20 Закона Российской Федерации №4979-I от 14.05.1993 «О ветеринарии»',
            'ст. 21 Закона России от 21.07.1993 «О государственной тайне»',
            'ст. 22 Закона РФ №943-I «О налоговых органах Российской Федерации»',
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=965, article="20"),
        LawLink(law_id=960, article="21"),
        LawLink(law_id=990, article="22"),
    )


def test_rf_law_titles_that_include_federal_law_prefix() -> None:
    text = TestTextBuilder.build(
        [
            'ст. 40 Федерального закона «О беженцах»',
            'ст. 41 Федерального закона «О прокуратуре Российской Федерации»',
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=970, article="40"),
        LawLink(law_id=985, article="41"),
    )


def test_rf_law_unique_titles_resolve_without_number() -> None:
    text = TestTextBuilder.build(
        [
            'ст. 30 Закона «О космической деятельности»',
            'ст. 31 Закона РФ «О государственной тайне»',
            'ст. 32 «О ветеринарии»',
            'ст. 33 «О налоговых органах Российской Федерации»',
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=959, article="30"),
        LawLink(law_id=960, article="31"),
        LawLink(law_id=965, article="32"),
        LawLink(law_id=990, article="33"),
    )
