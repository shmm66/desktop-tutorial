from __future__ import annotations

import math
import tkinter as tk


def _palette(p):
    return {
        "bg": p.get("panel3", "#0B1724"),
        "grid": p.get("line", "#203345"),
        "text": p.get("text", "#EAF2F7"),
        "muted": p.get("muted", "#8EA3B5"),
        "green": p.get("accent", "#32E0B5"),
        "red": p.get("danger", "#FF6F7D"),
        "gold": p.get("gold", "#F2C46D"),
        "blue": p.get("blue", "#68A8FF"),
        "violet": p.get("violet", "#A996FF"),
        "soft": p.get("soft", "#152737"),
    }


def _canvas(parent, height=410):
    c=tk.Canvas(parent,height=height,bg="#0A111A",highlightthickness=0,bd=0)
    c.pack(fill="both",expand=True,padx=8,pady=8)
    c.update_idletasks()
    return c


def _grid(c, P):
    w=max(900,c.winfo_width(),1120)
    for y in range(54,356,38):
        c.create_line(24,y,w-24,y,fill=P["grid"],width=1)
    for x in range(55,w-24,70):
        c.create_line(x,46,x,366,fill=P["grid"],width=1)


def _title(c,P,title,subtitle):
    c.create_text(34,22,text=title,anchor="w",fill=P["text"],
                  font=("Segoe UI",15,"bold"))
    c.create_text(34,44,text=subtitle,anchor="w",fill=P["muted"],
                  font=("Segoe UI",8))


def _label(c,x,y,text,color,anchor="center",size=9):
    c.create_text(x,y,text=text,anchor=anchor,fill=color,
                  font=("Segoe UI",size,"bold"))


def _zone(c,x1,y1,x2,y2,fill,outline,label,P,alpha=False):
    c.create_rectangle(x1,y1,x2,y2,fill=fill,outline=outline,width=2)
    if label:
        _label(c,(x1+x2)/2,(y1+y2)/2,label,outline,size=9)


def _line(c,pts,color,width=3,dash=()):
    c.create_line(*pts,fill=color,width=width,smooth=True,dash=dash)


def _arrow(c,x1,y1,x2,y2,color,text=None,P=None):
    c.create_line(x1,y1,x2,y2,fill=color,width=3,arrow=tk.LAST)
    if text:
        _label(c,(x1+x2)/2,(y1+y2)/2-12,text,color,size=8)


def _candles(c, bullish=True, x0=70, step=70, scale=1.2, base=320):
    if bullish:
        data=[(72,104,58,94),(94,126,84,116),(116,143,104,111),(111,135,77,83),
              (83,106,70,101),(101,139,95,132),(132,171,122,163),(163,202,152,194),(194,224,184,216)]
    else:
        data=[(194,226,184,202),(202,236,188,194),(194,224,170,178),(178,207,164,201),
              (201,226,191,198),(198,219,162,170),(170,205,155,160),(160,191,137,146),(146,177,124,134)]
    for i,(o,h,l,cl) in enumerate(data):
        x=x0+i*step
        y=lambda v: base-v*scale
        col="#32E0B5" if cl>=o else "#FF6F7D"
        c.create_line(x,y(h),x,y(l),fill=col,width=2)
        top,bot=sorted((y(o),y(cl)))
        c.create_rectangle(x-9,top,x+9,max(bot,top+2),fill=col,outline=col)


def _two_instruments(c,P):
    _title(c,P,"SMT Divergence","Compare correlated swing behavior; it is context, not a standalone entry.")
    _label(c,65,78,"ASSET A",P["green"],anchor="w",size=10)
    _label(c,65,217,"ASSET B",P["violet"],anchor="w",size=10)
    a=[(90,180),(180,150),(270,170),(360,125),(450,148),(540,95),(630,122),(720,68),(810,92),(900,48),(990,73)]
    b=[(90,330),(180,300),(270,318),(360,270),(450,294),(540,240),(630,260),(720,210),(810,232),(900,255),(990,205)]
    _line(c,[v for p in a for v in p],P["green"],4); _line(c,[v for p in b for v in p],P["violet"],4)
    c.create_oval(885,34,915,64,outline=P["gold"],width=4)
    c.create_oval(885,240,915,270,outline=P["gold"],width=4)
    _label(c,900,110,"NON-CONFIRMATION",P["gold"],size=10)
    _label(c,900,128,"SMT",P["gold"],size=13)
    _label(c,560,388,"Use matching swing points, then wait for an independent price trigger.",P["muted"],size=9)


