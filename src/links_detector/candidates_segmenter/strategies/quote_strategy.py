from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass

from links_detector.normalization import NormalizedText


@dataclass(frozen=True)
class QuoteMatch:
    start: int
    end: int
    original_text: str
    value: str

    def __str__(self) -> str:
        return f"{self.original_text} ({self.start}, {self.end}) -> value={self.value}"


class QuoteCandidateStrategy:
    """Find quoted spans in text."""

    _PATTERN = re.compile(r'(?P<double>"[^"\n]+")|(?P<guillemets>«[^»\n]+»)')

    def find(self, text: NormalizedText) -> Iterator[QuoteMatch]:
        for match in self._PATTERN.finditer(text.original):
            start = match.start()
            end = match.end()
            original_text = text.original[start:end]
            value = original_text[1:-1]

            if sum(char.isalpha() for char in value) < 3:
                continue

            yield QuoteMatch(
                start=start,
                end=end,
                original_text=original_text,
                value=value,
            )
