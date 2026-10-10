import pytest

from links_detector.finalizer import LinksFinalizer


@pytest.fixture(scope="module")
def finalizer() -> LinksFinalizer:
    return LinksFinalizer()


def links(finalizer: LinksFinalizer, text: str) -> list[tuple]:
    return [
        (link.law_id, link.article, link.point_article, link.subpoint_article)
        for link in finalizer.extract(text).all_links
    ]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("п. 1 ст. 5 и п. 2 ст. 7 НК РФ", [(15, "5", "1", None), (15, "7", "2", None)]),
        ("п. 2 и п. 3 ст. 5 НК РФ", [(15, "5", "2", None), (15, "5", "3", None)]),
        (
            "статьи 5, 6, 7 и 8 и 9 НК РФ",
            [(15, value, None, None) for value in ("5", "6", "7", "8", "9")],
        ),
        (
            "пп. 1 п. 2, пп. 3 п. 4 ст. 5 НК РФ",
            [(15, "5", "2", "1"), (15, "5", "4", "3")],
        ),
        ("ч. 1 п. 2 ст. 5 УК РФ", [(13, "5", "1", "2")]),
        ("п. 2 ч. 1 ст. 12.8 КоАП", [(17, "12.8", "1", "2")]),
        (
            "пп. 1 п. 2, ч. 3 ст. 5 УК РФ",
            [(13, "5", "2", "1"), (13, "5", "3", None)],
        ),
        (
            "ст. 5 ч. 3 п. 2 пп. 1 УК РФ",
            [(13, "5", "3", None), (13, "5", "2", "1")],
        ),
        (
            "ч. 1 п. 2 пп. 3 ст. 5 УК РФ",
            [(13, "5", "1", None), (13, "5", "2", "3")],
        ),
        ("п.10 ст.5 НК РФ", [(15, "5", "10", None)]),
        ("пп. «а» п. 2 ст. 5 НК РФ", [(15, "5", "2", "а")]),
        ("п. 43.2-6 ст. 5 НК РФ", [(15, "5", "43.2-6", None)]),
        ("статьи 1-3 НК РФ", [(15, "1-3", None, None)]),
        ("статьи 5 – 7 НК РФ", [(15, "5-7", None, None)]),
        ("ст. 12 - 2024 года НК РФ", [(15, "12", None, None)]),
        ("в статье о налогах НК РФ", []),
        ("в пункте 2 и в статье 5 НК РФ", [(15, "5", "2", None)]),
        ("согласно пункту 1 и с учетом ст. 5 НК РФ", [(15, "5", "1", None)]),
        ("т.п. 5 человек, ГК РФ", []),
        ("и т. п. 5 человек, ГК РФ", []),
        ("в т.ч. 5 человек, ГК РФ", []),
        ("на результат. ст. 13 АПК РФ", [(0, "13", None, None)]),
    ],
)
def test_structure_expansion(finalizer: LinksFinalizer, text: str, expected) -> None:
    assert links(finalizer, text) == expected
