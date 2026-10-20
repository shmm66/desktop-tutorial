from __future__ import annotations

import concurrent.futures
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.market_data import _forex_live, _crypto_live

USER_AGENT = "TraderPlannerPro/8.2.0"
RADAR_CACHE = Path.home() / "TraderPlannerPro" / "radar_cache.json"


@dataclass
class RadarSignal:
    symbol: str
    name: str
    price: float
    change_pct: Optional[float]
    trend: str  # "bullish", "bearish", "neutral"
    strength: float  # 0.0 to 1.0
    rsi: Optional[float] = None
    volume_ratio: Optional[float] = None
    setup: str = ""
    score: float = 0.0  # composite score for ranking


@dataclass
class RadarScanResult:
    market: str
    timestamp: str
    source: str
    signals: List[RadarSignal] = field(default_factory=list)
    status: str = "unavailable"  # live, cache, unavailable
    message: str = ""


def _score_signal(signal: RadarSignal) -> float:
    """Composite score for ranking radar signals."""
    base = signal.strength
    if signal.rsi is not None:
        rsi = signal.rsi
        if signal.trend == "bullish" and 30 <= rsi <= 50:
            base *= 1.1
        elif signal.trend == "bearish" and 50 <= rsi <= 70:
            base *= 1.1
    if signal.volume_ratio is not None and signal.volume_ratio > 1.0:
        base *= min(signal.volume_ratio, 1.5)
    return round(base, 3)


def _classify_trend(change_pct: Optional[float]) -> str:
    """Classify price change trend."""
    if change_pct is None:
        return "neutral"
    if change_pct > 0.5:
        return "bullish"
    if change_pct < -0.5:
        return "bearish"
    return "neutral"


def _scan_symbol(symbol_data: dict, symbol_name: str) -> Optional[RadarSignal]:
    """Analyze a single symbol and produce a RadarSignal."""
    price = symbol_data.get("price")
    change = symbol_data.get("change")
    change_pct = symbol_data.get("change_pct") if "change_pct" in symbol_data else (
        (change / price * 100.0) if price and change and price != 0 else None
    )
    trend = _classify_trend(change_pct)
    strength = abs(change_pct) if change_pct is not None else 0.0

    rsi = symbol_data.get("rsi")
    volume_ratio = symbol_data.get("volume_ratio")

    setup = ""
    if trend == "bullish" and rsi is not None and rsi < 40:
        setup = "RSI oversold bounce"
    elif trend == "bearish" and rsi is not None and rsi > 60:
        setup = "RSI overbought reversal"
    elif change_pct is not None and abs(change_pct) > 2.0:
        setup = "High momentum move"

    signal = RadarSignal(
        symbol=symbol_name,
        name=symbol_name,
        price=price or 0.0,
        change_pct=change_pct,
        trend=trend,
        strength=round(strength, 2),
        rsi=rsi,
        volume_ratio=volume_ratio,
        setup=setup,
        score=_score_signal(RadarSignal(
            symbol=symbol_name,
            name=symbol_name,
            price=price or 0.0,
            change_pct=change_pct,
            trend=trend,
            strength=strength,
            rsi=rsi,
            volume_ratio=volume_ratio,
            setup=setup,
        ).__dict__),
    )
    return signal


def _scan_forex() -> tuple[List[RadarSignal], str]:
    """Scan Forex symbols for trading opportunities. Returns (signals, source)."""
    from app.market_data import _forex_live

    symbols_data, source = _forex_live()
    signals = []
    for data in symbols_data:
        signal = _scan_symbol(data, data.get("symbol", "Unknown"))
        if signal is not None:
            signals.append(signal)
    return signals, source


def _scan_crypto() -> tuple[List[RadarSignal], str]:
    """Scan Crypto symbols for trading opportunities. Returns (signals, source)."""
    from app.market_data import _crypto_live

    symbols_data, source = _crypto_live()
    signals = []
    for data in symbols_data:
        signal = _scan_symbol(data, data.get("symbol", "Unknown"))
        if signal is not None:
            signals.append(signal)
    return signals, source


def scan_radar(market: str = "Both") -> RadarScanResult:
    """
    Run a radar scan for the specified market(s).

    Args:
        market: "Forex", "Crypto", or "Both"

    Returns:
        RadarScanResult with signals ranked by score.
    """
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result = RadarScanResult(market=market, timestamp=now, source="unavailable")

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    futures: Dict[str, Any] = {}
    if market in ("Forex", "Both"):
        futures["forex"] = executor.submit(_scan_forex)
    if market in ("Crypto", "Both"):
        futures["crypto"] = executor.submit(_scan_crypto)

    all_signals: List[RadarSignal] = []

    for key, future in futures.items():
        try:
            signals, source_key = future.result(timeout=8.0)
            all_signals.extend(signals)
        except Exception:
            pass

    # Sort by score descending
    all_signals.sort(key=lambda s: s.score, reverse=True)

    if all_signals:
        result.signals = all_signals
        result.status = "live"
        result.source = "live_scan"
        result.message = f"Found {len(all_signals)} trading opportunities"
    else:
        # Try cache
        try:
            if RADAR_CACHE.exists():
                cached = json.loads(RADAR_CACHE.read_text(encoding="utf-8"))
                if isinstance(cached, dict) and cached.get("market") == ("Forex" if market in ("Forex", "Both") else "Crypto") and cached.get("signals"):
                    saved = cached["signals"]
                    parsed = []
                    for s in saved:
                        try:
                            parsed.append(RadarSignal(**s))
                        except Exception:
                            continue
                    if parsed:
                        parsed.sort(key=lambda s: s.score, reverse=True)
                        result.signals = parsed
                        result.status = "cache"
                        result.source = "cache"
                        result.message = "Live feed unavailable; showing last saved radar snapshot."
        except Exception:
            pass
        if not result.signals:
            result.message = "No market data reachable right now."

    try:
        # Cache the result
        cache_payload = {
            "market": market,
            "timestamp": now,
            "source": result.source,
            "signals": [s.__dict__ for s in result.signals] if result.signals else [],
        }
        RADAR_CACHE.parent.mkdir(parents=True, exist_ok=True)
        tmp = RADAR_CACHE.with_suffix(".tmp")
        with threading.Lock():
            tmp.write_text(json.dumps(cache_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(RADAR_CACHE)
    except Exception:
        pass

    executor.shutdown(wait=False, cancel_futures=True)
    return result


def get_radar_summary(signals: List[RadarSignal]) -> str:
    """Generate a human-readable summary of radar signals."""
    if not signals:
        return "هیچ سیگنال پیدا نشد"

    bullish = sum(1 for s in signals if s.trend == "bullish")
    bearish = sum(1 for s in signals if s.trend == "bearish")
    neutral = sum(1 for s in signals if s.trend == "neutral")

    parts: list[str] = []
    if bullish:
        parts.append(f"{bullish} bullish")
    if bearish:
        parts.append(f"{bearish} bearish")
    if neutral:
        parts.append(f"{neutral} neutral")

    return " | ".join(parts) if parts else "No signals"


# Back-compat: expose fetch_market for external use
__all__ = ["RadarSignal", "RadarScanResult", "scan_radar", "get_radar_summary"]