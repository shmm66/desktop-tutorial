from __future__ import annotations

import tkinter as tk


def _line(c, pts, fill, width=2, dash=None):
    c.create_line(*pts, fill=fill, width=width, smooth=True, dash=dash or ())


def _label(c, x, y, text, fill, anchor="center", size=10, bold=True):
    c.create_text(x, y, text=text, fill=fill, anchor=anchor,
                  font=("Segoe UI", size, "bold" if bold else "normal"))


def _zone(c, x1, y1, x2, y2, fill, outline, text, text_fill):
    c.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=2)
    _label(c, (x1 + x2) / 2, (y1 + y2) / 2, text, text_fill, size=9)


def _candles(c, candles, x0=70, step=56, scale=1.0, base=260):
    for i, (o, h, l, cl) in enumerate(candles):
        x = x0 + i * step

        def y(v):
            return base - v * scale

        fill = "#39E6B1" if cl >= o else "#FF6F7D"
        c.create_line(x, y(h), x, y(l), fill=fill, width=2)
        top, bot = sorted((y(o), y(cl)))
        c.create_rectangle(x - 10, top, x + 10, max(bot, top + 2), fill=fill, outline=fill)


def _arrow(c, x1, y1, x2, y2, fill, text=""):
    c.create_line(x1, y1, x2, y2, fill=fill, width=3, arrow=tk.LAST)
    if text:
        _label(c, (x1 + x2) / 2, (y1 + y2) / 2 - 12, text, fill, size=9)


def _grid(c, W, bg, grid, text, family, model):
    c.configure(width=W, height=390)
    for y in range(70, 350, 45):
        c.create_line(20, y, W - 20, y, fill=grid, width=1)
    _label(c, 24, 28, family.upper() + "  •  " + model, text, anchor="w", size=13)
    _label(c, W - 24, 28, "SETUP MAP • EDUCATIONAL", text, anchor="e", size=8)


def _ict_2022(c, palette):
    text, muted = palette["text"], palette["muted"]
    accent, danger, gold, blue = palette["accent"], palette["danger"], palette["gold"], palette.get("blue", "#63A7FF")
    candles = [
        (60, 105, 42, 96), (96, 138, 82, 125), (124, 145, 102, 112),
        (112, 128, 74, 82), (84, 98, 52, 64), (65, 102, 58, 98),
        (98, 140, 94, 132), (132, 164, 120, 156), (156, 182, 144, 176),
        (176, 196, 168, 190), (190, 210, 176, 204),
    ]
    _candles(c, candles, x0=90, step=67, scale=1.15, base=310)
    c.create_line(60, 195, 850, 195, fill=gold, dash=(7, 5), width=2)
    _label(c, 70, 180, "LIQUIDITY POOL", gold, anchor="w", size=9)
    c.create_line(90, 315, 850, 315, fill=danger, dash=(6, 5), width=2)
    _label(c, 98, 334, "SELL-SIDE LIQUIDITY", danger, anchor="w", size=8)
    _label(c, 360, 325, "SWEEP", danger, size=9)
    c.create_oval(357, 302, 383, 328, outline=danger, width=3)
    _arrow(c, 410, 285, 540, 150, accent, "MSS / DISPLACEMENT")
    _zone(c, 520, 135, 650, 183, "#153C35", accent, "FVG", accent)
    _arrow(c, 705, 205, 600, 158, blue, "RETURN")
    _label(c, 890, 104, "TARGET", gold, size=9)
    c.create_line(790, 115, 1070, 115, fill=gold, width=3)
    _label(c, 420, 365, "Liquidity → Sweep → MSS/Displacement → FVG → Return", text, size=10)


