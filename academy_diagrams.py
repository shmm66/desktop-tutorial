from __future__ import annotations

import math
import tkinter as tk


def _line(c, pts, fill, width=2, dash=None):
    c.create_line(*pts, fill=fill, width=width, smooth=True, dash=dash or ())


def _label(c, x, y, text, fill, anchor="center", size=10, bold=True):
    c.create_text(x, y, text=text, fill=fill, anchor=anchor,
                  font=("Segoe UI", size, "bold" if bold else "normal"))


def _zone(c, x1, y1, x2, y2, fill, outline, text, text_fill):
    c.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=2)
    _label(c, (x1+x2)/2, (y1+y2)/2, text, text_fill, size=9)


def _candles(c, candles, x0=42, step=46, scale=1.0, base=205):
    for i, (o, h, l, cl) in enumerate(candles):
        x = x0 + i*step
        def y(v): return base - v*scale
        up = cl >= o
        fill = "#39E6B1" if up else "#FF6F7D"
        outline = fill
        c.create_line(x, y(h), x, y(l), fill=fill, width=2)
        top, bot = sorted((y(o), y(cl)))
        c.create_rectangle(x-9, top, x+9, max(bot, top+2), fill=fill, outline=outline)


def draw_setup(parent, family, model, palette):
    """Draw a clean, semantic educational chart for one setup.

    These are schematics rather than unlabeled web screenshots: every zone and
    marker is tied to the selected Academy term, preventing mismatched visuals.
    """
    c = tk.Canvas(parent, height=330, bg=palette["panel3"], highlightthickness=0)
    c.pack(fill="x", padx=8, pady=8)
    W = 1180
    c.configure(width=W)

    bg = palette["panel3"]
    grid = palette["line"]
    text = palette["text"]
    muted = palette["muted"]
    accent = palette["accent"]
    violet = palette.get("violet", "#9B8CFF")
    gold = palette["gold"]
    danger = palette["danger"]
    blue = palette.get("blue", "#63A7FF")

    for y in range(55, 305, 50):
        c.create_line(20, y, W-20, y, fill=grid, width=1)
    _label(c, 24, 24, f"{family.upper()}  •  {model}", accent, anchor="w", size=12)
    _label(c, W-24, 24, "EDUCATIONAL SCHEMATIC", muted, anchor="e", size=8)

    m = model.lower()

    # SMC / structure models
    if family.lower() == "smc":
        if "liquidity sweep" in m or "liquidity + displacement" in m:
            pts = [(50,235),(120,200),(185,222),(250,150),(310,195),(365,128),(420,185),
                   (480,105),(545,145),(600,92),(655,160),(720,118),(790,175),(855,110),(925,145),(1050,80)]
            _line(c, [v for p in pts for v in p], blue, 4)
            c.create_line(240,150,350,150,fill=muted,dash=(5,4))
            _label(c, 295,142, "Prior Swing High", muted, size=8)
            c.create_line(540,145,650,145,fill=gold,dash=(6,4))
            _label(c, 598,137, "Liquidity Pool", gold, size=8)
            c.create_oval(646,152,664,170,outline=danger,width=3)
            _label(c, 655,190, "SWEEP", danger, size=9)
            c.create_line(720,118,855,118,fill=accent,width=3)
            _label(c, 790,106, "BOS", accent, size=10)
            _zone(c, 760, 140, 875, 178, "#16382F", accent, "OB / FVG", accent)
            _label(c, 820,202, "Retest / Entry Area", text, size=9)
            _label(c, 1020,70, "Target Liquidity", gold, size=9)
        elif "order block" in m:
            pts = [(60,230),(120,205),(170,218),(220,125),(270,170),(325,105),(380,145),(430,80),(500,122),(560,92),(640,130),(720,115),(820,155),(930,105),(1050,80)]
            _line(c,[v for p in pts for v in p],blue,4)
            _zone(c, 330, 102, 430, 142, "#3B2E16", gold, "ORDER BLOCK", gold)
            _zone(c, 525, 132, 625, 168, "#16382F", accent, "FVG", accent)
            _label(c, 560,210,"Displacement",text,size=9)
            c.create_line(900,155,960,155,fill=accent,width=3)
            _label(c, 960,175,"Retest",accent,size=9)
        elif "breaker" in m:
            pts = [(60,205),(140,165),(215,190),(280,135),(345,170),(420,110),(500,135),(580,210),(650,170),(730,230),(820,175),(930,125),(1050,90)]
            _line(c,[v for p in pts for v in p],blue,4)
            _zone(c, 420, 100, 535, 142, "#3B2E16", gold, "ORIGINAL OB", gold)
            _label(c, 600,226,"OB fails / flips",danger,size=9)
            _zone(c, 610, 178, 760, 218, "#172B45", violet, "BREAKER", violet)
            c.create_line(760,198,860,198,fill=accent,width=3)
            _label(c, 815,216,"Reclaim",accent,size=9)
        else:
            pts = [(60,170),(120,145),(180,162),(240,120),(300,145),(360,108),(420,135),(500,100),(575,115),(650,190),(730,150),(810,178),(900,105),(1040,80)]
            _line(c,[v for p in pts for v in p],blue,4)
            c.create_line(360,108,575,108,fill=muted,dash=(5,4))
            _label(c, 468,98,"Structure",muted,size=9)
            c.create_oval(642,182,660,200,outline=danger,width=3)
            _label(c, 652,220,"CHOCH / MSS",danger,size=9)
            _zone(c, 725, 150, 840, 184, "#16382F",accent,"FVG",accent)
            _label(c, 870,120,"Reversal / Retest",text,size=9)
        return c

    # ICT models
    if "2022" in m:
        pts=[(60,190),(120,165),(180,185),(240,150),(300,178),(365,135),(430,168),(505,120),
             (570,178),(625,230),(690,180),(760,205),(830,145),(900,170),(1015,95)]
        _line(c,[v for p in pts for v in p],blue,4)
        c.create_line(470,168,610,168,fill=gold,dash=(6,4))
        _label(c,540,156,"Liquidity",gold,size=9)
        c.create_oval(610,222,628,240,outline=danger,width=3)
        _label(c,618,257,"Sweep",danger,size=9)
        c.create_line(680,180,835,180,fill=accent,width=3)
        _label(c,760,168,"MSS / Displacement",accent,size=9)
        _zone(c, 720, 195, 835, 228, "#16382F", accent, "FVG", accent)
        _label(c, 890,205,"Return → Entry",text,size=9)
    elif "silver bullet" in m:
        for x in (170, 420, 670, 920):
            c.create_line(x,65,x,290,fill=grid,dash=(4,5))
        c.create_rectangle(420,80,540,285,fill="#172B45",outline=violet,width=2)
        _label(c,480,70,"FIXED TIME WINDOW",violet,size=10)
        pts=[(60,220),(120,190),(190,215),(255,175),(320,205),(385,150),(430,165),(470,130),(520,178),(575,120),(650,142),(730,105),(820,145),(930,100),(1040,76)]
        _line(c,[v for p in pts for v in p],blue,4)
        _zone(c, 480, 145, 560, 180, "#16382F", accent, "FVG", accent)
        _label(c, 670,92,"Displacement → FVG → Return",text,size=9)
    elif "unicorn" in m:
        _zone(c, 370, 118, 600, 190, "#172B45", violet, "BREAKER", violet)
        _zone(c, 470, 130, 690, 205, "#16382F", accent, "FVG", accent)
        c.create_oval(540,145,620,195,outline=gold,width=3)
        _label(c,580,170,"UNICORN OVERLAP",gold,size=9)
        pts=[(60,230),(130,190),(205,210),(280,150),(340,175),(410,100),(500,165),(580,115),(660,155),(760,95),(880,135),(1015,75)]
        _line(c,[v for p in pts for v in p],blue,4)
    elif "power of three" in m or "amd" in m:
        bands=[("ACCUMULATION",50,320,accent),("MANIPULATION",320,650,danger),("DISTRIBUTION",650,1120,gold)]
        for label,x1,x2,color in bands:
            c.create_rectangle(x1,75,x2,275,outline=color,width=2)
            _label(c,(x1+x2)/2,88,label,color,size=9)
        pts=[(70,220),(150,200),(230,218),(300,205),(360,150),(420,250),(480,215),(540,175),(600,230),(675,160),(760,120),(850,95),(940,70),(1050,55)]
        _line(c,[v for p in pts for v in p],blue,4)
        _label(c,485,266,"liquidity raid / false move",danger,size=9)
    elif "judas" in m:
        c.create_rectangle(330,75,620,285,outline=violet,width=2)
        _label(c,475,88,"SESSION WINDOW",violet,size=9)
        pts=[(60,200),(140,170),(210,180),(280,145),(350,110),(420,210),(490,235),(560,190),(650,150),(740,115),(850,80),(1020,60)]
        _line(c,[v for p in pts for v in p],blue,4)
        c.create_oval(410,202,428,220,outline=danger,width=3)
        _label(c,420,242,"JUDAS MOVE",danger,size=9)
        c.create_line(500,190,590,190,fill=accent,width=3)
        _label(c,545,175,"Reversal + Displacement",accent,size=9)
    else:
        _label(c, W/2, 160, "ICT model schematic", text, size=18)
        _label(c, W/2, 195, "Context → Liquidity → Displacement → Entry Model → Target", muted, size=10)
    return c


