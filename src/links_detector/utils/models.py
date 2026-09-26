from dataclasses import dataclass
from pathlib import Path

from links_detector.models import LawLink


@dataclass(frozen=True)
class DatasetSample:
    index: int
    path: Path
    text: str
    expected: list[LawLink] | None = None
