"""Model for structured legal-act families.

This model is shared by families whose source aliases follow the same pattern:

- presidential_order: indices 21..54
- federal_law: indices 55..542
- presidential_decree: indices 543..957
- fundamentals_of_legislation: index 958
- rf_law: indices 959..990

A concrete document in these families is represented by:
family metadata + law_id + number + date + title.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StructuredLawItem:
    law_id: int
    number: str
    date: str
    title: str
    title_unique: bool