def _smc_liquidity(c,P):
    _title(c,P,"SMC • Liquidity Sweep + BOS","Broad SMC workflow: liquidity → confirmed break → reaction area → retest.")
    _candles(c,True,x0=92,step=70)
    c.create_line(58,112,400,112,fill=P["gold"],dash=(8,5),width=2)
    _label(c,64,91,"EQUAL HIGHS / BSL",P["gold"],anchor="w",size=9)
    c.create_oval(360,96,388,124,outline=P["red"],width=3); _label(c,374,143,"SWEEP",P["red"],size=8)
    c.create_line(486,143,486,252,fill=P["green"],width=4); _label(c,502,200,"BOS CLOSE",P["green"],anchor="w",size=10)
    _zone(c,590,180,760,236,"#153B32",P["green"],"FVG / REACTION",P)
    _arrow(c,960,134,765,208,P["blue"],"RETEST")
    _zone(c,850,92,1060,132,"#3A2229",P["red"],"INVALIDATION",P)
    _label(c,600,388,"Sweep alone ≠ signal. The structural break must be confirmed before the retest.",P["text"],size=9)


def _smc_ob_fvg(c,P):
    _title(c,P,"SMC • Order Block + FVG Retest","Keep the Order Block and the three-candle FVG as separate objects.")
    _candles(c,True,x0=100,step=92)
    _zone(c,335,174,474,232,"#3A2229",P["red"],"ORDER BLOCK",P)
    _zone(c,505,126,675,184,"#153B32",P["green"],"3-CANDLE FVG",P)
    _arrow(c,930,111,678,156,P["blue"],"RETRACE")
    c.create_line(775,272,1048,272,fill=P["gold"],dash=(6,5),width=2)
    _label(c,785,252,"INVALIDATION BELOW MODEL / STRUCTURAL FAIL",P["gold"],anchor="w",size=8)
    _label(c,600,388,"The FVG is an imbalance; the OB is a zone. Do not visually merge their definitions.",P["text"],size=9)


def _smc_breaker(c,P):
    _title(c,P,"SMC • Breaker Block Reclaim","A breaker begins as a failed order block and flips role after the structural violation.")
    _candles(c,False,x0=110,step=100)
    _zone(c,320,160,540,222,"#3A2229",P["red"],"ORIGINAL OB",P)
    _arrow(c,555,206,625,112,P["red"],"FAIL / CLOSE THROUGH")
    _zone(c,665,150,850,212,"#233149",P["violet"],"BREAKER",P)
    _arrow(c,990,120,853,183,P["blue"],"RETEST")
    c.create_line(880,276,1060,276,fill=P["gold"],dash=(6,5),width=2)
    _label(c,885,258,"TARGET / OPPOSING LIQUIDITY",P["gold"],anchor="w",size=8)
    _label(c,600,388,"No failure → no breaker. The flip comes after the structural violation.",P["text"],size=9)


def _smc_shift(c,P):
    _title(c,P,"SMC • CHoCH / MSS + FVG","A broad reversal workflow; the structural shift is distinct from the entry zone.")
    _candles(c,False,x0=84,step=68)
    c.create_line(360,148,560,148,fill=P["gold"],dash=(7,5),width=2)
    _label(c,365,130,"PRIOR SWING",P["gold"],anchor="w",size=8)
    _arrow(c,440,285,585,122,P["green"],"MSS / DISPLACEMENT")
    _zone(c,610,145,785,198,"#153B32",P["green"],"FVG",P)
    _arrow(c,980,235,790,175,P["blue"],"RETURN")
    _zone(c,820,286,1045,322,"#3A2229",P["red"],"INVALIDATION",P)
    _label(c,600,388,"MSS/CHoCH describes structure; FVG describes imbalance. They are not synonyms.",P["text"],size=9)


def _smc_flow(c,P):
    _title(c,P,"SMC • Liquidity + Displacement + Retest","Generic SMC sequence without borrowing a named ICT model.")
    _candles(c,True,x0=72,step=66)
    for x,label,col in [(80,"LIQUIDITY",P["gold"]),(360,"SWEEP",P["red"]),(560,"DISPLACEMENT",P["green"]),(790,"RETEST",P["blue"])]:
        _label(c,x,85,label,col,anchor="w",size=8)
    c.create_line(72,108,315,108,fill=P["gold"],dash=(7,5),width=2)
    c.create_oval(300,94,328,122,outline=P["red"],width=3)
    _arrow(c,390,286,560,125,P["green"])
    _zone(c,700,150,865,208,"#153B32",P["green"],"REACTION ZONE",P)
    _arrow(c,1015,120,870,182,P["blue"])
    _label(c,600,388,"This is a generic SMC workflow; it is deliberately not labeled as 2022 / Silver Bullet / Unicorn.",P["text"],size=9)


