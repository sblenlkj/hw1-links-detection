from dataclasses import dataclass


@dataclass(frozen=True)
class ResolvedDocument:
    law_id: int
    family: str
