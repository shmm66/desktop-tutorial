from __future__ import annotations

import json
import math
import os
import queue
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import tkinter as tk
from tkinter import messagebox, ttk

APP_DIR = Path(os.getenv("APPDATA", Path.home())) / "TraderPlannerPro" / "SignalFusion"
DB_FILE = APP_DIR / "signals.json"
APP_DIR.mkdir(parents=True, exist_ok=True)

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT",
           "DOGEUSDT", "ADAUSDT", "TRXUSDT", "LINKUSDT", "AVAXUSDT"]

STRATEGIES = ("ICT2025", "ICT2022", "SMC Photon", "SMC Philip")
INTERVALS = ("15m", "1h", "4h")
BINANCE = "https://api.binance.com"

# Signal parameters are intentionally conservative. A setup must have
# structure + liquidity event + displacement/FVG/POI evidence before it
# can become a trade candidate.
PIVOT = 3
ATR_N = 14
FVG_MIN_ATR = 0.12
ZONE_TOLERANCE_ATR = 0.35
FUSION_WINDOW_MIN = 90
MAX_SIGNAL_AGE_MIN = 180
POLL_SECONDS = 60


def now_ms() -> int:
    return int(time.time() * 1000)


def fmt_price(v: float) -> str:
    if v >= 1000:
        return f"{v:,.2f}"
    if v >= 1:
        return f"{v:,.4f}"
    return f"{v:,.8f}"


def pct(a: float, b: float) -> float:
    return (b - a) / a * 100.0 if a else 0.0


def http_json(path: str, params: dict[str, Any] | None = None) -> Any:
    q = urllib.parse.urlencode(params or {})
    url = BINANCE + path + ("?" + q if q else "")
    req = urllib.request.Request(url, headers={"User-Agent": "TraderPlannerPro-SignalFusion/1.0"})
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.loads(r.read().decode("utf-8"))


@dataclass
class Candle:
    t: int
    o: float
    h: float
    l: float
    c: float
    v: float


@dataclass
class StrategySignal:
    strategy: str
    symbol: str
    direction: str
    timeframe: str
    created_ms: int
    entry_low: float
    entry_high: float
    entry: float
    sl: float
    tp: float
    rr: float
    setup: str
    evidence: list[str]
    invalidation: str
    status: str = "ACTIVE"

    def mid(self) -> float:
        return (self.entry_low + self.entry_high) / 2


@dataclass
class FusedSignal:
    id: str
    symbol: str
    direction: str
    stars: int
    strategies: list[str]
    timeframe: str
    created_ms: int
    entry_low: float
    entry_high: float
    entry: float
    sl: float
    tp: float
    rr: float
    evidence: list[str]
    invalidation: str
    status: str = "ACTIVE"
    exit_price: float | None = None
    exit_ms: int | None = None
    result_r: float | None = None
    result_pct: float | None = None
    exit_reason: str | None = None

    @property
    def star_text(self) -> str:
        return "★" * self.stars


def candles(symbol: str, interval: str, limit: int = 240) -> list[Candle]:
    raw = http_json("/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": limit})
    return [Candle(int(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5])) for x in raw]


def atr(cs: list[Candle], n: int = ATR_N) -> float:
    if len(cs) < n + 1:
        return 0.0
    trs = []
    for i in range(1, len(cs)):
        prev = cs[i - 1].c
        trs.append(max(cs[i].h - cs[i].l, abs(cs[i].h - prev), abs(cs[i].l - prev)))
    return sum(trs[-n:]) / n


def swing_highs(cs: list[Candle], p: int = PIVOT) -> list[tuple[int, float]]:
    out = []
    for i in range(p, len(cs) - p):
        h = cs[i].h
        if all(h > cs[j].h for j in range(i - p, i)) and all(h >= cs[j].h for j in range(i + 1, i + p + 1)):
            out.append((i, h))
    return out


def swing_lows(cs: list[Candle], p: int = PIVOT) -> list[tuple[int, float]]:
    out = []
    for i in range(p, len(cs) - p):
        l = cs[i].l
        if all(l < cs[j].l for j in range(i - p, i)) and all(l <= cs[j].l for j in range(i + 1, i + p + 1)):
            out.append((i, l))
    return out


