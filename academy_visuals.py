from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from urllib.request import Request, urlopen
from urllib.parse import urlparse

USER_AGENT = "TraderPlannerPro/7.4 (+https://github.com/shmm66/desktop-tutorial)"

EDUCATION_SOURCES: Dict[str, Tuple[str, str]] = {
    "candlestick": (
        "TradingView Support — Introduction to Candlestick Charts and Patterns",
        "https://www.tradingview.com/support/solutions/43000745269-introduction-to-candlestick-charts-and-patterns/",
    ),
    "structure": (
        "TradingView — ICT-Based Market Structure, Liquidity & Order Block Framework",
        "https://www.tradingview.com/chart/XAUUSD/JhztA6F9-ICT-Based-Market-Structure-Liquidity-Order-Block-Framework/",
    ),
    "liquidity": (
        "TradingView — Liquidity Sweep Setup | MSS + FVG + Order Block",
        "https://www.tradingview.com/chart/GOLD/GXZP7v3b-Liquidity-Sweep-Setup-MSS-FVG-Order-Block/",
    ),
    "fvg": (
        "TradingView — Educational Post: FVG (Fair Value Gap)",
        "https://www.tradingview.com/chart/BTCUSDT/ls1qkg1J-EDUCATIONAL-POST-FVG-Fair-Value-Gap/",
    ),
    "order_block": (
        "TradingView — Educational Series: What Is an Order Block (OB)?",
        "https://www.tradingview.com/chart/XAUUSD/M8FJGt2o-Educational-Series-What-Is-an-Order-Block-OB/",
    ),
    "breaker": (
        "TradingView — Market Concepts: Lesson 05 — Breaker Blocks",
        "https://www.tradingview.com/chart/BTCUSDT/GF9ddICw-Market-Concepts-Lesson-05-Breaker-Blocks/",
    ),
    "unicorn": (
        "TradingView — ICT Unicorn Model - The powerful Model",
        "https://www.tradingview.com/chart/DXY/VZbs9Ofu-ICT-Unicorn-Model-The-powerful-Model/",
    ),
    "smt": (
        "TradingView — SMT (Smart Money Technique) | Advanced Institutional Concept",
        "https://www.tradingview.com/chart/GOLD/QZNZVNUf-SMT-Smart-Money-Technique-Advanced-Institutional-Concept/",
    ),
    "timing": (
        "TradingView — Judas Swing | London Killzone | Optimal Trade Entry",
        "https://www.tradingview.com/chart/GBPUSD/ahxFLqq4-Judas-Swing-London-Killzone-Optimal-Trade-Entry-Explained/",
    ),
    "technical": (
        "TradingView — 7 Expert Risk Management Techniques for Trading",
        "https://www.tradingview.com/chart/BTCUSDT/20ywMQSe-7-Expert-Risk-Management-Techniques-for-Trading/",
    ),
}

    "bullish_engulfing": ("TradingView Support — Engulfing Bullish", "https://www.tradingview.com/support/solutions/43000583771-engulfing-bullish/"),
    "bearish_engulfing": ("TradingView Support — Engulfing Bearish", "https://www.tradingview.com/support/solutions/43000583769-engulfing-bearish/"),
    "doji": ("TradingView Support — Doji", "https://www.tradingview.com/support/solutions/43000583767-doji/"),
    "hammer": ("TradingView Support — Hammer Bullish", "https://www.tradingview.com/support/solutions/43000583775-hammer-bullish/"),
    "shooting_star": ("TradingView Support — Shooting Star Bearish", "https://www.tradingview.com/support/solutions/43000583789-shooting-star-bearish/"),
    "morning_star": ("TradingView Support — Morning Star Bullish", "https://www.tradingview.com/support/solutions/43000583787-morning-star-bullish/"),
    "evening_star": ("TradingView Support — Evening Star Bearish", "https://www.tradingview.com/support/solutions/43000583772-evening-star-bearish/"),
    "three_white_soldiers": ("TradingView Support — Three White Soldiers Bullish", "https://www.tradingview.com/support/solutions/43000583793-three-white-soldiers-bullish/"),
    "three_black_crows": ("TradingView Support — Three Black Crows Bearish", "https://www.tradingview.com/support/solutions/43000583792-three-black-crows-bearish/"),
    "inside_bar": ("TradingView Support — InSide Bar Strategy", "https://www.tradingview.com/support/solutions/43000591665-inside-bar-strategy/"),
    "tweezer_top": ("TradingView Support — Tweezer Top Bearish", "https://www.tradingview.com/support/solutions/43000592710-tweezer-top-bearish/"),
    "tweezer_bottom": ("TradingView Support — Tweezer Bottom Bullish", "https://www.tradingview.com/support/solutions/43000592709-tweezer-bottom-bullish/"),
    "marubozu": ("TradingView Support — Marubozu White/Black", "https://www.tradingview.com/support/solutions/43000583786-marubozu-white-bullish/"),
    "spinning_top": ("TradingView Support — Spinning Top White/Black", "https://www.tradingview.com/support/solutions/43000583790-spinning-top-white/"),
}

