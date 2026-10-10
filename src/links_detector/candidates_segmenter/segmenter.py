from __future__ import annotations

import re
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
_CLAUSE_END = re.compile(r"[,;]\s*")
_SENTENCE_END = re.compile(r"[.!?…]\s+(?=[А-ЯЁA-Z«\"])|\n\s*\n")


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
            has_structure = any(
                isinstance(item, _STRUCTURE_TYPES) for item in current
            )
            has_document = any(
                isinstance(item, _DOCUMENT_TYPES) for item in current
            )
            structure_after_document = (
                current
                and isinstance(match, _STRUCTURE_TYPES)
                and isinstance(current[-1], _DOCUMENT_TYPES)
            )
            carried = (
                self._carried_documents(current, match, text.original, has_structure)
                if structure_after_document and not gap_too_large
                else []
            )

            should_close = (
                current
                and (
                    gap_too_large
                    or (
                        isinstance(match, DiscourseMatch)
                        and (has_document or not match.continuation)
                    )
                    or (structure_after_document and carried is not current)
                )
            )

            if should_close:
                closed = [item for item in current if item not in carried]
                if closed:
                    segments.append(self._build_segment(closed))
                current = list(carried)

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

    @classmethod
    def _carried_documents(
        cls,
        current: list[SegmentMatch],
        structure: SegmentMatch,
        text: str,
        has_structure: bool,
    ) -> list[SegmentMatch]:
        if _SENTENCE_END.search(text, current[-1].end, structure.start):
            return []

        last_structure_end = max(
            (item.end for item in current if isinstance(item, _STRUCTURE_TYPES)),
            default=current[0].start,
        )
        start = cls._last_boundary(
            _SENTENCE_END, text, last_structure_end, current[-1].start
        )
        if has_structure:
            first_document = next(
                (
                    item for item in current
                    if isinstance(item, _DOCUMENT_TYPES)
                    and item.start >= last_structure_end
                ),
                current[-1],
            )
            clause_start = cls._last_boundary(
                _CLAUSE_END, text, first_document.end, current[-1].start
            )
            if clause_start is not None:
                start = max(start or 0, clause_start)

        if start is None:
            return [] if has_structure else current

        return [item for item in current if item.start >= start]

    @staticmethod
    def _last_boundary(
        pattern: re.Pattern[str],
        text: str,
        start: int,
        end: int,
    ) -> int | None:
        last = None
        for boundary in pattern.finditer(text, start, end):
            last = boundary.end()
        return last

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