def _ict_2022(c,P):
    _title(c,P,"ICT • 2022 Model","Named ICT sequence: liquidity raid → displacement/MSS → FVG → return.")
    _candles(c,False,x0=80,step=68)
    c.create_line(55,176,360,176,fill=P["gold"],dash=(7,5),width=2); _label(c,62,158,"LIQUIDITY POOL",P["gold"],anchor="w",size=8)
    c.create_oval(338,162,368,192,outline=P["red"],width=3); _label(c,353,211,"RAID / SWEEP",P["red"],size=8)
    _arrow(c,390,290,535,112,P["green"],"MSS + DISPLACEMENT")
    _zone(c,555,138,725,194,"#153B32",P["green"],"FVG",P)
    _arrow(c,970,230,728,170,P["blue"],"RETURN")
    c.create_line(760,104,1060,104,fill=P["gold"],width=3); _label(c,770,84,"DOL / OPPOSING LIQUIDITY",P["gold"],anchor="w",size=8)
    _label(c,600,388,"The entry is the return into the FVG after the structural displacement step.",P["text"],size=9)


def _ict_silver(c,P):
    _title(c,P,"ICT • Silver Bullet","Time-window model: defined window first, then displacement and FVG.")
    c.create_rectangle(395,66,695,346,outline=P["violet"],width=3); _label(c,545,82,"DEFINED TIME WINDOW",P["violet"],size=10)
    _candles(c,True,x0=110,step=88)
    c.create_line(75,182,320,182,fill=P["gold"],dash=(7,5),width=2); _label(c,82,164,"LIQUIDITY",P["gold"],anchor="w",size=8)
    _arrow(c,355,288,510,118,P["green"],"DISPLACEMENT")
    _zone(c,560,150,720,200,"#153B32",P["green"],"FVG",P)
    _arrow(c,930,222,722,176,P["blue"],"RETURN")
    _label(c,545,388,"Silver Bullet ≠ generic FVG. The time constraint is part of the named model.",P["text"],size=9)


def _ict_unicorn(c,P):
    _title(c,P,"ICT • Unicorn Model","A named ICT overlap of a breaker and an FVG.")
    _candles(c,True,x0=160,step=92)
    _zone(c,500,155,840,228,"#263149",P["violet"],"BREAKER",P)
    _zone(c,625,135,895,202,"#153B32",P["green"],"FVG",P)
    c.create_rectangle(635,146,815,202,outline=P["gold"],width=4)
    _label(c,725,120,"UNICORN OVERLAP",P["gold"],size=11)
    _arrow(c,1015,240,845,180,P["blue"],"RETEST")
    _label(c,600,388,"The defining visual is the overlap; without both components it is not the same model.",P["text"],size=9)


def _ict_ote(c,P):
    _title(c,P,"ICT • OTE / Premium-Discount","Location framework: dealing range → equilibrium → 62–79% retracement → trigger.")
    c.create_rectangle(100,72,1045,338,outline=P["grid"],width=2)
    c.create_line(100,205,1045,205,fill=P["gold"],dash=(8,5),width=2); _label(c,570,188,"EQUILIBRIUM 50%",P["gold"],size=9)
    _zone(c,250,220,600,306,"#263149",P["blue"],"DISCOUNT • OTE 62–79%",P)
    _zone(c,650,104,990,190,"#3A2229",P["red"],"PREMIUM • OTE 62–79%",P)
    _label(c,110,93,"DEALING RANGE",P["text"],anchor="w",size=10)
    _label(c,600,372,"OTE is a location framework; liquidity and a trigger still decide whether the location becomes actionable.",P["text"],size=9)


def _ict_amd(c,P):
    _title(c,P,"ICT • Power of Three (AMD)","A day/session sequencing framework: Accumulation → Manipulation → Distribution.")
    bands=[("ACCUMULATION",55,360,P["green"]),("MANIPULATION",360,730,P["red"]),("DISTRIBUTION",730,1075,P["gold"])]
    for label,x1,x2,col in bands:
        c.create_rectangle(x1,78,x2,324,outline=col,width=3); _label(c,(x1+x2)/2,94,label,col,size=9)
    pts=[(75,250),(150,238),(225,248),(300,242),(360,230),(420,286),(480,178),(545,248),(625,270),(705,220),(775,250),(850,192),(925,150),(1000,115),(1060,92)]
    _line(c,[v for p in pts for v in p],P["blue"],4)
    _label(c,550,302,"LIQUIDITY RAID / FALSE MOVE",P["red"],size=9)
    _label(c,565,388,"AMD is a sequencing framework, not a single candlestick pattern or entry zone.",P["text"],size=9)