REMOTE_IMAGES = {
    "candlestick": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43635857165/original/-Ia8yAZJrCU4h3GbdUIpsOThy0H_d6CBTg.png?1785426335=",
    "bullish_engulfing": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140576863/original/FzSw1eshLDDK6tbAKjWAEcvsbGwV_P6I1g.png?1594035480=",
    "bearish_engulfing": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140575464/original/ADUJsusxPP04iHaA9Uw11EjW1h8V8TDKoA.png?1594035191=",
    "doji": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140574680/original/Xp7aOIXvJW7K5ISvRgpuU4JMEeANkdhHlA.png?1594035038=",
    "hammer": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140655364/original/OxDwofTwjzrB3U39MQIA84SBJEGSHqzsmw.png?1594049237=",
    "shooting_star": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140663222/original/CnuC4FilCeARVduBmClqt_AEBFTuc8K4Jg.png?1594050818=",
    "morning_star": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140663117/original/fBm54T9JW5iwHZKV1XXuGIgnCRu_Xwr1ig.png?1594050798=",
    "evening_star": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140577088/original/WWwb0D6fWZj4r9nl9cJ8fSqITe4dfgfBUQ.png?1594035521=",
    "three_white_soldiers": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140663547/original/nYiI0HB78VkeXFVHUm3FPHYH48RDA4LVLw.png?1594050904=",
    "three_black_crows": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140663635/original/Vv2TmQIXNaE2ATUZ7vrkDAixoWypa6kDmg.png?1594050919=",
    "structure": "https://s3.tradingview.com/j/JhztA6F9_mid.webp",
    "liquidity": "https://s3.tradingview.com/g/GXZP7v3b_mid.webp",
    "fvg": "https://s3.tradingview.com/l/ls1qkg1J_mid.webp",
    "order_block": "https://s3.tradingview.com/m/M8FJGt2o_mid.webp",
    "breaker": "https://s3.tradingview.com/g/GF9ddICw_mid.webp",
    "unicorn": "https://s3.tradingview.com/v/VZbs9Ofu_mid.webp",
    "smt": "https://s3.tradingview.com/q/QZNZVNUf_mid.webp",
    "timing": "https://s3.tradingview.com/a/ahxFLqq4_mid.webp",
    "technical": "https://s3.tradingview.com/2/20ywMQSe_mid.webp",
}