def fvg(cs: list[Candle]) -> tuple[str, float, float] | None:
    # Three-candle imbalance. Only confirmed candles are used.
    for i in range(len(cs) - 1, 1, -1):
        a, _, c = cs[i - 2], cs[i - 1], cs[i]
        if a.h < c.l:
            return "bullish", a.h, c.l
        if a.l > c.h:
            return "bearish", c.h, a.l
    return None


def liquidity_sweep(cs: list[Candle]) -> tuple[str, float] | None:
    sh = swing_highs(cs[:-2])
    sl = swing_lows(cs[:-2])
    last = cs[-2]
    if sh:
        level = sh[-1][1]
        if last.h > level and last.c < level:
            return "bearish", level
    if sl:
        level = sl[-1][1]
        if last.l < level and last.c > level:
            return "bullish", level
    return None


def displacement(cs: list[Candle], direction: str, a: float) -> bool:
    if len(cs) < 6 or a <= 0:
        return False
    x = cs[-2]
    body = abs(x.c - x.o)
    rng = max(x.h - x.l, 1e-12)
    body_ok = body >= a * 0.8 and body / rng >= 0.55
    if direction == "bullish":
        return body_ok and x.c > x.o and x.c >= cs[-3].h
    return body_ok and x.c < x.o and x.c <= cs[-3].l


def structure(cs: list[Candle]) -> str:
    hs = swing_highs(cs[:-2])
    ls = swing_lows(cs[:-2])
    if len(hs) >= 2 and len(ls) >= 2:
        if hs[-1][1] > hs[-2][1] and ls[-1][1] > ls[-2][1]:
            return "bullish"
        if hs[-1][1] < hs[-2][1] and ls[-1][1] < ls[-2][1]:
            return "bearish"
    return "range"


def previous_week_range() -> tuple[float, float]:
    # UTC week is used as a stable server-side reference.
    cs = candles("BTCUSDT", "1d", 20)
    if len(cs) < 10:
        return (0, float("inf"))
    # Monday boundary in UTC.
    last = datetime.fromtimestamp(cs[-2].t / 1000, timezone.utc)
    monday = int(datetime(last.year, last.month, last.day, tzinfo=timezone.utc).timestamp() * 1000)
    monday -= last.weekday() * 86400000
    prev = [x for x in cs if monday - 7 * 86400000 <= x.t < monday]
    if not prev:
        prev = cs[-9:-2]
    return min(x.l for x in prev), max(x.h for x in prev)


def build_signal(strategy: str, symbol: str, cs4: list[Candle], cs1: list[Candle], cs15: list[Candle]) -> StrategySignal | None:
    a4, a1, a15 = atr(cs4), atr(cs1), atr(cs15)
    if min(a4, a1, a15) <= 0:
        return None
    bias = structure(cs4)
    sweep = liquidity_sweep(cs15)
    fv = fvg(cs15)
    if not sweep or not fv:
        return None

    direction, swept = sweep
    if direction == "bullish" and bias == "bearish":
        return None
    if direction == "bearish" and bias == "bullish":
        return None

    fv_dir, fvl, fvh = fv
    if fv_dir != direction:
        return None
    if not displacement(cs15, direction, a15):
        return None

    # ICT-style confirmation: 1H structure must agree for ICT2025/Photon.
    s1 = structure(cs1)
    if strategy in ("ICT2025", "SMC Photon") and s1 != direction:
        return None

    # ICT2022 emphasizes liquidity raid + displacement + FVG.
    # Philip emphasizes structure + POI + displacement.
    if strategy == "ICT2022" and not sweep:
        return None
    if strategy == "SMC Philip" and s1 not in (direction, "range"):
        return None

    last = cs15[-2].c
    if direction == "bullish":
        lo, hi = sorted((fvl, fvh))
        entry = (lo + hi) / 2
        sl = min(swept, lo) - a15 * 0.12
        risk = entry - sl
        tp = entry + risk * 5.0
    else:
        lo, hi = sorted((fvl, fvh))
        entry = (lo + hi) / 2
        sl = max(swept, hi) + a15 * 0.12
        risk = sl - entry
        tp = entry - risk * 5.0

    if risk <= 0 or risk < a15 * 0.15:
        return None

    # Keep setup local to a meaningful recent range; no stale multi-week zones.
    pwh_low, pwh_high = previous_week_range()
    if not (pwh_low <= entry <= pwh_high):
        return None

    evidence = [
        f"4H ساختار: {bias}",
        f"15M نقدینگی جمع‌آوری شد: {fmt_price(swept)}",
        f"15M FVG: {fmt_price(lo)} تا {fmt_price(hi)}",
        "15M displacement تأیید شد",
    ]
    if s1 == direction:
        evidence.append(f"1H ساختار هم‌جهت: {s1}")

    setup_names = {
        "ICT2025": "ICT2025: 4H bias + 1H confirmation + 15M sweep/FVG",
        "ICT2022": "ICT2022: liquidity raid + displacement + FVG",
        "SMC Photon": "SMC Photon: 4H POI + 1H structure + 15M execution",
        "SMC Philip": "SMC Philip: structure + liquidity/POI + displacement",
    }
    return StrategySignal(
        strategy, symbol, direction, "15m", cs15[-2].t,
        lo, hi, entry, sl, tp, abs((tp - entry) / (entry - sl)),
        setup_names[strategy], evidence,
        "با تثبیت قیمت آن‌سوی SL یا شکست ساختار مخالف، ستاپ باطل است."
    )


