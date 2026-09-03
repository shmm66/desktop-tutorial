from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CryptoTrade:
    symbol: str
    direction: str
    quantity: float = 0.0
    entry: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    leverage: float = 1.0
    margin: float = 0.0
    fees: float = 0.0
    funding: float = 0.0
    liquidation_price: float | None = None
    exchange: str = ""
    setup: str = ""
    notes: str = ""
