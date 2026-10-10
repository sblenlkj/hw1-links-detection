from contextlib import asynccontextmanager
import logging

from fastapi import Depends, FastAPI, HTTPException

from links_detector.finalizer import FinalizerResult, LinksFinalizer
from links_detector.models import LawLink

from .dependencies import get_finalizer
from .models import (
    AmbiguousLinkResponse,
    AmbiguousLinksResponse,
    LawLinkResponse,
    LinksResponse,
    TextRequest,
)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.finalizer = LinksFinalizer()
    yield
    del app.state.finalizer


app = FastAPI(
    title="Law Links Service",
    description="Сервис для выделения юридических ссылок из текста",
    version="1.0.0",
    lifespan=lifespan,
)


def _law_link_response(link: LawLink) -> LawLinkResponse:
    return LawLinkResponse(
        law_id=link.law_id,
        article=link.article,
        point_article=link.point_article,
        subpoint_article=link.subpoint_article,
    )


def _extract(finalizer: LinksFinalizer, text: str) -> FinalizerResult:
    try:
        return finalizer.extract(text)
    except Exception as error:
        logger.exception("Unexpected error while detecting legal references")
        raise HTTPException(
            status_code=500,
            detail="Internal error while detecting legal references",
        ) from error


@app.post(
    "/detect",
    response_model=LinksResponse,
    summary="Detect legal references",
    description=(
        "Extracts all detected legal references in one list. "
        "Unambiguous references are returned together with every candidate "
        "from ambiguous references, in the order they appear in the text."
    ),
)
def detect(
    data: TextRequest,
    finalizer: LinksFinalizer = Depends(get_finalizer),
) -> LinksResponse:
    result = _extract(finalizer, data.text)
    return LinksResponse(
        links=[_law_link_response(link) for link in result.all_links]
    )


@app.post(
    "/detect-ambiguous",
    response_model=AmbiguousLinksResponse,
    summary="Detect ambiguous legal references",
    description=(
        "Extracts references that match more than one possible law_id. "
        "Each ambiguous reference is returned as a group of LawLink candidates."
    ),
)
def detect_ambiguous(
    data: TextRequest,
    finalizer: LinksFinalizer = Depends(get_finalizer),
) -> AmbiguousLinksResponse:
    result = _extract(finalizer, data.text)
    return AmbiguousLinksResponse(
        ambiguous=[
            AmbiguousLinkResponse(
                candidates=[
                    _law_link_response(link)
                    for link in item.candidates
                ]
            )
            for item in result.ambiguous
        ]
    )


@app.get(
    "/health",
    summary="Health check",
    description="Checks that the API service is running.",
)
def health_check() -> dict[str, str]:
    return {"status": "healthy"}
