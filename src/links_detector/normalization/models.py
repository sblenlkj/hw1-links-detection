from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizedText:
    original: str
    lowercase: str
