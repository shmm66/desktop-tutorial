from __future__ import annotations


def risk_amount(balance: float, risk_percent: float) -> float:
    if balance < 0:
        raise ValueError("balance cannot be negative")
    if not 0 <= risk_percent <= 100:
        raise ValueError("risk_percent must be between 0 and 100")
    return balance * risk_percent / 100.0


def position_size(balance: float, risk_percent: float, entry: float, stop_loss: float, point_value: float = 1.0) -> float:
    if entry == stop_loss:
        raise ValueError("entry and stop_loss must differ")
    if point_value <= 0:
        raise ValueError("point_value must be positive")
    loss_per_unit = abs(entry - stop_loss) * point_value
    return risk_amount(balance, risk_percent) / loss_per_unit
