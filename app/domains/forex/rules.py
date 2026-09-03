from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ForexRules:
    """Pure Forex calculations. No UI/database dependencies."""

    pip_size: float = 0.0001
    lot_units: int = 100_000

    def pip_distance(self, entry: float, stop: float) -> float:
        if self.pip_size <= 0:
            raise ValueError("pip_size must be positive")
        return abs(entry - stop) / self.pip_size

    def position_lots(self, risk_amount: float, entry: float, stop: float) -> float:
        if risk_amount < 0:
            raise ValueError("risk_amount cannot be negative")
        pips = self.pip_distance(entry, stop)
        if pips == 0:
            raise ValueError("entry and stop must differ")
        # Generic approximation; broker/account-currency conversion belongs to a provider.
        pip_value_per_lot = self.lot_units * self.pip_size
        return risk_amount / (pips * pip_value_per_lot)

    def net_cost(self, spread: float, commission: float, swap: float) -> float:
        return spread + commission + swap
