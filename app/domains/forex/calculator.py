from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ForexCalculator:
    """Broker-agnostic calculator; currency conversion is supplied by caller."""

    def pip_value(self, lot_size: float, pip_size: float, quote_to_account: float = 1.0) -> float:
        if lot_size <= 0 or pip_size <= 0 or quote_to_account <= 0:
            raise ValueError("lot_size, pip_size and conversion must be positive")
        return lot_size * pip_size * quote_to_account

    def risk_amount(self, balance: float, risk_percent: float) -> float:
        if balance < 0 or risk_percent < 0:
            raise ValueError("balance and risk percent cannot be negative")
        return balance * risk_percent / 100

    def lots_for_risk(self, balance: float, risk_percent: float, stop_pips: float, pip_value_per_lot: float) -> float:
        if stop_pips <= 0 or pip_value_per_lot <= 0:
            raise ValueError("stop_pips and pip value must be positive")
        return self.risk_amount(balance, risk_percent) / (stop_pips * pip_value_per_lot)

    def reward_risk(self, entry: float, stop: float, target: float) -> float:
        risk = abs(entry - stop)
        if risk == 0:
            raise ValueError("entry and stop must differ")
        return abs(target - entry) / risk
