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
USER_AGENT = "TraderPlannerPro/8.4.0 (+https://github.com/shmm66/desktop-tutorial)"

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
KRAKEN_TICKER_ENDPOINT = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD,ETHUSD,SOLUSD,XRPUSD,ADAUSD,DOGEUSD,BNBUSD"
COINBASE_PRODUCTS = [("BTC","BTC-USD"),("ETH","ETH-USD"),("SOL","SOL-USD"),("XRP","XRP-USD"),("ADA","ADA-USD"),("DOGE","DOGE-USD"),("BNB","BNB-USD")]
COINCAP_ENDPOINT = "https://api.coincap.io/v2/assets?limit=20"
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
    "https://api.frankfurter.app/latest?from=USD&to=EUR,GBP,JPY,CHF,AUD,CAD",
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


def _yahoo_symbol(symbol: str, timeout=2.8):
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


def _crypto_from_coincap():
    try:
        data = _request_json(COINCAP_ENDPOINT, timeout=3.0)
        rows = data.get("data") or []
        wanted = {label: symbol.replace("-USD","").lower() for label, symbol in CRYPTO_FALLBACK}
        out=[]
        for row in rows:
            symbol=str(row.get("symbol","")).upper()
            label=next((name for name,code in CRYPTO_FALLBACK if code.startswith(symbol+"-")),None)
            if not label:
                continue
            price=_safe_float(row.get("priceUsd"))
            change=_safe_float(row.get("changePercent24Hr"))
            if price is None:
                continue
            out.append({"symbol":label,"name":row.get("name",label),"price":price,"change":change})
        order={label:i for i,(label,_) in enumerate(CRYPTO_FALLBACK)}
        out.sort(key=lambda x: order.get(x["symbol"],999))
        return out, "CoinCap public asset data" if len(out)>=5 else "unavailable"
    except Exception:
        return [], "unavailable"


def _crypto_from_binance():
    for endpoint in BINANCE_TICKER_ENDPOINTS:
        try:
            rows = _request_json(endpoint, timeout=3.0)
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


def _crypto_from_kraken():
    try:
        data = _request_json(KRAKEN_TICKER_ENDPOINT, timeout=3.0)
        result = data.get("result") or {}
        aliases = [
            ("BTC", "XXBTZUSD"), ("ETH", "XETHZUSD"), ("SOL", "SOLUSD"),
            ("XRP", "XXRPZUSD"), ("ADA", "ADAUSD"), ("DOGE", "DOGEUSD")
        ]
        rows=[]
        for label,key in aliases:
            row = result.get(key)
            if not row:
                # Kraken may return compact aliases.
                row = next((v for k,v in result.items() if str(k).upper().replace("X","").replace("Z","") == key.replace("X","").replace("Z","")), None)
            if not row:
                continue
            last = (row.get("c") or [None])[0]
            open_price = (row.get("o") or [None])[0]
            price = _safe_float(last)
            op = _safe_float(open_price)
            if price is None:
                continue
            change = None if op in (None,0) else (price-op)/op*100.0
            rows.append({"symbol":label,"name":label,"price":price,"change":change})
        return rows, "Kraken public market data" if len(rows)>=3 else "unavailable"
    except Exception:
        return [], "unavailable"



def _crypto_from_coinbase():
    def fetch_one(pair):
        try:
            data = _request_json(f"https://api.exchange.coinbase.com/products/{pair}/ticker", timeout=3.0)
            price = _safe_float(data.get("price"))
            open_price = _safe_float(data.get("open"))
            if price is None:
                return None
            change = None if open_price in (None, 0) else (price - open_price) / open_price * 100.0
            return price, change
        except Exception:
            return None

    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(COINBASE_PRODUCTS)) as pool:
        futures = {pool.submit(fetch_one, pair): label for label, pair in COINBASE_PRODUCTS}
        for future in concurrent.futures.as_completed(futures):
            value = future.result()
            if not value:
                continue
            price, change = value
            label = futures[future]
            rows.append({"symbol": label, "name": label, "price": price, "change": change})
    order = {label: i for i, (label, _) in enumerate(COINBASE_PRODUCTS)}
    rows.sort(key=lambda x: order.get(x["symbol"], 999))
    return rows, "Coinbase Exchange public market data" if len(rows) >= 4 else "unavailable"


