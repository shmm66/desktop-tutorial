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


def _smc_liquidity_bos(c, palette):
    text = palette["text"]
    accent, danger, gold, blue = palette["accent"], palette["danger"], palette["gold"], palette.get("blue", "#63A7FF")
    # Clear SMC anatomy: equal highs -> sweep -> BOS close -> FVG/OB retest.
    _candles(c, [
        (70, 120, 52, 98), (98, 136, 86, 126), (126, 148, 112, 136),
        (136, 176, 128, 168), (168, 190, 150, 158), (158, 166, 118, 124),
        (124, 154, 118, 146), (146, 184, 138, 176), (176, 202, 160, 196),
    ], x0=95, step=100, scale=1.15, base=315)
    c.create_line(85, 110, 380, 110, fill=gold, dash=(7,5), width=2)
    _label(c, 90, 93, "EQH / BUY-SIDE LIQUIDITY", gold, anchor="w", size=9)
    c.create_oval(360, 94, 388, 122, outline=danger, width=3)
    _label(c, 375, 138, "SWEEP", danger, size=9)
    c.create_line(490, 155, 490, 235, fill=accent, width=3)
    _label(c, 505, 198, "BOS CLOSE", accent, anchor="w", size=10)
    _zone(c, 610, 190, 780, 238, "#16382F", accent, "FVG / OB", accent)
    _arrow(c, 940, 160, 760, 215, blue, "RETEST")
    _zone(c, 860, 90, 1060, 132, "#3A2730", danger, "INVALIDATION", danger)
    _label(c, 590, 355, "SMC: liquidity event → confirmed structure break → reaction area → retest.", text, size=9)


def _smc_ob_fvg(c, palette):
    text = palette["text"]
    accent, gold, blue, danger = palette["accent"], palette["gold"], palette.get("blue", "#63A7FF"), palette["danger"]
    _candles(c, [
        (70, 120, 55, 62), (62, 98, 45, 92), (92, 122, 84, 116),
        (116, 205, 112, 198), (198, 228, 188, 214), (214, 236, 203, 230),
        (230, 244, 210, 220), (220, 232, 174, 182), (182, 212, 176, 205),
    ], x0=105, step=98, scale=1.1, base=315)
    _zone(c, 350, 170, 460, 225, "#3A2730", danger, "LAST OPPOSING CANDLE = ORDER BLOCK", danger)
    _zone(c, 500, 132, 655, 182, "#16382F", accent, "3-CANDLE FVG", accent)
    _arrow(c, 900, 125, 635, 160, blue, "RETRACE")
    _label(c, 885, 100, "ENTRY AREA", gold, size=10)
    _label(c, 590, 355, "SMC: displacement creates two distinct objects — OB and the three-candle FVG.", text, size=9)


def _smc_breaker(c, palette):
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


def _smc_structure(c, palette):
    text, accent, gold, blue = palette["text"], palette["accent"], palette["gold"], palette.get("blue", "#63A7FF")
    pts=[(70,255),(145,205),(220,235),(295,160),(370,195),(445,120),(520,165),(595,95),(670,145),(745,78)]
    _line(c,[v for p in pts for v in p],blue,4)
    _label(c,95,278,"HL",accent,size=9); _label(c,305,182,"HH",accent,size=9)
    _label(c,455,142,"HL",accent,size=9); _label(c,690,120,"HH",accent,size=9)
    c.create_line(445,120,620,120,fill=gold,dash=(7,5),width=2)
    _label(c,530,102,"STRUCTURAL REFERENCE",gold,size=9)
    _arrow(c,745,78,900,180,accent,"BOS / CLOSE")
    _label(c,910,170,"STRUCTURE BREAK",accent,anchor="w",size=10)
    _label(c,600,365,"SMC structure: swing sequence first; BOS/CHoCH is evaluated against a defined reference.",text,size=9)

def _smc_liquidity(c, palette):
    text, accent, danger, gold, blue = palette["text"], palette["accent"], palette["danger"], palette["gold"], palette.get("blue","#63A7FF")
    c.create_line(90,110,420,110,fill=gold,dash=(7,5),width=2)
    c.create_line(90,285,420,285,fill=gold,dash=(7,5),width=2)
    _label(c,95,92,"EQUAL HIGHS / BUY-SIDE LIQUIDITY",gold,anchor="w",size=9)
    _label(c,95,304,"EQUAL LOWS / SELL-SIDE LIQUIDITY",gold,anchor="w",size=9)
    _candles(c,[(70,145,55,135),(135,150,80,90),(90,125,70,112),(112,155,95,142),(142,175,105,118),(118,210,112,195)],x0=250,step=105,scale=1.2,base=320)
    c.create_oval(625,95,655,125,outline=danger,width=3)
    _label(c,640,78,"SWEEP",danger,size=9)
    _arrow(c,670,110,800,245,accent,"RAID / RECLAIM")
    _zone(c,825,220,1030,275,"#16382F",accent,"POST-SWEEP REACTION",accent)
    _label(c,595,365,"Liquidity map: equal/obvious highs and lows are reference pools; the sweep itself is not a complete entry.",text,size=9)

def _smc_order_block(c, palette):
    text, accent, danger, gold, blue = palette["text"], palette["accent"], palette["danger"], palette["gold"], palette.get("blue","#63A7FF")
    _candles(c,[(70,120,50,60),(60,110,48,100),(100,132,92,124),(124,225,118,215),(215,250,205,240),(240,265,228,258)],x0=100,step=125,scale=1.05,base=320)
    _zone(c,340,170,490,225,"#3A2730",danger,"ORDER BLOCK",danger)
    _arrow(c,525,205,690,95,accent,"DISPLACEMENT")
    _arrow(c,980,105,690,198,blue,"RETEST")
    c.create_line(340,238,490,238,fill=gold,dash=(7,5),width=2)
    _label(c,415,258,"INVALIDATION",gold,size=9)
    _label(c,575,365,"Order Block: identify the qualifying opposing candle/zone in context, then define invalidation and retest rules.",text,size=9)

def _smc_fvg(c, palette):
    text, accent, gold, blue = palette["text"], palette["accent"], palette.get("blue","#63A7FF")
    candles=[(90,150,70,135),(135,175,128,168),(168,250,160,242),(242,270,230,260)]
    _candles(c,candles,x0=180,step=130,scale=1.0,base=320)
    c.create_rectangle(420,150,555,205,fill="#16382F",outline=accent,width=3)
    _label(c,488,178,"FAIR VALUE GAP",accent,size=10)
    _arrow(c,890,120,555,180,blue,"RETURN / REBALANCE")
    _label(c,580,365,"FVG: a three-candle imbalance area between the relevant wicks; entry rules must define fill/mitigation and invalidation.",text,size=9)


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
        if "order block" in m and "fvg" in m:
            _smc_ob_fvg(c, palette)
        elif "order block" in m:
            _smc_order_block(c, palette)
        elif "fair value gap" in m or m.strip() == "fvg":
            _smc_fvg(c, palette)
        elif "market structure" in m or "swing high" in m or "swing low" in m or "higher high" in m or "lower low" in m:
            _smc_structure(c, palette)
        elif "liquidity sweep" in m and "bos" in m:
            _smc_liquidity_bos(c, palette)
        elif "liquidity" in m and "sweep" in m:
            _smc_liquidity(c, palette)
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
