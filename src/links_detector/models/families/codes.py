"""Models for code-family documents.

The code family covers indices 0..20 in the source law_aliases dataset.

A code is represented by its canonical name and, when available, a short
abbreviation. Variants with "Российской Федерации", "России", and "РФ"
are intentionally not stored here and should be handled by matching logic.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CodeItem:
    law_id: int
    name: str
    short_name: str | None
