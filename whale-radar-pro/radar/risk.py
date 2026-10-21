"""Position sizing helpers; estimates only, never sends orders."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PositionSize:
    margin: float
    risk_amount: float
    stop_distance_pct: float
    notional: float
    leverage: float


def calculate_position_size(margin: float, risk_amount: float, stop_distance_pct: float) -> PositionSize:
    """Size a position so the stop loss approximates risk_amount.

    stop_distance_pct is the absolute entry-to-stop move as a percentage of entry,
    e.g. 1.25 means a 1.25% price move. Leverage is capped by available margin.
    Fees, slippage, funding and venue-specific limits are excluded.
    """
    if margin <= 0:
        raise ValueError("Margin must be greater than zero")
    if risk_amount <= 0:
        raise ValueError("Risk amount must be greater than zero")
    if risk_amount > margin:
        raise ValueError("Risk amount cannot exceed the entered margin")
    if not 0 < stop_distance_pct <= 100:
        raise ValueError("Stop distance must be greater than 0 and at most 100 percent")
    notional = risk_amount / (stop_distance_pct / 100.0)
    leverage = notional / margin
    return PositionSize(margin, risk_amount, stop_distance_pct, notional, leverage)
