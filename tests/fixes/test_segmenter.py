from links_detector.candidates_segmenter.segmenter import CandidateSegmentor
from links_detector.normalization import TextNormalizer


def test_large_gap_splits_candidate_segment() -> None:
    raw = (
        "пункт 4 статьи 185 "
        + "обычный текст " * 15
        + "Федеральный закон №61-ФЗ"
    )
    text = TextNormalizer().normalize(raw)

    segments = CandidateSegmentor().segment(text)

    assert len(segments) == 2
    assert segments[0].valid is False
    assert segments[1].valid is False


def test_small_gap_keeps_structure_and_document_together() -> None:
    raw = "пункт 4 статьи 185 настоящего Федерального закона №61-ФЗ"
    text = TextNormalizer().normalize(raw)

    segments = CandidateSegmentor().segment(text)

    valid_segments = [segment for segment in segments if segment.valid]
    assert len(valid_segments) == 1
