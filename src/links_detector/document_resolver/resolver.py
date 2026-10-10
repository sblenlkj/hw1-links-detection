from __future__ import annotations

import json
import re
from pathlib import Path

from links_detector.candidates_segmenter.models import Segment
from links_detector.candidates_segmenter.strategies.discourse_strategy import DiscourseMatch
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
    ) -> tuple[ResolvedDocument, ...]:
        if not segment.valid:
            return ()

        structures = [
            match for match in segment.matches
            if not isinstance(match, (FamilyMatch, QuoteMatch, DiscourseMatch))
        ]
        documents = [
            match for match in segment.matches
            if isinstance(match, (FamilyMatch, QuoteMatch))
        ]

        for family_match in self._family_candidates(segment, structures):
            following = [
                match for match in documents if match.start > family_match.start
            ]
            window_end = (
                following[0].start
                if following and isinstance(following[0], FamilyMatch)
                else segment.next_start
            )
            quote_match = next(
                (match for match in following if isinstance(match, QuoteMatch)),
                None,
            )
            family = family_match.family
            law_ids = self._resolve_family(
                family=family,
                items=self._families.get(family, ()),
                quote=quote_match.value if quote_match else None,
                search_text=text.original[family_match.start:window_end],
                full_text=text.original,
                anchor=family_match,
            )
            if law_ids:
                return tuple(
                    ResolvedDocument(law_id=law_id, family=family)
                    for law_id in law_ids
                )

        quote_match = next(
            (match for match in segment.matches if isinstance(match, QuoteMatch)),
            None,
        )
        if quote_match is not None:
            resolved = self._resolve_title_globally(quote_match.value)
            if resolved:
                return resolved

        return ()

    @staticmethod
    def _family_candidates(
        segment: Segment,
        structures: list,
    ) -> list[FamilyMatch]:
        families = [
            match for match in segment.matches if isinstance(match, FamilyMatch)
        ]
        if not structures:
            return families

        last_structure_end = structures[-1].end
        after = [match for match in families if match.start >= last_structure_end]
        before = [match for match in families if match.start < last_structure_end]
        return after + before[::-1]

    def _resolve_family(
        self,
        family: str,
        items: tuple[dict, ...],
        quote: str | None,
        search_text: str,
        full_text: str,
        anchor: FamilyMatch,
    ) -> tuple[int, ...]:
        if quote is not None:
            by_title = self._match_title(items, quote)
            if len(by_title) == 1:
                return (by_title[0]["law_id"],)
            if by_title:
                items = tuple(by_title)

        if family in STRUCTURED_FAMILIES:
            return self._resolve_structured(items, search_text)

        if family == "code":
            law_id = self._code_resolver.resolve(
                full_text,
                anchor_start=anchor.start,
                anchor_end=anchor.end,
            )
            return (law_id,) if law_id is not None else ()

        if family == "federal_accounting_standard":
            law_id = self._resolve_fsbu(items, search_text)
            return (law_id,) if law_id is not None else ()

        if family == "accounting_regulation":
            law_id = self._resolve_pbu(items, search_text)
            return (law_id,) if law_id is not None else ()

        return ()

    @staticmethod
    def _match_title(items: tuple[dict, ...], title: str) -> list[dict]:
        normalized_title = _normalize(title)
        matches: list[dict] = []

        for item in items:
            item_title = item.get("title")
            if not item_title:
                continue

            if _normalize(item_title) == normalized_title:
                matches.append(item)
                continue

            nested_federal_law = re.fullmatch(
                r'Федеральный\s+закон\s+["«](.+?)["»]',
                item_title,
                re.IGNORECASE,
            )
            if (
                nested_federal_law
                and _normalize(nested_federal_law.group(1)) == normalized_title
            ):
                matches.append(item)

        return matches

    @staticmethod
    def _resolve_structured(
        items: tuple[dict, ...],
        search_text: str,
    ) -> tuple[int, ...]:
        candidates = list(items)

        number_matches = [
            item
            for item in candidates
            if re.search(
                rf"(?<![\w-])(?:№|N)\s*{re.escape(item['number'].lstrip('№'))}(?!\w)",
                search_text,
                re.IGNORECASE,
            )
        ]
        if not number_matches:
            return ()

        candidates = number_matches

        date_matches = [
            item
            for item in candidates
            if item["date"] in search_text
        ]
        if date_matches:
            candidates = date_matches

        return tuple(item["law_id"] for item in candidates)

    @staticmethod
    def _resolve_fsbu(items: tuple[dict, ...], search_text: str) -> int | None:
        normalized_text = _normalize(search_text)
        matches = [
            item
            for item in items
            if item.get("fsbu")
            and re.search(
                rf"(?<![\w/])ФСБУ\s+{re.escape(item['fsbu'])}(?![\w/])",
                normalized_text,
                re.IGNORECASE,
            )
        ]

        if len(matches) == 1:
            return matches[0]["law_id"]

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

    def _resolve_title_globally(self, title: str) -> tuple[ResolvedDocument, ...]:
        matches: list[ResolvedDocument] = []

        for family, items in self._families.items():
            for item in self._match_title(items, title):
                matches.append(
                    ResolvedDocument(
                        law_id=item["law_id"],
                        family=family,
                    )
                )

        return tuple(matches)

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
