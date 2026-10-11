from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRUCTURED_ACTS_PATH = PROJECT_ROOT / "law_aliases" / "families" / "structured_acts.json"


def main() -> None:
    data = json.loads(STRUCTURED_ACTS_PATH.read_text(encoding="utf-8"))

    updated = 0

    for block in data:
        for item in block["items"].values():
            number = item.get("number")
            if number is None:
                continue

            if not number.startswith("№"):
                raise ValueError(
                    f"Unexpected number format for law_id={item['law_id']}: {number!r}"
                )

            item["number"] = number[1:]
            updated += 1

    STRUCTURED_ACTS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Updated {updated} numbers in {STRUCTURED_ACTS_PATH}")


if __name__ == "__main__":
    main()
