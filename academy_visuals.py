from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import sys

USER_AGENT = "TraderPlannerPro/7.8.0 (+https://github.com/shmm66/desktop-tutorial)"

# Each visual key has one specific source page and one exact source image.
# The app never draws tags on these source images. It only resizes them for display.
EDUCATION_SOURCES: Dict[str, Tuple[str, str]] = {
    "smc_overview": (
        "TradingView — (XAU/USD) Smart Money Concepts | Market Structure & Liquidity",
        "https://www.tradingview.com/chart/XAUUSD/GsHdsZeJ-XAU-USD-Smart-Money-Concepts-Market-Structure-Liquidity/",
    ),
    "smc_liquidity": (
        "TradingView — Liquidity Sweep Setup | MSS + FVG + Order Block",
        "https://www.tradingview.com/chart/GOLD/GXZP7v3b-Liquidity-Sweep-Setup-MSS-FVG-Order-Block/",
    ),
    "ict_2022": (
        "TradingView — JSONFX - ICT 2022 Model",
        "https://www.tradingview.com/script/WPpilwER-JSONFX-ICT-2022-Model/",
    ),
    "ict_silver_bullet": (
        "TradingView — ICT Silver Bullet",
        "https://www.tradingview.com/script/yxRodYFg-ICT-Silver-Bullet/",
    ),
    "ict_amd": (
        "TradingView — Power of Three (AMD) Map",
        "https://www.tradingview.com/script/ct19Gmwe-Power-of-Three-AMD-Map-AGPro-Series/",
    ),
    "ict_judas": (
        "TradingView — What is an ICT Judas Swing?",
        "https://www.tradingview.com/chart/EURJPY/nJa2FjKR-What-is-an-ICT-Judas-Swing/",
    ),
    "ict_ote": (
        "TradingView — OTE optimal trade entry (ICT); visible chart only: Dynamic",
        "https://www.tradingview.com/script/yLKbFuXN-OTE-optimal-trade-entry-ICT-visible-chart-only-Dynamic/",
    ),
    "order_block": (
        "TradingView — Educational Series: What Is an Order Block (OB)?",
        "https://www.tradingview.com/chart/XAUUSD/M8FJGt2o-Educational-Series-What-Is-an-Order-Block-OB/",
    ),
    "fvg": (
        "TradingView — Educational Post: FVG (Fair Value Gap)",
        "https://www.tradingview.com/chart/BTCUSDT/ls1qkg1J-EDUCATIONAL-POST-FVG-Fair-Value-Gap/",
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
    "candlestick": (
        "TradingView Support — Introduction to Candlestick Charts and Patterns",
        "https://www.tradingview.com/support/solutions/43000745269-introduction-to-candlestick-charts-and-patterns/",
    ),
    "bullish_engulfing": (
        "TradingView Support — Engulfing Bullish",
        "https://www.tradingview.com/support/solutions/43000583771-engulfing-bullish/",
    ),
    "bearish_engulfing": (
        "TradingView Support — Engulfing Bearish",
        "https://www.tradingview.com/support/solutions/43000583769-engulfing-bearish/",
    ),
    "doji": (
        "TradingView Support — Doji",
        "https://www.tradingview.com/support/solutions/43000583767-doji/",
    ),
    "hammer": (
        "TradingView Support — Hammer Bullish",
        "https://www.tradingview.com/support/solutions/43000583775-hammer-bullish/",
    ),
    "shooting_star": (
        "TradingView Support — Shooting Star Bearish",
        "https://www.tradingview.com/support/solutions/43000583789-shooting-star-bearish/",
    ),
    "morning_star": (
        "TradingView Support — Morning Star Bullish",
        "https://www.tradingview.com/support/solutions/43000583787-morning-star-bullish/",
    ),
    "evening_star": (
        "TradingView Support — Evening Star Bearish",
        "https://www.tradingview.com/support/solutions/43000583772-evening-star-bearish/",
    ),
    "tweezer_top": (
        "TradingView Support — Tweezer Top Bearish",
        "https://www.tradingview.com/support/solutions/43000592710-tweezer-top-bearish/",
    ),
    "tweezer_bottom": (
        "TradingView Support — Tweezer Bottom Bullish",
        "https://www.tradingview.com/support/solutions/43000592709-tweezer-bottom-bullish/",
    ),
    "three_white_soldiers": (
        "TradingView Support — Three White Soldiers Bullish",
        "https://www.tradingview.com/support/solutions/43000583793-three-white-soldiers-bullish/",
    ),
    "three_black_crows": (
        "TradingView Support — Three Black Crows Bearish",
        "https://www.tradingview.com/support/solutions/43000583792-three-black-crows-bearish/",
    ),
    "marubozu": (
        "TradingView Support — Marubozu White Bullish",
        "https://www.tradingview.com/support/solutions/43000583786-marubozu-white-bullish/",
    ),
    "spinning_top": (
        "TradingView Support — Spinning Top Black",
        "https://www.tradingview.com/support/solutions/43000583791-spinning-top-black/",
    ),
    "long_legged_doji": (
        "TradingView Support — Doji / Long-Legged Doji family",
        "https://www.tradingview.com/support/solutions/43000583767-doji/",
    ),
    "technical": (
        "TradingView — 7 Expert Risk Management Techniques for Trading",
        "https://www.tradingview.com/chart/BTCUSDT/20ywMQSe-7-Expert-Risk-Management-Techniques-for-Trading/",
    ),
}

REMOTE_IMAGES: Dict[str, str] = {
    "smc_overview": "https://s3.tradingview.com/g/GsHdsZeJ_mid.webp",
    "smc_liquidity": "https://s3.tradingview.com/g/GXZP7v3b_mid.webp",
    "ict_2022": "https://s3.tradingview.com/w/WPpilwER_mid.webp?v=1781278974",
    "ict_silver_bullet": "https://s3.tradingview.com/y/yxRodYFg_mid.webp",
    "ict_amd": "https://s3.tradingview.com/c/ct19Gmwe_mid.webp?v=1782410560",
    "ict_judas": "https://s3.tradingview.com/n/nJa2FjKR_mid.webp",
    "ict_ote": "https://s3.tradingview.com/y/yLKbFuXN_mid.webp?v=1672863647",
    "order_block": "https://s3.tradingview.com/m/M8FJGt2o_mid.webp",
    "fvg": "https://s3.tradingview.com/l/ls1qkg1J_mid.webp",
    "breaker": "https://s3.tradingview.com/g/GF9ddICw_mid.webp",
    "unicorn": "https://s3.tradingview.com/v/VZbs9Ofu_mid.webp",
    "smt": "https://s3.tradingview.com/q/QZNZVNUf_mid.webp",
    "timing": "https://s3.tradingview.com/a/ahxFLqq4_mid.webp",
    "candlestick": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43635857165/original/-Ia8yAZJrCU4h3GbdUIpsOThy0H_d6CBTg.png?1785426335=",
    "bullish_engulfing": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140576863/original/FzSw1eshLDDK6tbAKjWAEcvsbGwV_P6I1g.png?1594035480=",
    "bearish_engulfing": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140575464/original/ADUJsusxPP04iHaA9Uw11EjW1h8V8TDKoA.png?1594035191=",
    "doji": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140574680/original/Xp7aOIXvJW7K5ISvRgpuU4JMEeANkdhHlA.png?1594035038=",
    "hammer": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140655364/original/OxDwofTwjzrB3U39MQIA84SBJEGSHqzsmw.png?1594049237=",
    "shooting_star": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140663222/original/CnuC4FilCeARVduBmClqt_AEBFTuc8K4Jg.png?1594050818=",
    "morning_star": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140663117/original/fBm54T9JW5iwHZKV1XXuGIgnCRu_Xwr1ig.png?1594050798=",
    "evening_star": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140577088/original/WWwb0D6fWZj4r9nl9cJ8fSqITe4dfgfBUQ.png?1594035521=",
    "tweezer_top": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43154904284/original/ZzNHsnqYXL7FHbMUbbFptBrXpZ59jJ70fg.png?1599140098=",
    "tweezer_bottom": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43154904006/original/gIM6m6P0cZSwOXhAmdiKEyoFN9v5k7vEpw.png?1599140049=",
    "three_white_soldiers": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140663547/original/nYiI0HB78VkeXFVHUm3FPHYH48RDA4LVLw.png?1594050904=",
    "three_black_crows": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140663635/original/Vv2TmQIXNaE2ATUZ7vrkDAixoWypa6kDmg.png?1594050919=",
    "marubozu": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140663051/original/ZxnIiMHC0Vw_HnBXm4xzx5P5Vub9plAlhg.png?1594050779=",
    "spinning_top": "https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43140663458/original/2j7_Xg1lX8wWwETjmQSa4X1VlxmpPYXk7A.png?1594050885=",
    "long_legged_doji": "https://s3.tradingview.com/4/48g0fJv6_mid.webp",
    "technical": "https://s3.tradingview.com/2/20ywMQSe_mid.webp",
}

STRATEGY_VISUALS = {
    "liquidity sweep + bos": "smc_liquidity",
    "order block + fvg retest": "order_block",
    "breaker block reclaim": "breaker",
    "choch/mss + fvg reversal": "smc_liquidity",
    "liquidity + displacement + retest": "smc_liquidity",
    "ict 2022 model": "ict_2022",
    "ict silver bullet": "ict_silver_bullet",
    "ict unicorn model": "unicorn",
    "power of three (amd)": "ict_amd",
    "judas swing / killzone reversal": "ict_judas",
    "ict ote / premium-discount framework": "ict_ote",
    "smt divergence": "smt",
}

# Exact concept maps. These are intentionally specific so a glossary term does not
# silently inherit a visually unrelated chart.
GLOSSARY_VISUALS = {
    "market structure": "smc_overview",
    "higher high": "smc_overview", "higher low": "smc_overview", "lower high": "smc_overview", "lower low": "smc_overview",
    "swing high": "smc_overview", "swing low": "smc_overview", "bos": "smc_overview", "choch": "smc_overview", "mss": "smc_overview",
    "external structure": "smc_overview", "internal structure": "smc_overview", "displacement": "smc_overview",
    "liquidity": "smc_liquidity", "buy-side liquidity": "smc_liquidity", "sell-side liquidity": "smc_liquidity",
    "liquidity pool": "smc_liquidity", "liquidity sweep": "smc_liquidity", "liquidity raid": "smc_liquidity",
    "equal highs": "smc_liquidity", "equal lows": "smc_liquidity", "session high/low": "smc_liquidity",
    "previous day high": "smc_liquidity", "previous day low": "smc_liquidity", "draw on liquidity": "smc_liquidity",
    "order block (bullish)": "order_block", "order block (bearish)": "order_block", "order block": "order_block", "mitigation block": "order_block",
    "breaker block": "breaker", "fair value gap": "fvg", "inverse fair value gap": "fvg", "balanced price range": "fvg",
    "ote": "ict_ote", "fibonacci 62%-79%": "ict_ote", "premium/discount array": "ict_ote",
    "killzone": "timing", "asian killzone": "timing", "london killzone": "timing", "new york killzone": "timing",
    "judas swing": "ict_judas", "silver bullet": "ict_silver_bullet", "2022 model": "ict_2022",
    "power of three / amd": "ict_amd", "accumulation": "ict_amd", "manipulation": "ict_amd", "distribution": "ict_amd",
    "unicorn model": "unicorn", "smt divergence": "smt", "correlation": "smt",
    "candle": "candlestick", "pin bar": "candlestick", "inside bar": "candlestick", "doji": "doji",
    "hammer": "hammer", "shooting star": "shooting_star", "morning star": "morning_star", "evening star": "evening_star",
    "tweezer top": "tweezer_top", "tweezer bottom": "tweezer_bottom", "three white soldiers": "three_white_soldiers",
    "three black crows": "three_black_crows", "marubozu": "marubozu", "spinning top": "spinning_top", "long-legged doji": "long_legged_doji",
    "bullish engulfing": "bullish_engulfing", "bearish engulfing": "bearish_engulfing", "engulfing": "candlestick",
}

# Backward-compatible semantic aliases used by older content/tests.
EDUCATION_SOURCES.update({
    "structure": EDUCATION_SOURCES["smc_overview"],
    "liquidity": EDUCATION_SOURCES["smc_liquidity"],
})
REMOTE_IMAGES.update({
    "structure": REMOTE_IMAGES["smc_overview"],
    "liquidity": REMOTE_IMAGES["smc_liquidity"],
    "timing": REMOTE_IMAGES["ict_judas"],
})
 
PATTERN_VISUALS = {
    "pin bar / rejection candle": "candlestick",
    "bullish engulfing": "bullish_engulfing",
    "bearish engulfing": "bearish_engulfing",
    "inside bar": "candlestick",
    "morning star": "morning_star",
    "evening star": "evening_star",
    "hammer": "hammer",
    "shooting star": "shooting_star",
    "doji": "doji",
    "tweezer top": "tweezer_top",
    "tweezer bottom": "tweezer_bottom",
    "three white soldiers": "three_white_soldiers",
    "three black crows": "three_black_crows",
    "marubozu": "marubozu",
    "spinning top": "spinning_top",
    "long-legged doji": "long_legged_doji",
}


def strategy_visual_key(name: str) -> str:
    value = str(name).strip().lower()
    if value and value[0].isdigit() and ")" in value:
        value = value.split(")", 1)[1].strip()
    return STRATEGY_VISUALS.get(value, "smc_overview")


def pattern_visual_key(name: str) -> str:
    return PATTERN_VISUALS.get(str(name).strip().lower(), "candlestick")


def glossary_visual_key(term: str, category: str = "", context: str = "") -> str:
    text = " ".join(str(x or "") for x in (term, category, context)).strip().lower()
    # Specific/named ICT concepts must win before generic keywords like "liquidity".
    for token, key in sorted(GLOSSARY_VISUALS.items(), key=lambda kv: len(kv[0]), reverse=True):
        if token in text:
            return key
    # Exact family fallbacks, only when they are semantically safe.
    if "candlestick" in text or "candle" in text:
        return "candlestick"
    if "risk" in text:
        return "technical"
    return "smc_overview"


def visual_key_for(term: str, category: str = "", context: str = "") -> str:
    return glossary_visual_key(term, category, context)


def source_for_visual(key: str) -> Tuple[str, str]:
    return EDUCATION_SOURCES.get(key, EDUCATION_SOURCES["smc_overview"])


def image_url_for_visual(key: str) -> str:
    return REMOTE_IMAGES.get(key, "")


def remote_extension(url: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix in {".png", ".jpg", ".jpeg", ".webp"} else ".bin"


def bundled_asset_for_visual(key: str):
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    folder = root / "education_sources"
    url = image_url_for_visual(key)
    if not url:
        return None
    target = folder / f"{key}{remote_extension(url)}"
    return target if target.exists() and target.stat().st_size > 5000 else None


def render_visual(path: Path, key: str, title: str = "", subtitle: str = "", size=(1400, 800)) -> Path:
    """Return an exact source image path without adding labels or re-encoding it."""
    _ = title, subtitle, size
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    url = image_url_for_visual(key)
    if not url:
        raise ValueError(f"No exact educational visual is mapped for '{key}'")
    target = path.with_suffix(remote_extension(url))

    if target.exists() and target.stat().st_size > 5000:
        return target

    bundled = bundled_asset_for_visual(key)
    if bundled:
        target.write_bytes(bundled.read_bytes())
        return target

    request = Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "image/avif,image/webp,image/png,image/jpeg,*/*"},
    )
    with urlopen(request, timeout=20) as response:
        payload = response.read()
    if len(payload) < 5000:
        raise ValueError(f"Remote source image is unexpectedly small for '{key}'")
    target.write_bytes(payload)
    if path != target and path.exists():
        path.unlink()
    return target
