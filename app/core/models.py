from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Profile:
    full_name: str = ""
    email: str = ""
    language: str = "fa"


@dataclass(frozen=True)
class TradingAccount:
    market: str
    name: str
    broker_or_exchange: str = ""
    currency: str = "USD"
    initial_balance: float = 0.0


@dataclass(frozen=True)
class Trade:
    market: str
    symbol: str
    direction: str
    account_id: Optional[int] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_price: Optional[float] = None
    risk_percent: Optional[float] = None
    quantity: Optional[float] = None
    fees: float = 0.0
    funding: float = 0.0
    result_r: Optional[float] = None
    pnl: Optional[float] = None
    setup: str = ""
    emotion: str = ""
    mistake: str = ""
    lesson: str = ""
    screenshot_path: str = ""
    opened_at: Optional[str] = None
    closed_at: Optional[str] = None
    notes: str = ""
