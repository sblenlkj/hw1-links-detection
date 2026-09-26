from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass

from links_detector.normalization import NormalizedText


@dataclass(frozen=True)
class ArticleMatch:
    start: int
    end: int
    original_text: str
    values: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.original_text} ({self.start}, {self.end})"


@dataclass(frozen=True)
class PartMatch:
    start: int
    end: int
    original_text: str
    values: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.original_text} ({self.start}, {self.end})"


@dataclass(frozen=True)
class PointMatch:
    start: int
    end: int
    original_text: str
    values: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.original_text} ({self.start}, {self.end})"


@dataclass(frozen=True)
class SubpointMatch:
    start: int
    end: int
    original_text: str
    values: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.original_text} ({self.start}, {self.end})"


_VALUE = r'(?:"[^"]+"|\d+(?:\.\d+)*|[а-яё])'
_VALUES = rf'{_VALUE}(?:\s*,\s*{_VALUE})*(?:\s+и\s+{_VALUE})?'


def _extract_values(text: str) -> tuple[str, ...]:
    return tuple(
        value.strip('"')
        for value in re.findall(_VALUE, text)
        if value != "и"
    )


class ArticleCandidateStrategy:
    _PATTERN = re.compile(
        rf"(?<!\w)(?:ст\.|стать(?:я|и|е|ю|ей|ями|ях|ям)|статей)\s+(?P<values>{_VALUES})(?!\w)"
    )

    def find(self, text: NormalizedText) -> Iterator[ArticleMatch]:
        for match in self._PATTERN.finditer(text.lowercase):
            start = match.start()
            end = match.end()
            original_text = text.original[start:end]
            yield ArticleMatch(
                start=start,
                end=end,
                original_text=original_text,
                values=_extract_values(match.group("values")),
            )


class PartCandidateStrategy:
    _PATTERN = re.compile(
        rf"(?<!\w)(?:ч\.|част(?:ь|и|ью|ей|ями|ях|ям))\s+(?P<values>{_VALUES})(?!\w)"
    )

    def find(self, text: NormalizedText) -> Iterator[PartMatch]:
        for match in self._PATTERN.finditer(text.lowercase):
            start = match.start()
            end = match.end()
            original_text = text.original[start:end]
            yield PartMatch(
                start=start,
                end=end,
                original_text=original_text,
                values=_extract_values(match.group("values")),
            )


class PointCandidateStrategy:
    _PATTERN = re.compile(
        rf"(?<!\w)(?:п\.|пунта|пункт(?:ы|а|у|ом|е|ов|ах|ам|ами)?)\s+(?P<values>{_VALUES})(?!\w)"
    )

    def find(self, text: NormalizedText) -> Iterator[PointMatch]:
        for match in self._PATTERN.finditer(text.lowercase):
            start = match.start()
            end = match.end()
            original_text = text.original[start:end]
            yield PointMatch(
                start=start,
                end=end,
                original_text=original_text,
                values=_extract_values(match.group("values")),
            )


class SubpointCandidateStrategy:
    _PATTERN = re.compile(
        rf"(?<!\w)(?:пп\.|подпункт(?:ы|а|у|ом|е|ов|ах|ам|ами)?)\s+(?P<values>{_VALUES})(?!\w)"
    )

    def find(self, text: NormalizedText) -> Iterator[SubpointMatch]:
        for match in self._PATTERN.finditer(text.lowercase):
            start = match.start()
            end = match.end()
            original_text = text.original[start:end]
            yield SubpointMatch(
                start=start,
                end=end,
                original_text=original_text,
                values=_extract_values(match.group("values")),
            )
