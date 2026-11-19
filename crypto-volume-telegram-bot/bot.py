import os
import asyncio
import statistics
import logging
from datetime import datetime, timezone

import httpx

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
CG_KEY = os.getenv("COINGECKO_DEMO_API_KEY", "").strip()
CMC_KEY = os.getenv("COINMARKETCAP_API_KEY", "").strip()
TOP_N = min(100, max(10, int(os.getenv("TOP_N", "100"))))
RVOL_MIN = float(os.getenv("ALERT_RVOL", "2.0"))
RVOL_MAX = float(os.getenv("ALERT_COLLAPSE", "0.5"))

CG = "https://api.coingecko.com/api/v3"
OKX = "https://www.okx.com"
BYBIT = "https://api.bybit.com"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("scanner")


async def get(client, url, params=None, headers=None):
    last_error = None
    for attempt in range(4):
        try:
            response = await client.get(url, params=params, headers=headers, timeout=25)
            if response.status_code == 429 or response.status_code >= 500:
                last_error = RuntimeError(f"HTTP {response.status_code} from {url}")
                await asyncio.sleep(min(2 ** attempt, 12))
                continue
            response.raise_for_status()
            payload = response.json()

            if isinstance(payload, dict):
                if "code" in payload and str(payload.get("code")) != "0":
                    raise RuntimeError(f"API error from {url}: {payload.get('code')} {payload.get('msg', '')}")
                if "retCode" in payload and int(payload.get("retCode", 0)) != 0:
                    raise RuntimeError(f"API error from {url}: {payload.get('retCode')} {payload.get('retMsg', '')}")
            return payload

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status != 429 and status < 500:
                raise RuntimeError(f"Non-retryable HTTP {status} from {url}") from exc
            last_error = exc
            await asyncio.sleep(min(2 ** attempt, 12))
        except RuntimeError:
            raise
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(min(2 ** attempt, 12))

    raise RuntimeError(f"API request failed: {url}: {last_error}")


async def get_universe(client):
    headers = {"x-cg-demo-api-key": CG_KEY} if CG_KEY else {}
    try:
        data = await get(
            client,
            CG + "/coins/markets",
            {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": TOP_N,
                "page": 1,
                "sparkline": "false",
                "price_change_percentage": "24h,7d",
            },
            headers,
        )
        return [
            {
                "symbol": coin["symbol"].upper(),
                "name": coin["name"],
                "rank": coin.get("market_cap_rank"),
                "change24": coin.get("price_change_percentage_24h"),
                "change7": coin.get("price_change_percentage_7d_in_currency"),
            }
            for coin in data
        ]
    except Exception as exc:
        log.warning("CoinGecko failed: %s", exc)

    if CMC_KEY:
        data = await get(
            client,
            "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest",
            {"start": 1, "limit": TOP_N, "convert": "USD"},
            {"X-CMC_PRO_API_KEY": CMC_KEY},
        )
        return [
            {
                "symbol": coin["symbol"].upper(),
                "name": coin["name"],
                "rank": coin.get("cmc_rank"),
                "change24": coin["quote"]["USD"].get("percent_change_24h"),
                "change7": coin["quote"]["USD"].get("percent_change_7d"),
            }
            for coin in data.get("data", [])
        ]

    raise RuntimeError("Universe API unavailable. Add a CoinGecko Demo key or CMC key.")


async def load_okx_pairs(client):
    payload = await get(client, OKX + "/api/v5/public/instruments", {"instType": "SPOT"})
    pairs = {}
    for item in payload.get("data", []):
        if item.get("state") == "live" and item.get("quoteCcy") == "USDT":
            pairs[item.get("baseCcy", "").upper()] = item["instId"]
    if not pairs:
        raise RuntimeError("OKX returned no live USDT spot pairs.")
    return pairs


async def load_bybit_pairs(client):
    payload = await get(
        client,
        BYBIT + "/v5/market/instruments-info",
        {"category": "spot"},
    )
    pairs = {}
    for item in payload.get("result", {}).get("list", []):
        if item.get("status") == "Trading" and item.get("quoteCoin") == "USDT":
            pairs[item.get("baseCoin", "").upper()] = item["symbol"]
    if not pairs:
        raise RuntimeError("Bybit returned no trading USDT spot pairs.")
    return pairs


def relative_volume(volumes):
    if len(volumes) < 48:
        raise RuntimeError("Insufficient closed hourly candles.")
    baseline = volumes[:-1][-167:]
    median_volume = statistics.median(baseline)
    if median_volume <= 0:
        raise RuntimeError("Invalid volume baseline.")
    return volumes[-1] / median_volume, volumes[-1], median_volume


async def fetch_okx_volume(client, inst_id):
    payload = await get(
        client,
        OKX + "/api/v5/market/candles",
        {"instId": inst_id, "bar": "1H", "limit": "200"},
    )
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    candles = [
        candle
        for candle in payload.get("data", [])
        if len(candle) >= 9 and candle[8] == "1" and int(candle[0]) + 3_600_000 <= now_ms
    ]
    candles.sort(key=lambda candle: int(candle[0]))
    # OKX field 7 is quote-currency turnover (USDT for these pairs).
    volumes = [float(candle[7]) for candle in candles]
    return relative_volume(volumes)