def _crypto_live():
    # Primary ranking by market cap.
    try:
        rows = _request_json(CRYPTO_ENDPOINT, timeout=3.0)
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

    # Fast no-key aggregator fallback.
    result, source = _crypto_from_coincap()
    if result:
        return result, source

    # Fast exchange fallback. Binance exposes public ticker market data.
    result, source = _crypto_from_binance()
    if result:
        return result, source

    # Exchange fallback.
    result, source = _crypto_from_kraken()
    if result:
        return result, source

    result, source = _crypto_from_coinbase()
    if result:
        return result, source

    # Aggregated fallback.
    try:
        rows = _request_json(CRYPTO_FALLBACK_ENDPOINT, timeout=3.0)
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


def _free_fx_rates():
    for endpoint in EXCHANGE_RATE_ENDPOINTS:
        try:
            data = _request_json(endpoint, timeout=3.0)
            rates = data.get("rates") or {}
            if not rates:
                continue
            normalized = {}
            for key, value in rates.items():
                number = _safe_float(value)
                if number is not None:
                    normalized[str(key).upper()] = number
            if normalized:
                return normalized
        except Exception:
            continue
    return {}


def _gold_spot():
    try:
        data = _request_json(GOLD_SPOT_ENDPOINT, timeout=3.0)
        rows = data.get("prices") or []
        if rows:
            row = rows[0]
            value = _safe_float(row.get("price"))
            if value is not None:
                return value, None
    except Exception:
        pass
    return None


def _croncopia_metals():
    result = {}
    for label, slug in CRONCOPIA_METALS.items():
        try:
            data = _request_json(f"{CRONCOPIA_BASE}/{slug}.json", timeout=2.8)
            price = _safe_float(data.get("price"))
            if price is None:
                continue
            # Normalize the published unit to the common dashboard display unit.
            unit = str(data.get("unit") or "").lower()
            if label == "COPPER" and "per t" in unit:
                price = price / 2204.62262185
            result[label] = price
        except Exception:
            continue
    return result


def _forex_free_fallback():
    rates = _free_fx_rates()
    if not rates:
        return []
    result = []
    for label, code in (
        ("EUR/USD", "EUR"), ("GBP/USD", "GBP"), ("USD/JPY", "JPY"),
        ("USD/CHF", "CHF"), ("AUD/USD", "AUD"), ("USD/CAD", "CAD"),
        ("GOLD", "XAU"), ("SILVER", "XAG"),
    ):
        value = rates.get(code)
        if value is None:
            continue
        # USD base rates: USD/XXX is direct; XXX/USD is the reciprocal.
        if label in ("EUR/USD", "GBP/USD", "AUD/USD"):
            price = 1.0 / value if value else None
        else:
            price = value
        if price is not None:
            result.append({"symbol": label, "name": label, "price": price, "change": None})
    gold = _gold_spot()
    if gold:
        for row in result:
            if row["symbol"] == "GOLD":
                row["price"] = gold[0]
    return result


def _forex_live():
    # Preferred source: live Yahoo chart quotes. If blocked/unavailable,
    # supplement with a no-key FX reference feed so the dashboard still shows
    # usable market context instead of a permanent loading state.
    result = _parallel_yahoo(FOREX_SYMBOLS)
    if len(result) >= 5:
        return result, "Yahoo Finance"
    fallback = _forex_free_fallback()
    by_label = {row["symbol"]: row for row in result}
    for row in fallback:
        by_label.setdefault(row["symbol"], row)
    metal_prices = _croncopia_metals()
    for label, price in metal_prices.items():
        by_label.setdefault(label, {"symbol": label, "name": label, "price": price, "change": None})
    merged = [by_label[label] for label, _ in FOREX_SYMBOLS if label in by_label]
    return merged, ("Yahoo Finance + no-key FX/metals fallback" if merged else "unavailable")


