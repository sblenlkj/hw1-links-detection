from links_detector.finalizer import LinksFinalizer
from links_detector.models import LawLink


def test_separate_references_do_not_form_cartesian_product() -> None:
    result = LinksFinalizer().extract("п. 1 ст. 5 и п. 2 ст. 7 НК РФ")

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=15, article="5", point_article="1"),
        LawLink(law_id=15, article="7", point_article="2"),
    )


def test_continuation_words_do_not_force_segment_break() -> None:
    result = LinksFinalizer().extract("ст. 5, а также ст. 7 НК РФ")

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=15, article="5"),
        LawLink(law_id=15, article="7"),
    )


def test_single_multi_value_reference_still_uses_cartesian_product() -> None:
    result = LinksFinalizer().extract("пункты 1 и 2 статей 5 и 7 НК РФ")

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=15, article="5", point_article="1"),
        LawLink(law_id=15, article="5", point_article="2"),
        LawLink(law_id=15, article="7", point_article="1"),
        LawLink(law_id=15, article="7", point_article="2"),
    )
