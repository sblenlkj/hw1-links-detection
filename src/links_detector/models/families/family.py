from dataclasses import dataclass


@dataclass(frozen=True)
class Family:
    name: str
    aliases: tuple[str, ...]
