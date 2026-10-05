from __future__ import annotations

import json
import threading
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter, date2num
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

BINANCE_ENDPOINTS = [
    "https://api.binance.com/api/v3/klines",
    "https://data-api.binance.vision/api/v3/klines",
]
YAHOO_ENDPOINTS = [
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
    "https://query2.finance.yahoo.com/v8/finance/chart/{symbol}",
]
COINGECKO_TOP = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false&price_change_percentage=24h"
COINGECKO_GLOBAL = "https://api.coingecko.com/api/v3/global"

FOREX_ITEMS = [
    ("Gold", "GC=F"), ("Silver", "SI=F"), ("Copper", "HG=F"),
    ("EUR/USD", "EURUSD=X"), ("GBP/USD", "GBPUSD=X"), ("USD/JPY", "JPY=X"),
    ("USD/CHF", "CHF=X"), ("AUD/USD", "AUDUSD=X"), ("USD/CAD", "CAD=X"),
    ("NZD/USD", "NZDUSD=X"), ("DXY", "DX-Y.NYB"), ("S&P 500", "^GSPC"),
    ("NASDAQ 100", "^NDX"), ("Dow Jones", "^DJI"), ("WTI Oil", "CL=F"),
    ("Brent Oil", "BZ=F"), ("Apple", "AAPL"), ("Microsoft", "MSFT"),
    ("NVIDIA", "NVDA"), ("Amazon", "AMZN"), ("Meta", "META"), ("Tesla", "TSLA"),
]
INTERVALS = [
    ("1m", "1m"), ("3m", "3m"), ("5m", "5m"), ("15m", "15m"),
    ("30m", "30m"), ("1H", "1h"), ("4H", "4h"), ("1D", "1d"),
    ("1W", "1w"), ("1M", "1M"),
]

def _json(url: str, timeout: float = 7.0):
    req = urllib.request.Request(url, headers={
        "User-Agent": "TraderPlannerPro/NativeTradingDesk",
        "Accept": "application/json,text/plain,*/*",
    })
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def _f(v):
    try:
        return float(v)
    except Exception:
        return None

def _fmt_price(v):
    if v is None:
        return "—"
    a = abs(v)
    if a >= 1000:
        return f"{v:,.2f}"
    if a >= 1:
        return f"{v:,.4f}"
    return f"{v:.8f}".rstrip("0").rstrip(".")

def _fmt_cap(v):
    if not v:
        return "—"
    if v >= 1e12:
        return f"USD {v/1e12:.2f}T"
    if v >= 1e9:
        return f"USD {v/1e9:.2f}B"
    if v >= 1e6:
        return f"USD {v/1e6:.2f}M"
    return f"USD {v:,.0f}"

def _yahoo_range(interval):
    return {
        "1m": ("1d", "1m"), "3m": ("5d", "5m"), "5m": ("5d", "5m"),
        "15m": ("1mo", "15m"), "30m": ("1mo", "30m"), "1h": ("3mo", "1h"),
        "4h": ("1y", "1h"), "1d": ("5y", "1d"), "1w": ("10y", "1wk"),
        "1M": ("max", "1mo"),
    }.get(interval, ("3mo", "1h"))

def _binance_klines(symbol, interval, limit=420):
    params = urllib.parse.urlencode({"symbol": symbol.upper(), "interval": interval, "limit": limit})
    for base in BINANCE_ENDPOINTS:
        try:
            rows = _json(base + "?" + params)
            out = []
            for r in rows:
                if len(r) < 6:
                    continue
                out.append({
                    "time": datetime.fromtimestamp(float(r[0]) / 1000, tz=timezone.utc),
                    "open": _f(r[1]), "high": _f(r[2]), "low": _f(r[3]),
                    "close": _f(r[4]), "volume": _f(r[5]) or 0.0,
                })
            if len(out) > 20:
                return out, "Binance"
        except Exception:
            continue
    return [], "unavailable"

