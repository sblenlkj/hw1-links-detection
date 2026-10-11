from links_detector.api.app import detect
from links_detector.api.models import TextRequest
from links_detector.finalizer import LinksFinalizer


def test_detect_preserves_text_order_with_ambiguous_candidates() -> None:
    response = detect(
        TextRequest(
            text="ст. 1 НК РФ, ст. 2 ФЗ №127-ФЗ, ст. 3 НК РФ"
        ),
        LinksFinalizer(),
    )

    links = [(link.law_id, link.article) for link in response.links]

    assert links[0] == (15, "1")
    assert links[-1] == (15, "3")
    assert {law_id for law_id, article in links[1:-1] if article == "2"} == {
        55,
        142,
        386,
        456,
        488,
    }
