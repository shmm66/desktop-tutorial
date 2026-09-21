from __future__ import annotations

import concurrent.futures
import json
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "TraderPlannerPro"
CACHE_PATH = ROOT / "market_cache.json"
USER_AGENT = "TraderPlannerPro/7.6 (+https://github.com/shmm66/desktop-tutorial)"

CRYPTO_FALLBACK = [
    ("BTC", "BTC-USD"), ("ETH", "ETH-USD"), ("USDT", "USDT-USD"),
    ("BNB", "BNB-USD"), ("XRP", "XRP-USD"), ("USDC", "USDC-USD"),
    ("SOL", "SOL-USD"), ("TRX", "TRX-USD"), ("DOGE", "DOGE-USD"), ("ADA", "ADA-USD"),
]
BINANCE_CRYPTO = [
    ("BTC", "BTCUSDT"), ("ETH", "ETHUSDT"), ("USDT", "USDTUSD"),
    ("BNB", "BNBUSDT"), ("XRP", "XRPUSDT"), ("USDC", "USDCUSDT"),
    ("SOL", "SOLUSDT"), ("TRX", "TRXUSDT"), ("DOGE", "DOGEUSDT"), ("ADA", "ADAUSDT"),
]

FOREX_SYMBOLS = [
    ("GOLD", "GC=F"), ("SILVER", "SI=F"), ("COPPER", "HG=F"),
    ("EUR/USD", "EURUSD=X"), ("GBP/USD", "GBPUSD=X"), ("USD/JPY", "JPY=X"),
    ("USD/CHF", "CHF=X"), ("AUD/USD", "AUDUSD=X"), ("WTI OIL", "CL=F"),
    ("S&P 500", "^GSPC"), ("NASDAQ 100", "^NDX"), ("DOW 30", "^DJI"),
    ("US DOLLAR", "DX-Y.NYB"), ("APPLE", "AAPL"), ("MICROSOFT", "MSFT"),
    ("NVIDIA", "NVDA"), ("AMAZON", "AMZN"),
]

CRYPTO_ENDPOINT = (
    "https://api.coingecko.com/api/v3/coins/markets?"
    "vs_currency=usd&order=market_cap_desc&per_page=10&page=1&"
    "sparkline=false&price_change_percentage=24h"
)
CRYPTO_FALLBACK_ENDPOINT = "https://api.coinpaprika.com/v1/tickers?quotes=USD&limit=25"
BINANCE_TICKER_ENDPOINTS = [
    "https://data-api.binance.vision/api/v3/ticker/24hr",
    "https://api.binance.com/api/v3/ticker/24hr",
    "https://api-gcp.binance.com/api/v3/ticker/24hr",
]
GLOBAL_ENDPOINT = "https://api.coingecko.com/api/v3/global"
GLOBAL_FALLBACK_ENDPOINT = "https://api.coinpaprika.com/v1/global"
YAHOO_ENDPOINTS = [
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=5m",
    "https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=5m",
]
FEAR_GREED_ENDPOINTS = [
    "https://api.alternative.me/fng/?limit=1",
]
VIX_SYMBOL = "^VIX"

_cache_lock = threading.Lock()


