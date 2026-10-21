"""Validated, provider-independent trader screening."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Trader:
    address: str
    display_name: str
    return_pct: float
    win_rate_pct: float
    trades: int = 0
    source: str = "Hyperliquid"


def qualifies(trader: Trader, min_return_pct: float, min_win_rate_pct: float) -> bool:
    return trader.return_pct >= min_return_pct and trader.win_rate_pct >= min_win_rate_pct


def rank_traders(traders: list[Trader], min_return_pct: float, min_win_rate_pct: float, limit: int = 10) -> list[Trader]:
    if not 1 <= limit <= 10:
        raise ValueError("Trader list limit must be between 1 and 10")
    selected = [t for t in traders if qualifies(t, min_return_pct, min_win_rate_pct)]
    return sorted(selected, key=lambda t: (t.win_rate_pct, t.return_pct, t.trades), reverse=True)[:limit]
