from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TraderProfile:
    full_name: str = ""
    professional_title: str = ""
    email: str = ""
    country: str = ""
    timezone: str = ""
    trading_style: str = "Day Trader"
    broker: str = ""
    account_currency: str = "USD"
    initial_balance: float = 0.0

    def display_name(self) -> str:
        return self.full_name.strip() or "Trader"
