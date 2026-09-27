from links_detector.finalizer import LinksFinalizer
from links_detector.models import LawLink

from links_detector.utils.test_text_builder import TestTextBuilder


def test_code_family_variants_from_source_aliases() -> None:
    text = TestTextBuilder.build(
        [
            "Согласно ст. 10 Арбитражного процессуального кодекса Российской Федерации",
            "ст. 11 п. 4 Арбитражного процессуального кодекса России",
            "ст. 12 Арбитражный процессуального кодекса РФ",
            "ст. 13 АПК России",
            "ст. 14 АПК РФ",
            "В соотвествии с ст. 15 АПК",
            "ст. 70 Трудового кодекса Российской Федерации",
            "ст. 213 Кодекса Российской Федерации об административных правонарушениях",
            "ст. 214 КоАП РФ",
        ]
    )

    result = LinksFinalizer().extract(text)

    assert result.ambiguous == ()
    assert result.links == (
        LawLink(law_id=0, article="10"),
        LawLink(law_id=0, article="11", point_article="4"),
        LawLink(law_id=0, article="12"),
        LawLink(law_id=0, article="13"),
        LawLink(law_id=0, article="14"),
        LawLink(law_id=0, article="15"),
        LawLink(law_id=10, article="70"),
        LawLink(law_id=17, article="213"),
        LawLink(law_id=17, article="214"),
    )
