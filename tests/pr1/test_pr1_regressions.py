from links_detector.finalizer import LinksFinalizer
from links_detector.models import LawLink


def test_numeric_point_does_not_absorb_preposition_before_article() -> None:
    result = LinksFinalizer().extract("в пункте 2 и в статье 5 НК РФ")

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=15, article="5", point_article="2"),
    )


def test_numeric_point_does_not_absorb_word_before_article() -> None:
    result = LinksFinalizer().extract("согласно пункту 1 и с учетом ст. 5 НК РФ")

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=15, article="5", point_article="1"),
    )


def test_t_p_is_not_parsed_as_point_marker() -> None:
    result = LinksFinalizer().extract("т.п. 5 человек, ГК РФ")

    assert result.links == ()
    assert result.ambiguous == ()


def test_spaced_t_p_is_not_parsed_as_point_marker() -> None:
    result = LinksFinalizer().extract("и т. п. 5 человек, ГК РФ")

    assert result.links == ()
    assert result.ambiguous == ()


def test_t_ch_is_not_parsed_as_part_marker() -> None:
    result = LinksFinalizer().extract("в т.ч. 5 человек, ГК РФ")

    assert result.links == ()
    assert result.ambiguous == ()


def test_hyphen_with_spaces_is_not_article_range() -> None:
    result = LinksFinalizer().extract("ст. 12 - 2024 года НК РФ")

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=15, article="12"),
    )


def test_all_links_preserve_text_order_across_ambiguous_segments() -> None:
    result = LinksFinalizer().extract(
        "ст. 1 НК РФ, ст. 2 ФЗ №127-ФЗ, ст. 3 НК РФ"
    )

    assert result.all_links[0] == LawLink(law_id=15, article="1")
    assert result.all_links[-1] == LawLink(law_id=15, article="3")

    middle = result.all_links[1:-1]
    assert {link.article for link in middle} == {"2"}
    assert {link.law_id for link in middle} == {55, 142, 386, 456, 488}


def test_exact_duplicates_are_deduplicated_but_different_detail_is_kept() -> None:
    result = LinksFinalizer().extract(
        "ст. 105 УК РФ, ст. 105 УК РФ, п. 5 ст. 105 УК РФ"
    )

    assert result.all_links == (
        LawLink(law_id=13, article="105"),
        LawLink(law_id=13, article="105", point_article="5"),
    )
