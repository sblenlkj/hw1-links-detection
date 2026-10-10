from __future__ import annotations

from itertools import product

from links_detector.candidates_segmenter.segmenter import CandidateSegmentor
from links_detector.candidates_segmenter.models import Segment
from links_detector.candidates_segmenter.strategies.structure_strategy import (
    ArticleMatch,
    PartMatch,
    PointMatch,
    SubpointMatch,
)
from links_detector.document_resolver import DocumentResolver, ResolvedDocument
from links_detector.models import LawLink
from links_detector.normalization import TextNormalizer

from .models import AmbiguousLinks, FinalizerResult, FinalizerStats, SegmentResolution


StructureMatch = ArticleMatch | PartMatch | PointMatch | SubpointMatch

_LEVELS: dict[type, int] = {
    SubpointMatch: 0,
    PointMatch: 1,
    PartMatch: 2,
    ArticleMatch: 3,
}

_NESTED_LEVELS = {SubpointMatch, PointMatch, PartMatch}


def _split_overfull(chain: list[StructureMatch]) -> list[list[StructureMatch]]:
    if not {type(item) for item in chain} >= _NESTED_LEVELS:
        return [chain]

    without_part = [item for item in chain if not isinstance(item, PartMatch)]
    part = [
        item for item in chain
        if isinstance(item, (PartMatch, ArticleMatch))
    ]

    def first_nested(items: list[StructureMatch]) -> int:
        return min(
            item.start for item in items if not isinstance(item, ArticleMatch)
        )

    return sorted((without_part, part), key=first_nested)


class LinksFinalizer:
    """Facade for segmentation, document resolution and LawLink expansion."""

    def __init__(self) -> None:
        self._normalizer = TextNormalizer()
        self._segmentor = CandidateSegmentor()
        self._resolver = DocumentResolver()

    def extract(self, text: str) -> FinalizerResult:
        normalized = self._normalizer.normalize(text)
        segments = self._segmentor.segment(normalized)

        invalid_segments = 0
        resolver_failed = 0
        resolved_segments = 0
        ambiguous_segments = 0
        expanded_segments = 0
        expanded: list[LawLink] = []
        ordered: list[LawLink] = []
        ambiguous: list[AmbiguousLinks] = []
        resolutions: list[SegmentResolution] = []

        for segment in segments:
            if not segment.valid:
                invalid_segments += 1
                resolutions.append(SegmentResolution(segment=segment, resolved=()))
                continue

            resolved = self._resolver.resolve(segment, normalized)
            resolutions.append(SegmentResolution(segment=segment, resolved=resolved))
            if not resolved:
                resolver_failed += 1
                continue

            resolved_segments += 1
            if len(resolved) > 1:
                ambiguous_segments += 1

            candidate_ids = ", ".join(str(item.law_id) for item in resolved)
            comment = (
                f"ambiguous law_id: candidates {candidate_ids}"
                if len(resolved) > 1
                else None
            )

            segment_links: list[LawLink] = []
            for document in resolved:
                segment_links.extend(self._expand(segment, document, comment=comment))

            if len(segment_links) > 1:
                expanded_segments += 1

            if len(resolved) > 1:
                ambiguous.append(AmbiguousLinks(candidates=tuple(segment_links)))
            else:
                expanded.extend(segment_links)
            ordered.extend(segment_links)

        unique_links = tuple(dict.fromkeys(expanded))

        return FinalizerResult(
            links=unique_links,
            all_links=tuple(dict.fromkeys(ordered)),
            ambiguous=tuple(ambiguous),
            stats=FinalizerStats(
                total_segments=len(segments),
                invalid_segments=invalid_segments,
                resolver_failed=resolver_failed,
                resolved_segments=resolved_segments,
                ambiguous_segments=ambiguous_segments,
                expanded_segments=expanded_segments,
                produced_links=len(expanded) + sum(
                    len(item.candidates) for item in ambiguous
                ),
                unique_links=len(unique_links),
            ),
            segments=tuple(segments),
            resolutions=tuple(resolutions),
        )

    @staticmethod
    def _split_chains(segment: Segment) -> list[list[StructureMatch]]:
        chains: list[list[StructureMatch]] = []
        current: list[StructureMatch] = []
        direction = 0

        for match in segment.matches:
            if type(match) not in _LEVELS:
                continue

            level = _LEVELS[type(match)]
            if current:
                step = level - _LEVELS[type(current[-1])]
                enumeration = step == 0 and not direction
                breaks_order = step == 0 or step * direction < 0
                if breaks_order and not enumeration:
                    chains.append(current)
                    current = []
                    direction = 0
                elif step:
                    direction = 1 if step > 0 else -1

            current.append(match)

        if current:
            chains.append(current)

        absorbed: set[int] = set()
        for index in range(len(chains) - 2, -1, -1):
            top = max(_LEVELS[type(match)] for match in chains[index])
            inherited = [
                match for match in chains[index + 1]
                if _LEVELS[type(match)] > top
            ]
            chains[index] = chains[index] + inherited
            if len(inherited) == len(chains[index + 1]):
                absorbed.add(index + 1)

        return [
            split
            for index, chain in enumerate(chains)
            if index not in absorbed
            for split in _split_overfull(chain)
        ]

    @classmethod
    def _expand(
        cls,
        segment: Segment,
        resolved: ResolvedDocument,
        comment: str | None = None,
    ) -> list[LawLink]:
        links: list[LawLink] = []
        for chain in cls._split_chains(segment):
            links.extend(cls._expand_chain(chain, resolved, comment))
        return links

    @staticmethod
    def _expand_chain(
        chain: list[StructureMatch],
        resolved: ResolvedDocument,
        comment: str | None,
    ) -> list[LawLink]:
        by_type: dict[type, tuple[str, ...]] = {}
        for match in chain:
            by_type[type(match)] = by_type.get(type(match), ()) + match.values

        articles = by_type.get(ArticleMatch, ())
        parts = by_type.get(PartMatch, ())
        points = by_type.get(PointMatch, ())
        subpoints = by_type.get(SubpointMatch, ())

        if parts and points and not subpoints:
            point_values, subpoint_values = parts, points
        else:
            point_values = points or parts
            subpoint_values = subpoints

        return [
            LawLink(
                law_id=resolved.law_id,
                article=article,
                point_article=point,
                subpoint_article=subpoint,
                comment=comment,
            )
            for article, point, subpoint in product(
                articles or (None,),
                point_values or (None,),
                subpoint_values or (None,),
            )
        ]
