from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


def _decimal(value: float | int | str | Decimal) -> Decimal:
    """Convert numeric input without inheriting binary floating-point artifacts."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("numeric value is invalid") from exc


def _as_float(value: Decimal) -> float:
    """Keep the public API backward-compatible while calculating with Decimal."""
    return float(value)


@dataclass(frozen=True, slots=True)
class ForexCalculator:
    """Broker-agnostic calculator; currency conversion is supplied by caller.

    Financial arithmetic is performed with Decimal so common FX decimal inputs
    do not accumulate binary floating-point error.
    """

    def pip_value(self, lot_size: float, pip_size: float, quote_to_account: float = 1.0) -> float:
        lot = _decimal(lot_size)
        pip = _decimal(pip_size)
        conversion = _decimal(quote_to_account)
        if lot <= 0 or pip <= 0 or conversion <= 0:
            raise ValueError("lot_size, pip_size and conversion must be positive")
        return _as_float(lot * pip * conversion)

    def risk_amount(self, balance: float, risk_percent: float) -> float:
        balance_d = _decimal(balance)
        risk_d = _decimal(risk_percent)
        if balance_d < 0 or risk_d < 0:
            raise ValueError("balance and risk percent cannot be negative")
        return _as_float(balance_d * risk_d / Decimal("100"))

    def lots_for_risk(self, balance: float, risk_percent: float, stop_pips: float, pip_value_per_lot: float) -> float:
        stop = _decimal(stop_pips)
        pip_value = _decimal(pip_value_per_lot)
        if stop <= 0 or pip_value <= 0:
            raise ValueError("stop_pips and pip value must be positive")
        risk = _decimal(self.risk_amount(balance, risk_percent))
        return _as_float(risk / (stop * pip_value))

    def reward_risk(self, entry: float, stop: float, target: float) -> float:
        entry_d = _decimal(entry)
        stop_d = _decimal(stop)
        target_d = _decimal(target)
        risk = abs(entry_d - stop_d)
        if risk == 0:
            raise ValueError("entry and stop must differ")
        ratio = abs(target_d - entry_d) / risk
        return _as_float(ratio.quantize(Decimal("0.0000000001")))
