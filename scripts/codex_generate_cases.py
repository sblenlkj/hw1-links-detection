from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALIASES_DIR = PROJECT_ROOT / "law_aliases" / "families"
DEFAULT_OUTPUT = PROJECT_ROOT / ".artifacts" / "codex_test_cases.json"


def load_documents() -> list[tuple[str, tuple[str, ...], dict[str, Any]]]:
    documents: list[tuple[str, tuple[str, ...], dict[str, Any]]] = []

    for path in sorted(ALIASES_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        groups = data if isinstance(data, list) else [data]

        for group in groups:
            family = group["family"]
            family_name = family["name"]
            aliases = tuple(family.get("aliases", ()))

            for item in group["items"].values():
                documents.append((family_name, aliases, item))

    return documents


def choose_document_form(
    family: str,
    aliases: tuple[str, ...],
    item: dict[str, Any],
    rng: random.Random,
) -> str:
    options: list[str] = []

    if family == "code":
        if item.get("short_name"):
            options.append(item["short_name"])
        if item.get("name"):
            options.append(item["name"])

    elif family == "federal_accounting_standard":
        if item.get("fsbu"):
            options.append(f"ФСБУ {item['fsbu']}")
        if item.get("title"):
            options.append(f'"{item["title"]}"')

    elif family == "accounting_regulation":
        if item.get("pbu"):
            options.append(item["pbu"])
        if item.get("title"):
            options.append(f'"{item["title"]}"')

    else:
        number = item.get("number")
        date = item.get("date")
        title = item.get("title")

        if number:
            for alias in aliases:
                options.append(f"{alias} {number}")
                if date:
                    options.append(f"{alias} от {date} {number}")

        if title:
            options.append(f'"{title}"')

    if not options:
        raise ValueError(f"No usable document form for law_id={item['law_id']}")

    return rng.choice(options)


def choose_structure(
    rng: random.Random,
    kind: str,
) -> tuple[str, list[dict[str, str | None]]]:
    article_values = [str(value) for value in rng.sample(range(1, 251), k=2)]
    point_values = [str(value) for value in rng.sample(range(1, 13), k=2)]
    part_values = [str(value) for value in rng.sample(range(1, 9), k=2)]
    subpoint_values = rng.sample(("а", "б", "в", "г", "д"), k=2)

    article = article_values[0]
    point = point_values[0]
    part = part_values[0]
    subpoint = subpoint_values[0]

    if kind == "article":
        return (
            f"статья {article}",
            [{"article": article, "point_article": None, "subpoint_article": None}],
        )

    if kind == "articles":
        return (
            f"статьи {article_values[0]} и {article_values[1]}",
            [
                {"article": value, "point_article": None, "subpoint_article": None}
                for value in article_values
            ],
        )

    if kind == "point":
        return (
            f"пункт {point}",
            [{"article": None, "point_article": point, "subpoint_article": None}],
        )

    if kind == "points":
        return (
            f"пункты {point_values[0]} и {point_values[1]}",
            [
                {"article": None, "point_article": value, "subpoint_article": None}
                for value in point_values
            ],
        )

    if kind == "part_article":
        return (
            f"часть {part} статьи {article}",
            [{"article": article, "point_article": part, "subpoint_article": None}],
        )

    if kind == "parts_article":
        return (
            f"части {part_values[0]} и {part_values[1]} статьи {article}",
            [
                {"article": article, "point_article": value, "subpoint_article": None}
                for value in part_values
            ],
        )

    if kind == "point_article":
        return (
            f"пункт {point} статьи {article}",
            [{"article": article, "point_article": point, "subpoint_article": None}],
        )

    if kind == "points_article":
        return (
            f"пункты {point_values[0]} и {point_values[1]} статьи {article}",
            [
                {"article": article, "point_article": value, "subpoint_article": None}
                for value in point_values
            ],
        )

    if kind == "subpoint_point_article":
        return (
            f'подпункт "{subpoint}" пункта {point} статьи {article}',
            [
                {
                    "article": article,
                    "point_article": point,
                    "subpoint_article": subpoint,
                }
            ],
        )

    if kind == "subpoints_point_article":
        return (
            (
                f'подпункты "{subpoint_values[0]}" и "{subpoint_values[1]}" '
                f"пункта {point} статьи {article}"
            ),
            [
                {
                    "article": article,
                    "point_article": point,
                    "subpoint_article": value,
                }
                for value in subpoint_values
            ],
        )

    if kind == "points_articles":
        return (
            (
                f"пункты {point_values[0]} и {point_values[1]} "
                f"статей {article_values[0]} и {article_values[1]}"
            ),
            [
                {
                    "article": article_value,
                    "point_article": point_value,
                    "subpoint_article": None,
                }
                for article_value in article_values
                for point_value in point_values
            ],
        )

    raise ValueError(f"Unknown structure kind: {kind}")


STRUCTURE_KINDS = (
    "article",
    "articles",
    "point",
    "points",
    "part_article",
    "parts_article",
    "point_article",
    "points_article",
    "subpoint_point_article",
    "subpoints_point_article",
    "points_articles",
)


def sample_balanced(
    documents: list[tuple[str, tuple[str, ...], dict[str, Any]]],
    count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    by_family: dict[str, list[tuple[tuple[str, ...], dict[str, Any]]]] = defaultdict(list)

    for family, aliases, item in documents:
        by_family[family].append((aliases, item))

    if count > sum(len(items) for items in by_family.values()):
        raise ValueError("Requested more unique documents than available")

    families = list(by_family)
    rng.shuffle(families)

    quotas = {family: 0 for family in families}
    remaining = count

    for family in families:
        if remaining == 0:
            break
        quotas[family] = 1
        remaining -= 1

    while remaining > 0:
        available = [
            family
            for family in families
            if quotas[family] < len(by_family[family])
        ]
        if not available:
            raise ValueError("Not enough unique documents to satisfy balanced sampling")

        rng.shuffle(available)
        for family in available:
            if remaining == 0:
                break
            quotas[family] += 1
            remaining -= 1

    selected_documents: list[
        tuple[str, tuple[str, ...], dict[str, Any]]
    ] = []

    for family, quota in quotas.items():
        for aliases, item in rng.sample(by_family[family], k=quota):
            selected_documents.append((family, aliases, item))

    rng.shuffle(selected_documents)

    structure_kinds = list(STRUCTURE_KINDS)
    rng.shuffle(structure_kinds)
    chosen_kinds = [
        structure_kinds[index % len(structure_kinds)]
        for index in range(len(selected_documents))
    ]

    selected: list[dict[str, Any]] = []
    for (family, aliases, item), structure_kind in zip(
        selected_documents,
        chosen_kinds,
        strict=True,
    ):
        structure, expected_links = choose_structure(rng, structure_kind)
        selected.append(
            {
                "law_id": item["law_id"],
                "family": family,
                "structure_kind": structure_kind,
                "structure": structure,
                "document_form": choose_document_form(family, aliases, item, rng),
                "expected_links": [
                    {"law_id": item["law_id"], **link}
                    for link in expected_links
                ],
            }
        )

    return selected


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create balanced black-box test targets for Codex."
    )
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--references", type=int, default=3)
    parser.add_argument("--seed", type=int, default=137)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if args.runs < 1:
        raise SystemExit("--runs must be >= 1")
    if args.references < 1:
        raise SystemExit("--references must be >= 1")

    total = args.runs * args.references
    selected = sample_balanced(load_documents(), total, random.Random(args.seed))

    runs = []
    for index in range(args.runs):
        start = index * args.references
        end = start + args.references
        runs.append(
            {
                "run_id": index + 1,
                "targets": selected[start:end],
            }
        )

    family_counts: dict[str, int] = defaultdict(int)
    for item in selected:
        family_counts[item["family"]] += 1

    structure_counts: dict[str, int] = defaultdict(int)
    for item in selected:
        structure_counts[item["structure_kind"]] += 1

    payload = {
        "seed": args.seed,
        "runs": runs,
        "family_counts": dict(sorted(family_counts.items())),
        "structure_counts": dict(sorted(structure_counts.items())),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote {total} targets to {args.output}")
    print("Family distribution:")
    for family, count in payload["family_counts"].items():
        print(f"- {family}: {count}")

    print("Structure distribution:")
    for structure_kind, count in payload["structure_counts"].items():
        print(f"- {structure_kind}: {count}")


if __name__ == "__main__":
    main()
