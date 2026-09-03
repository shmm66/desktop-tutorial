from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum


class AssetClass(StrEnum):
    FOREX = "forex"
    CRYPTO = "crypto"


class TradeDirection(StrEnum):
    LONG = "long"
    SHORT = "short"


class TradeOutcome(StrEnum):
    OPEN = "open"
    WIN = "win"
    LOSS = "loss"
    BREAKEVEN = "breakeven"


def _decimal(value: Decimal | int | float | str | None) -> Decimal | None:
    return None if value is None else Decimal(str(value))


@dataclass(slots=True)
class JournalEntry:
    """Broker-neutral trade journal record shared by Forex and Crypto modes."""

    asset_class: AssetClass
    symbol: str
    direction: TradeDirection
    entry_price: Decimal | int | float | str
    quantity: Decimal | int | float | str
    opened_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str | None = None
    stop_loss: Decimal | int | float | str | None = None
    take_profit: Decimal | int | float | str | None = None
    exit_price: Decimal | int | float | str | None = None
    fees: Decimal | int | float | str = Decimal("0")
    funding: Decimal | int | float | str = Decimal("0")
    outcome: TradeOutcome = TradeOutcome.OPEN
    setup: str = ""
    thesis: str = ""
    emotion: str = ""
    notes: str = ""
    image_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol is required")
        if Decimal(str(self.entry_price)) <= 0:
            raise ValueError("entry_price must be positive")
        if Decimal(str(self.quantity)) <= 0:
            raise ValueError("quantity must be positive")
        self.entry_price = Decimal(str(self.entry_price))
        self.quantity = Decimal(str(self.quantity))
        self.stop_loss = _decimal(self.stop_loss)
        self.take_profit = _decimal(self.take_profit)
        self.exit_price = _decimal(self.exit_price)
        self.fees = Decimal(str(self.fees))
        self.funding = Decimal(str(self.funding))

    @property
    def gross_pnl(self) -> Decimal | None:
        if self.exit_price is None:
            return None
        delta = self.exit_price - self.entry_price
        if self.direction is TradeDirection.SHORT:
            delta = -delta
        return delta * self.quantity

    @property
    def net_pnl(self) -> Decimal | None:
        gross = self.gross_pnl
        return None if gross is None else gross - self.fees - self.funding
