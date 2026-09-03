from __future__ import annotations

from decimal import Decimal


Number = int | float | str | Decimal


def _d(value: Number) -> Decimal:
    return Decimal(str(value))


def risk_amount(balance: Number, risk_percent: Number) -> Decimal:
    account = _d(balance)
    percent = _d(risk_percent)
    if account < 0:
        raise ValueError("balance cannot be negative")
    if not Decimal("0") <= percent <= Decimal("100"):
        raise ValueError("risk_percent must be between 0 and 100")
    return account * percent / Decimal("100")


def position_size(
    balance: Number,
    risk_percent: Number,
    entry: Number,
    stop_loss: Number,
    point_value: Number = Decimal("1"),
) -> Decimal:
    entry_price = _d(entry)
    stop = _d(stop_loss)
    point = _d(point_value)
    if entry_price == stop:
        raise ValueError("entry and stop_loss must differ")
    if point <= 0:
        raise ValueError("point_value must be positive")
    loss_per_unit = abs(entry_price - stop) * point
    return risk_amount(balance, risk_percent) / loss_per_unit
