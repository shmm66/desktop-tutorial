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
USER_AGENT = "TraderPlannerPro/7.9.0 (+https://github.com/shmm66/desktop-tutorial)"

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
CRYPTO_FALLBACK_ENDPOINT = "https://api.coinpaprika.com/v1/tickers?quotes=USD&limit=25"\nCOINCAP_ENDPOINT = "https://api.coincap.io/v2/assets?ids=bitcoin,ethereum,tether,binance-coin,xrp,usd-coin,solana,tron,dogecoin,cardano"
KRAKEN_TICKER_ENDPOINT = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD,ETHUSD,SOLUSD,XRPUSD,ADAUSD,DOGEUSD,BNBUSD"
BINANCE_TICKER_ENDPOINTS = [
    "https://data-api.binance.vision/api/v3/ticker/24hr",
    "https://api.binance.com/api/v3/ticker/24hr",
    "https://api-gcp.binance.com/api/v3/ticker/24hr",
]
GLOBAL_ENDPOINT = "https://api.coingecko.com/api/v3/global"
GLOBAL_FALLBACK_ENDPOINT = "https://api.coinpaprika.com/v1/global"
CRONCOPIA_METALS = {"GOLD":"gold","SILVER":"silver","COPPER":"copper"}
CRONCOPIA_BASE = "https://croncopia.com/api/metals"

EXCHANGE_RATE_ENDPOINTS = [
    "https://open.er-api.com/v6/latest/USD",
    "https://api.exchangerate.fun/latest?base=USD",
    "https://api.exchangerate.fun/latest?base=USD&symbols=EUR,GBP,JPY,CHF,AUD,CAD,XAU,XAG",
]
GOLD_SPOT_ENDPOINT = "https://goldprice.dev/v1/prices?symbol=XAU-USD-SPOT"
YAHOO_ENDPOINTS = [
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=5m",
    "https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=5m",
]
YAHOO_ENDPOINT = YAHOO_ENDPOINTS[0]
FEAR_GREED_ENDPOINTS = [
    "https://api.alternative.me/fng/?limit=1",
]
FEAR_GREED_ENDPOINT = FEAR_GREED_ENDPOINTS[0]
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


def _seed_path():
    root = Path(getattr(__import__("sys"), "_MEIPASS", Path(__file__).resolve().parent))
    return root / "market_seed.json"


def _read_cache():
    try:
        with _cache_lock:
            payload = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return {}
        # V7.8 migration: a single-market cache becomes a per-market cache.
        if isinstance(payload.get("markets"), dict):
            return payload
        market = payload.get("market")
        if market:
            return {"markets": {market: payload}}
        return {}
    except (OSError, ValueError, TypeError):
        return {}


def _cache_for_market(mode: str):
    market = "Forex" if str(mode).lower() == "forex" else "Crypto"
    data = _read_cache()
    item = (data.get("markets") or {}).get(market)
    return item if isinstance(item, dict) else {}


def _write_cache(payload):
    market = "Forex" if str(payload.get("market")).lower() == "forex" else "Crypto"
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        current = _read_cache()
        markets = current.setdefault("markets", {})
        markets[market] = payload
        tmp = CACHE_PATH.with_suffix(".tmp")
        with _cache_lock:
            tmp.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(CACHE_PATH)
    except OSError:
        pass


def _read_seed(mode):
    market = "Forex" if str(mode).lower() == "forex" else "Crypto"
    try:
        raw = json.loads(_seed_path().read_text(encoding="utf-8"))
        payload = (raw.get("markets") or {}).get(market) if isinstance(raw, dict) else None
        if isinstance(payload, dict) and payload.get("items"):
            payload = dict(payload)
            payload["market"] = market
            payload["status"] = "snapshot"
            payload["source"] = payload.get("source") or "Build snapshot"
            payload["message"] = "Build snapshot available; waiting for live feed."
            return payload
    except (OSError, ValueError, TypeError):
        pass
    return {}


