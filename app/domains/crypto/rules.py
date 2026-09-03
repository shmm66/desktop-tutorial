from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


Number = int | float | str | Decimal


def _d(value: Number) -> Decimal:
    return Decimal(str(value))


@dataclass(frozen=True, slots=True)
class CryptoRules:
    """Pure crypto spot/futures calculations with deterministic Decimal arithmetic."""

    def notional(self, quantity: Number, entry: Number) -> Decimal:
        qty = _d(quantity)
        price = _d(entry)
        if qty < 0 or price < 0:
            raise ValueError("quantity and entry cannot be negative")
        return qty * price

    def margin_required(self, quantity: Number, entry: Number, leverage: Number) -> Decimal:
        lev = _d(leverage)
        if lev <= 0:
            raise ValueError("leverage must be positive")
        return self.notional(quantity, entry) / lev

    def liquidation_buffer(self, entry: Number, liquidation_price: Number) -> Decimal:
        price = _d(entry)
        liq = _d(liquidation_price)
        if price <= 0 or liq < 0:
            raise ValueError("invalid prices")
        return abs(price - liq) / price

    def net_pnl(self, gross_pnl: Number, fees: Number, funding: Number) -> Decimal:
        return _d(gross_pnl) - _d(fees) - _d(funding)