def _global_indicators():
    result = {}
    for endpoint in (GLOBAL_ENDPOINT, GLOBAL_FALLBACK_ENDPOINT):
        try:
            data = _request_json(endpoint, timeout=3.0)
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
            data = _request_json(endpoint, timeout=3.0)
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


def cached_market_payload(mode: str):
    market = "Forex" if str(mode).lower() == "forex" else "Crypto"
    cached = _read_cache()
    if cached.get("market") == market and isinstance(cached.get("items"), list) and cached.get("items"):
        return {
            "market": market,
            "updated_at": cached.get("updated_at"),
            "source": cached.get("source") or "cache",
            "items": cached.get("items", []),
            "indicators": cached.get("indicators", {}),
            "status": "cache",
            "message": "Loading live feed in background; showing last saved snapshot first.",
        }
    return {
        "market": market,
        "updated_at": None,
        "source": "unavailable",
        "items": [],
        "indicators": {},
        "status": "unavailable",
        "message": "",
    }


def fetch_market(mode: str):
    market = "Forex" if str(mode).lower() == "forex" else "Crypto"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Do not let one blocked endpoint keep the desktop in a perpetual spinner.
    # Quotes get a hard overall deadline; secondary indicators are best-effort.
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="TPMarket")
    item_future = executor.submit(_forex_live if market == "Forex" else _crypto_live)
    indicator_futures = {
        "global": executor.submit(_global_indicators),
        "fear": executor.submit(_fear_greed),
        "vix": executor.submit(_market_vix),
    }

    items, source = [], "unavailable"
    try:
        items, source = item_future.result(timeout=7.0)
    except Exception:
        try:
            item_future.cancel()
        except Exception:
            pass

    indicators = {}
    for key, future in indicator_futures.items():
        try:
            value = future.result(timeout=1.25)
            if key == "global" and isinstance(value, dict):
                indicators.update(value)
            elif key == "fear":
                indicators["fear_greed"] = value
            elif key == "vix":
                indicators["vix"] = value
        except Exception:
            if key == "fear":
                indicators["fear_greed"] = None
            elif key == "vix":
                indicators["vix"] = None

    indicators["market_regime"] = "LIVE" if items else "OFFLINE"
    try:
        executor.shutdown(wait=False, cancel_futures=True)
    except Exception:
        try:
            executor.shutdown(wait=False)
        except Exception:
            pass

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
    if cached.get("market") == market and isinstance(cached.get("items"), list) and cached.get("items"):
        return {
            "market": market,
            "updated_at": cached.get("updated_at"),
            "source": cached.get("source") or "cache",
            "items": cached.get("items", []),
            "indicators": cached.get("indicators", indicators),
            "status": "cache",
            "message": "Live feed unavailable; showing last saved market snapshot.",
        }

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
        self._state_lock = threading.Lock()
        self._active_refresh_generation = None
        self._generation = 0

    def start(self, market: str):
        self.set_market(market)
        if self._running:
            self.refresh_now()
            return
        self._running = True
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._future = self._executor.submit(self._worker)

    def set_market(self, market: str):
        normalized = "Forex" if market == "Forex" else "Crypto"
        if normalized != self._market:
            self._generation += 1
        self._market = normalized

    def generation(self):
        return self._generation

    def refresh_now(self):
        market = self._market
        generation = self._generation
        # One request per generation, not one global request forever. This lets
        # a new Crypto/Forex selection refresh immediately even if the previous
        # market request is still waiting on a slow endpoint.
        with self._state_lock:
            if self._active_refresh_generation == generation:
                return
            self._active_refresh_generation = generation

        def run():
            try:
                payload = fetch_market(market)
                if generation != self._generation or market != self._market:
                    return
                if self.callback:
                    self.callback(payload)
            finally:
                with self._state_lock:
                    if self._active_refresh_generation == generation:
                        self._active_refresh_generation = None

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
            generation = self._generation
            payload = fetch_market(market)
            if generation == self._generation and market == self._market and self.callback:
                try:
                    self.callback(payload)
                except Exception:
                    pass
            for _ in range(self.refresh_seconds):
                if not self._running:
                    break
                time.sleep(1)
