from pydantic import BaseModel


class TextRequest(BaseModel):
    text: str


class LawLinkResponse(BaseModel):
    law_id: int
    article: str | None = None
    point_article: str | None = None
    subpoint_article: str | None = None


class LinksResponse(BaseModel):
    links: list[LawLinkResponse]


class AmbiguousLinkResponse(BaseModel):
    candidates: list[LawLinkResponse]


class AmbiguousLinksResponse(BaseModel):
    ambiguous: list[AmbiguousLinkResponse]