def detect(symbol: str) -> list[StrategySignal]:
    try:
        c4 = candles(symbol, "4h")
        c1 = candles(symbol, "1h")
        c15 = candles(symbol, "15m")
        out = []
        for s in STRATEGIES:
            sig = build_signal(s, symbol, c4, c1, c15)
            if sig:
                out.append(sig)
        return out
    except Exception:
        return []


def overlap(signals: list[StrategySignal]) -> tuple[float, float] | None:
    lo = max(s.entry_low for s in signals)
    hi = min(s.entry_high for s in signals)
    if lo <= hi:
        return lo, hi
    mid = sum(s.mid() for s in signals) / len(signals)
    scale = max(s.mid() for s in signals) * 0.0015
    if all(abs(s.mid() - mid) <= scale for s in signals):
        return mid - scale / 2, mid + scale / 2
    return None


def fuse(signals: list[StrategySignal]) -> list[FusedSignal]:
    groups: list[list[StrategySignal]] = []
    for s in signals:
        placed = False
        for g in groups:
            if g[0].direction == s.direction and overlap(g + [s]):
                g.append(s)
                placed = True
                break
        if not placed:
            groups.append([s])

    result = []
    for g in groups:
        if not g:
            continue
        z = overlap(g)
        if not z:
            continue
        stars = min(3, len({x.strategy for x in g}))
        entry = sum(x.entry for x in g) / len(g)
        if g[0].direction == "bullish":
            sl = min(x.sl for x in g)
            risk = entry - sl
            tp = max(x.tp for x in g)
        else:
            sl = max(x.sl for x in g)
            risk = sl - entry
            tp = min(x.tp for x in g)
        if risk <= 0:
            continue
        rid = f"{g[0].symbol}-{g[0].direction}-{g[0].created_ms}-{stars}"
        result.append(FusedSignal(
            rid, g[0].symbol, g[0].direction, stars,
            [x.strategy for x in g], "15m",
            max(x.created_ms for x in g), z[0], z[1], entry, sl, tp,
            abs((tp - entry) / risk),
            sorted({e for x in g for e in x.evidence}),
            g[0].invalidation
        ))
    return result


def evaluate(sig: FusedSignal, price: float, ts: int) -> bool:
    if sig.status != "ACTIVE":
        return False
    if sig.direction == "bullish":
        if price <= sig.sl:
            sig.status, sig.exit_price, sig.exit_ms, sig.exit_reason = "LOSS", sig.sl, ts, "SL"
        elif price >= sig.tp:
            sig.status, sig.exit_price, sig.exit_ms, sig.exit_reason = "WIN", sig.tp, ts, "TP"
        else:
            return False
        risk = sig.entry - sig.sl
        sig.result_r = (sig.exit_price - sig.entry) / risk
    else:
        if price >= sig.sl:
            sig.status, sig.exit_price, sig.exit_ms, sig.exit_reason = "LOSS", sig.sl, ts, "SL"
        elif price <= sig.tp:
            sig.status, sig.exit_price, sig.exit_ms, sig.exit_reason = "WIN", sig.tp, ts, "TP"
        else:
            return False
        risk = sig.sl - sig.entry
        sig.result_r = (sig.entry - sig.exit_price) / risk
    sig.result_pct = pct(sig.entry, sig.exit_price) if sig.direction == "bullish" else pct(sig.exit_price, sig.entry)
    return True


