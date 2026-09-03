from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CryptoRules:
    """Pure spot/futures calculations. No UI/database dependencies."""

    def notional(self, quantity: float, entry: float) -> float:
        if quantity < 0 or entry < 0:
            raise ValueError("quantity and entry cannot be negative")
        return quantity * entry

    def margin_required(self, quantity: float, entry: float, leverage: float) -> float:
        if leverage <= 0:
            raise ValueError("leverage must be positive")
        return self.notional(quantity, entry) / leverage

    def liquidation_buffer(self, entry: float, liquidation_price: float) -> float:
        if entry <= 0 or liquidation_price < 0:
            raise ValueError("invalid prices")
        return abs(entry - liquidation_price) / entry

    def net_pnl(self, gross_pnl: float, fees: float, funding: float) -> float:
        return gross_pnl - fees - funding
