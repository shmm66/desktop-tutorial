"""Best-effort public Hyperliquid leaderboard reader.

The public leaderboard payload is not a guaranteed stable API contract. Missing metrics
remain unknown: a leaderboard rank or ROI is not a substitute for verified win rate.
"""
from __future__ import annotations

import requests

from .models import Trader

LEADERBOARD_URL = "https://stats-data.hyperliquid.xyz/Mainnet/leaderboard"


def _optional_number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _percent(value: object) -> float | None:
    number = _optional_number(value)
    if number is None:
        return None
    # ROI values in windowPerformances are commonly fractions; explicit fields ending
    # in Pct are already percentages and are handled by the caller.
    return number


def fetch_leaderboard(timeout: float = 12.0) -> list[Trader]:
    response = requests.get(
        LEADERBOARD_URL,
        timeout=timeout,
        headers={"User-Agent": "WhaleRadarPro/2.0"},
    )
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
        return_pct = _optional_number(row.get("returnPct"))
        if return_pct is None:
            roi = _optional_number(row.get("roi"))
            if roi is not None:
                return_pct = roi * 100 if abs(roi) <= 1 else roi

        window = row.get("windowPerformances") or row.get("performance") or []
        if isinstance(window, list) and window and isinstance(window[0], (list, dict)):
            item = window[0]
            perf = item[1] if isinstance(item, list) and len(item) > 1 and isinstance(item[1], dict) else item
            if isinstance(perf, dict):
                roi = _percent(perf.get("roi"))
                if return_pct is None and roi is not None:
                    return_pct = roi * 100 if abs(roi) <= 1 else roi

        # Never infer win rate from leaderboard placement or return. Only accept an
        # explicit win-rate field; absent/unknown values are represented as None.
        win_rate = _optional_number(row.get("winRatePct"))
        if win_rate is None:
            raw_win_rate = _optional_number(row.get("winRate"))
            if raw_win_rate is not None:
                win_rate = raw_win_rate * 100 if 0 <= raw_win_rate <= 1 else raw_win_rate

        raw_trades = row.get("numTrades", row.get("trades"))
        parsed_trades = _optional_number(raw_trades)
        trades = int(parsed_trades) if parsed_trades is not None and parsed_trades >= 0 else None

        traders.append(Trader(str(account), str(display), return_pct, win_rate, trades))

    if not traders:
        raise ValueError("Hyperliquid returned no parseable trader rows; upstream format may have changed")
    return traders