def _resample_4h(rows):
    buckets = {}
    for r in rows:
        t = r["time"].astimezone(timezone.utc)
        bucket = t.replace(hour=(t.hour // 4) * 4, minute=0, second=0, microsecond=0)
        b = buckets.get(bucket)
        if b is None:
            buckets[bucket] = {
                "time": bucket, "open": r["open"], "high": r["high"],
                "low": r["low"], "close": r["close"], "volume": r["volume"],
            }
        else:
            b["high"] = max(b["high"], r["high"])
            b["low"] = min(b["low"], r["low"])
            b["close"] = r["close"]
            b["volume"] += r["volume"]
    return [buckets[k] for k in sorted(buckets)]

def _yahoo_history(symbol, interval):
    range_value, yahoo_interval = _yahoo_range(interval)
    encoded = urllib.parse.quote(symbol, safe="")
    for base in YAHOO_ENDPOINTS:
        try:
            url = base.format(symbol=encoded) + "?" + urllib.parse.urlencode({
                "range": range_value, "interval": yahoo_interval,
                "events": "history", "includeAdjustedClose": "true",
            })
            payload = _json(url)
            result = (payload.get("chart", {}).get("result") or [None])[0]
            if not result:
                continue
            ts = result.get("timestamp") or []
            quote = (((result.get("indicators") or {}).get("quote") or [None])[0] or {})
            opens, highs = quote.get("open") or [], quote.get("high") or []
            lows, closes = quote.get("low") or [], quote.get("close") or []
            vols = quote.get("volume") or []
            out = []
            for i, raw_ts in enumerate(ts):
                if i >= len(opens):
                    break
                o = _f(opens[i]) if i < len(opens) else None
                h = _f(highs[i]) if i < len(highs) else None
                l = _f(lows[i]) if i < len(lows) else None
                c = _f(closes[i]) if i < len(closes) else None
                if None in (o, h, l, c):
                    continue
                v = _f(vols[i]) if i < len(vols) else 0.0
                out.append({
                    "time": datetime.fromtimestamp(float(raw_ts), tz=timezone.utc),
                    "open": o, "high": h, "low": l, "close": c, "volume": v or 0.0,
                })
            if interval == "4h":
                out = _resample_4h(out)
            if len(out) > 20:
                return out[-420:], "Yahoo Finance"
        except Exception:
            continue
    return [], "unavailable"

def _coingecko_ohlc(coin_id, interval):
    days = {"1h": 30, "4h": 90, "1d": 365, "1w": 365, "1M": 365}.get(interval, 30)
    try:
        url = "https://api.coingecko.com/api/v3/coins/" + urllib.parse.quote(str(coin_id), safe="") + "/ohlc?" + urllib.parse.urlencode({
            "vs_currency": "usd", "days": days
        })
        rows = _json(url)
        out = []
        for r in rows or []:
            if len(r) < 5:
                continue
            out.append({
                "time": datetime.fromtimestamp(float(r[0]) / 1000, tz=timezone.utc),
                "open": _f(r[1]), "high": _f(r[2]), "low": _f(r[3]),
                "close": _f(r[4]), "volume": 0.0,
            })
        if len(out) > 20:
            return out[-420:], "CoinGecko OHLC"
    except Exception:
        pass
    return [], "unavailable"


def _fetch_crypto_universe():
    try:
        rows = _json(COINGECKO_TOP)
        result = []
        for idx, r in enumerate(rows or [], 1):
            symbol = str(r.get("symbol") or "").upper()
            if not symbol:
                continue
            result.append({
                "rank": int(r.get("market_cap_rank") or idx),
                "symbol": symbol,
                "name": r.get("name") or symbol,
                "id": r.get("id") or symbol.lower(),
                "price": _f(r.get("current_price")),
                "change": _f(r.get("price_change_percentage_24h")),
                "binance": symbol + "USDT",
            })
        return result, "CoinGecko"
    except Exception:
        return [], "unavailable"

def _fetch_global():
    try:
        d = _json(COINGECKO_GLOBAL).get("data") or {}
        pct = d.get("market_cap_percentage") or {}
        return {
            "total_market_cap": _f((d.get("total_market_cap") or {}).get("usd")),
            "volume_24h": _f((d.get("total_volume") or {}).get("usd")),
            "btc_dominance": _f(pct.get("btc")),
            "usdt_dominance": _f(pct.get("usdt")),
        }
    except Exception:
        return {}

class NativeTradingDesk(tk.Frame):
    """Native Tk/Matplotlib Trading Desk. No browser, HTML or WebView."""

    def __init__(self, parent, colors, language="en"):
        super().__init__(parent, bg=colors["bg"])
        self.colors = colors
        self.language = language
        self.mode = "Crypto"
        self.symbol = "BTCUSDT"
        self.symbol_name = "BTC / USDT"
        self.interval = "1h"
        self.data = []
        self.universe = []
        self.draw_mode = "cursor"
        self.draw_first = None
        self.draw_artists = []
        self.cross_v = None
        self.cross_h = None
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Connecting to market feed…")
        self.symbol_var = tk.StringVar(value=self.symbol_name)
        self.interval_var = tk.StringVar(value="1H")
        self._build()
        self._load_market()

    def _panel(self, parent):
        return tk.Frame(parent, bg=self.colors["panel2"],
                        highlightbackground=self.colors["line"], highlightthickness=1, bd=0)

    def _build(self):
        top = tk.Frame(self, bg=self.colors["panel"], height=58)
        top.pack(fill="x", padx=6, pady=(6, 4))
        top.pack_propagate(False)
        tk.Label(top, text="TRADING DESK", bg=self.colors["panel"], fg=self.colors["accent"],
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=(12, 18))

        for label, mode in (("CRYPTO", "Crypto"), ("FOREX", "Forex")):
            tk.Button(top, text=label, command=lambda m=mode: self.switch_mode(m),
                      bg=self.colors["soft"], fg=self.colors["text"],
                      activebackground=self.colors["accent"], activeforeground=self.colors["bg"],
                      relief="flat", padx=12, pady=7).pack(side="left", padx=3)

        tk.Entry(top, textvariable=self.search_var, bg=self.colors["soft"], fg=self.colors["text"],
                 insertbackground=self.colors["text"], relief="flat", width=22).pack(side="left", padx=8)
        tk.Button(top, text="Search", command=self._search,
                  bg=self.colors["soft"], fg=self.colors["text"], relief="flat", padx=10).pack(side="left")

        self.interval_box = ttk.Combobox(top, textvariable=self.interval_var,
                                         values=[x[0] for x in INTERVALS], state="readonly", width=7)
        self.interval_box.pack(side="left", padx=8)
        self.interval_box.bind("<<ComboboxSelected>>", lambda e: self._interval_changed())

        tk.Button(top, text="↻ Refresh", command=self.refresh,
                  bg=self.colors["soft"], fg=self.colors["text"], relief="flat", padx=10).pack(side="right", padx=4)
        tk.Button(top, text="⌂ Home", command=self._home,
                  bg=self.colors["soft"], fg=self.colors["text"], relief="flat", padx=10).pack(side="right", padx=4)

        body = tk.Frame(self, bg=self.colors["bg"])
        body.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        left = self._panel(body)
        left.pack(side="left", fill="y", padx=(0, 4))
        left.configure(width=270)
        left.pack_propagate(False)
        tk.Label(left, text="WATCHLIST", bg=self.colors["panel2"], fg=self.colors["text"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 3))
        self.watch_info = tk.Label(left, text="Top 100 • online", bg=self.colors["panel2"],
                                   fg=self.colors["muted"], font=("Segoe UI", 8))
        self.watch_info.pack(anchor="w", padx=10, pady=(0, 8))
        self.listbox = tk.Listbox(left, bg=self.colors["panel3"], fg=self.colors["text"],
                                  selectbackground=self.colors["accent"], selectforeground=self.colors["bg"],
                                  relief="flat", bd=0, activestyle="none", font=("Consolas", 9))
        self.listbox.pack(fill="both", expand=True, padx=6, pady=6)
        self.listbox.bind("<<ListboxSelect>>", self._watch_select)

        center = self._panel(body)
        center.pack(side="left", fill="both", expand=True, padx=4)
        chart_head = tk.Frame(center, bg=self.colors["panel2"], height=58)
        chart_head.pack(fill="x")
        chart_head.pack_propagate(False)
        tk.Label(chart_head, textvariable=self.symbol_var, bg=self.colors["panel2"], fg=self.colors["text"],
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=12, pady=8)
        self.meta_label = tk.Label(chart_head, text="LIVE", bg=self.colors["panel2"], fg=self.colors["muted"],
                                   font=("Consolas", 8))
        self.meta_label.pack(side="left", padx=4)

        tools = tk.Frame(chart_head, bg=self.colors["panel2"])
        tools.pack(side="right", padx=8)
        for text, mode in (("Cursor","cursor"),("H-Line","hline"),("Trend","trend"),("Rect","rect"),("Clear","clear")):
            tk.Button(tools, text=text, command=lambda m=mode: self._draw_tool(m),
                      bg=self.colors["soft"], fg=self.colors["text"], relief="flat", padx=7).pack(side="left", padx=2)

        self.figure = Figure(figsize=(9, 6), dpi=100, facecolor=self.colors["panel3"])
        self.ax = self.figure.add_axes([0.07, 0.08, 0.90, 0.86])
        self.ax.set_facecolor(self.colors["panel3"])
        self.ax.grid(True, alpha=0.10, linewidth=0.7)
        self.canvas = FigureCanvasTkAgg(self.figure, master=center)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=2)

        toolbar = NavigationToolbar2Tk(self.canvas, center, pack_toolbar=False)
        toolbar.update()
        toolbar.configure(background=self.colors["panel2"])
        toolbar.pack(fill="x", padx=4, pady=(0, 5))
        self.canvas.mpl_connect("button_press_event", self._chart_click)
        self.canvas.mpl_connect("motion_notify_event", self._crosshair)
        self.canvas.mpl_connect("scroll_event", self._wheel_zoom)

        right = self._panel(body)
        right.pack(side="left", fill="y", padx=(4, 0))
        right.configure(width=220)
        right.pack_propagate(False)
        tk.Label(right, text="MARKET SNAPSHOT", bg=self.colors["panel2"], fg=self.colors["text"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 8))
        self.metrics = {}
        for key, title in (
            ("total_market_cap", "Total Market Cap"), ("volume_24h", "24h Volume"),
            ("btc_dominance", "BTC Dominance"), ("usdt_dominance", "USDT Dominance"),
        ):
            box = tk.Frame(right, bg=self.colors["panel3"])
            box.pack(fill="x", padx=8, pady=4)
            tk.Label(box, text=title, bg=self.colors["panel3"], fg=self.colors["muted"],
                     font=("Segoe UI", 8)).pack(anchor="w", padx=8, pady=(6, 0))
            v = tk.Label(box, text="—", bg=self.colors["panel3"], fg=self.colors["text"],
                         font=("Consolas", 11, "bold"))
            v.pack(anchor="w", padx=8, pady=(0, 7))
            self.metrics[key] = v
        tk.Label(right, text="DATA SOURCE", bg=self.colors["panel2"], fg=self.colors["text"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(14, 4))
        tk.Label(right, textvariable=self.status_var, bg=self.colors["panel2"], fg=self.colors["gold"],
                 justify="left", wraplength=190, font=("Segoe UI", 8)).pack(anchor="w", padx=10, pady=(0, 10))
        tk.Label(right, text="Native controls: mouse wheel zoom, toolbar pan/zoom/home/save.\nDrawing tools: H-Line, Trend, Rect.",
                 bg=self.colors["panel2"], fg=self.colors["muted"], justify="left", wraplength=190,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=10, pady=8)

    def _home(self):
        try:
            self.master.master.go_home()
        except Exception:
            pass

    def _load_market(self):
        threading.Thread(target=self._market_worker, daemon=True).start()

    def refresh(self):
        self._load_market()
        self._load_chart()

    def switch_mode(self, mode):
        if mode == self.mode:
            return
        self.mode = mode
        self.symbol = "BTCUSDT" if mode == "Crypto" else "GC=F"
        self.symbol_name = "BTC / USDT" if mode == "Crypto" else "Gold"
        self.symbol_var.set(self.symbol_name)
        self._load_market()

    def _market_worker(self):
        try:
            if self.mode == "Crypto":
                universe, source = _fetch_crypto_universe()
                global_data = _fetch_global()
            else:
                universe = [{"rank": i + 1, "symbol": s, "name": n, "price": None, "change": None}
                            for i, (n, s) in enumerate(FOREX_ITEMS)]
                source = "Yahoo Finance"
                global_data = {}
            self.after(0, lambda: self._market_ready(universe, source, global_data))
        except Exception as exc:
            self.after(0, lambda: self.status_var.set(f"Market feed error: {exc}"))

    def _market_ready(self, universe, source, global_data):
        self.universe = universe
        self.watch_info.config(text=f"{self.mode} • {source}")
        self._render_watchlist()
        for key, label in self.metrics.items():
            value = global_data.get(key)
            if key in ("btc_dominance", "usdt_dominance"):
                label.config(text=f"{value:.2f}%" if value is not None else "—")
            else:
                label.config(text=_fmt_cap(value))
        self.status_var.set(f"{source} • online")
        self._load_chart()

    def _render_watchlist(self):
        self.listbox.delete(0, tk.END)
        q = self.search_var.get().strip().lower()
        rows = [r for r in self.universe if not q or q in str(r.get("name","")).lower() or q in str(r.get("symbol","")).lower()]
        for row in rows[:100]:
            sym = row.get("symbol","")
            price = _fmt_price(row.get("price"))
            change = row.get("change")
            ch = "—" if change is None else f"{change:+.2f}%"
            self.listbox.insert(tk.END, f"{sym:<12} {price:>15} {ch:>8}  | {row.get('name','')}")
        if rows:
            idx = next((i for i, r in enumerate(rows) if r.get("symbol") == self.symbol or r.get("binance") == self.symbol), 0)
            self.listbox.selection_set(min(idx, len(rows) - 1))
            self.listbox.see(min(idx, len(rows) - 1))

    def _search(self):
        self._render_watchlist()

    def _watch_select(self, _event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        q = self.search_var.get().strip().lower()
        rows = [r for r in self.universe if not q or q in str(r.get("name","")).lower() or q in str(r.get("symbol","")).lower()]
        if sel[0] >= len(rows):
            return
        row = rows[sel[0]]
        if self.mode == "Crypto":
            self.symbol = row.get("binance") or ("COINGECKO:" + str(row.get("id") or row.get("symbol","")).lower())
            self.symbol_name = f"{row.get('symbol')} / USDT"
        else:
            self.symbol = row.get("symbol")
            self.symbol_name = row.get("name")
        self.symbol_var.set(self.symbol_name)
        self._load_chart()

    def _interval_changed(self):
        self.interval = dict(INTERVALS).get(self.interval_var.get(), "1h")
        self._load_chart()

    def _load_chart(self):
        symbol, interval, mode = self.symbol, self.interval, self.mode
        self.status_var.set(f"Loading {self.symbol_name} • {self.interval_var.get()}…")
        threading.Thread(target=self._chart_worker, args=(symbol, interval, mode), daemon=True).start()

    def _chart_worker(self, symbol, interval, mode):
        if mode == "Crypto":
            if symbol.startswith("COINGECKO:"):
                rows, source = _coingecko_ohlc(symbol.split(":", 1)[1], interval)
            else:
                rows, source = _binance_klines(symbol, interval)
                if not rows and symbol.endswith("USDT"):
                    rows, source = _yahoo_history(symbol[:-4] + "-USD", interval)
        else:
            rows, source = _yahoo_history(symbol, interval)
        self.after(0, lambda: self._draw_chart(rows, source, symbol))

    def _draw_chart(self, rows, source, symbol):
        self.data = rows
        old_volume = getattr(self, "_volume_ax", None)
        if old_volume is not None:
            try:
                old_volume.remove()
            except Exception:
                pass
            self._volume_ax = None
        self.ax.clear()
        self.ax.set_facecolor(self.colors["panel3"])
        self.ax.grid(True, alpha=0.10, linewidth=0.7)
        if not rows:
            self.ax.text(0.5, 0.5, "Historical candle feed unavailable",
                         transform=self.ax.transAxes, ha="center", va="center",
                         color=self.colors["muted"], fontsize=12)
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.canvas.draw_idle()
            self.status_var.set(f"{symbol} • no historical feed")
            return

        xs = [date2num(r["time"].replace(tzinfo=None)) for r in rows]
        width = max((xs[-1] - xs[0]) / max(len(xs), 1) * 0.72, 0.00015)
        for x, row in zip(xs, rows):
            color = self.colors["accent"] if row["close"] >= row["open"] else self.colors["danger"]
            self.ax.vlines(x, row["low"], row["high"], color=color, linewidth=0.8)
            body_low = min(row["open"], row["close"])
            body_h = max(abs(row["close"] - row["open"]), 1e-12)
            self.ax.add_patch(Rectangle((x - width/2, body_low), width, body_h,
                                        facecolor=color, edgecolor=color, linewidth=0.5))

        volumes = [row.get("volume", 0.0) or 0.0 for row in rows]
        if any(v > 0 for v in volumes):
            self._volume_ax = self.ax.twinx()
            self._volume_ax.set_zorder(self.ax.get_zorder() - 1)
            self._volume_ax.patch.set_alpha(0)
            max_v = max(volumes) or 1.0
            scaled = [v / max_v for v in volumes]
            self._volume_ax.fill_between(xs, 0, scaled, color=self.colors["blue"], alpha=0.13, step="mid")
            self._volume_ax.set_ylim(0, 1)
            self._volume_ax.set_yticks([])
            for spine in self._volume_ax.spines.values():
                spine.set_visible(False)
        
        self.ax.xaxis.set_major_locator(AutoDateLocator())
        self.ax.xaxis.set_major_formatter(ConciseDateFormatter(self.ax.xaxis.get_major_locator()))
        self.ax.tick_params(axis="both", colors=self.colors["muted"], labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_color(self.colors["line"])
        self.ax.set_ylabel("Price", color=self.colors["muted"], fontsize=8)
        self.ax.set_title(f"{self.symbol_name}  •  {self.interval_var.get()}  •  {source}",
                          loc="left", color=self.colors["text"], fontsize=10, pad=10)
        last = rows[-1]["close"]
        self.ax.axhline(last, color=self.colors["gold"], linewidth=0.8, alpha=0.55, linestyle="--")
        self.meta_label.config(text=f"{source} • {len(rows)} candles • {datetime.now().strftime('%H:%M:%S')}")
        self.status_var.set(f"{source} • online")
        self.canvas.draw_idle()

    def _wheel_zoom(self, event):
        if event.inaxes != self.ax or event.xdata is None:
            return
        left, right = self.ax.get_xlim()
        center = event.xdata
        scale = 0.82 if event.button == "up" else 1.22
        new_left = center - (center - left) * scale
        new_right = center + (right - center) * scale
        self.ax.set_xlim(new_left, new_right)
        self.canvas.draw_idle()

    def _draw_tool(self, mode):
        if mode == "clear":
            for artist in self.draw_artists:
                try:
                    artist.remove()
                except Exception:
                    pass
            self.draw_artists.clear()
            self.draw_mode = "cursor"
            self.canvas.draw_idle()
            return
        self.draw_mode = mode
        self.draw_first = None
        self.status_var.set({
            "cursor": "Cursor mode",
            "hline": "Horizontal line: click price",
            "trend": "Trend line: click two points",
            "rect": "Rectangle: click two corners",
        }.get(mode, mode))

    def _chart_click(self, event):
        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            return
        if self.draw_mode == "hline":
            artist = self.ax.axhline(event.ydata, color=self.colors["gold"], linewidth=1.0, alpha=0.9)
            self.draw_artists.append(artist)
            self.draw_mode = "cursor"
            self.canvas.draw_idle()
        elif self.draw_mode == "trend":
            if self.draw_first is None:
                self.draw_first = (event.xdata, event.ydata)
            else:
                x1, y1 = self.draw_first
                line = Line2D([x1, event.xdata], [y1, event.ydata],
                              color=self.colors["cyan"], linewidth=1.1)
                self.ax.add_line(line)
                self.draw_artists.append(line)
                self.draw_first = None
                self.draw_mode = "cursor"
                self.canvas.draw_idle()
        elif self.draw_mode == "rect":
            if self.draw_first is None:
                self.draw_first = (event.xdata, event.ydata)
            else:
                x1, y1 = self.draw_first
                x2, y2 = event.xdata, event.ydata
                rect = Rectangle((min(x1, x2), min(y1, y2)), abs(x2-x1), abs(y2-y1),
                                 fill=False, edgecolor=self.colors["violet"], linewidth=1.1)
                self.ax.add_patch(rect)
                self.draw_artists.append(rect)
                self.draw_first = None
                self.draw_mode = "cursor"
                self.canvas.draw_idle()

    def _crosshair(self, event):
        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            return
        if self.cross_v is not None:
            try:
                self.cross_v.remove()
            except Exception:
                pass
        if self.cross_h is not None:
            try:
                self.cross_h.remove()
            except Exception:
                pass
        self.cross_v = self.ax.axvline(event.xdata, color=self.colors["muted"], linewidth=0.5, alpha=0.35)
        self.cross_h = self.ax.axhline(event.ydata, color=self.colors["muted"], linewidth=0.5, alpha=0.35)
        self.canvas.draw_idle()
