from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ForexRules:
    """Pure Forex calculations. No UI/database dependencies."""

    pip_size: Decimal = Decimal("0.0001")
    lot_units: int = 100_000

    def pip_distance(self, entry: float | Decimal, stop: float | Decimal) -> Decimal:
        if self.pip_size <= 0:
            raise ValueError("pip_size must be positive")
        distance = abs(Decimal(str(entry)) - Decimal(str(stop)))
        return distance / self.pip_size

    def position_lots(self, risk_amount: float | Decimal, entry: float | Decimal, stop: float | Decimal) -> Decimal:
        risk = Decimal(str(risk_amount))
        if risk < 0:
            raise ValueError("risk_amount cannot be negative")
        pips = self.pip_distance(entry, stop)
        if pips == 0:
            raise ValueError("entry and stop must differ")
        pip_value_per_lot = Decimal(self.lot_units) * self.pip_size
        return risk / (pips * pip_value_per_lot)

    def net_cost(self, spread: float | Decimal, commission: float | Decimal, swap: float | Decimal) -> Decimal:
        return sum((Decimal(str(spread)), Decimal(str(commission)), Decimal(str(swap))), Decimal("0"))
