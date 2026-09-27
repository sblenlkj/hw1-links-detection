from __future__ import annotations

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass

from links_detector.normalization import NormalizedText
from links_detector.utils.paths import PROJECT_ROOT


@dataclass(frozen=True)
class FamilyMatch:
    start: int
    end: int
    original_text: str
    family: str

    def __str__(self) -> str:
        return (
            f"{self.original_text} ({self.start}, {self.end}) "
            f"-> family={self.family}"
        )


class FamilyCandidateStrategy:
    """Find legal-document family markers."""

    _FAMILY_PATTERNS = (
        (
            "presidential_order",
            r"(?:Распоряжени\w{0,5}(?:\s+Президент\w{0,5})?|РП)",
        ),
        (
            "federal_law",
            r"(?:Федеральн\w{0,5}\s+закон\w{0,5}|ФЗ)",
        ),
        (
            "presidential_decree",
            r"(?:Указ\w{0,5}(?:\s+Президент\w{0,5})?)",
        ),
        (
            "fundamentals_of_legislation",
            r"(?:Основ\w{0,5}\s+законодательств\w{0,5})",
        ),
        (
            "rf_law",
            r"(?:Закон\w{0,5})",
        ),
        (
            "federal_accounting_standard",
            r"(?:ФЕДЕРАЛЬН\w{0,5}\s+СТАНДАРТ\w{0,5}\s+"
            r"БУХГАЛТЕРСК\w{0,5}\s+УЧЕТ\w{0,5}|ФСБУ)",
        ),
        (
            "accounting_regulation",
            r"(?:ПБУ|ПОЛОЖЕНИ\w{0,5}\s+ПО\s+"
            r"БУХГАЛТЕРСК\w{0,5}\s+УЧЕТ\w{0,5})",
        ),
        (
            "code",
            r"(?:кодекс\w{0,5}|Кодекс\w{0,5})",
        ),
    )

    def __init__(self) -> None:
        code_short_names = self._load_code_short_names()

        family_patterns = tuple(
            (
                family,
                self._extend_code_pattern(pattern, code_short_names)
                if family == "code"
                else pattern,
            )
            for family, pattern in self._FAMILY_PATTERNS
        )

        self._patterns = tuple(
            (
                family,
                re.compile(rf"(?<![\w-])(?:{pattern})(?!\w)"),
            )
            for family, pattern in family_patterns
        )

    @staticmethod
    def _load_code_short_names() -> tuple[str, ...]:
        path = PROJECT_ROOT / "law_aliases" / "families" / "codes.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        return tuple(
            item["short_name"]
            for item in data["items"].values()
            if item.get("short_name")
        )

    @staticmethod
    def _extend_code_pattern(
        pattern: str,
        short_names: tuple[str, ...],
    ) -> str:
        escaped = "|".join(
            re.escape(short_name)
            for short_name in sorted(short_names, key=len, reverse=True)
        )
        return rf"(?:{pattern}|{escaped})"

    def find(self, text: NormalizedText) -> Iterator[FamilyMatch]:
        matches: list[FamilyMatch] = []

        for family, pattern in self._patterns:
            for match in pattern.finditer(text.original):
                matches.append(
                    FamilyMatch(
                        start=match.start(),
                        end=match.end(),
                        original_text=text.original[match.start():match.end()],
                        family=family,
                    )
                )

        yield from sorted(matches, key=lambda match: (match.start, match.end))
