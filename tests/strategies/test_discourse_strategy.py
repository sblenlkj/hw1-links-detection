import pytest

from links_detector.candidates_segmenter.strategies.discourse_strategy import (
    DiscourseCandidateStrategy,
)
from links_detector.normalization import TextNormalizer


@pytest.mark.parametrize(
    "marker",
    [
        "в соответствии с",
        "на основании",
        "руководствуясь",
        "согласно",
        "в силу",
        "предусмотрено",
        "в порядке, установленном",
        "кроме того",
        "дополнительно",
        "при этом",
        "также",
        "вместе с тем",
        "наряду с этим",
        "наконец",
        "в частности",
    ],
)
def test_default_discourse_markers(marker: str) -> None:
    raw = f"Текст. {marker.capitalize()} ст. 14."
    text = TextNormalizer().normalize(raw)
    matches = list(DiscourseCandidateStrategy().find(text))

    assert len(matches) == 1
    assert matches[0].original_text.lower() == marker
    assert raw[matches[0].start:matches[0].end] == matches[0].original_text


def test_discourse_does_not_match_inside_word() -> None:
    raw = "несогласно"
    assert list(
        DiscourseCandidateStrategy().find(TextNormalizer().normalize(raw))
    ) == []
