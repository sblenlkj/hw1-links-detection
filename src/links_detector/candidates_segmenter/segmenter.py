from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from links_detector.normalization import NormalizedText

from .models import Segment, SegmentMatch
from .strategies.discourse_strategy import (
    DiscourseCandidateStrategy,
    DiscourseMatch,
)
from .strategies.family_strategy import FamilyCandidateStrategy, FamilyMatch
from .strategies.quote_strategy import QuoteCandidateStrategy, QuoteMatch
from .strategies.structure_strategy import (
    ArticleCandidateStrategy,
    ArticleMatch,
    PartCandidateStrategy,
    PartMatch,
    PointCandidateStrategy,
    PointMatch,
    SubpointCandidateStrategy,
    SubpointMatch,
)


_STRUCTURE_TYPES = (ArticleMatch, PartMatch, PointMatch, SubpointMatch)
_DOCUMENT_TYPES = (FamilyMatch, QuoteMatch)
_MAX_MATCH_GAP = 120


class CandidateSegmentor:
    """Merge strategy matches and split them into candidate segments."""

    def __init__(self) -> None:
        self._strategies = (
            DiscourseCandidateStrategy(),
            SubpointCandidateStrategy(),
            PointCandidateStrategy(),
            PartCandidateStrategy(),
            ArticleCandidateStrategy(),
            FamilyCandidateStrategy(),
            QuoteCandidateStrategy(),
        )

    def segment(self, text: NormalizedText) -> list[Segment]:
        matches = self._find_matches(text)
        segments: list[Segment] = []
        current: list[SegmentMatch] = []

        for match in matches:
            gap_too_large = (
                current
                and match.start - current[-1].end > _MAX_MATCH_GAP
            )
            should_close = (
                current
                and (
                    gap_too_large
                    or isinstance(match, DiscourseMatch)
                    or (
                        isinstance(match, _STRUCTURE_TYPES)
                        and isinstance(current[-1], (FamilyMatch, QuoteMatch))
                    )
                )
            )

            if should_close:
                segments.append(self._build_segment(current))
                current = []

            current.append(match)

            if isinstance(match, QuoteMatch):
                segments.append(self._build_segment(current))
                current = []

        if current:
            segments.append(self._build_segment(current))

        return [
            replace(
                segment,
                next_start=segments[index + 1].start
                if index + 1 < len(segments)
                else len(text.original),
            )
            for index, segment in enumerate(segments)
        ]

    def _find_matches(self, text: NormalizedText) -> list[SegmentMatch]:
        matches: list[SegmentMatch] = []

        for strategy in self._strategies:
            matches.extend(strategy.find(text))

        return sorted(matches, key=lambda match: (match.start, match.end))

    @staticmethod
    def _build_segment(matches: Iterable[SegmentMatch]) -> Segment:
        matches_tuple = tuple(matches)

        has_structure = any(
            isinstance(match, _STRUCTURE_TYPES)
            for match in matches_tuple
        )
        has_document = any(
            isinstance(match, _DOCUMENT_TYPES)
            for match in matches_tuple
        )

        return Segment(
            matches=matches_tuple,
            valid=has_structure and has_document,
        )