def _ict_silver_bullet(c, palette):
    text, muted = palette["text"], palette["muted"]
    accent, danger, violet, blue = palette["accent"], palette["danger"], palette.get("violet", "#9B8CFF"), palette.get("blue", "#63A7FF")
    c.create_rectangle(480, 60, 720, 350, outline=violet, width=3)
    _label(c, 600, 78, "DEFINED TIME WINDOW", violet, size=11)
    candles = [(45, 84, 28, 76), (76, 102, 60, 95), (95, 120, 84, 90),
               (90, 112, 52, 64), (64, 100, 58, 98), (98, 132, 90, 124),
               (124, 150, 116, 140), (140, 160, 128, 150)]
    _candles(c, candles, x0=140, step=105, scale=1.3, base=310)
    _zone(c, 570, 155, 710, 205, "#16382F", accent, "FVG", accent)
    _arrow(c, 835, 235, 675, 180, blue, "RETURN")
    _label(c, 60, 365, "Time window is a constraint; displacement + FVG define the entry model.", text, anchor="w", size=9)


def _ict_unicorn(c, palette):
    text = palette["text"]
    accent, violet, gold, blue = palette["accent"], palette.get("violet", "#9B8CFF"), palette["gold"], palette.get("blue", "#63A7FF")
    candles = [(60, 110, 42, 98), (98, 146, 80, 134), (134, 160, 112, 120),
               (120, 135, 72, 80), (80, 125, 75, 118), (118, 150, 108, 142),
               (142, 180, 130, 172)]
    _candles(c, candles, x0=180, step=110, scale=1.25, base=315)
    _zone(c, 505, 150, 840, 225, "#172B45", violet, "BREAKER", violet)
    _zone(c, 620, 132, 880, 205, "#16382F", accent, "FVG", accent)
    c.create_rectangle(635, 145, 815, 205, outline=gold, width=4)
    _label(c, 725, 125, "UNICORN OVERLAP", gold, size=11)
    _arrow(c, 915, 230, 800, 180, blue, "RETEST")
    _label(c, 50, 365, "Breaker + FVG overlap is the named Unicorn concept shown here.", text, anchor="w", size=9)


def _ict_ote(c, palette):
    text, gold, blue, accent, danger = palette["text"], palette["gold"], palette.get("blue", "#63A7FF"), palette["accent"], palette["danger"]
    c.create_rectangle(130, 70, 1080, 335, outline=palette["line"], width=2)
    c.create_line(130, 202, 1080, 202, fill=gold, width=2, dash=(8, 5))
    _label(c, 605, 188, "EQUILIBRIUM 50%", gold, size=9)
    _zone(c, 260, 215, 600, 310, "#173148", blue, "DISCOUNT / OTE 62–79%", blue)
    _zone(c, 650, 96, 990, 190, "#3A2730", danger, "PREMIUM / OTE 62–79%", danger)
    _arrow(c, 250, 300, 560, 255, accent, "LONG CONTEXT")
    _arrow(c, 970, 125, 700, 150, danger, "SHORT CONTEXT")
    _label(c, 600, 360, "OTE is a location framework; liquidity + structure + trigger are still separate.", text, size=9)


def _ict_amd(c, palette):
    text = palette["text"]
    accent, danger, gold, blue = palette["accent"], palette["danger"], palette["gold"], palette.get("blue", "#63A7FF")
    bands = [("ACCUMULATION", 50, 390, accent), ("MANIPULATION", 390, 760, danger), ("DISTRIBUTION", 760, 1120, gold)]
    for label, x1, x2, color in bands:
        c.create_rectangle(x1, 78, x2, 315, outline=color, width=3)
        _label(c, (x1 + x2) / 2, 92, label, color, size=10)
    pts = [(70, 250), (150, 235), (230, 248), (310, 240), (385, 230), (430, 280),
           (490, 165), (550, 250), (625, 275), (690, 220), (760, 250), (840, 190),
           (920, 150), (1010, 118), (1080, 88)]
    _line(c, [v for p in pts for v in p], blue, 4)
    _label(c, 575, 300, "LIQUIDITY RAID / FALSE MOVE", danger, size=9)
    _label(c, 600, 365, "A framework for sequencing the session/day, not a candlestick pattern.", text, size=9)


