"""Best-effort public Hyperliquid leaderboard reader.

The public leaderboard payload is not a guaranteed stable API contract. Parsing is
intentionally defensive; callers must surface fetch errors rather than invent data.
"""
from __future__ import annotations
import requests
from .models import Trader

LEADERBOARD_URL = "https://stats-data.hyperliquid.xyz/Mainnet/leaderboard"


def _number(value: object) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def fetch_leaderboard(timeout: float = 12.0) -> list[Trader]:
    response = requests.get(LEADERBOARD_URL, timeout=timeout, headers={"User-Agent": "WhaleRadarPro/2.0"})
    response.raise_for_status()
    payload = response.json()
    rows = payload.get("leaderboardRows", payload.get("leaderboard", [])) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("Unexpected Hyperliquid leaderboard response format")
    traders: list[Trader] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        account = row.get("ethAddress") or row.get("address") or row.get("user") or ""
        if not account:
            continue
        display = row.get("displayName") or row.get("name") or str(account)[:8] + "…"
        window = row.get("windowPerformances") or row.get("performance") or []
        return_pct = _number(row.get("returnPct", row.get("roi", 0)))
        win_rate = _number(row.get("winRatePct", row.get("winRate", 0)))
        trades = int(_number(row.get("numTrades", row.get("trades", 0))))
        if isinstance(window, list) and window and isinstance(window[0], (list, dict)):
            item = window[0]
            if isinstance(item, list) and len(item) > 1 and isinstance(item[1], dict):
                perf = item[1]
                return_pct = _number(perf.get("roi", return_pct)) * (100 if abs(_number(perf.get("roi", 0))) <= 1 else 1)
        traders.append(Trader(str(account), str(display), return_pct, win_rate, trades))
    if not traders:
        raise ValueError("Hyperliquid returned no parseable trader rows; upstream format may have changed")
    return traders
