"""Generate attractive, self-contained offline trading lesson diagrams.

This script deliberately creates original educational illustrations locally;
it never downloads screenshots or makes network requests.
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

WIDTH, HEIGHT = 1100, 620
BG = "#07111D"
PANEL = "#0D1A29"
GRID = "#1D3042"
TEXT = "#EAF2F7"
MUTED = "#839AAC"
TEAL = "#35E5C4"
RED = "#FF7181"
GOLD = "#F5CF77"
BLUE = "#68B8FF"
VIOLET = "#AA97FF"

SPECS = {
    "market_structure.png": ("MARKET STRUCTURE", "BOS • swing structure", "A break is a structural event, not a standalone entry."),
    "liquidity_sweep.png": ("LIQUIDITY SWEEP", "External liquidity • rejection", "A sweep needs a reaction; a wick is not a promise."),
    "order_block.png": ("ORDER BLOCK", "Displacement • origin zone", "Context and invalidation come before entry."),
    "fvg.png": ("FAIR VALUE GAP", "Three-candle imbalance", "An imbalance is a location, not a guaranteed reversal."),
    "ict_killzone.png": ("SESSION TIMING", "Plan the window • mark the range", "Time narrows attention; it does not create direction."),
    "silver_bullet.png": ("SILVER BULLET MODEL", "Liquidity • displacement • FVG", "Require the full sequence and predefined risk."),
    "candlestick_patterns.png": ("CANDLESTICK LANGUAGE", "Bodies • wicks • location", "Interpret the candle only in its market context."),
    "risk_reward.png": ("RISK / REWARD", "Predefine stop • size • target", "Reward-to-risk is not the same as win probability."),
}

def _font(size: int, bold: bool = False):
    candidates = ([r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"] if bold
                  else [r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"])
    candidates += ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()

def _chart_image(name: str, spec: tuple[str, str, str]) -> Image.Image:
    title, subtitle, footer = spec
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((18, 18, WIDTH - 18, HEIGHT - 18), radius=18, fill=PANEL, outline=GRID, width=2)
    draw.text((46, 38), "TRADER PLANNER PRO  /  OFFLINE ACADEMY", font=_font(16, True), fill=TEAL)
    draw.text((46, 70), title, font=_font(31, True), fill=TEXT)
    draw.text((48, 111), subtitle, font=_font(17, True), fill=GOLD)
    x0, y0, x1, y1 = 55, 164, 1040, 510
    for n in range(9):
        y = y0 + n * (y1-y0) / 8
        draw.line((x0, y, x1, y), fill=GRID, width=1)
    for n in range(13):
        x = x0 + n * (x1-x0) / 12
        draw.line((x, y0, x, y1), fill=GRID, width=1)
    # Deterministic price path: a smooth alternating trend with a varied wave.
    path = []
    for i in range(46):
        t = i / 45
        if name in ("liquidity_sweep.png", "ict_killzone.png", "silver_bullet.png"):
            trend = 0.43 - 0.42*t
        elif name in ("market_structure.png", "fvg.png", "order_block.png"):
            trend = 0.70 - 0.44*t
        elif name == "risk_reward.png":
            trend = 0.66 - 0.34*t
        else:
            trend = 0.52 + 0.08*math.sin(t*math.pi)
        wave = 0.055*math.sin(i*1.23) + 0.025*math.sin(i*0.41+0.7)
        val = max(0.09, min(0.91, trend+wave))
        path.append((x0+28+i*(x1-x0-56)/45, y0+val*(y1-y0)))
    def price_y(v):
        return y0 + v*(y1-y0)
    # Price candles derived from the path, with a little fixed candle variation.
    for i, (x, py) in enumerate(path):
        drift = ((i % 7)-3)*2.0
        open_y = py + drift + (7 if i % 2 else -7)
        close_y = py - drift + (-8 if i % 3 else 8)
        hi = max(open_y, close_y) - (10 + (i % 4)*3)
        lo = min(open_y, close_y) + (9 + (i % 3)*3)
        bullish = close_y < open_y
        color = TEAL if bullish else RED
        draw.line((x, hi, x, lo), fill=color, width=2)
        half = 6
        top, bottom = sorted((open_y, close_y))
        draw.rectangle((x-half, top, x+half, max(top+3, bottom)), fill=color, outline=color)
    # Concept-specific annotation overlays.
    if name == "market_structure.png":
        lvl = y0+0.37*(y1-y0)
        draw.line((x0+230,lvl,x1-70,lvl),fill=GOLD,width=3)
        draw.text((x1-290,lvl-26),"STRUCTURE LEVEL",font=_font(14,True),fill=GOLD)
        draw.line((x0+500,lvl-46,x0+660,lvl-8),fill=BLUE,width=4)
        draw.text((x0+610,lvl-72),"BOS",font=_font(20,True),fill=BLUE)
    elif name == "liquidity_sweep.png":
        lvl=y0+0.24*(y1-y0)
        draw.line((x0+110,lvl,x1-90,lvl),fill=GOLD,width=2)
        draw.text((x0+115,lvl-26),"EQUAL HIGHS / LIQUIDITY",font=_font(14,True),fill=GOLD)
        xx=x0+820
        draw.ellipse((xx-28,lvl-33,xx+28,lvl+23),outline=BLUE,width=4)
        draw.text((xx-105,lvl+34),"SWEEP → REJECTION",font=_font(14,True),fill=BLUE)
    elif name == "order_block.png":
        xa, xb=x0+485,x0+675; ya,yb=y0+0.50*(y1-y0),y0+0.70*(y1-y0)
        draw.rounded_rectangle((xa,ya,xb,yb),radius=8,fill="#164A4A",outline=TEAL,width=3)
        draw.text((xa+12,ya+12),"ORIGIN ZONE",font=_font(15,True),fill=TEXT)
        draw.line((xb+10,ya-60,xb+86,ya-100),fill=GOLD,width=3)
        draw.text((xb+12,ya-128),"DISPLACEMENT",font=_font(13,True),fill=GOLD)
    elif name == "fvg.png":
        xa,xb=x0+350,x0+505; ya,yb=y0+0.28*(y1-y0),y0+0.43*(y1-y0)
        draw.rectangle((xa,ya,xb,yb),fill="#183D60",outline=BLUE,width=3)
        draw.text((xa+8,ya+8),"FVG",font=_font(22,True),fill=TEXT)
        draw.line((xb+15,(ya+yb)/2,xb+110,(ya+yb)/2-22),fill=GOLD,width=3)
        draw.text((xb+30,(ya+yb)/2-50),"IMBALANCE",font=_font(13,True),fill=GOLD)
    elif name in ("ict_killzone.png","silver_bullet.png"):
        xa,xb=x0+540,x0+850
        draw.rectangle((xa,y0,xb,y1),fill="#132C42",outline=BLUE,width=2)
        draw.text((xa+18,y0+12),"FOCUS WINDOW",font=_font(15,True),fill=BLUE)
        if name == "silver_bullet.png":
            draw.rounded_rectangle((xa+28,y0+100,xb-20,y0+165),radius=8,fill="#164A4A",outline=TEAL,width=2)
            draw.text((xa+42,y0+119),"CONFIRMED FVG",font=_font(16,True),fill=TEXT)
    elif name == "candlestick_patterns.png":
        # A large illustrative engulfing pair in a reserved upper-right chart area.
        cx,cy=x1-190,y0+80
        draw.line((cx,cy-42,cx,cy+46),fill=RED,width=3)
        draw.rectangle((cx-15,cy-15,cx+15,cy+30),fill=RED)
        cx2=cx+62
        draw.line((cx2,cy-68,cx2,cy+65),fill=TEAL,width=3)
        draw.rectangle((cx2-18,cy-48,cx2+18,cy+45),fill=TEAL)
        draw.text((cx-98,cy+76),"CLOSE-CONFIRMED",font=_font(13,True),fill=GOLD)
    elif name == "risk_reward.png":
        entry=y0+0.48*(y1-y0); stop=y0+0.72*(y1-y0); target=y0+0.20*(y1-y0)
        draw.line((x0+90,entry,x1-50,entry),fill=BLUE,width=3)
        draw.line((x0+90,stop,x1-50,stop),fill=RED,width=3)
        draw.line((x0+90,target,x1-50,target),fill=TEAL,width=3)
        draw.text((x0+96,target-24),"TARGET",font=_font(14,True),fill=TEAL)
        draw.text((x0+96,entry-24),"ENTRY",font=_font(14,True),fill=BLUE)
        draw.text((x0+96,stop-24),"STOP / INVALIDATION",font=_font(14,True),fill=RED)
        draw.text((x1-230,target+45),"R:R ≠ WIN RATE",font=_font(17,True),fill=GOLD)
    draw.line((42, 548, WIDTH-42, 548), fill=GRID, width=2)
    draw.text((46, 566), footer, font=_font(15), fill=MUTED)
    draw.text((WIDTH-220, 566), "ILLUSTRATIVE • NOT A SIGNAL", font=_font(11, True), fill=GOLD)
    return image

def build_assets(target_dir: Path | str = Path("assets") / "academy") -> list[Path]:
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)
    outputs = []
    for name, spec in SPECS.items():
        path = target / name
        _chart_image(name, spec).save(path, format="PNG", optimize=True)
        outputs.append(path)
    return outputs

if __name__ == "__main__":
    for path in build_assets():
        print(f"Created {path} ({path.stat().st_size:,} bytes)")