def _ict_judas(c,P):
    _title(c,P,"ICT • Judas Swing / Killzone","Defined session window → initial raid → reversal/displacement → reaction area.")
    c.create_rectangle(345,62,690,340,outline=P["violet"],width=3); _label(c,518,78,"SESSION WINDOW",P["violet"],size=10)
    _candles(c,False,x0=100,step=96)
    c.create_oval(425,272,453,300,outline=P["red"],width=3); _label(c,439,318,"JUDAS RAID",P["red"],size=8)
    _arrow(c,500,280,610,155,P["green"],"REVERSAL")
    _zone(c,610,150,770,202,"#153B32",P["green"],"FVG / OB",P)
    c.create_line(800,120,1060,120,fill=P["gold"],width=3); _label(c,810,101,"OPPOSING LIQUIDITY",P["gold"],anchor="w",size=8)
    _label(c,600,388,"The first move alone is not the whole model; the timing and reversal sequence matter.",P["text"],size=9)


def draw_setup(parent, family, model, palette):
    P=_palette(palette)
    c=_canvas(parent)
    _grid(c,P)
    fam=str(family).lower()
    title=str(model).lower()
    if fam=="smc":
        if "liquidity sweep" in title:
            _smc_liquidity(c,P)
        elif "order block" in title:
            _smc_ob_fvg(c,P)
        elif "breaker" in title:
            _smc_breaker(c,P)
        elif "choch" in title or "mss" in title:
            _smc_shift(c,P)
        else:
            _smc_flow(c,P)
    else:
        if "2022" in title:
            _ict_2022(c,P)
        elif "silver bullet" in title:
            _ict_silver(c,P)
        elif "unicorn" in title:
            _ict_unicorn(c,P)
        elif "ote" in title or "premium" in title:
            _ict_ote(c,P)
        elif "power of three" in title or "amd" in title:
            _ict_amd(c,P)
        elif "judas" in title or "killzone" in title:
            _ict_judas(c,P)
        elif "smt" in title:
            _two_instruments(c,P)
        else:
            _ict_2022(c,P)
    return c


