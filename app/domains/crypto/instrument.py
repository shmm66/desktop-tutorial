from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CryptoMarketType(StrEnum):
    SPOT = "spot"
    FUTURES = "futures"


@dataclass(frozen=True, slots=True)
class CryptoInstrument:
    symbol: str
    exchange: str = ""
    market_type: CryptoMarketType = CryptoMarketType.SPOT