def _ict_judas(c, palette):
    text = palette["text"]
    accent, danger, violet, gold, blue = palette["accent"], palette["danger"], palette.get("violet", "#9B8CFF"), palette["gold"], palette.get("blue", "#63A7FF")
    c.create_rectangle(355, 62, 690, 340, outline=violet, width=3)
    _label(c, 522, 78, "SESSION WINDOW", violet, size=10)
    candles = [(55, 92, 42, 82), (82, 116, 72, 104), (104, 126, 94, 99),
               (99, 120, 55, 64), (64, 105, 60, 96), (96, 138, 88, 132),
               (132, 165, 126, 158), (158, 186, 148, 175)]
    _candles(c, candles, x0=120, step=105, scale=1.2, base=315)
    c.create_oval(425, 276, 451, 302, outline=danger, width=3)
    _label(c, 438, 318, "JUDAS RAID", danger, size=9)
    _arrow(c, 505, 275, 615, 155, accent, "REVERSAL")
    _zone(c, 615, 150, 745, 198, "#16382F", accent, "FVG / OB", accent)
    _label(c, 830, 110, "OPPOSING LIQUIDITY", gold, size=9)
    c.create_line(750, 120, 1080, 120, fill=gold, width=3)
    _label(c, 600, 365, "Initial move → structural reversal → displacement → entry area → opposing liquidity.", text, size=9)


def _ict_smt(c, palette):
    text = palette["text"]
    accent, violet, gold = palette["accent"], palette.get("violet", "#9B8CFF"), palette["gold"]
    c.create_line(70, 165, 1080, 165, fill=palette["line"])
    c.create_line(70, 300, 1080, 300, fill=palette["line"])
    _label(c, 80, 76, "INSTRUMENT A", accent, anchor="w", size=10)
    _label(c, 80, 215, "INSTRUMENT B", violet, anchor="w", size=10)
    a = [(100, 220), (190, 185), (280, 205), (370, 155), (460, 180), (550, 115), (640, 145), (730, 82), (820, 100), (920, 55), (1010, 86)]
    b = [(100, 350), (190, 320), (280, 335), (370, 285), (460, 310), (550, 250), (640, 272), (730, 210), (820, 235), (920, 245), (1010, 195)]
    _line(c, [v for p in a for v in p], accent, 4)
    _line(c, [v for p in b for v in p], violet, 4)
    c.create_oval(905, 42, 935, 72, outline=gold, width=4)
    c.create_oval(905, 228, 935, 258, outline=gold, width=4)
    _label(c, 920, 115, "NON-CONFIRMATION", gold, size=10)
    _label(c, 920, 135, "SMT DIVERGENCE", gold, size=11)
    _label(c, 560, 365, "Compare corresponding swings; SMT is context, not a standalone entry trigger.", text, size=9)


def _smc_generic(c, palette, model):
    text = palette["text"]
    accent, danger, gold, blue = palette["accent"], palette["danger"], palette["gold"], palette.get("blue", "#63A7FF")
    pts = [(50, 280), (110, 245), (170, 270), (230, 210), (290, 250), (350, 180), (420, 225),
           (500, 150), (570, 192), (640, 245), (710, 200), (780, 235), (850, 170), (930, 130), (1050, 95)]
    _line(c, [v for p in pts for v in p], blue, 4)
    c.create_line(350, 180, 530, 180, fill=gold, dash=(7, 5), width=2)
    _label(c, 440, 165, "LIQUIDITY / SWING", gold, size=9)
    c.create_oval(630, 232, 655, 257, outline=danger, width=3)
    _label(c, 643, 278, "SWEEP / SHIFT", danger, size=9)
    if "order block" in model.lower():
        _zone(c, 690, 180, 825, 225, "#3B2E16", gold, "ORDER BLOCK", gold)
    elif "breaker" in model.lower():
        _zone(c, 690, 180, 825, 225, "#172B45", palette.get("violet", "#9B8CFF"), "BREAKER", palette.get("violet", "#9B8CFF"))
    else:
        _zone(c, 690, 180, 825, 225, "#16382F", accent, "FVG / ENTRY AREA", accent)
    _arrow(c, 915, 205, 810, 205, blue, "RETEST")
    _label(c, 610, 365, "Broad SMC flow: liquidity + structure + zone + retest + invalidation.", text, size=9)


