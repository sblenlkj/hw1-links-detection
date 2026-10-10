import pytest
from fastapi import HTTPException

from links_detector.api.app import detect, detect_ambiguous
from links_detector.api.models import TextRequest
from links_detector.finalizer import LinksFinalizer


def test_detect_keeps_ambiguous_candidates_in_text_order() -> None:
    response = detect(
        TextRequest(text="ст. 1 НК РФ, ст. 2 ФЗ №127-ФЗ, ст. 3 НК РФ"),
        LinksFinalizer(),
    )
    links = [(link.law_id, link.article) for link in response.links]

    assert links[0] == (15, "1")
    assert links[-1] == (15, "3")
    assert len(links) == 7


def test_endpoints_report_internal_errors_the_same_way(monkeypatch) -> None:
    def fail(self, text):
        raise RuntimeError("boom")

    monkeypatch.setattr(LinksFinalizer, "extract", fail)
    finalizer = LinksFinalizer()

    for endpoint in (detect, detect_ambiguous):
        with pytest.raises(HTTPException) as error:
            endpoint(TextRequest(text="ст. 1 НК РФ"), finalizer)
        assert error.value.status_code == 500
