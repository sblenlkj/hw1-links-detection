from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = PROJECT_ROOT / ".artifacts" / "codex_test_cases.json"
DEFAULT_INPUT = PROJECT_ROOT / ".artifacts" / "codex_generated_texts.json"
DEFAULT_REPORT = PROJECT_ROOT / ".artifacts" / "codex_test_report.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def post_detect(base_url: str, text: str, timeout: float) -> list[dict[str, Any]]:
    response = requests.post(
        f"{base_url.rstrip('/')}/detect",
        json={"text": text},
        timeout=timeout,
    )
    response.raise_for_status()

    payload = response.json()
    links = payload.get("links")
    if not isinstance(links, list):
        raise ValueError("Invalid /detect response: expected {links: [...]}")

    return links


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send Codex-generated texts to /detect and compare law_ids."
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--base-url", default="http://127.0.0.1:8978")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    cases = load_json(args.cases)
    generated = load_json(args.input)

    case_by_id = {
        run["run_id"]: run
        for run in cases["runs"]
    }
    text_by_id = {
        run["run_id"]: run["text"]
        for run in generated["runs"]
    }

    reports = []
    passed = 0

    for run_id, case in case_by_id.items():
        if run_id not in text_by_id:
            reports.append(
                {
                    "run_id": run_id,
                    "status": "ERROR",
                    "error": "Missing generated text for this run",
                }
            )
            continue

        text = text_by_id[run_id]

        expected_links = {
            (
                link["law_id"],
                link.get("article"),
                link.get("point_article"),
                link.get("subpoint_article"),
            )
            for target in case["targets"]
            for link in target["expected_links"]
        }
        expected_ids = sorted({link[0] for link in expected_links})

        try:
            links = post_detect(args.base_url, text, args.timeout)
            detected_links = {
                (
                    link["law_id"],
                    link.get("article"),
                    link.get("point_article"),
                    link.get("subpoint_article"),
                )
                for link in links
                if link.get("law_id") is not None
            }
            detected_ids = sorted({link[0] for link in detected_links})

            missed_links = sorted(
                expected_links - detected_links,
                key=lambda item: tuple("" if value is None else str(value) for value in item),
            )
            unexpected_links = sorted(
                detected_links - expected_links,
                key=lambda item: tuple("" if value is None else str(value) for value in item),
            )
            missed_ids = sorted(set(expected_ids) - set(detected_ids))
            unexpected_ids = sorted(set(detected_ids) - set(expected_ids))

            status = "PASS" if not missed_links else "FAIL"

            if status == "PASS":
                passed += 1

            reports.append(
                {
                    "run_id": run_id,
                    "status": status,
                    "expected_law_ids": expected_ids,
                    "detected_law_ids": detected_ids,
                    "missed_law_ids": missed_ids,
                    "unexpected_law_ids": unexpected_ids,
                    "expected_links": [
                        {
                            "law_id": item[0],
                            "article": item[1],
                            "point_article": item[2],
                            "subpoint_article": item[3],
                        }
                        for item in sorted(
                            expected_links,
                            key=lambda item: tuple(
                                "" if value is None else str(value)
                                for value in item
                            ),
                        )
                    ],
                    "missed_links": [
                        {
                            "law_id": item[0],
                            "article": item[1],
                            "point_article": item[2],
                            "subpoint_article": item[3],
                        }
                        for item in missed_links
                    ],
                    "unexpected_links": [
                        {
                            "law_id": item[0],
                            "article": item[1],
                            "point_article": item[2],
                            "subpoint_article": item[3],
                        }
                        for item in unexpected_links
                    ],
                    "targets": case["targets"],
                    "text": text,
                    "response_links": links,
                }
            )
        except Exception as exc:
            reports.append(
                {
                    "run_id": run_id,
                    "status": "ERROR",
                    "expected_law_ids": expected_ids,
                    "targets": case["targets"],
                    "text": text,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    result = {
        "summary": {
            "runs": len(case_by_id),
            "passed": passed,
            "failed_or_error": len(case_by_id) - passed,
        },
        "runs": reports,
    }

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        f"PASS {passed}/{len(case_by_id)}; "
        f"report: {args.report}"
    )
    for item in reports:
        print(
            f"RUN {item['run_id']}: {item['status']}"
            + (
                f" | missed_links={item.get('missed_links', [])}"
                if item["status"] != "PASS"
                else ""
            )
        )

    raise SystemExit(0 if passed == len(case_by_id) else 1)


if __name__ == "__main__":
    main()