def _single_pattern(c,P,title,kind):
    _title(c,P,f"CANDLE • {title}","Exact candlestick anatomy • context + confirmation still required.")
    # Keep candle bodies visually distinct; wick dominance is the feature being taught.
    if kind=="bull":
        c.create_line(260,105,260,310,fill=P["green"],width=3)
        c.create_rectangle(238,185,282,240,fill=P["green"],outline=P["green"])
        _label(c,260,88,"PRIOR BEARISH BODY",P["red"],size=8)
        c.create_line(430,86,430,318,fill=P["green"],width=3)
        c.create_rectangle(407,140,453,260,fill=P["green"],outline=P["green"])
        _label(c,430,64,"BULLISH BODY OVERTAKES PRIOR BODY",P["green"],size=8)
    elif kind=="bear":
        c.create_line(260,92,260,305,fill=P["red"],width=3)
        c.create_rectangle(238,170,282,245,fill=P["red"],outline=P["red"])
        c.create_line(430,84,430,320,fill=P["red"],width=3)
        c.create_rectangle(407,128,453,274,fill=P["red"],outline=P["red"])
        _label(c,430,62,"BEARISH BODY OVERTAKES PRIOR BODY",P["red"],size=8)
    elif kind=="hammer":
        c.create_line(360,80,360,318,fill=P["green"],width=3)
        c.create_rectangle(338,106,382,145,fill=P["green"],outline=P["green"])
        _label(c,360,64,"LONG LOWER WICK",P["green"],size=10)
    elif kind=="shooting":
        c.create_line(360,82,360,320,fill=P["red"],width=3)
        c.create_rectangle(338,226,382,264,fill=P["red"],outline=P["red"])
        _label(c,360,64,"LONG UPPER WICK",P["red"],size=10)
    elif kind=="doji":
        c.create_line(360,95,360,310,fill=P["muted"],width=3)
        c.create_rectangle(340,196,380,207,fill=P["muted"],outline=P["muted"])
        _label(c,360,72,"OPEN ≈ CLOSE",P["gold"],size=11)
    elif kind=="inside":
        c.create_line(300,92,300,310,fill=P["green"],width=3)
        c.create_rectangle(272,150,328,242,fill=P["green"],outline=P["green"])
        c.create_line(430,125,430,285,fill=P["blue"],width=3)
        c.create_rectangle(407,168,453,227,fill=P["blue"],outline=P["blue"])
        _label(c,430,92,"SECOND CANDLE INSIDE PRIOR RANGE",P["blue"],size=9)
    elif kind=="morning":
        _candles(c,False,x0=220,step=120); c.create_line(485,100,485,315,fill=P["green"],width=3)
        c.create_rectangle(466,145,504,270,fill=P["green"],outline=P["green"]); _label(c,485,72,"REVERSAL SEQUENCE",P["green"],size=10)
    elif kind=="evening":
        _candles(c,True,x0=220,step=120); c.create_line(485,100,485,315,fill=P["red"],width=3)
        c.create_rectangle(466,145,504,270,fill=P["red"],outline=P["red"]); _label(c,485,72,"REVERSAL SEQUENCE",P["red"],size=10)
    elif kind=="tweezer_top":
        for x in (350,455):
            c.create_line(x,112,x,288,fill=P["red"],width=3); c.create_rectangle(x-21,168,x+21,235,fill=P["red"],outline=P["red"])
        c.create_line(325,112,480,112,fill=P["gold"],dash=(7,5),width=2); _label(c,402,90,"MATCHING / NEAR-MATCHING HIGHS",P["gold"],size=9)
    elif kind=="tweezer_bottom":
        for x in (350,455):
            c.create_line(x,122,x,300,fill=P["green"],width=3); c.create_rectangle(x-21,170,x+21,238,fill=P["green"],outline=P["green"])
        c.create_line(325,300,480,300,fill=P["gold"],dash=(7,5),width=2); _label(c,402,322,"MATCHING / NEAR-MATCHING LOWS",P["gold"],size=9)
    elif kind=="3white":
        for i,x in enumerate((300,405,510)):
            c.create_line(x,132-i*8,x,292-i*6,fill=P["green"],width=3); c.create_rectangle(x-22,172-i*8,x+22,250-i*6,fill=P["green"],outline=P["green"])
        _label(c,405,90,"THREE PROGRESSIVE BULLISH CLOSES",P["green"],size=10)
    elif kind=="3black":
        for i,x in enumerate((300,405,510)):
            c.create_line(x,122+i*8,x,288+i*6,fill=P["red"],width=3); c.create_rectangle(x-22,160+i*8,x+22,238+i*6,fill=P["red"],outline=P["red"])
        _label(c,405,90,"THREE PROGRESSIVE BEARISH CLOSES",P["red"],size=10)
    elif kind=="marubozu":
        c.create_line(360,92,360,305,fill=P["green"],width=3); c.create_rectangle(334,110,386,286,fill=P["green"],outline=P["green"])
        _label(c,360,72,"LITTLE / NO WICK",P["green"],size=10)
    elif kind=="spinning":
        c.create_line(360,82,360,320,fill=P["muted"],width=3); c.create_rectangle(338,188,382,214,fill=P["muted"],outline=P["muted"])
        _label(c,360,64,"SMALL BODY + TWO-SIDED WICKS",P["gold"],size=9)
    else:
        c.create_line(360,80,360,320,fill=P["muted"],width=3); c.create_rectangle(338,196,382,207,fill=P["muted"],outline=P["muted"])


def draw_candlestick(parent, title, palette):
    name=str(title).lower()
    if "bullish engulf" in name:
        kind="bull"
    elif "bearish engulf" in name:
        kind="bear"
    elif "hammer" in name:
        kind="hammer"
    elif "shooting" in name:
        kind="shooting"
    elif "doji" in name:
        kind="doji"
    elif "inside bar" in name:
        kind="inside"
    elif "morning star" in name:
        kind="morning"
    elif "evening star" in name:
        kind="evening"
    elif "tweezer top" in name:
        kind="tweezer_top"
    elif "tweezer bottom" in name:
        kind="tweezer_bottom"
    elif "three white" in name:
        kind="3white"
    elif "three black" in name:
        kind="3black"
    elif "marubozu" in name:
        kind="marubozu"
    elif "spinning" in name:
        kind="spinning"
    else:
        kind="pin"
    P=_palette(palette)
    c=_canvas(parent)
    _grid(c,P)
    _single_pattern(c,P,title,kind)
    _label(c,600,388,"Candlestick pattern ≠ ICT setup. Pattern + location + market context + confirmation.",P["muted"],size=9)
    return c
