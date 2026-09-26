"""Focused diagnostics for structured-document resolution.

This intentionally mirrors DocumentResolver._resolve_structured step by step
without changing production resolver code.
"""

import re

from links_detector.candidates_segmenter.segmenter import CandidateSegmentor
from links_detector.candidates_segmenter.strategies.family_strategy import FamilyMatch
from links_detector.document_resolver import DocumentResolver
from links_detector.normalization import TextNormalizer


CASES = (
    "Согласно п. 1 Указа Президента РФ №240 применяются специальные правила.",
    "В соответствии с п. 2 Указа Президента Российской Федерации от 17.04.2025 №240 применяется упрощённый порядок.",
    "На основании пунктов 1 и 2 Указа Президента РФ №69 создаётся фонд.",
)


def matching_numbers(items: tuple[dict, ...], search_text: str) -> list[dict]:
    return [
        item
        for item in items
        if re.search(
            rf"(?<![\w-])(?:№\s*)?{re.escape(item['number'])}(?!\w)",
            search_text,
            re.IGNORECASE,
        )
    ]


def matching_dates(items: list[dict], search_text: str) -> list[dict]:
    return [item for item in items if item["date"] in search_text]


def main() -> None:
    resolver = DocumentResolver()
    segmentor = CandidateSegmentor()

    for case_index, raw in enumerate(CASES, start=1):
        text = TextNormalizer().normalize(raw)
        segments = segmentor.segment(text)

        print(f"\nCASE {case_index}")
        print("=" * 80)
        print(raw)

        for segment_index, segment in enumerate(segments, start=1):
            print(
                f"\nsegment #{segment_index}: valid={segment.valid} "
                f"span=({segment.start}, {segment.end}) "
                f"next_start={segment.next_start}"
            )
            for match in segment.matches:
                print(f"  {type(match).__name__}: {match}")

            family_match = next(
                (
                    match
                    for match in segment.matches
                    if isinstance(match, FamilyMatch)
                ),
                None,
            )

            if not segment.valid or family_match is None:
                print("  debug: skipped")
                continue

            family = family_match.family
            items = resolver._families.get(family, ())
            search_end = segment.next_start if segment.next_start is not None else len(text.original)
            search_text = text.original[segment.start:search_end]

            print(f"  family: {family}")
            print(f"  search_text: {search_text!r}")
            print(f"  family_items: {len(items)}")

            number_matches = matching_numbers(items, search_text)
            print(
                "  number_matches:",
                [
                    (item["law_id"], item["number"], item["date"])
                    for item in number_matches
                ],
            )

            candidates = number_matches if number_matches else list(items)
            date_matches = matching_dates(candidates, search_text)
            print(
                "  date_matches:",
                [
                    (item["law_id"], item["number"], item["date"])
                    for item in date_matches
                ],
            )

            if date_matches:
                candidates = date_matches

            print(
                "  final_candidates:",
                [
                    (item["law_id"], item["number"], item["date"])
                    for item in candidates
                ],
            )
            print("  direct_resolve:", resolver.resolve(segment, text))


if __name__ == "__main__":
    main()
