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

        unique_links = tuple(dict.fromkeys(expanded))

        return FinalizerResult(
            links=unique_links,
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
    def _expand(
        segment: Segment,
        resolved: ResolvedDocument,
        comment: str | None = None,
    ) -> list[LawLink]:
        articles: list[str | None] = []
        points: list[str | None] = []
        subpoints: list[str | None] = []

        for match in segment.matches:
            if isinstance(match, ArticleMatch):
                articles.extend(match.values)
            elif isinstance(match, (PartMatch, PointMatch)):
                points.extend(match.values)
            elif isinstance(match, SubpointMatch):
                subpoints.extend(match.values)

        article_values = tuple(articles) or (None,)
        point_values = tuple(points) or (None,)
        subpoint_values = tuple(subpoints) or (None,)

        return [
            LawLink(
                law_id=resolved.law_id,
                article=article,
                point_article=point,
                subpoint_article=subpoint,
                comment=comment,
            )
            for article, point, subpoint in product(
                article_values,
                point_values,
                subpoint_values,
            )
        ]
