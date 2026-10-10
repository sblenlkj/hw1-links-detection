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


_NUMBER = r"\d+(?:\.\d+)*(?:(?:-|\s*[–—]\s*)\d+(?:\.\d+)*)?"
_QUOTED = r'(?:"[а-яёa-z0-9.]{1,5}"|«[а-яёa-z0-9.]{1,5}»)'
_LETTER = r"(?<!\w)(?![пч]\.)[а-яё](?!\w)"
_SEPARATOR = r"(?:\s*,\s*(?:(?:и|или)\s+)?|\s+(?:и|или)\s+)"
_MARKER_START = r"(?<!\w)(?<!\bт\.)(?<!\bт\.\s)"


def _enumeration(value: str) -> str:
    return rf"{value}(?:{_SEPARATOR}{value})*"


_NUMBER_VALUES = _enumeration(rf"(?:{_QUOTED}|{_NUMBER})")
_LETTER_VALUES = _enumeration(rf"(?:{_QUOTED}|{_LETTER})")
_VALUES = rf"(?:{_NUMBER_VALUES}|{_LETTER_VALUES})"
_ARTICLE_VALUES = _NUMBER_VALUES


def _extract_values(text: str) -> tuple[str, ...]:
    return tuple(
        re.sub(r"\s+", "", value).strip('"«»').replace("–", "-").replace("—", "-")
        for value in re.split(_SEPARATOR, text)
        if value
    )


class ArticleCandidateStrategy:
    _PATTERN = re.compile(
        rf"{_MARKER_START}(?:ст\.\s*|(?:стать(?:я|и|е|ю|ей|ями|ях|ям)|статей)\s+)(?P<values>{_ARTICLE_VALUES})(?!\w)"
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
        rf"{_MARKER_START}(?:ч\.\s*|част(?:ь|и|ью|ей|ями|ях|ям)\s+)(?P<values>{_VALUES})(?!\w)"
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
        rf"{_MARKER_START}(?:п\.\s*|(?:пунта|пункт(?:ы|а|у|ом|е|ов|ах|ам|ами)?)\s+)(?P<values>{_VALUES})(?!\w)"
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
        rf"{_MARKER_START}(?:пп\.\s*|подпункт(?:ы|а|у|ом|е|ов|ах|ам|ами)?\s+)(?P<values>{_VALUES})(?!\w)"
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
