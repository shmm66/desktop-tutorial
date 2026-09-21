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
    c.configure(width=W, height=410)
    for y in range(78, 352, 42):
        c.create_line(24, y, W - 24, y, fill=grid, width=1)
    _label(c, 26, 28, family.upper() + "  •  " + model, text, anchor="w", size=14)
    badge = "#193244" if str(family).lower() == "ict" else "#18352E"
    c.create_rectangle(W - 248, 14, W - 24, 42, fill=badge, outline="")
    _label(c, W - 136, 28, "SETUP MAP • NO TRADE SIGNAL", text, size=8)
\n\ndef _ict_2022(c, palette):
    text = palette["text"]
    accent = palette["accent"]
    danger = palette["danger"]
    gold = palette["gold"]
    blue = palette.get("blue", "#63A7FF")
    violet = palette.get("violet", "#9B8CFF")

    candles = [
        (68, 110, 46, 97), (97, 132, 83, 124), (124, 150, 105, 113),
        (113, 132, 72, 82), (82, 98, 54, 63), (63, 104, 58, 98),
        (98, 136, 91, 129), (129, 165, 121, 158), (158, 192, 148, 184),
        (184, 214, 170, 206), (206, 232, 198, 226),
    ]
    _candles(c, candles, x0=92, step=66, scale=1.12, base=315)

    # 1) liquidity target / raid
    c.create_line(70, 185, 370, 185, fill=gold, dash=(7, 5), width=2)
    _label(c, 72, 168, "EXTERNAL LIQUIDITY", gold, anchor="w", size=9)
    c.create_oval(352, 172, 382, 202, outline=danger, width=3)
    _label(c, 367, 220, "SWEEP", danger, size=9)

    # 2) structural shift + displacement
    _arrow(c, 405, 294, 520, 120, accent, "MSS / DISPLACEMENT")
    c.create_line(455, 142, 575, 142, fill=violet, dash=(4, 4), width=2)
    _label(c, 515, 128, "DISPLACEMENT LEG", violet, size=8)

    # 3) FVG and retrace
    _zone(c, 525, 142, 670, 192, "#153C35", accent, "FVG / ENTRY AREA", accent)
    _arrow(c, 742, 220, 650, 168, blue, "RETURN")
    _label(c, 670, 244, "RETRACE INTO FVG", blue, size=9)

    # 4) invalidation + target
    _zone(c, 730, 278, 880, 322, "#3A2730", danger, "INVALIDATION", danger)
    c.create_line(790, 106, 1080, 106, fill=gold, width=3)
    _label(c, 805, 88, "OPPOSING LIQUIDITY / TARGET", gold, anchor="w", size=9)
    _arrow(c, 860, 235, 1020, 112, gold, "TARGET")

    _label(
        c, 585, 383,
        "Sweep → MSS / displacement → FVG → return → target (educational model map)",
        text, size=10
    )
\n\ndef _ict_silver_bullet(c, palette):
    text = palette["text"]
    accent = palette["accent"]
    danger = palette["danger"]
    violet = palette.get("violet", "#9B8CFF")
    blue = palette.get("blue", "#63A7FF")
    gold = palette["gold"]

    c.create_rectangle(448, 58, 752, 350, outline=violet, width=3)
    _label(c, 600, 77, "DEFINED SILVER BULLET TIME WINDOW", violet, size=11)

    candles = [
        (46, 84, 30, 74), (74, 102, 58, 95), (95, 124, 83, 91),
        (91, 112, 52, 64), (64, 101, 58, 97), (97, 134, 88, 127),
        (127, 154, 118, 146), (146, 170, 135, 160),
    ]
    _candles(c, candles, x0=118, step=98, scale=1.24, base=315)

    c.create_line(88, 178, 340, 178, fill=gold, dash=(7, 5), width=2)
    _label(c, 90, 160, "LIQUIDITY TARGET", gold, anchor="w", size=8)
    c.create_oval(330, 166, 358, 194, outline=danger, width=3)
    _label(c, 344, 210, "RUN / RAID", danger, size=8)

    _arrow(c, 380, 286, 520, 125, accent, "DISPLACEMENT")
    _zone(c, 566, 150, 718, 202, "#16382F", accent, "FVG", accent)
    _arrow(c, 860, 225, 714, 180, blue, "RETRACE")
    _label(c, 820, 115, "TIME + DISPLACEMENT + FVG", violet, size=9)
    _label(c, 580, 383, "The time window is the constraint; the FVG is the entry mechanism in this model.", text, size=9)
\n\ndef _ict_unicorn(c, palette):
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


def _smc_liquidity_bos(c, palette):
    text = palette["text"]
    accent = palette["accent"]
    danger = palette["danger"]
    gold = palette["gold"]
    blue = palette.get("blue", "#63A7FF")

    candles = [
        (70, 118, 52, 98), (98, 136, 86, 126), (126, 149, 112, 137),
        (137, 178, 129, 170), (170, 193, 150, 158), (158, 167, 119, 124),
        (124, 153, 118, 145), (145, 184, 137, 176), (176, 208, 161, 200),
    ]
    _candles(c, candles, x0=92, step=96, scale=1.14, base=315)

    c.create_line(72, 110, 380, 110, fill=gold, dash=(7, 5), width=2)
    _label(c, 76, 92, "EQUAL HIGHS / BUY-SIDE LIQUIDITY", gold, anchor="w", size=9)
    c.create_oval(355, 94, 385, 124, outline=danger, width=3)
    _label(c, 372, 144, "LIQUIDITY SWEEP", danger, size=9)

    c.create_line(486, 150, 486, 244, fill=accent, width=4)
    _label(c, 502, 198, "BOS CLOSE", accent, anchor="w", size=10)

    _zone(c, 600, 182, 790, 238, "#183A31", accent, "REACTION AREA", accent)
    _label(c, 695, 248, "FVG / OB", accent, size=8)
    _arrow(c, 958, 148, 792, 210, blue, "RETEST")
    _zone(c, 860, 94, 1068, 132, "#3A2730", danger, "INVALIDATION", danger)

    _label(c, 590, 385, "SMC flow: liquidity event → confirmed structure break → reaction area → retest.", text, size=9)
