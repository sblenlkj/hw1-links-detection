from dataclasses import dataclass


@dataclass(frozen=True)
class LawLink:
    law_id: int
    article: str | None = None
    point_article: str | None = None
    subpoint_article: str | None = None
