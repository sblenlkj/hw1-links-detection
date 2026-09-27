"""Models for accounting-document families.

Federal accounting standards are identified by their title and, when present,\nby an FSBУ identifier.

Accounting regulations (PBU) are identified by a PBU identifier and can
also be resolved by their title.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FederalAccountingStandardItem:
    law_id: int
    title: str


@dataclass(frozen=True)
class AccountingRegulationItem:
    law_id: int
    pbu: str | None
    title: str