def _crypto_from_coincap():
    try:
        data = _request_json(COINCAP_ENDPOINT, timeout=5.0)
        rows = data.get("data") or []
        result = []
        symbol_map = {
            "bitcoin":"BTC","ethereum":"ETH","tether":"USDT","binance-coin":"BNB",
            "xrp":"XRP","usd-coin":"USDC","solana":"SOL","tron":"TRX",
            "dogecoin":"DOGE","cardano":"ADA",
        }
        for row in rows:
            rid = str(row.get("id",""))
            label = symbol_map.get(rid)
            price = _safe_float(row.get("priceUsd"))
            change = _safe_float(row.get("changePercent24Hr"))
            if label and price is not None:
                result.append({"symbol":label,"name":label,"price":price,"change":change})
        if len(result) >= 5:
            order = ["BTC","ETH","USDT","BNB","XRP","USDC","SOL","TRX","DOGE","ADA"]
            result.sort(key=lambda x: order.index(x["symbol"]) if x["symbol"] in order else 999)
            return result, "CoinCap public market data"
    except Exception:
        pass
    return [], "unavailable"


def _crypto_live():
    # Aggregated ranking first, then exchange/public fallbacks.
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

    for loader in (_crypto_from_binance, _crypto_from_kraken, _crypto_from_coincap):
        result, source = loader()
        if result:
            return result, source

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


def cached_market_payload(mode: str):
    market = "Forex" if str(mode).lower() == "forex" else "Crypto"
    cached = _cache_for_market(market)
    if isinstance(cached.get("items"), list) and cached.get("items"):
        return {
            "market": market,
            "updated_at": cached.get("updated_at"),
            "source": cached.get("source") or "cache",
            "items": cached.get("items", []),
            "indicators": cached.get("indicators", {}),
            "status": "cache",
            "message": "Showing the last saved snapshot while the live feed refreshes.",
        }
    seed = _read_seed(market)
    if seed:
        return seed
    return {
        "market": market,
        "updated_at": None,
        "source": "unavailable",
        "items": [],
        "indicators": {},
        "status": "unavailable",
        "message": "Waiting for a live market feed.",
    }


def fetch_market(mode: str):
    market = "Forex" if str(mode).lower() == "forex" else "Crypto"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        item_future = pool.submit(_forex_live if market == "Forex" else _crypto_live)
        indicator_futures = {
            "global": pool.submit(_global_indicators),
            "fear": pool.submit(_fear_greed),
            "vix": pool.submit(_market_vix),
        }
        try:
            items, source = item_future.result()
        except Exception:
            items, source = [], "unavailable"
        indicators = {}
        try: indicators.update(indicator_futures["global"].result())
        except Exception: pass
        try: indicators["fear_greed"] = indicator_futures["fear"].result()
        except Exception: indicators["fear_greed"] = None
        try: indicators["vix"] = indicator_futures["vix"].result()
        except Exception: indicators["vix"] = None
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

    cached = _cache_for_market(market)
    if isinstance(cached.get("items"), list) and cached.get("items"):
        return {
            "market": market,
            "updated_at": cached.get("updated_at"),
            "source": cached.get("source") or "cache",
            "items": cached.get("items", []),
            "indicators": cached.get("indicators", indicators),
            "status": "cache",
            "message": "Live feed unavailable; showing last saved market snapshot.",
        }

    seed = _read_seed(market)
    if seed:
        seed["indicators"] = indicators or seed.get("indicators", {})
        seed["updated_at"] = seed.get("updated_at") or now
        return seed

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
        self._generation = 0
        self._running = False
        self._executor = None

    def start(self, market: str):
        self.set_market(market)
        if self._running:
            self.refresh_now()
            return
        self._running = True
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._executor.submit(self._worker)

    def set_market(self, market: str):
        new_market = "Forex" if market == "Forex" else "Crypto"
        if new_market != self._market:
            self._generation += 1
        self._market = new_market

    def refresh_now(self):
        market = self._market
        generation = self._generation

        def run():
            try:
                payload = fetch_market(market)
                if self.callback and self._running is not False:
                    # Drop stale responses after a Crypto ↔ Forex switch.
                    if market == self._market and generation == self._generation:
                        self.callback(payload)
            except Exception:
                pass

        threading.Thread(target=run, name="TraderPlannerMarketRefresh", daemon=True).start()

    def stop(self):
        self._running = False
        self._generation += 1
        if self._executor:
            try:
                self._executor.shutdown(wait=False, cancel_futures=True)
            except Exception:
                pass
            self._executor = None

    def _worker(self):
        while self._running:
            market = self._market
            generation = self._generation
            try:
                payload = fetch_market(market)
                if self.callback and market == self._market and generation == self._generation:
                    self.callback(payload)
            except Exception:
                pass
            for _ in range(self.refresh_seconds):
                if not self._running:
                    break
                time.sleep(1)
