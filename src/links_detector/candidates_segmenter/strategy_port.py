from collections.abc import Iterator
from typing import Protocol, TypeVar

from links_detector.normalization import NormalizedText


T = TypeVar("T", covariant=True)


class CandidateStrategyPort(Protocol[T]):
    def find(self, text: NormalizedText) -> Iterator[T]:
        ...