VISUAL_ALIASES = {
    "bullish engulfing":"bullish_engulfing","engulfing bullish":"bullish_engulfing",
    "bearish engulfing":"bearish_engulfing","engulfing bearish":"bearish_engulfing",
    "morning star":"morning_star","evening star":"evening_star",
    "three white soldiers":"three_white_soldiers","three black crows":"three_black_crows",
    "inside bar":"inside_bar","tweezer top":"tweezer_top","tweezer bottom":"tweezer_bottom",
    "shooting star":"shooting_star","hammer":"hammer","doji":"doji","marubozu":"marubozu","spinning top":"spinning_top",
    "fair value gap":"fvg","fvg":"fvg","imbalance":"fvg","ifvg":"fvg","bpr":"fvg",
    "order block":"order_block","orderblock":"order_block","mitigation block":"order_block","ob":"order_block",
    "breaker block":"breaker","breaker":"breaker","unicorn":"unicorn",
    "bos":"structure","choch":"structure","mss":"structure","market structure":"structure","swing high":"structure","swing low":"structure",
    "liquidity":"liquidity","bsl":"liquidity","ssl":"liquidity","sweep":"liquidity","equal high":"liquidity","equal low":"liquidity",
    "killzone":"timing","judas":"timing","silver bullet":"timing","amd":"timing","power of three":"timing","premium":"timing","discount":"timing","ote":"timing",
    "smt":"smt","smart money divergence":"smt","risk":"technical","rr":"technical","psychology":"technical",
    "candlestick":"candlestick","candlestick pattern":"candlestick",
}

def visual_key_for(term: str, category: str = "", context: str = "") -> str:
    text = f"{term} {category} {context}".lower()
    for token in sorted(VISUAL_ALIASES, key=len, reverse=True):
        if token in text:
            return VISUAL_ALIASES[token]
    if "cand" in text or "candle" in text:
        return "candlestick"
    if "structure" in text:
        return "structure"
    if "liquidity" in text:
        return "liquidity"
    return "technical"

def source_for_visual(key: str) -> Tuple[str, str]:
    return EDUCATION_SOURCES.get(key, EDUCATION_SOURCES["technical"])

def image_url_for_visual(key: str) -> str:
    return REMOTE_IMAGES.get(key, "")

def _font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()

def _rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def _candle(draw, x, top, bottom, body_top, body_bottom, up=True, scale=1.0):
    wick = (232, 239, 247)
    body = (39, 211, 176) if up else (255, 111, 125)
    draw.line((x, top, x, bottom), fill=wick, width=max(2, int(4*scale)))
    bw = max(14, int(34*scale))
    draw.rounded_rectangle((x-bw, body_top, x+bw, body_bottom), radius=max(4, int(8*scale)), fill=body)

def _base(title: str, subtitle: str, key: str, size=(1400, 800)):
    W, H = size
    img = Image.new("RGBA", (W, H), (7, 12, 20, 255))
    d = ImageDraw.Draw(img)
    # Subtle depth gradient.
    for y in range(H):
        t = y / max(1, H-1)
        c = (
            int(9 + 7*t),
            int(16 + 11*t),
            int(28 + 19*t),
            255,
        )
        d.line((0, y, W, y), fill=c)
    # Glow and frame.
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle((38, 38, W-38, H-38), radius=40, outline=(39,211,176,90), width=12)
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(glow)
    _rounded(d, (34, 34, W-34, H-34), 38, (13, 23, 35, 245), (39, 211, 176, 150), 2)
    d.text((74, 66), title, font=_font(42, True), fill=(234,242,247))
    d.text((76, 120), subtitle, font=_font(20), fill=(144,163,179))
    d.text((W-76, 72), key.upper(), font=_font(16, True), fill=(242,196,109), anchor="ra")
    return img, d

def visual_key_for(term: str, category: str = "", context: str = "") -> str:
    text = f"{term} {category} {context}".lower()
    for token, key in VISUAL_ALIASES.items():
        if token in text:
            return key
    if "cand" in text or "candle" in text:
        return "candlestick"
    if "time" in text or "session" in text:
        return "timing"
    if "risk" in text:
        return "risk"
    if "structure" in text:
        return "structure"
    if "liquidity" in text:
        return "liquidity"
    return "smc"

