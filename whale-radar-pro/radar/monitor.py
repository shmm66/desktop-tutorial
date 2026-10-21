"""Read-only polling helpers for monitoring a selected Hyperliquid wallet."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import requests

from .hyperliquid import INFO_URL


def fill_identity(fill: dict) -> str:
    """Build a stable best-effort identity for a fill returned by the public API."""
    explicit = fill.get("hash") or fill.get("tid")
    if explicit:
        return str(explicit)
    fields = {key: fill.get(key) for key in ("oid", "time", "coin", "dir", "px", "sz", "closedPnl")}
    raw = json.dumps(fields, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def fetch_recent_fills(address: str, lookback_seconds: int = 120, timeout: float = 8.0) -> list[dict]:
    """Fetch recent public fills for one wallet. No private key or exchange API key is used."""
    if not address or not address.startswith("0x"):
        raise ValueError("Select a valid Hyperliquid wallet address first.")
    end = datetime.now(timezone.utc)
    start = end - timedelta(seconds=max(30, min(lookback_seconds, 600)))
    response = requests.post(
        INFO_URL,
        json={"type": "userFillsByTime", "user": address, "startTime": int(start.timestamp() * 1000), "endTime": int(end.timestamp() * 1000)},
        timeout=timeout,
        headers={"Content-Type": "application/json", "User-Agent": "WhaleRadarPro/2.0"},
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("Hyperliquid returned an unexpected fills response.")
    return [fill for fill in payload if isinstance(fill, dict)]
