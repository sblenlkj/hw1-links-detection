from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from links_detector.finalizer import LinksFinalizer
from links_detector.models import LawLink

from .dependencies import get_finalizer
from .models import (
    AmbiguousLinkResponse,
    AmbiguousLinksResponse,
    LawLinkResponse,
    LinksResponse,
    TextRequest,
)


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


@app.post(
    "/detect",
    response_model=LinksResponse,
    summary="Detect legal references",
    description=(
        "Extracts legal references that resolve to exactly one law_id. "
        "Ambiguous references are excluded; use /detect-ambiguous to inspect them."
    ),
)
def detect(
    data: TextRequest,
    finalizer: LinksFinalizer = Depends(get_finalizer),
) -> LinksResponse:
    result = finalizer.extract(data.text)
    return LinksResponse(
        links=[_law_link_response(link) for link in result.links]
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
    result = finalizer.extract(data.text)
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