def source_for_visual(key: str) -> Tuple[str, str]:
    if key == "candlestick":
        return EDUCATION_SOURCES["candlestick"]
    if key in {"structure", "fvg", "order_block", "breaker", "unicorn"}:
        return EDUCATION_SOURCES["structure"]
    if key == "liquidity":
        return EDUCATION_SOURCES["liquidity"]
    if key == "timing":
        return EDUCATION_SOURCES["timing"]
    return EDUCATION_SOURCES["smc"]

def _candles_board(img, d, xs, base_y=630, scale=1.0, highlight=None):
    hi = [(700, 240, 410, 290, 520), (760, 260, 430, 310, 520), (830, 205, 380, 245, 510),
          (900, 170, 360, 205, 470), (980, 220, 380, 260, 500), (1060, 185, 345, 215, 450)]
    for i, (x, top, body_top, body_bottom, bottom) in enumerate(hi):
        _candle(d, x, top, bottom, body_top, body_bottom, up=(i % 3 != 1), scale=scale)
    if highlight:
        x1, y1, x2, y2 = highlight
        _rounded(d, (x1, y1, x2, y2), 18, (39,211,176,30), (39,211,176,190), 3)

def bundled_asset_for_visual(key: str):
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    folder = root / "education_sources"
    url = image_url_for_visual(key)
    if not url:
        return None
    target = folder / f"{key}{remote_extension(url)}"
    return target if target.exists() and target.stat().st_size > 5000 else None