\n\ndef _smc_ob_fvg(c, palette):
    text = palette["text"]
    accent = palette["accent"]
    gold = palette["gold"]
    blue = palette.get("blue", "#63A7FF")
    danger = palette["danger"]

    _candles(c, [
        (70, 120, 55, 62), (62, 98, 45, 92), (92, 122, 84, 116),
        (116, 205, 112, 198), (198, 228, 188, 214), (214, 236, 203, 230),
        (230, 244, 210, 220), (220, 232, 174, 182), (182, 212, 176, 205),
    ], x0=105, step=98, scale=1.1, base=315)

    _zone(c, 330, 168, 460, 228, "#3A2730", danger, "ORDER BLOCK", danger)
    _label(c, 395, 245, "last opposing candle / base", danger, size=8)
    _zone(c, 500, 126, 660, 184, "#16382F", accent, "3-CANDLE FVG", accent)
    _label(c, 580, 202, "IMBALANCE", accent, size=8)
    _arrow(c, 900, 112, 658, 155, blue, "RETRACE / ENTRY")
    c.create_line(760, 270, 1030, 270, fill=gold, dash=(6, 5), width=2)
    _label(c, 765, 252, "INVALIDATION BELOW MODEL OR STRUCTURAL FAIL", gold, anchor="w", size=8)
    _label(c, 590, 385, "SMC separates the OB and the three-candle FVG; the retest defines the reaction area.", text, size=9)
\n\ndef _smc_breaker(c, palette):
    text = palette["text"]
    accent, danger, violet, gold, blue = palette["accent"], palette["danger"], palette.get("violet", "#9B8CFF"), palette["gold"], palette.get("blue", "#63A7FF")
    _candles(c, [
        (80, 122, 60, 112), (112, 146, 100, 132), (132, 160, 118, 140),
        (140, 178, 136, 168), (168, 188, 120, 126), (126, 152, 112, 118),
        (118, 142, 88, 96), (96, 130, 84, 124),
    ], x0=120, step=110, scale=1.15, base=315)
    _zone(c, 330, 165, 530, 225, "#3A2730", danger, "ORIGINAL ORDER BLOCK", danger)
    c.create_line(330, 195, 530, 195, fill=gold, dash=(7,5), width=2)
    _arrow(c, 560, 210, 610, 120, danger, "FAIL / CLOSE THROUGH")
    _zone(c, 650, 165, 860, 225, "#172B45", violet, "BREAKER ZONE = FLIPPED ROLE", violet)
    _arrow(c, 1010, 120, 825, 195, blue, "RETEST")
    _label(c, 590, 355, "SMC breaker: a failed OB that flips role after a confirmed break.", text, size=9)


def _smc_mss_fvg(c, palette):
    text = palette["text"]
    accent, danger, gold, blue = palette["accent"], palette["danger"], palette["gold"], palette.get("blue", "#63A7FF")
    _line(c, [70, 240, 140, 210, 210, 230, 280, 175, 350, 205, 420, 160], blue, 4)
    c.create_line(280, 175, 450, 175, fill=gold, dash=(7,5), width=2)
    _label(c, 300, 155, "KEY SWING", gold, size=9)
    c.create_oval(410, 145, 438, 173, outline=danger, width=3)
    _label(c, 424, 195, "MSS / CHoCH", accent, size=9)
    _arrow(c, 470, 230, 590, 105, accent, "DISPLACEMENT")
    _zone(c, 610, 105, 790, 155, "#16382F", accent, "FVG", accent)
    _arrow(c, 930, 110, 790, 132, blue, "RETEST")
    _label(c, 595, 355, "SMC reversal workflow: context → structural shift → displacement → FVG reaction.", text, size=9)


def _smc_liquidity_displacement(c, palette):
    text = palette["text"]
    accent, danger, gold, blue = palette["accent"], palette["danger"], palette["gold"], palette.get("blue", "#63A7FF")
    _zone(c, 70, 100, 250, 145, "#3A2730", danger, "LIQUIDITY POOL", danger)
    _arrow(c, 260, 125, 390, 280, danger, "SWEEP / RAID")
    _arrow(c, 405, 280, 565, 105, accent, "DISPLACEMENT")
    c.create_line(400, 165, 650, 165, fill=gold, dash=(7,5), width=2)
    _label(c, 525, 147, "STRUCTURE BREAK", gold, size=9)
    _zone(c, 620, 140, 820, 195, "#16382F", accent, "REACTION ZONE", accent)
    _arrow(c, 1020, 105, 805, 165, blue, "RETEST")
    _label(c, 595, 355, "Broad SMC model: liquidity → displacement → reaction zone → retest, with fixed invalidation.", text, size=9)


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
        if "liquidity sweep" in m and "bos" in m:
            _smc_liquidity_bos(c, palette)
        elif "order block" in m and "fvg" in m:
            _smc_ob_fvg(c, palette)
        elif "breaker" in m:
            _smc_breaker(c, palette)
        elif "choch" in m or "mss" in m:
            _smc_mss_fvg(c, palette)
        else:
            _smc_liquidity_displacement(c, palette)
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
