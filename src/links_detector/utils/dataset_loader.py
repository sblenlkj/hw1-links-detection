from __future__ import annotations

import json
from pathlib import Path

from links_detector.models import LawLink

from .models import DatasetSample
from .paths import DATASET_DIR


class DatasetLoader:
    """Load dataset samples by numeric index."""

    def __init__(
        self,
        dataset_dir: Path = DATASET_DIR,
        markdown_subdir: str = "markdown",
        gold_subdir: str = "gold",
    ) -> None:
        self.dataset_dir = dataset_dir
        self.markdown_dir = dataset_dir / markdown_subdir
        self.gold_dir = dataset_dir / gold_subdir

    def load(self, index: int) -> DatasetSample:
        markdown_path = self._resolve_markdown(index)
        text = markdown_path.read_text(encoding="utf-8")

        gold_path = self.gold_dir / f"{markdown_path.stem}.jsonl"
        expected = self._load_expected(gold_path)

        return DatasetSample(
            index=index,
            path=markdown_path,
            text=text,
            expected=expected,
        )

    def _load_expected(self, gold_path: Path) -> list[LawLink] | None:
        if not gold_path.exists():
            return None

        result: list[LawLink] = []
        for line_number, line in enumerate(
            gold_path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not line.strip():
                continue

            raw = json.loads(line)
            if not isinstance(raw, dict):
                raise ValueError(
                    f"Gold JSONL line {line_number} must be an object: {gold_path}"
                )

            result.append(LawLink(**raw))

        return result

    def _resolve_markdown(self, index: int) -> Path:
        if index < 0:
            raise ValueError("Dataset index must be non-negative")

        prefix = f"{index:02d}_"
        matches = sorted(self.markdown_dir.glob(f"{prefix}*.md"))

        if not matches:
            raise FileNotFoundError(
                f"No dataset markdown file found for index {index:02d} in {self.markdown_dir}"
            )

        if len(matches) > 1:
            names = ", ".join(path.name for path in matches)
            raise RuntimeError(
                f"Multiple dataset files found for index {index:02d}: {names}"
            )

        return matches[0]
