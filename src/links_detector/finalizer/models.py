from dataclasses import dataclass

from links_detector.candidates_segmenter.models import Segment
from links_detector.document_resolver import ResolvedDocument
from links_detector.models import LawLink


@dataclass(frozen=True)
class SegmentResolution:
    segment: Segment
    resolved: tuple[ResolvedDocument, ...]


@dataclass(frozen=True)
class FinalizerStats:
    total_segments: int
    invalid_segments: int
    resolver_failed: int
    resolved_segments: int
    ambiguous_segments: int
    expanded_segments: int
    produced_links: int
    unique_links: int


@dataclass(frozen=True)
class AmbiguousLinks:
    candidates: tuple[LawLink, ...]


@dataclass(frozen=True)
class FinalizerResult:
    links: tuple[LawLink, ...]
    all_links: tuple[LawLink, ...]
    ambiguous: tuple[AmbiguousLinks, ...]
    stats: FinalizerStats
    segments: tuple[Segment, ...]
    resolutions: tuple[SegmentResolution, ...]