async def fetch_bybit_volume(client, symbol):
    payload = await get(
        client,
        BYBIT + "/v5/market/kline",
        {"category": "spot", "symbol": symbol, "interval": "60", "limit": "200"},
    )
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    candles = [
        candle
        for candle in payload.get("result", {}).get("list", [])
        if len(candle) >= 7 and int(candle[0]) + 3_600_000 <= now_ms
    ]
    candles.sort(key=lambda candle: int(candle[0]))
    # Bybit field 6 is turnover in quote currency (USDT for these pairs).
    volumes = [float(candle[6]) for candle in candles]
    return relative_volume(volumes)


async def main():
    if not TG_TOKEN or not CHAT_ID:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")

    limits = httpx.Limits(max_connections=16, max_keepalive_connections=8)
    async with httpx.AsyncClient(
        limits=limits,
        headers={"User-Agent": "CryptoVolumeScanner/0.2"},
    ) as client:
        assets = await get_universe(client)

        okx_pairs = {}
        bybit_pairs = {}
        try:
            okx_pairs = await load_okx_pairs(client)
            log.info("OKX live USDT spot pairs: %s", len(okx_pairs))
        except Exception as exc:
            log.warning("OKX instrument list unavailable: %s", exc)

        try:
            bybit_pairs = await load_bybit_pairs(client)
            log.info("Bybit trading USDT spot pairs: %s", len(bybit_pairs))
        except Exception as exc:
            log.warning("Bybit instrument list unavailable: %s", exc)

        if not okx_pairs and not bybit_pairs:
            raise RuntimeError("Both OKX and Bybit public spot instrument APIs are unavailable.")

        semaphore = asyncio.Semaphore(8)

        async def scan(asset):
            symbol = asset["symbol"]
            errors = []

            async with semaphore:
                if symbol in okx_pairs:
                    try:
                        rvol, volume, median_volume = await fetch_okx_volume(client, okx_pairs[symbol])
                        return {
                            **asset,
                            "status": "ok",
                            "venue": "OKX",
                            "rvol": rvol,
                            "volume": volume,
                            "median": median_volume,
                        }
                    except Exception as exc:
                        errors.append("OKX: " + str(exc)[:100])

                if symbol in bybit_pairs:
                    try:
                        rvol, volume, median_volume = await fetch_bybit_volume(client, bybit_pairs[symbol])
                        return {
                            **asset,
                            "status": "ok",
                            "venue": "Bybit",
                            "rvol": rvol,
                            "volume": volume,
                            "median": median_volume,
                        }
                    except Exception as exc:
                        errors.append("Bybit: " + str(exc)[:100])

            if symbol not in okx_pairs and symbol not in bybit_pairs:
                return {**asset, "status": "not_listed"}
            return {**asset, "status": "error", "error": " | ".join(errors)}

        rows = await asyncio.gather(*(scan(asset) for asset in assets))
        valid = [row for row in rows if row["status"] == "ok"]
        surge = sorted(
            [row for row in valid if row["rvol"] >= RVOL_MIN],
            key=lambda row: row["rvol"],
            reverse=True,
        )[:10]
        collapse = sorted(
            [row for row in valid if row["rvol"] <= RVOL_MAX],
            key=lambda row: row["rvol"],
        )[:10]

        venue_counts = {
            venue: sum(1 for row in valid if row["venue"] == venue)
            for venue in ("OKX", "Bybit")
        }
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        out = [
            f"📊 CRYPTO VOLUME SCANNER | {stamp}",
            f"Top universe: {len(assets)} | Valid Spot USDT markets: {len(valid)}/{len(assets)}",
            f"Venue coverage: OKX {venue_counts['OKX']} | Bybit {venue_counts['Bybit']}",
            "Hourly quote turnover vs median of up to previous 167 closed hourly candles.",
            "Volume unit: USDT. Volume changes alone do not prove capital inflow/outflow.",
            "",
            "🚀 SURGE",
        ]
        out += [
            f"{row['symbol']} (#{row.get('rank') or '-'}) — {row['rvol']:.2f}x | "
            f"1h {row['volume']:,.0f} USDT | 24h price {row.get('change24')}% | {row['venue']}"
            for row in surge
        ] or ["No surge above threshold."]

        out += ["", "🧊 COLLAPSE"]
        out += [
            f"{row['symbol']} — {row['rvol']:.2f}x | "
            f"1h {row['volume']:,.0f} USDT | 24h price {row.get('change24')}% | {row['venue']}"
            for row in collapse
        ] or ["No collapse below threshold."]

        missing = [row["symbol"] for row in rows if row["status"] != "ok"]
        out += [
            "",
            "🩺 DATA HEALTH",
            f"Valid: {len(valid)}/{len(assets)} | unavailable/partial: {len(missing)}",
        ]
        if missing:
            out.append("Not covered: " + ", ".join(missing[:30]))

        out += [
            "",
            "Sources: CoinGecko/CMC universe + OKX/Bybit Spot OHLCV.",
            "Scope: Binance is intentionally not used because GitHub runner received HTTP 451.",
            "Futures/OI/Funding/Liquidations and BTC-relative strength are not yet implemented.",
        ]

        response = await client.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": "\n".join(out)[:3900],
                "disable_web_page_preview": True,
            },
            timeout=20,
        )
        response.raise_for_status()
        if not response.json().get("ok"):
            raise RuntimeError("Telegram rejected the message.")

        log.info(
            "Report sent. valid=%s total=%s OKX=%s Bybit=%s",
            len(valid),
            len(assets),
            venue_counts["OKX"],
            venue_counts["Bybit"],
        )


if __name__ == "__main__":
    asyncio.run(main())
