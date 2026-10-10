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
        ("ст. 3 Федерального закона № 402-ФЗ", [(224, "3", None, None)]),
        ("ст. 3 Федерального закона N 402-ФЗ", [(224, "3", None, None)]),
        ("ст. 3 Федерального закона № 152-ФЗ от 27.07.2006", [(330, "3", None, None)]),
        ("ст. 3 федерального закона №402-ФЗ", [(224, "3", None, None)]),
        ("ст. 5 НАЛОГОВОГО КОДЕКСА", [(15, "5", None, None)]),
        ("ст. 10 ГК РФ (в отличие от УК РФ)", [(5, "10", None, None)]),
        ("ст. 5, а также ст. 7 НК РФ", [(15, "5", None, None), (15, "7", None, None)]),
        (
            "статье 17 Конституции РФ, в соответствии с п. 5 ст. 105 УК РФ",
            [(13, "105", "5", None)],
        ),
        ("Налоговый кодекс РФ, статья 5", [(15, "5", None, None)]),
        ("НК РФ.ст. 5", [(15, "5", None, None)]),
        (
            "Налоговый кодекс РФ. Совсем другой абзац про что-то. "
            "Статья 5 устава компании.",
            [],
        ),
        (
            "ст. 5 Налогового кодекса РФ. Трудовой кодекс РФ, статья 7",
            [(15, "5", None, None), (10, "7", None, None)],
        ),
        (
            "ст. 5 НК РФ, Трудовой кодекс РФ, статья 7",
            [(15, "5", None, None), (10, "7", None, None)],
        ),
        (
            "ст. 5 НК РФ; Трудовой кодекс РФ, статья 7",
            [(15, "5", None, None), (10, "7", None, None)],
        ),
        (
            "ст. 5 НК РФ.п. 2 ст. 7 ГК РФ",
            [(15, "5", None, None), (5, "7", "2", None)],
        ),
    ],
)
def test_document_binding(finalizer: LinksFinalizer, text: str, expected) -> None:
    assert links(finalizer, text) == expected