def draw_candlestick(parent, pattern, palette):
    c = tk.Canvas(parent, height=250, bg=palette["panel3"], highlightthickness=0)
    c.pack(fill="x", padx=8, pady=8)
    text, muted = palette["text"], palette["muted"]
    accent, danger, gold = palette["accent"], palette["danger"], palette["gold"]
    _label(c, 20, 20, pattern.upper(), accent, anchor="w", size=12)

    p = pattern.lower()
    if "bullish engulfing" in p:
        candles=[(70,95,25,45),(50,110,35,105)]
        _candles(c,candles,x0=160,step=90,scale=1.15,base=205)
        _label(c,250,228,"Bullish body fully covers previous body",accent,size=10)
    elif "bearish engulfing" in p:
        candles=[(45,100,30,85),(105,120,20,25)]
        _candles(c,candles,x0=160,step=90,scale=1.15,base=205)
        _label(c,250,228,"Bearish body fully covers previous body",danger,size=10)
    elif "hammer" in p:
        _candles(c,[(80,105,20,78)],x0=250,step=90,scale=1.25,base=205)
        _label(c,250,228,"Small body • long lower shadow",accent,size=10)
    elif "shooting star" in p:
        _candles(c,[(65,130,58,84)],x0=250,step=90,scale=1.15,base=205)
        _label(c,250,228,"Small body • long upper shadow",danger,size=10)
    elif "doji" in p:
        _candles(c,[(60,105,15,61)],x0=250,step=90,scale=1.0,base=205)
        _label(c,250,228,"Open ≈ Close",gold,size=10)
    elif "morning star" in p:
        _candles(c,[(90,120,55,60),(55,72,48,60),(62,112,55,108)],x0=140,step=90,scale=1.05,base=205)
        _label(c,275,228,"Bearish → small body → strong bullish",accent,size=10)
    elif "evening star" in p:
        _candles(c,[(55,110,50,105),(105,125,88,105),(108,118,35,45)],x0=140,step=90,scale=1.05,base=205)
        _label(c,275,228,"Bullish → small body → strong bearish",danger,size=10)
    else:
        _candles(c,[(55,100,35,60),(62,115,42,98),(98,120,70,110)],x0=120,step=80,scale=1.0,base=205)
        _label(c,250,228,"Pattern anatomy • use with context and confirmation",muted,size=10)
    return c