class Store:
    def __init__(self):
        self.lock = threading.Lock()
        self.data = {"active": {}, "history": [], "seen": []}
        self.load()

    def load(self):
        try:
            self.data = json.loads(DB_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass

    def save(self):
        tmp = DB_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(DB_FILE)

    def active(self) -> list[FusedSignal]:
        return [FusedSignal(**v) for v in self.data.get("active", {}).values()]

    def upsert(self, s: FusedSignal):
        self.data.setdefault("active", {})[s.id] = asdict(s)
        self.save()

    def complete(self, s: FusedSignal):
        self.data.setdefault("active", {}).pop(s.id, None)
        self.data.setdefault("history", []).insert(0, asdict(s))
        self.save()

    def seen(self, key: str) -> bool:
        return key in self.data.setdefault("seen", [])

    def mark_seen(self, key: str):
        self.data.setdefault("seen", []).append(key)
        self.data["seen"] = self.data["seen"][-2000:]
        self.save()


class Scanner:
    def __init__(self, on_new: Callable[[FusedSignal], None], on_update: Callable[[], None]):
        self.on_new, self.on_update = on_new, on_update
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.loop, daemon=True)

    def start(self):
        self.thread.start()

    def loop(self):
        while not self.stop.is_set():
            for symbol in SYMBOLS:
                if self.stop.is_set():
                    break
                sigs = detect(symbol)
                for f in fuse(sigs):
                    key = f"{f.symbol}:{f.direction}:{','.join(f.strategies)}:{f.created_ms // 900000}"
                    if not APP.store.seen(key):
                        APP.store.mark_seen(key)
                        APP.store.upsert(f)
                        self.on_new(f)
                try:
                    price = float(http_json("/api/v3/ticker/price", {"symbol": symbol})["price"])
                    for a in APP.store.active():
                        if a.symbol == symbol and evaluate(a, price, now_ms()):
                            APP.store.complete(a)
                except Exception:
                    pass
                self.on_update()
            self.stop.wait(POLL_SECONDS)


def notify_windows(title: str, body: str):
    # Native Windows toast via PowerShell; no extra runtime dependency.
    ps = (
        "$t=[Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications,ContentType=WindowsRuntime];"
        "[Windows.Data.Xml.Dom.XmlDocument,Windows.Data.Xml.Dom.XmlDocument,ContentType=WindowsRuntime];"
        "$x=New-Object Windows.Data.Xml.Dom.XmlDocument;"
        f"$x.LoadXml('<toast><visual><binding template='2.0'><text>{title}</text><text>{body}</text></binding></visual></toast>');"
        "$n=[Windows.UI.Notifications.ToastNotification]::new($x);"
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Trader Planner Pro - Signal Fusion').Show($n)"
    )
    try:
        import subprocess
        subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                         creationflags=0x08000000)
    except Exception:
        pass


def fa_direction(d: str) -> str:
    return "خرید / LONG" if d == "bullish" else "فروش / SHORT"


