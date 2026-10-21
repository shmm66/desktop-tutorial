"""Hyperliquid leaderboard and explicitly approximate recent closed-fill metrics.

The public leaderboard does not guarantee win-rate data. When missing, this module
samples a bounded set of higher-return wallets via the official Info API and derives a
7-day *closed-fill* win-rate proxy from realized closedPnl values. Partial exits can
count as multiple fills, so this is not represented as a position-level win rate.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
import requests

from .models import Trader

LEADERBOARD_URL = "https://stats-data.hyperliquid.xyz/Mainnet/leaderboard"
INFO_URL = "https://api.hyperliquid.xyz/info"
LOOKBACK_DAYS = 7
MAX_HISTORY_WALLETS = 15
MAX_WORKERS = 4


def _optional_number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
        return number if number == number and abs(number) != float("inf") else None
    except (TypeError, ValueError):
        return None


def _percent(value: object) -> float | None:
    return _optional_number(value)


def closed_fill_stats(fills: object) -> tuple[float | None, int]:
    """Return win-rate percentage and sample count for non-zero realized close fills.

    This deliberately counts close fills, not unique positions. `closedPnl` is the
    realized result supplied by Hyperliquid; open fills and zero-PnL fills are ignored.
    """
    if not isinstance(fills, list):
        return None, 0
    wins = losses = 0
    for fill in fills:
        if not isinstance(fill, dict):
            continue
        pnl = _optional_number(fill.get("closedPnl"))
        if pnl is None or pnl == 0:
            continue
        direction = str(fill.get("dir") or "").casefold()
        if "close" not in direction and "liquidat" not in direction:
            continue
        if pnl > 0:
            wins += 1
        else:
            losses += 1
    sample = wins + losses
    return ((wins / sample) * 100 if sample else None), sample


def _fetch_closed_fill_stats(address: str, start_ms: int, end_ms: int, timeout: float) -> tuple[float | None, int]:
    response = requests.post(
        INFO_URL,
        json={"type": "userFillsByTime", "user": address, "startTime": start_ms, "endTime": end_ms, "aggregateByTime": True},
        timeout=timeout,
        headers={"Content-Type": "application/json", "User-Agent": "WhaleRadarPro/2.0"},
    )
    response.raise_for_status()
    return closed_fill_stats(response.json())


def _parse_row(row: dict) -> Trader | None:
    account = row.get("ethAddress") or row.get("address") or row.get("user") or ""
    if not account:
        return None
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

    win_rate = _optional_number(row.get("winRatePct"))
    if win_rate is None:
        raw_win_rate = _optional_number(row.get("winRate"))
        if raw_win_rate is not None:
            win_rate = raw_win_rate * 100 if 0 <= raw_win_rate <= 1 else raw_win_rate

    parsed_trades = _optional_number(row.get("numTrades", row.get("trades")))
    trades = int(parsed_trades) if parsed_trades is not None and parsed_trades >= 0 else None
    return Trader(str(account), str(display), return_pct, win_rate, trades)


def enrich_missing_win_rates(traders: list[Trader], timeout: float = 8.0, max_wallets: int = MAX_HISTORY_WALLETS) -> list[Trader]:
    """Enrich missing metrics for a bounded group of high-return wallets.

    A single wallet history failure leaves that wallet's metrics unknown; it never
    turns API errors into a zero win rate. Requests run concurrently with a small cap.
    """
    if not traders or max_wallets < 1:
        return traders
    candidates = [t for t in traders if t.win_rate_pct is None and t.return_pct is not None]
    candidates.sort(key=lambda t: t.return_pct if t.return_pct is not None else float("-inf"), reverse=True)
    candidates = candidates[:min(max_wallets, MAX_HISTORY_WALLETS)]
    if not candidates:
        return traders

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=LOOKBACK_DAYS)
    start_ms, end_ms = int(start.timestamp() * 1000), int(end.timestamp() * 1000)
    results: dict[str, tuple[float | None, int]] = {}
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(candidates))) as pool:
        futures = {
            pool.submit(_fetch_closed_fill_stats, trader.address, start_ms, end_ms, timeout): trader.address
            for trader in candidates
        }
        for future in as_completed(futures):
            address = futures[future]
            try:
                results[address] = future.result()
            except (requests.RequestException, ValueError, TypeError):
                continue

    enriched: list[Trader] = []
    for trader in traders:
        stats = results.get(trader.address)
        if trader.win_rate_pct is None and stats is not None:
            win_rate, sample = stats
            if sample:
                enriched.append(Trader(trader.address, trader.display_name, trader.return_pct, win_rate, sample, "Hyperliquid · 7d closed-fill proxy"))
                continue
        enriched.append(trader)
    return enriched


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

    traders = [parsed for row in rows if isinstance(row, dict) and (parsed := _parse_row(row)) is not None]
    if not traders:
        raise ValueError("Hyperliquid returned no parseable trader rows; upstream format may have changed")
    return enrich_missing_win_rates(traders, timeout=min(timeout, 8.0))