def remote_extension(url: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix in {".png", ".jpg", ".jpeg", ".webp"} else ".bin"

def render_visual(path: Path, key: str, title: str, subtitle: str, size=(1400, 800)) -> Path:
    """Cache original external educational image bytes without re-encoding."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 5000:
        return path
    url = image_url_for_visual(key)
    if url:
        target = path.with_suffix(remote_extension(url))
        if target.exists() and target.stat().st_size > 5000:
            return target
        bundled = bundled_asset_for_visual(key)
        if bundled:
            target.write_bytes(bundled.read_bytes())
            return target
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "image/avif,image/webp,image/png,image/jpeg,*/*"})
        with urlopen(request, timeout=15) as response:
            payload = response.read()
        if len(payload) < 5000:
            raise ValueError("Remote source image is unexpectedly small")
        target.write_bytes(payload)
        if path != target and path.exists():
            path.unlink()
        return target

    # Unknown key: retain the legacy generated reference only as an unreachable safety fallback.
    img, d = _base(title, subtitle, key, size)
    W, H = size

    if key == "candlestick":
        _rounded(d, (80, 190, W-80, 695), 28, (18, 30, 44, 255), (39,56,74,255), 2)
        _candles_board(img, d, [])
        d.text((110, 235), "HIGH", font=_font(18, True), fill=(144,163,179))
        d.text((110, 640), "LOW", font=_font(18, True), fill=(144,163,179))
        d.text((1080, 260), "WICK", font=_font(18, True), fill=(242,196,109))
        d.line((1100, 292, 1064, 370), fill=(242,196,109), width=4)
        d.text((1090, 470), "BODY", font=_font(18, True), fill=(39,211,176))
        d.line((1110, 495, 1060, 480), fill=(39,211,176), width=4)
        d.text((90, 710), "OHLC is visualized by the candle body and wick.", font=_font(18), fill=(144,163,179))

    elif key == "structure":
        _rounded(d, (80, 190, W-80, 690), 28, (18,30,44,255), (39,56,74,255), 2)
        pts = [(130,560),(260,470),(390,530),(520,360),(660,445),(800,305),(930,380),(1080,250),(1240,315)]
        d.line(pts, fill=(99,167,255), width=8, joint="curve")
        for i,(x,y) in enumerate(pts):
            d.ellipse((x-9,y-9,x+9,y+9), fill=(234,242,247))
            label = ["L","H","L","HH","HL","HH","HL","HH","HL"][i]
            d.text((x, y-32), label, font=_font(18, True), fill=(242,196,109), anchor="mm")
        d.line((520,360,520,600), fill=(255,111,125), width=3)
        d.line((520,600,800,600), fill=(255,111,125), width=3)
        d.text((540, 610), "BOS / CHoCH", font=_font(22, True), fill=(255,111,125))
        d.text((90, 710), "Structure = a sequence of meaningful highs and lows.", font=_font(18), fill=(144,163,179))

    elif key == "liquidity":
        _rounded(d, (80, 190, W-80, 690), 28, (18,30,44,255), (39,56,74,255), 2)
        y=340
        d.line((110, y, 1260, y), fill=(242,196,109), width=5)
        d.text((110, y-50), "BUY-SIDE LIQUIDITY", font=_font(22, True), fill=(242,196,109))
        pts=[(140,600),(280,520),(420,545),(560,430),(700,475),(820,355),(930,400),(1040,270),(1200,345)]
        d.line(pts, fill=(99,167,255), width=7)
        d.line((1040,270,1090,180), fill=(255,111,125), width=7)
        d.line((1090,180,1160,300), fill=(255,111,125), width=7)
        d.text((940, 155), "SWEEP", font=_font(24, True), fill=(255,111,125))
        d.ellipse((1080,170,1100,190), fill=(255,111,125))
        d.text((110, 710), "A sweep is a price interaction with an obvious liquidity area.", font=_font(18), fill=(144,163,179))

    elif key == "order_block":
        _rounded(d, (80,190,W-80,690),28,(18,30,44,255),(39,56,74,255),2)
        _candles_board(img,d,[],highlight=(845,335,1080,565))
        d.text((850, 300), "ORDER BLOCK", font=_font(24, True), fill=(242,196,109))
        d.line((1085,450,1210,360), fill=(242,196,109), width=5)
        d.text((1100, 330), "reaction area", font=_font(18), fill=(144,163,179))
        d.text((90,710),"Track the zone around the origin of a strong displacement.",font=_font(18),fill=(144,163,179))

    elif key == "fvg":
        _rounded(d, (80,190,W-80,690),28,(18,30,44,255),(39,56,74,255),2)
        _candle(d, 320, 310, 620, 395, 545, up=False, scale=1.2)
        _candle(d, 540, 250, 580, 300, 500, up=True, scale=1.2)
        _candle(d, 760, 215, 530, 270, 465, up=True, scale=1.2)
        _rounded(d, (575,310,725,465),20,(39,211,176,30),(39,211,176,190),3)
        d.text((600,265),"FVG",font=_font(28,True),fill=(39,211,176))
        d.text((90,710),"An imbalance zone between neighboring price ranges.",font=_font(18),fill=(144,163,179))

    elif key == "breaker":
        _rounded(d, (80,190,W-80,690),28,(18,30,44,255),(39,56,74,255),2)
        d.line((130,410,1260,410),fill=(242,196,109),width=18)
        d.text((135,350),"FORMER SUPPORT / RESISTANCE",font=_font(18,True),fill=(242,196,109))
        d.line([(240,300),(520,470),(700,380),(910,520),(1120,440)],fill=(99,167,255),width=8,joint="curve")
        d.text((740,525),"ROLE FLIP",font=_font(28,True),fill=(255,111,125))
        d.text((90,710),"A breaker tracks a failed zone after its role changes.",font=_font(18),fill=(144,163,179))

    elif key == "pd":
        _rounded(d,(80,190,W-80,690),28,(18,30,44,255),(39,56,74,255),2)
        d.rectangle((180,250,1180,620),fill=(27,44,61),outline=(39,56,74))
        mid=435
        d.line((180,mid,1180,mid),fill=(242,196,109),width=4)
        d.text((620,280),"PREMIUM",font=_font(25,True),fill=(255,111,125))
        d.text((625,540),"DISCOUNT",font=_font(25,True),fill=(39,211,176))
        d.text((635,414),"EQUILIBRIUM 50%",font=_font(20,True),fill=(242,196,109))
        d.rounded_rectangle((500,370,900,445),radius=26,outline=(99,167,255),width=5)
        d.text((605,386),"OTE / VALUE AREA",font=_font(18,True),fill=(99,167,255))
        d.text((90,710),"Premium/discount frames location inside a defined dealing range.",font=_font(18),fill=(144,163,179))

    elif key == "timing":
        _rounded(d,(80,190,W-80,690),28,(18,30,44,255),(39,56,74,255),2)
        blocks=[("ASIA",180,360),("LONDON",430,650),("NEW YORK",720,970),("OVERLAP",1010,1230)]
        for label,x1,x2 in blocks:
            _rounded(d,(x1,330,x2,470),22,(27,43,58,255),(39,211,176,100),2)
            d.text(((x1+x2)//2,400),label,font=_font(24,True),fill=(234,242,247),anchor="mm")
        d.text((180,540),"DEFINE WINDOW",font=_font(18,True),fill=(242,196,109))
        d.text((90,710),"Timing models require a fixed, pre-defined session window.",font=_font(18),fill=(144,163,179))

    elif key == "unicorn":
        _rounded(d,(80,190,W-80,690),28,(18,30,44,255),(39,56,74,255),2)
        _rounded(d,(360,300,900,540),28,(39,211,176,22),(39,211,176,170),4)
        _rounded(d,(440,330,820,510),22,(99,167,255,18),(99,167,255,160),4)
        d.text((560,370),"BREAKER",font=_font(30,True),fill=(242,196,109))
        d.text((585,430),"+ FVG",font=_font(32,True),fill=(39,211,176))
        d.text((90,710),"The Unicorn model is commonly presented as overlapping breaker + FVG context.",font=_font(18),fill=(144,163,179))

    elif key == "smt":
        _rounded(d,(80,190,W-80,690),28,(18,30,44,255),(39,56,74,255),2)
        d.text((140,235),"ASSET A",font=_font(22,True),fill=(99,167,255))
        d.text((740,235),"ASSET B",font=_font(22,True),fill=(39,211,176))
        a=[(140,590),(300,500),(460,550),(620,420),(780,470),(940,350),(1100,390)]
        b=[(140,570),(300,490),(460,515),(620,445),(780,500),(940,410),(1100,430)]
        d.line(a,fill=(99,167,255),width=7,joint="curve"); d.line(b,fill=(39,211,176),width=7,joint="curve")
        d.line((940,350,940,410),fill=(242,196,109),width=5)
        d.text((900,270),"DIVERGENCE",font=_font(22,True),fill=(242,196,109))
        d.text((90,710),"SMT divergence compares related instruments for relative strength/difference.",font=_font(18),fill=(144,163,179))

    elif key == "risk":
        _rounded(d,(80,190,W-80,690),28,(18,30,44,255),(39,56,74,255),2)
        values=[0,1,2,3,4,5]
        x=180; y0=580
        bars=[90,130,170,120,210,155]
        for i,b in enumerate(bars):
            d.rounded_rectangle((x+i*160,y0-b,x+i*160+80,y0),radius=12,fill=(39,211,176) if i<3 else (255,111,125))
        d.text((160,235),"FIXED RISK",font=_font(28,True),fill=(242,196,109))
        d.text((160,285),"SIZE -> STOP -> R:R",font=_font(22,True),fill=(234,242,247))
        d.text((90,710),"Use explicit risk rules, invalidation and position sizing.",font=_font(18),fill=(144,163,179))

    else:
        _rounded(d,(80,190,W-80,690),28,(18,30,44,255),(39,56,74,255),2)
        _candles_board(img,d,[])
        d.text((90,710),"Context matters: structure, liquidity, displacement and reaction.",font=_font(18),fill=(144,163,179))

    img.convert("RGB").save(path, "JPEG", quality=88, optimize=True, progressive=True)
    return path