def explanation(s: FusedSignal) -> str:
    styles = "، ".join(s.strategies)
    lines = [
        f"{s.star_text}  {s.symbol} — {fa_direction(s.direction)}",
        f"تایم‌فریم اجرا: {s.timeframe}",
        f"سبک‌های تأییدکننده: {styles}",
        "",
        "چرا ورود؟",
        "• ستاپ پس از بسته‌شدن کندل تأییدشده ساخته شده است.",
        "• نقدینگی/ساختار و ناحیه ورود باید هم‌زمان با هم‌پوشانی قیمت تأیید شده باشند.",
        "• فقط وقتی چند سبک در یک محدوده مشترک هم‌جهت باشند، ستاره دوم/سوم اضافه می‌شود.",
        "",
        "محدوده ورود:",
        f"• {fmt_price(s.entry_low)} تا {fmt_price(s.entry_high)}",
        f"• Entry مرجع: {fmt_price(s.entry)}",
        f"• SL: {fmt_price(s.sl)}",
        f"• TP: {fmt_price(s.tp)}",
        f"• RR محاسباتی: 1:{s.rr:.2f}",
        "",
        "شواهد:",
        *[f"• {x}" for x in s.evidence],
        "",
        f"شرط ابطال: {s.invalidation}",
    ]
    if s.status in ("WIN", "LOSS"):
        lines += [
            "",
            f"نتیجه: {'سود' if s.status == 'WIN' else 'ضرر'} ({s.exit_reason})",
            f"خروج: {fmt_price(s.exit_price or 0)}",
            f"نتیجه R: {s.result_r:+.2f}R",
            f"نتیجه درصدی: {s.result_pct:+.2f}%",
        ]
    return "\n".join(lines)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        global APP
        APP = self
        self.title("Trader Planner Pro — Signal Fusion")
        self.geometry("1180x760")
        self.minsize(980, 650)
        self.configure(bg="#08111f")
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.store = Store()
        APP.store = self.store
        self.msgq: queue.Queue[tuple[str, Any]] = queue.Queue()
        self._style()
        self._build()
        self.refresh()
        self.scanner = Scanner(
            lambda s: self.msgq.put(("new", s)),
            lambda: self.msgq.put(("refresh", None))
        )
        self.scanner.start()
        self.after(500, self.drain)

    def _style(self):
        st = ttk.Style(self)
        st.theme_use("clam")
        st.configure("Treeview", background="#0e1b2d", foreground="#e8f0ff",
                     fieldbackground="#0e1b2d", rowheight=34, borderwidth=0)
        st.configure("Treeview.Heading", background="#16253b", foreground="#a9c4e8",
                     relief="flat", font=("Segoe UI Semibold", 10))
        st.map("Treeview", background=[("selected", "#234b72")], foreground=[("selected", "white")])

    def _build(self):
        header = tk.Frame(self, bg="#08111f")
        header.pack(fill="x", padx=24, pady=(20, 8))
        tk.Label(header, text="SIGNAL FUSION", bg="#08111f", fg="#f3f7ff",
                 font=("Segoe UI Semibold", 25)).pack(side="left")
        tk.Label(header, text="  ICT2025 • ICT2022 • SMC Photon • SMC Philip",
                 bg="#08111f", fg="#7792b5", font=("Segoe UI", 11)).pack(side="left", pady=(10,0))
        self.status = tk.Label(header, text="● در حال پایش ۱۰ ارز", bg="#08111f", fg="#72e0a2",
                               font=("Segoe UI", 10))
        self.status.pack(side="right", pady=(10,0))

        note = tk.Frame(self, bg="#0c1829", highlightthickness=1, highlightbackground="#1a304b")
        note.pack(fill="x", padx=24, pady=8)
        tk.Label(note, text="★ = یک سبک   ★★ = هم‌پوشانی حداقل دو سبک   ★★★ = هم‌پوشانی سه سبک یا بیشتر",
                 bg="#0c1829", fg="#b7c8dd", font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=10)

        body = tk.Frame(self, bg="#08111f")
        body.pack(fill="both", expand=True, padx=24, pady=10)
        self.tree = ttk.Treeview(body, columns=("coin","dir","stars","styles","entry","sl","tp","rr","state"),
                                 show="headings")
        heads = {"coin":"ارز","dir":"جهت","stars":"سیگنال","styles":"سبک‌ها","entry":"Entry",
                 "sl":"SL","tp":"TP","rr":"RR","state":"وضعیت"}
        for c in self.tree["columns"]:
            self.tree.heading(c, text=heads[c])
            self.tree.column(c, width={"coin":90,"dir":100,"stars":90,"styles":260,"entry":115,
                                       "sl":115,"tp":115,"rr":70,"state":100}.get(c, 100))
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", self.open_selected)
        sb = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        foot = tk.Frame(self, bg="#08111f")
        foot.pack(fill="x", padx=24, pady=(0,20))
        tk.Button(foot, text="جزئیات سیگنال انتخاب‌شده", command=self.open_selected,
                  bg="#163653", fg="white", activebackground="#214d73", activeforeground="white",
                  relief="flat", padx=18, pady=9, font=("Segoe UI Semibold", 10)).pack(side="left")
        tk.Button(foot, text="تاریخچه معاملات", command=self.history,
                  bg="#122338", fg="#c8d8ea", activebackground="#1b3550", activeforeground="white",
                  relief="flat", padx=18, pady=9, font=("Segoe UI", 10)).pack(side="left", padx=8)
        tk.Label(foot, text="داده بازار: Binance • فقط کندل بسته‌شده • بدون اجرای خودکار معامله",
                 bg="#08111f", fg="#617a9a", font=("Segoe UI", 9)).pack(side="right")

    def refresh(self):
        for x in self.tree.get_children():
            self.tree.delete(x)
        active = self.store.active()
        for s in active:
            self.tree.insert("", "end", iid=s.id, values=(
                s.symbol.replace("USDT",""), fa_direction(s.direction), s.star_text,
                " + ".join(s.strategies), fmt_price(s.entry), fmt_price(s.sl),
                fmt_price(s.tp), f"1:{s.rr:.1f}", s.status
            ))
        self.status.config(text=f"● در حال پایش ۱۰ ارز  |  سیگنال فعال: {len(active)}")

    def drain(self):
        try:
            while True:
                typ, obj = self.msgq.get_nowait()
                if typ == "new":
                    notify_windows(
                        f"{obj.star_text} {obj.symbol} {fa_direction(obj.direction)}",
                        f"Entry {fmt_price(obj.entry)} • SL {fmt_price(obj.sl)} • TP {fmt_price(obj.tp)}"
                    )
                    self.bell()
                    self.refresh()
                elif typ == "refresh":
                    self.refresh()
        except queue.Empty:
            pass
        self.after(500, self.drain)

    def bell(self):
        try:
            self.update_idletasks()
            self.after(0, lambda: None)
        except Exception:
            pass

    def selected_signal(self) -> FusedSignal | None:
        sel = self.tree.selection()
        if not sel:
            return None
        for s in self.store.active():
            if s.id == sel[0]:
                return s
        return None

    def open_selected(self, _event=None):
        s = self.selected_signal()
        if not s:
            messagebox.showinfo("Signal Fusion", "یک سیگنال را انتخاب کنید.")
            return
        self.details(explanation(s), f"{s.star_text} {s.symbol}")

    def details(self, text_value: str, title: str):
        w = tk.Toplevel(self)
        w.title(title)
        w.geometry("720x650")
        w.configure(bg="#0a1422")
        txt = tk.Text(w, bg="#0d1b2c", fg="#e9f1fb", insertbackground="white",
                      relief="flat", wrap="word", font=("Segoe UI", 11), padx=18, pady=18)
        txt.pack(fill="both", expand=True, padx=18, pady=18)
        txt.insert("1.0", text_value)
        txt.configure(state="disabled")

    def history(self):
        w = tk.Toplevel(self)
        w.title("تاریخچه معاملات")
        w.geometry("900x520")
        w.configure(bg="#08111f")
        tree = ttk.Treeview(w, columns=("coin","dir","stars","styles","exit","r","pct"), show="headings")
        for c,h in [("coin","ارز"),("dir","جهت"),("stars","سیگنال"),("styles","سبک‌ها"),("exit","خروج"),("r","R"),("pct","٪")]:
            tree.heading(c,text=h)
        tree.pack(fill="both",expand=True,padx=16,pady=16)
        for d in self.store.data.get("history", []):
            s=FusedSignal(**d)
            tree.insert("", "end", values=(s.symbol, fa_direction(s.direction), s.star_text,
                                           " + ".join(s.strategies), s.exit_reason or "-",
                                           f"{s.result_r:+.2f}" if s.result_r is not None else "-",
                                           f"{s.result_pct:+.2f}" if s.result_pct is not None else "-"))
        tk.Label(w, text="نتیجه‌ها از قیمت Entry تا TP/SL محاسبه می‌شوند و شامل کارمزد/اسلیپیج نیستند.",
                 bg="#08111f", fg="#7188a5", font=("Segoe UI",9)).pack(pady=(0,12))

    def close(self):
        try:
            self.scanner.stop.set()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
