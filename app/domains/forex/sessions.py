from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ForexSession:
    name: str
    open_hour_utc: int
    close_hour_utc: int


SESSIONS = (
    ForexSession("Sydney", 21, 6),
    ForexSession("Tokyo", 0, 9),
    ForexSession("London", 8, 17),
    ForexSession("New York", 13, 22),
)
