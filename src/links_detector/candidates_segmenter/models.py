from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from .strategies.discourse_strategy import DiscourseMatch
from .strategies.family_strategy import FamilyMatch
from .strategies.quote_strategy import QuoteMatch
from .strategies.structure_strategy import (
    ArticleMatch,
    PartMatch,
    PointMatch,
    SubpointMatch,
)


SegmentMatch: TypeAlias = (
    DiscourseMatch
    | ArticleMatch
    | PartMatch
    | PointMatch
    | SubpointMatch
    | FamilyMatch
    | QuoteMatch
)

StructureMatch: TypeAlias = ArticleMatch | PartMatch | PointMatch | SubpointMatch


@dataclass(frozen=True)
class Segment:
    matches: tuple[SegmentMatch, ...]
    valid: bool
    next_start: int | None = None

    @property
    def start(self) -> int:
        return self.matches[0].start

    @property
    def end(self) -> int:
        return self.matches[-1].end
