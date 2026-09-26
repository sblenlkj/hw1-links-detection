from __future__ import annotations

import json
import re
from pathlib import Path

from links_detector.candidates_segmenter.models import Segment
from links_detector.candidates_segmenter.strategies.family_strategy import FamilyMatch
from links_detector.candidates_segmenter.strategies.quote_strategy import QuoteMatch
from links_detector.normalization import NormalizedText
from links_detector.utils.paths import PROJECT_ROOT

from .code_resolver import CodeResolver
from .models import ResolvedDocument


STRUCTURED_FAMILIES = {
    "presidential_order",
    "federal_law",
    "presidential_decree",
    "fundamentals_of_legislation",
    "rf_law",
}


def _normalize(value: str) -> str:
    value = value.lower().replace("ё", "е")
    return " ".join(value.split())


class DocumentResolver:
    """Resolve a valid segment to a law_id from compact family datasets."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or PROJECT_ROOT / "law_aliases" / "families"
        self._families = self._load_families()
        self._code_resolver = CodeResolver()

    def resolve(
        self,
        segment: Segment,
        text: NormalizedText,
    ) -> ResolvedDocument | None:
        if not segment.valid:
            return None

        family_match = next(
            (match for match in segment.matches if isinstance(match, FamilyMatch)),
            None,
        )
        quote_match = next(
            (match for match in segment.matches if isinstance(match, QuoteMatch)),
            None,
        )

        if family_match is not None:
            family = family_match.family
            items = self._families.get(family, ())
            law_id = self._resolve_family(
                family=family,
                items=items,
                quote=quote_match.value if quote_match else None,
                search_text=text.original[segment.start:segment.next_start],
            )
            if law_id is not None:
                return ResolvedDocument(law_id=law_id, family=family)

        if quote_match is not None:
            resolved = self._resolve_title_globally(quote_match.value)
            if resolved is not None:
                return resolved

        return None

    def _resolve_family(
        self,
        family: str,
        items: tuple[dict, ...],
        quote: str | None,
        search_text: str,
    ) -> int | None:
        if quote is not None:
            by_title = self._match_title(items, quote)
            if len(by_title) == 1:
                return by_title[0]["law_id"]
            if by_title:
                items = tuple(by_title)

        if family in STRUCTURED_FAMILIES:
            return self._resolve_structured(items, search_text)

        if family == "code":
            return self._code_resolver.resolve(search_text)

        if family == "accounting_regulation":
            return self._resolve_pbu(items, search_text)

        return None

    @staticmethod
    def _match_title(items: tuple[dict, ...], title: str) -> list[dict]:
        normalized_title = _normalize(title)
        return [
            item
            for item in items
            if item.get("title")
            and _normalize(item["title"]) == normalized_title
        ]

    @staticmethod
    def _resolve_structured(
        items: tuple[dict, ...],
        search_text: str,
    ) -> int | None:
        candidates = list(items)

        number_matches = [
            item
            for item in candidates
            if re.search(
                rf"(?<![\w-])(?:№\s*)?{re.escape(item['number'])}(?!\w)",
                search_text,
                re.IGNORECASE,
            )
        ]
        if number_matches:
            candidates = number_matches

        date_matches = [
            item
            for item in candidates
            if item["date"] in search_text
        ]
        if date_matches:
            candidates = date_matches

        if len(candidates) == 1:
            return candidates[0]["law_id"]

        return None

    @staticmethod
    def _resolve_pbu(items: tuple[dict, ...], search_text: str) -> int | None:
        normalized_text = _normalize(search_text)
        matches = [
            item
            for item in items
            if item.get("pbu")
            and _normalize(item["pbu"]) in normalized_text
        ]

        if len(matches) == 1:
            return matches[0]["law_id"]

        return None

    def _resolve_title_globally(self, title: str) -> ResolvedDocument | None:
        matches: list[ResolvedDocument] = []

        for family, items in self._families.items():
            for item in self._match_title(items, title):
                matches.append(
                    ResolvedDocument(
                        law_id=item["law_id"],
                        family=family,
                    )
                )

        if len(matches) == 1:
            return matches[0]

        return None

    def _load_families(self) -> dict[str, tuple[dict, ...]]:
        result: dict[str, tuple[dict, ...]] = {}

        structured = self._read_json("structured_acts.json")
        for block in structured:
            result[block["family"]["name"]] = tuple(block["items"].values())

        for filename in (
            "codes.json",
            "federal_accounting_standards.json",
            "accounting_regulations.json",
        ):
            block = self._read_json(filename)
            result[block["family"]["name"]] = tuple(block["items"].values())

        return result

    def _read_json(self, filename: str):
        path = self._data_dir / filename
        return json.loads(path.read_text(encoding="utf-8"))