def _request_json(url: str, timeout: float = 5.0):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json,text/plain,*/*",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read()
    return json.loads(payload.decode("utf-8"))


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_cache():
    try:
        with _cache_lock:
            payload = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _write_cache(payload):
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE_PATH.with_suffix(".tmp")
        with _cache_lock:
            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(CACHE_PATH)
    except OSError:
        pass


def _yahoo_symbol(symbol: str, timeout=3.5):
    for endpoint in YAHOO_ENDPOINTS:
        try:
            data = _request_json(endpoint.format(symbol=urllib.parse.quote(symbol, safe="")), timeout=timeout)
            result = (data.get("chart", {}).get("result") or [None])[0]
            if not result:
                continue
            meta = result.get("meta") or {}
            price = _safe_float(meta.get("regularMarketPrice"))
            previous = _safe_float(meta.get("previousClose"))
            if price is None:
                closes = (((result.get("indicators") or {}).get("quote") or [{}])[0]).get("close") or []
                values = [_safe_float(v) for v in closes]
                values = [v for v in values if v is not None]
                price = values[-1] if values else None
            if price is None:
                continue
            change = None if previous in (None, 0) else (price - previous) / previous * 100.0
            return price, change
        except Exception:
            continue
    return None


def _parallel_yahoo(symbols):
    result = []
    if not symbols:
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(12, len(symbols))) as pool:
        futures = {pool.submit(_yahoo_symbol, yahoo): label for label, yahoo in symbols}
        for future in concurrent.futures.as_completed(futures):
            label = futures[future]
            try:
                value = future.result()
            except Exception:
                value = None
            if not value:
                continue
            price, change = value
            result.append({"symbol": label, "name": label, "price": price, "change": change})
    order = {label: i for i, (label, _) in enumerate(symbols)}
    result.sort(key=lambda x: order.get(x["symbol"], 999))
    return result


def _crypto_from_binance():
    for endpoint in BINANCE_TICKER_ENDPOINTS:
        try:
            rows = _request_json(endpoint, timeout=5.0)
            if not isinstance(rows, list):
                continue
            by_symbol = {str(row.get("symbol", "")).upper(): row for row in rows}
            result = []
            for label, symbol in BINANCE_CRYPTO:
                row = by_symbol.get(symbol)
                if not row:
                    # USDT/USD or USDC/USD may not be listed on every public endpoint.
                    continue
                price = _safe_float(row.get("lastPrice"))
                change = _safe_float(row.get("priceChangePercent"))
                if price is None:
                    continue
                result.append({
                    "symbol": label,
                    "name": label,
                    "price": price,
                    "change": change,
                })
            if len(result) >= 5:
                return result, "Binance public market data"
        except Exception:
            continue
    return [], "unavailable"


def _crypto_live():
    # Primary ranking by market cap.
    try:
        rows = _request_json(CRYPTO_ENDPOINT, timeout=5.0)
        if isinstance(rows, list) and rows:
            result = []
            for row in rows[:10]:
                price = _safe_float(row.get("current_price"))
                if price is None:
                    continue
                result.append({
                    "symbol": str(row.get("symbol", "")).upper(),
                    "name": row.get("name", ""),
                    "price": price,
                    "change": _safe_float(row.get("price_change_percentage_24h")),
                })
            if len(result) >= 5:
                return result, "CoinGecko"
    except Exception:
        pass

    # Fast exchange fallback. Binance documents public ticker endpoints as unauthenticated market data. 
    result, source = _crypto_from_binance()
    if result:
        return result, source

    # Aggregated fallback.
    try:
        rows = _request_json(CRYPTO_FALLBACK_ENDPOINT, timeout=5.0)
        result = []
        for row in (rows or []):
            quote = ((row.get("quotes") or {}).get("USD") or {})
            price = _safe_float(quote.get("price"))
            if price is None:
                continue
            result.append({
                "symbol": str(row.get("symbol", "")).upper(),
                "name": row.get("name", ""),
                "price": price,
                "change": _safe_float(quote.get("percent_change_24h")),
            })
            if len(result) >= 10:
                break
        if result:
            return result, "CoinPaprika"
    except Exception:
        pass

    result = _parallel_yahoo(CRYPTO_FALLBACK)
    return result, "Yahoo Finance" if result else "unavailable"


def _forex_live():
    result = _parallel_yahoo(FOREX_SYMBOLS)
    return result, "Yahoo Finance" if result else "unavailable"


def _global_indicators():
    result = {}
    for endpoint in (GLOBAL_ENDPOINT, GLOBAL_FALLBACK_ENDPOINT):
        try:
            data = _request_json(endpoint, timeout=5.0)
            global_data = data.get("data") or {}
            pct = global_data.get("market_cap_percentage") or {}
            if pct:
                result["btc_dominance"] = _safe_float(pct.get("btc"))
                result["usdt_dominance"] = _safe_float(pct.get("usdt"))
                result["total_market_cap"] = _safe_float((global_data.get("total_market_cap") or {}).get("usd"))
                if any(value is not None for value in result.values()):
                    return result
            # CoinPaprika global shape fallback.
            mcap = global_data.get("market_cap_usd") or global_data.get("market_cap") or {}
            total = _safe_float(global_data.get("market_cap_usd") or mcap.get("usd") if isinstance(mcap, dict) else mcap)
            result["total_market_cap"] = total
        except Exception:
            continue
    return result


def _fear_greed():
    for endpoint in FEAR_GREED_ENDPOINTS:
        try:
            data = _request_json(endpoint, timeout=5.0)
            row = (data.get("data") or [None])[0] or {}
            value = _safe_float(row.get("value"))
            if value is None:
                continue
            return {
                "value": int(value),
                "label": str(row.get("value_classification") or ""),
                "timestamp": row.get("timestamp"),
            }
        except Exception:
            continue
    return None


def _market_vix():
    value = _yahoo_symbol(VIX_SYMBOL)
    if not value:
        return None
    price, change = value
    return {"value": price, "change": change}


def fetch_market(mode: str):
    market = "Forex" if str(mode).lower() == "forex" else "Crypto"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    items, source = _forex_live() if market == "Forex" else _crypto_live()

    indicators = _global_indicators()
    indicators["fear_greed"] = _fear_greed()
    indicators["vix"] = _market_vix()
    indicators["market_regime"] = "LIVE" if items else "OFFLINE"

    if items:
        payload = {
            "market": market,
            "updated_at": now,
            "source": source,
            "items": items,
            "indicators": indicators,
            "status": "live",
            "message": "",
        }
        _write_cache(payload)
        return payload

    cached = _read_cache()
    if cached.get("market") == market and isinstance(cached.get("items"), list):
        return {
            "market": market,
            "updated_at": cached.get("updated_at"),
            "source": cached.get("source") or "cache",
            "items": cached.get("items", []),
            "indicators": cached.get("indicators", indicators),
            "status": "cache",
            "message": "Live feed unavailable; showing last saved market snapshot.",
        }

    # Never leave the UI visually hanging on "loading". Return an explicit offline payload.
    return {
        "market": market,
        "updated_at": now,
        "source": "unavailable",
        "items": [],
        "indicators": indicators,
        "status": "unavailable",
        "message": "No market feed is reachable right now.",
    }


class MarketDataService:
    def __init__(self, callback=None, refresh_seconds: int = 60):
        self.callback = callback
        self.refresh_seconds = max(30, int(refresh_seconds))
        self._market = "Crypto"
        self._running = False
        self._executor = None
        self._future = None
        self._refresh_lock = threading.Lock()

    def start(self, market: str):
        self.set_market(market)
        if self._running:
            self.refresh_now()
            return
        self._running = True
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._future = self._executor.submit(self._worker)

    def set_market(self, market: str):
        self._market = "Forex" if market == "Forex" else "Crypto"

    def refresh_now(self):
        if not self._refresh_lock.acquire(blocking=False):
            return

        market = self._market

        def run():
            try:
                payload = fetch_market(market)
                if self.callback:
                    self.callback(payload)
            finally:
                self._refresh_lock.release()

        threading.Thread(target=run, name="TraderPlannerMarketRefresh", daemon=True).start()

    def stop(self):
        self._running = False
        if self._executor:
            try:
                self._executor.shutdown(wait=False, cancel_futures=True)
            except Exception:
                pass
            self._executor = None
            self._future = None

    def _worker(self):
        while self._running:
            market = self._market
            payload = fetch_market(market)
            if self.callback:
                try:
                    self.callback(payload)
                except Exception:
                    pass
            for _ in range(self.refresh_seconds):
                if not self._running:
                    break
                time.sleep(1)
