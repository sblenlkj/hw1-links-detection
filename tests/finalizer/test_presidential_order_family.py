from links_detector.finalizer import LinksFinalizer
from links_detector.models import LawLink
from links_detector.utils.test_text_builder import TestTextBuilder


def test_presidential_order_family_variants_from_source_aliases() -> None:
    text = TestTextBuilder.build(
        [
            "ст. 10 Распоряжения Президента Российской Федерации №34-рп",
            "ст. 11 Распоряжения Президента России №426-рп",
            "ст. 12 Распоряжения Президента РФ №384-рп",
            "ст. 13 Распоряжения Президента №276-рп",
            "ст. 14 Распоряжения №37-рп",
            "ст. 15 РП №257-рп",
            "Согласно ст. 16 Распоряжению Президента РФ №201-рп",
            "В соответствии со ст. 17 Распоряжением Президента РФ №174-рп",
            "ст. 18 Распоряжения Президента РФ №134-рп от 09.05.2022 «О межведомственной рабочей группе по выработке новых механизмов в сфере валютного регулирования и международных расчетов»",
            "ст. 19 Распоряжения Президента РФ «О некоторых вопросах рабочей группы Совета при Президенте Российской Федерации по стратегическому развитию и национальным проектам»",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=21, article="10"),
        LawLink(law_id=22, article="11"),
        LawLink(law_id=23, article="12"),
        LawLink(law_id=24, article="13"),
        LawLink(law_id=25, article="14"),
        LawLink(law_id=26, article="15"),
        LawLink(law_id=27, article="16"),
        LawLink(law_id=28, article="17"),
        LawLink(law_id=31, article="18"),
        LawLink(law_id=33, article="19"),
    )


def test_presidential_order_duplicate_title_is_ambiguous() -> None:
    text = TestTextBuilder.build(
        [
            "ст. 20 «О членах коллегии Министерства Российской Федерации по делам гражданской обороны, чрезвычайным ситуациям и ликвидации последствий стихийных бедствий»",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.links == ()
    assert len(result.ambiguous) == 1
    assert {
        (link.law_id, link.article)
        for link in result.ambiguous[0].candidates
    } == {
        (38, "20"),
        (40, "20"),
    }


def test_presidential_order_number_disambiguates_duplicate_title() -> None:
    text = TestTextBuilder.build(
        [
            "ст. 21 Распоряжения Президента РФ №267-рп «О членах коллегии Министерства Российской Федерации по делам гражданской обороны, чрезвычайным ситуациям и ликвидации последствий стихийных бедствий»",
            "ст. 22 Распоряжения Президента РФ №370-рп «О членах коллегии Министерства Российской Федерации по делам гражданской обороны, чрезвычайным ситуациям и ликвидации последствий стихийных бедствий»",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=38, article="21"),
        LawLink(law_id=40, article="22"),
    )
