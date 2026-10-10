from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass

from links_detector.normalization import NormalizedText


@dataclass(frozen=True)
class DiscourseMatch:
    start: int
    end: int
    original_text: str
    continuation: bool = False

    def __str__(self) -> str:
        return f"{self.original_text} ({self.start}, {self.end})"


class DiscourseCandidateStrategy:
    """Find phrases that often introduce a legal reference."""

    DEFAULT_MARKERS = (
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
    )

    CONTINUATION_MARKERS = frozenset(
        (
            "кроме того",
            "дополнительно",
            "при этом",
            "также",
            "вместе с тем",
            "наряду с этим",
            "в частности",
        )
    )

    def __init__(self) -> None:
        escaped = sorted(
            (re.escape(marker) for marker in self.DEFAULT_MARKERS),
            key=len,
            reverse=True,
        )
        self._pattern = re.compile(r"(?<!\w)(?:" + "|".join(escaped) + r")(?!\w)")

    def find(self, text: NormalizedText) -> Iterator[DiscourseMatch]:
        for match in self._pattern.finditer(text.lowercase):
            start = match.start()
            end = match.end()
            yield DiscourseMatch(
                start=start,
                end=end,
                original_text=text.original[start:end],
                continuation=match.group() in self.CONTINUATION_MARKERS,
            )