def draw_setup(parent, family, model, palette):
    c = tk.Canvas(parent, height=390, bg=palette["panel3"], highlightthickness=0)
    c.pack(fill="x", padx=8, pady=8)
    _grid(c, 1180, palette["panel3"], palette["line"], palette["text"], family, model)
    m = str(model).lower()

    if family.lower() == "ict":
        if "2022" in m:
            _ict_2022(c, palette)
        elif "silver bullet" in m:
            _ict_silver_bullet(c, palette)
        elif "unicorn" in m:
            _ict_unicorn(c, palette)
        elif "ote" in m or "premium-discount" in m:
            _ict_ote(c, palette)
        elif "power of three" in m or "amd" in m:
            _ict_amd(c, palette)
        elif "judas" in m:
            _ict_judas(c, palette)
        elif "smt" in m:
            _ict_smt(c, palette)
        else:
            _ict_2022(c, palette)
    else:
        _smc_generic(c, palette, m)
    return c


def draw_candlestick(parent, pattern, palette):
    c = tk.Canvas(parent, height=290, bg=palette["panel3"], highlightthickness=0)
    c.pack(fill="x", padx=8, pady=8)
    text, muted = palette["text"], palette["muted"]
    accent, danger, gold = palette["accent"], palette["danger"], palette["gold"]
    _label(c, 22, 24, str(pattern).upper(), accent, anchor="w", size=12)
    p = str(pattern).lower()

    if "bullish engulfing" in p:
        candles = [(72, 112, 55, 55), (52, 128, 45, 120)]
        _candles(c, candles, x0=280, step=130, scale=1.25, base=250)
        _label(c, 345, 275, "BEARISH CANDLE", danger, size=9)
        _label(c, 475, 275, "BULLISH BODY ENGULFS PRIOR BODY", accent, size=9)
        _arrow(c, 650, 190, 560, 190, accent, "CONFIRM WITH CONTEXT")
    elif "bearish engulfing" in p:
        candles = [(48, 118, 42, 112), (110, 122, 40, 48)]
        _candles(c, candles, x0=280, step=130, scale=1.25, base=250)
        _label(c, 345, 275, "BULLISH CANDLE", accent, size=9)
        _label(c, 475, 275, "BEARISH BODY ENGULFS PRIOR BODY", danger, size=9)
        _arrow(c, 650, 190, 560, 190, danger, "CONFIRM WITH CONTEXT")
    elif "hammer" in p:
        _candles(c, [(80, 105, 20, 78)], x0=360, step=90, scale=1.5, base=250)
        _label(c, 360, 275, "SMALL BODY", accent, size=9)
        _label(c, 360, 292, "LONG LOWER SHADOW", gold, size=9)
    elif "shooting star" in p:
        _candles(c, [(65, 130, 58, 84)], x0=360, step=90, scale=1.5, base=250)
        _label(c, 360, 275, "SMALL BODY", danger, size=9)
        _label(c, 360, 292, "LONG UPPER SHADOW", gold, size=9)
    elif "doji" in p:
        _candles(c, [(60, 110, 15, 61)], x0=360, step=90, scale=1.2, base=250)
        _label(c, 360, 278, "OPEN ≈ CLOSE", gold, size=10)
    elif "morning star" in p:
        candles = [(100, 128, 55, 60), (60, 73, 52, 62), (65, 118, 55, 112)]
        _candles(c, candles, x0=240, step=110, scale=1.35, base=250)
        _label(c, 350, 278, "BEARISH → SMALL → BULLISH", accent, size=10)
    elif "evening star" in p:
        candles = [(60, 118, 55, 112), (112, 126, 104, 110), (110, 118, 40, 45)]
        _candles(c, candles, x0=240, step=110, scale=1.35, base=250)
        _label(c, 350, 278, "BULLISH → SMALL → BEARISH", danger, size=10)
    else:
        candles = [(58, 105, 36, 74), (74, 120, 50, 102), (102, 126, 76, 118)]
        _candles(c, candles, x0=240, step=105, scale=1.25, base=250)
        _label(c, 380, 280, "PATTERN ANATOMY • CONTEXT + CONFIRMATION", muted, size=10)
    return c
