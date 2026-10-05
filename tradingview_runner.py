from __future__ import annotations

import json
import sys
import webbrowser
from urllib.parse import quote

try:
    import webview
except Exception:
    webview = None

APP = "Trader Planner Pro — TradingView Pro"
# Production test path: use TradingView candles directly; never synthesize OHLC in this layer.

INTERVALS = {
    "1m": "1",
    "3m": "3",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1H": "60",
    "4H": "240",
    "1D": "D",
    "1W": "W",
    "1M": "M",
}

CRYPTO_WATCHLIST = [
    "BINANCE:BTCUSDT", "BINANCE:ETHUSDT", "BINANCE:BNBUSDT",
    "BINANCE:SOLUSDT", "BINANCE:XRPUSDT", "BINANCE:ADAUSDT",
    "BINANCE:DOGEUSDT", "BINANCE:AVAXUSDT", "BINANCE:LINKUSDT",
    "BINANCE:TRXUSDT", "CRYPTOCAP:BTC.D", "CRYPTOCAP:USDT.D",
    "CRYPTOCAP:TOTAL", "CRYPTOCAP:TOTAL2", "CRYPTOCAP:TOTAL3",
]

FOREX_WATCHLIST = [
    "OANDA:XAUUSD", "OANDA:XAGUSD", "FXCM:COPPER",
    "OANDA:EURUSD", "OANDA:GBPUSD", "OANDA:USDJPY",
    "OANDA:USDCHF", "OANDA:AUDUSD", "OANDA:USDCAD",
    "OANDA:NZDUSD", "TVC:DXY", "SP:SPX", "NASDAQ:NDX",
    "DJ:DJI", "NYMEX:CL1!", "NYMEX:BRENT1!",
    "NASDAQ:AAPL", "NASDAQ:MSFT", "NASDAQ:NVDA", "NASDAQ:AMZN",
    "NASDAQ:META", "NASDAQ:TSLA", "NASDAQ:GOOGL", "NYSE:JPM",
]


def _escape_for_html(value: str) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def build_tradingview_html(symbol: str = "BINANCE:BTCUSDT",
                           interval: str = "60",
                           locale: str = "en",
                           theme: str = "dark",
                           watchlist: list[str] | None = None) -> str:
    interval = str(interval or "60")
    if interval not in set(INTERVALS.values()):
        interval = "60"
    locale = "fa" if str(locale).lower() == "fa" else "en"
    theme = "light" if str(theme).lower() == "light" else "dark"
    bg = "#0A1018" if theme == "dark" else "#F4F7FA"
    grid = "rgba(110,128,145,0.14)" if theme == "dark" else "rgba(46,64,78,0.14)"
    wl = watchlist or CRYPTO_WATCHLIST

    # TradingView's embeddable Advanced Chart widget is intentionally used here.
    # It provides the real chart UI/datafeed, symbol search, resolutions, drawing
    # toolbar, volume, studies and image/fullscreen actions without fabricating candles.
    config = {
        "autosize": True,
        "symbol": symbol,
        "interval": interval,
        "timezone": "exchange",
        "theme": theme,
        "style": "1",
        "backgroundColor": bg,
        "gridColor": grid,
        "withdateranges": True,
        "hide_side_toolbar": False,
        "hide_top_toolbar": False,
        "hide_legend": False,
        "hide_volume": False,
        "allow_symbol_change": True,
        "save_image": True,
        "calendar": False,
        "hotlist": False,
        "details": True,
        "locale": locale,
        "watchlist": wl,
        "compareSymbols": [],
        "studies": [],
        "support_host": "https://www.tradingview.com",
        "range": "12M",
        "enable_publishing": False,
        "show_popup_button": True,
    }

    cfg = json.dumps(config, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="{locale}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trader Planner Pro — TradingView Pro</title>
<style>
  html, body, #tv_chart_container {{
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
    overflow: hidden;
    background: {bg};
  }}
  body {{
    font-family: "Segoe UI", Arial, sans-serif;
  }}
  #loading {{
    position: fixed;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
    color: #dbe7ef;
    background: {bg};
    transition: opacity .25s ease;
  }}
  .loading-box {{
    min-width: 280px;
    padding: 24px 28px;
    border: 1px solid rgba(91, 128, 149, .28);
    border-radius: 18px;
    background: rgba(15, 24, 35, .86);
    box-shadow: 0 18px 50px rgba(0,0,0,.35);
    backdrop-filter: blur(18px);
    text-align: center;
  }}
  .brand {{
    font-weight: 700;
    letter-spacing: .08em;
    font-size: 13px;
  }}
  .sub {{
    margin-top: 8px;
    opacity: .65;
    font-size: 11px;
  }}
</style>
</head>
<body>
<div id="loading">
  <div class="loading-box">
    <div class="brand">TRADER PLANNER PRO • TRADINGVIEW PRO</div>
    <div class="sub">Loading official TradingView market chart…</div>
  </div>
</div>
<div id="tv_chart_container"></div>
<script type="text/javascript">
  const tvConfig = {cfg};
  const script = document.createElement("script");
  script.type = "text/javascript";
  script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
  script.async = true;
  script.innerHTML = JSON.stringify(tvConfig);
  document.getElementById("tv_chart_container").appendChild(script);
  window.addEventListener("load", () => {{
    const node = document.getElementById("loading");
    setTimeout(() => {{
      node.style.opacity = "0";
      setTimeout(() => node.remove(), 260);
    }}, 700);
  }});
</script>
</body>
</html>"""


def open_tradingview(symbol: str = "BINANCE:BTCUSDT",
                     interval: str = "1H",
                     locale: str = "en",
                     theme: str = "dark",
                     mode: str = "Crypto") -> int:
    tv_interval = INTERVALS.get(str(interval), str(interval) or "60")
    watchlist = FOREX_WATCHLIST if str(mode).lower() == "forex" else CRYPTO_WATCHLIST
    html = build_tradingview_html(symbol, tv_interval, locale, theme, watchlist)
    title = f"{APP} • {symbol} • {interval}"

    if webview is None:
        fallback = "https://www.tradingview.com/chart/?symbol=" + quote(symbol, safe=":")
        webbrowser.open(fallback)
        return 0

    try:
        webview.create_window(
            title,
            html=html,
            width=1680,
            height=1000,
            min_size=(1200, 760),
            resizable=True,
            fullscreen=False,
            background_color="#0A1018" if theme == "dark" else "#F4F7FA",
            text_select=False,
            zoomable=True,
        )
        webview.start(gui="edgechromium", debug=False)
        return 0
    except Exception:
        fallback = "https://www.tradingview.com/chart/?symbol=" + quote(symbol, safe=":")
        webbrowser.open(fallback)
        return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    symbol = args[0] if len(args) >= 1 and args[0] else "BINANCE:BTCUSDT"
    interval = args[1] if len(args) >= 2 and args[1] else "1H"
    locale = args[2] if len(args) >= 3 and args[2] else "en"
    theme = args[3] if len(args) >= 4 and args[3] else "dark"
    mode = args[4] if len(args) >= 5 and args[4] else "Crypto"
    return open_tradingview(symbol, interval, locale, theme, mode)


if __name__ == "__main__":
    raise SystemExit(main())
