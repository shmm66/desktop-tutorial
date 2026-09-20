from __future__ import annotations

import json
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "TraderPlannerPro"
CACHE_PATH = ROOT / "market_cache.json"
USER_AGENT = "TraderPlannerPro/7.4 (+https://github.com/shmm66/desktop-tutorial)"

CRYPTO_FALLBACK = [
    ("BTC", "BTC-USD"),
    ("ETH", "ETH-USD"),
    ("USDT", "USDT-USD"),
    ("BNB", "BNB-USD"),
    ("XRP", "XRP-USD"),
    ("USDC", "USDC-USD"),
    ("SOL", "SOL-USD"),
    ("TRX", "TRX-USD"),
    ("DOGE", "DOGE-USD"),
    ("ADA", "ADA-USD"),
]

FOREX_SYMBOLS = [
    ("GOLD", "GC=F"),
    ("SILVER", "SI=F"),
    ("COPPER", "HG=F"),
    ("EUR/USD", "EURUSD=X"),
    ("GBP/USD", "GBPUSD=X"),
    ("USD/JPY", "JPY=X"),
    ("USD/CHF", "CHF=X"),
    ("AUD/USD", "AUDUSD=X"),
    ("WTI OIL", "CL=F"),
    ("S&P 500", "^GSPC"),
    ("NASDAQ 100", "^NDX"),
    ("DOW 30", "^DJI"),
    ("APPLE", "AAPL"),
    ("MICROSOFT", "MSFT"),
    ("NVIDIA", "NVDA"),
    ("AMAZON", "AMZN"),
]

CRYPTO_ENDPOINT = (
    "https://api.coingecko.com/api/v3/coins/markets?"
    "vs_currency=usd&order=market_cap_desc&per_page=10&page=1&"
    "sparkline=false&price_change_percentage=24h"
)

YAHOO_ENDPOINT = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=5m"
FEAR_GREED_ENDPOINT = "https://api.alternative.me/fng/?limit=1"


def _request_json(url: str, timeout: float = 8.0):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_cache():
    try:
        payload = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _write_cache(payload):
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(CACHE_PATH)
    except OSError:
        pass


def _yahoo_symbol(symbol: str):
    try:
        data = _request_json(YAHOO_ENDPOINT.format(symbol=urllib.parse.quote(symbol, safe="")))
        result = (data.get("chart", {}).get("result") or [None])[0]
        if not result:
            return None
        meta = result.get("meta") or {}
        price = _safe_float(meta.get("regularMarketPrice"))
        previous = _safe_float(meta.get("previousClose"))
        if price is None:
            closes = (((result.get("indicators") or {}).get("quote") or [{}])[0]).get("close") or []
            values = [_safe_float(v) for v in closes if _safe_float(v) is not None]
            price = values[-1] if values else None
        if price is None:
            return None
        change = None
        if previous not in (None, 0):
            change = (price - previous) / previous * 100.0
        return price, change
    except Exception:
        return None


def _crypto_live():
    try:
        rows = _request_json(CRYPTO_ENDPOINT)
        if not isinstance(rows, list):
            return []
        result = []
        for row in rows[:10]:
            price = _safe_float(row.get("current_price"))
            change = _safe_float(row.get("price_change_percentage_24h_in_currency"))
            if price is None:
                continue
            result.append({
                "symbol": str(row.get("symbol", "")).upper(),
                "name": row.get("name", ""),
                "price": price,
                "change": change,
            })
        return result
    except Exception:
        result = []
        for symbol, yahoo in CRYPTO_FALLBACK:
            value = _yahoo_symbol(yahoo)
            if not value:
                continue
            price, change = value
            result.append({"symbol": symbol, "name": symbol, "price": price, "change": change})
        return result


def _forex_live():
    result = []
    for label, symbol in FOREX_SYMBOLS:
        value = _yahoo_symbol(symbol)
        if not value:
            continue
        price, change = value
        result.append({"symbol": label, "name": label, "price": price, "change": change})
    return result


def _fear_greed():
    try:
        data = _request_json(FEAR_GREED_ENDPOINT)
        row = (data.get("data") or [None])[0] or {}
        value = _safe_float(row.get("value"))
        if value is None:
            return None
        return {"value": int(value), "label": str(row.get("value_classification") or "")}
    except Exception:
        return None

def fetch_market(mode: str):
    market = "Forex" if str(mode).lower() == "forex" else "Crypto"
    rows = _forex_live() if market == "Forex" else _crypto_live()
    fear_greed = _fear_greed() if market == "Crypto" else None
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if rows:
        payload = {"market": market, "updated_at": now, "source": "live", "items": rows, "fear_greed": fear_greed}
        _write_cache(payload)
        return payload
    cached = _read_cache()
    if cached.get("market") == market and isinstance(cached.get("items"), list):
        return {
            "market": market,
            "updated_at": cached.get("updated_at"),
            "source": "cache",
            "items": cached.get("items", []),
            "fear_greed": cached.get("fear_greed"),
        }
    return {"market": market, "updated_at": now, "source": "unavailable", "items": []}


class MarketDataService:
    def __init__(self, callback=None, refresh_seconds: int = 60):
        self.callback = callback
        self.refresh_seconds = max(30, int(refresh_seconds))
        self._market = None
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

    def start(self, market: str):
        self._market = "Forex" if market == "Forex" else "Crypto"
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker, name="TraderPlannerMarketData", daemon=True)
        self._thread.start()

    def set_market(self, market: str):
        self._market = "Forex" if market == "Forex" else "Crypto"

    def stop(self):
        self._running = False

    def _worker(self):
        while self._running:
            market = self._market or "Crypto"
            payload = fetch_market(market)
            cb = self.callback
            if cb:
                try:
                    cb(payload)
                except Exception:
                    pass
            for _ in range(self.refresh_seconds):
                if not self._running:
                    break
                time.sleep(1)
