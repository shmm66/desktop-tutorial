from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ForexTrade:
    symbol: str
    direction: str
    lot_size: float = 0.0
    entry: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    spread: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    session: str = ""
    setup: str = ""
    notes: str = ""
