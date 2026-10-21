"""Practical local trading coach with optional, user-triggered OpenAI analysis.

Importing this module never starts network activity. Journal analysis is local and
deterministic; the cloud endpoint is only called when the user explicitly submits
a question and has configured an API key.
"""
from __future__ import annotations

import base64
import ctypes
import json
import os
import urllib.error
import urllib.request
from math import isfinite

from journal_agent import analyse_journal

DEFAULT_MODEL = "gpt-6.1-sol"


def seal_api_key(api_key: str) -> str:
    """Encrypt a key with Windows DPAPI; mark non-Windows development fallback."""
    key = str(api_key or "").strip()
    if not key:
        return ""
    if os.name != "nt":
        # The production app is Windows-only. This prefix prevents a development
        # fallback from being mistaken for OS-backed encryption.
        return "local-plain:" + key
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

    raw = key.encode("utf-8")
    source = ctypes.create_string_buffer(raw)
    input_blob = DATA_BLOB(len(raw), ctypes.cast(source, ctypes.POINTER(ctypes.c_ubyte)))
    output_blob = DATA_BLOB()
    crypt32 = ctypes.WinDLL("Crypt32.dll", use_last_error=True)
    kernel32 = ctypes.WinDLL("Kernel32.dll", use_last_error=True)
    crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(DATA_BLOB), wintypes.LPCWSTR, ctypes.POINTER(DATA_BLOB),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(DATA_BLOB),
    ]
    crypt32.CryptProtectData.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    ok = crypt32.CryptProtectData(
        ctypes.byref(input_blob), "Trader Planner Pro OpenAI key",
        None, None, None, 1, ctypes.byref(output_blob)
    )
    if not ok:
        raise OSError(ctypes.get_last_error(), "Windows could not encrypt the API key.")
    try:
        encrypted = ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(output_blob.pbData, ctypes.c_void_p))
    return "dpapi:" + base64.b64encode(encrypted).decode("ascii")


def unseal_api_key(stored: str) -> str:
    """Decrypt the saved user-scoped Windows key, or read a marked dev fallback."""
    value = str(stored or "")
    if not value:
        return ""
    if value.startswith("local-plain:"):
        return value[len("local-plain:"):]
    if not value.startswith("dpapi:"):
        # Backward compatibility with a key previously stored as plain text.
        return value
    if os.name != "nt":
        return ""
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

    raw = base64.b64decode(value[len("dpapi:"):], validate=True)
    source = ctypes.create_string_buffer(raw)
    input_blob = DATA_BLOB(len(raw), ctypes.cast(source, ctypes.POINTER(ctypes.c_ubyte)))
    output_blob = DATA_BLOB()
    description = ctypes.c_wchar_p()
    crypt32 = ctypes.WinDLL("Crypt32.dll", use_last_error=True)
    kernel32 = ctypes.WinDLL("Kernel32.dll", use_last_error=True)
    crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(DATA_BLOB), ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(DATA_BLOB),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(DATA_BLOB),
    ]
    crypt32.CryptUnprotectData.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    ok = crypt32.CryptUnprotectData(
        ctypes.byref(input_blob), ctypes.byref(description),
        None, None, None, 1, ctypes.byref(output_blob)
    )
    if not ok:
        raise OSError(ctypes.get_last_error(), "The saved API key could not be decrypted for this Windows user.")
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData).decode("utf-8")
    finally:
        kernel32.LocalFree(ctypes.cast(output_blob.pbData, ctypes.c_void_p))
        if description:
            kernel32.LocalFree(ctypes.cast(description, ctypes.c_void_p))


def _fmt(value, digits=2):
    try:
        number = float(value)
        if not isfinite(number):
            return "N/A"
        return f"{number:+.{digits}f}" if digits == 2 else f"{number:.{digits}f}"
    except (TypeError, ValueError, OverflowError):
        return "N/A"


def _top_group(groups, field="net_r", smallest=False):
    candidates = [g for g in (groups or []) if g.get("name") != "Unspecified" and g.get("count", 0) >= 2]
    if not candidates:
        return None
    return sorted(candidates, key=lambda g: (g.get(field, 0), -g.get("count", 0)), reverse=not smallest)[0]


def local_response(question: str, rows, profile: dict | None = None, goals=None,
                   plan_fields=None, market: str = "Crypto", language: str = "en") -> str:
    """Produce a practical, auditable coaching response from saved local data."""
    fa = str(language).lower().startswith("fa")
    profile = profile or {}
    goals = [g for g in (goals or profile.get("goals", [])) if isinstance(g, dict)]
    plan_fields = plan_fields or profile.get("plan_draft", {})
    metrics = analyse_journal(rows or [])
    q = str(question or "").strip().lower()
    name = str(profile.get("name") or ("پروفایل فعال" if fa else "Active profile"))

    if not rows:
        if fa:
            answer = (
                f"پروفایل «{name}» در بازار {market} هنوز معامله ثبت‌شده‌ای ندارد. "
                "برای تحلیل شخصی‌سازی‌شده، در ژورنال تاریخ، نماد، نتیجه برحسب R، ستاپ، سشن و اشتباه احتمالی را ثبت کن. "
                "تا وقتی داده وجود ندارد، نرخ برد یا مزیت آماری قابل استنتاج نیست."
            )
        else:
            answer = (
                f"Profile “{name}” has no saved {market} trades yet. "
                "For evidence-based coaching, record date, symbol, result in R, setup, session, and any execution mistake. "
                "Without trade data, win rate and statistical edge cannot be inferred."
            )
    else:
        count = metrics["count"]
        wr = metrics["win_rate"]
        net = metrics["net_r"]
        exp = metrics["expectancy_r"]
        pf = metrics["profit_factor"]
        dd = metrics["max_drawdown_r"]
        missing = metrics["missing_r_count"]
        worst_setup = _top_group(metrics["by_setup"], "avg_r", smallest=True)
        best_setup = _top_group(metrics["by_setup"], "avg_r", smallest=False)
        weak_session = _top_group(metrics["by_session"], "avg_r", smallest=True)
        if best_setup and worst_setup and best_setup.get("name") == worst_setup.get("name"):
            worst_setup = None
        mistakes = metrics["mistakes"][:3]
        if fa:
            lines = [
                f"بررسی محلی ژورنال {name} — بازار {market}",
                f"نمونه: {count} معامله | نرخ برد: {wr:.1f}% | خالص: {net:+.2f}R | امید ریاضی: {exp:+.2f}R/معامله",
                f"Profit Factor: {_fmt(pf, 2)} | بیشترین افت از اوج: {dd:.2f}R | معاملات بدون مقدار R: {missing}",
            ]
            if exp < 0:
                lines.append("نکته اصلی: امید ریاضی نمونه فعلی منفی است. پیش از افزایش حجم، اجرای قوانین و تفکیک نتایج ستاپ‌ها را بررسی کن.")
            elif exp > 0:
                lines.append("نکته اصلی: امید ریاضی این نمونه مثبت است؛ این به‌تنهایی تضمین عملکرد آینده نیست. اندازه نمونه، کارمزد و کیفیت ثبت را بررسی کن.")
            else:
                lines.append("نکته اصلی: در نمونه فعلی امید ریاضی نزدیک صفر است؛ هزینه‌ها و کیفیت ثبت ممکن است نتیجه را تغییر دهند.")
            if best_setup:
                lines.append(f"ستاپ با میانگین R بهتر در گروه‌های دارای حداقل ۲ معامله: {best_setup['name']} ({best_setup['avg_r']:+.2f}R در هر معامله؛ n={best_setup['count']}).")
            if worst_setup:
                lines.append(f"ستاپ نیازمند بازبینی: {worst_setup['name']} ({worst_setup['avg_r']:+.2f}R در هر معامله؛ n={worst_setup['count']}).")
            if weak_session:
                lines.append(f"سشن نیازمند بررسی: {weak_session['name']} ({weak_session['avg_r']:+.2f}R در هر معامله؛ n={weak_session['count']}).")
            if mistakes:
                lines.append("اشتباهات ثبت‌شده پرتکرار: " + "، ".join(f"{m} ({n})" for m, n in mistakes) + ".")
            if goals:
                due = sum(1 for g in goals if str(g.get("end_date", "")) < __import__("datetime").date.today().isoformat()
                          and float(g.get("progress", 0) or 0) < float(g.get("target", 1) or 1))
                lines.append(f"هدف‌های ثبت‌شده: {len(goals)} مورد؛ عقب‌افتاده: {due}.")
            if missing:
                lines.append("اقدام فوری: نتیجه برحسب R را برای معاملات ناقص ثبت کن؛ ردیف‌های ناقص در جمع بازده به‌صورت صفر گزارش می‌شوند.")
            if any(x in q for x in ("ریسک", "risk", "حد ضرر", "استاپ", "leverage", "اهرم", "حجم")):
                lines.append("کنترل ریسک: مبلغ ریسک را پیش از ورود ثابت کن، حجم را از فاصله واقعی حد ضرر به‌دست بیاور و بعد از ضرر حد ریسک را افزایش نده.")
            elif any(x in q for x in ("روان", "psych", "fomo", "انتقام", "revenge", "ترس")):
                lines.append("تمرین روانشناسی: پیش از سفارش یک چک‌لیست کوتاه انجام بده؛ اگر دلیل ورود، ابطال و ریسک را در یک جمله نمی‌توانی بیان کنی، معامله را رد کن.")
            elif any(x in q for x in ("هدف", "goal", "برنامه", "plan", "پلن")):
                lines.append("اقدام برای هدف‌ها: برای هر هدف معیار قابل‌شمارش، تاریخ پایان و حداقل اقدام روزانه بنویس؛ پیشرفت را از نتیجه سود جدا نگه دار.")
            else:
                lines.append("قدم بعدی: یک متغیر را انتخاب کن (ستاپ، سشن یا خطای اجرا)، قوانین دسته‌بندی را ثابت نگه دار و نمونه بعدی را جداگانه دنبال کن.")
            answer = "\n".join(lines)
        else:
            lines = [
                f"Local journal review — {name} / {market}",
                f"Sample: {count} trades | win rate: {wr:.1f}% | net: {net:+.2f}R | expectancy: {exp:+.2f}R/trade",
                f"Profit factor: {_fmt(pf)} | max peak-to-trough drawdown: {dd:.2f}R | rows missing R: {missing}",
            ]
            if exp < 0:
                lines.append("Main finding: expectancy is negative in this sample. Review rule compliance and setup-level results before increasing size.")
            elif exp > 0:
                lines.append("Main finding: this sample has positive expectancy, which does not guarantee future performance. Check sample size, fees, and recording quality.")
            else:
                lines.append("Main finding: expectancy is approximately flat in this sample; costs and logging quality can change the outcome.")
            if best_setup:
                lines.append(f"Stronger setup group (at least 2 trades): {best_setup['name']} ({best_setup['avg_r']:+.2f}R/trade; n={best_setup['count']}).")
            if worst_setup:
                lines.append(f"Setup to review: {worst_setup['name']} ({worst_setup['avg_r']:+.2f}R/trade; n={worst_setup['count']}).")
            if weak_session:
                lines.append(f"Session to review: {weak_session['name']} ({weak_session['avg_r']:+.2f}R/trade; n={weak_session['count']}).")
            if mistakes:
                lines.append("Most-recorded mistakes: " + ", ".join(f"{m} ({n})" for m, n in mistakes) + ".")
            if goals:
                from datetime import date
                due = sum(1 for g in goals if str(g.get("end_date", "")) < date.today().isoformat()
                          and float(g.get("progress", 0) or 0) < float(g.get("target", 1) or 1))
                lines.append(f"Saved goals: {len(goals)}; overdue: {due}.")
            if missing:
                lines.append("Immediate action: complete the missing R results; rows without R are counted as zero in return calculations.")
            if any(x in q for x in ("risk", "stop", "leverage", "position size", "sizing")):
                lines.append("Risk control: set monetary risk before entry, derive position size from actual stop distance, and never increase the risk limit immediately after a loss.")
            elif any(x in q for x in ("psych", "fomo", "revenge", "fear", "discipline")):
                lines.append("Psychology drill: use a short pre-trade checklist; if you cannot state the entry reason, invalidation, and risk in one sentence, skip the trade.")
            elif any(x in q for x in ("goal", "plan", "routine", "schedule")):
                lines.append("Goal action: define a measurable result, an end date, and a small daily action for each goal; track execution separately from P&L.")
            else:
                lines.append("Next step: choose one variable—setup, session, or execution error—keep the classification rules fixed, and track the next sample separately.")
            answer = "\n".join(lines)

    # Prefer advice from explicit Trading Plan fields when those fields exist.
    filled_plan = [(str(k), str(v).strip()) for k, v in (plan_fields or {}).items() if str(v or "").strip()]
    if filled_plan and any(x in q for x in ("plan", "پلن", "rule", "قانون", "strategy", "استراتژی")):
        if fa:
            answer += "\n\nپلن ذخیره‌شده: " + "؛ ".join(f"{k}: {v[:160]}" for k, v in filled_plan[:4])
        else:
            answer += "\n\nSaved plan fields: " + "; ".join(f"{k}: {v[:160]}" for k, v in filled_plan[:4])
    return answer


def build_ai_context(question: str, rows, profile: dict | None = None, market: str = "Crypto") -> str:
    """Create a compact context using journal-derived statistics, not credentials."""
    profile = profile or {}
    rows = [r for r in (rows or []) if isinstance(r, dict)]
    stats = analyse_journal(rows)
    safe_rows = []
    for row in rows[-25:]:
        safe_rows.append({
            "date": str(row.get("Date", ""))[:10],
            "symbol": str(row.get("Symbol", ""))[:24],
            "result_r": str(row.get("Result (R)", ""))[:20],
            "setup": str(row.get("Setup", ""))[:60],
            "session": str(row.get("Session", ""))[:30],
            "mistake": str(row.get("Mistake", ""))[:80],
        })
    return json.dumps({
        "question": str(question)[:4000],
        "market": str(market)[:20],
        "profile_name": str(profile.get("name", "Active profile"))[:80],
        "journal_metrics": {k: stats[k] for k in (
            "count", "wins", "losses", "breakeven", "win_rate", "net_r",
            "expectancy_r", "avg_win_r", "avg_loss_r", "profit_factor",
            "max_drawdown_r", "max_losing_streak", "missing_r_count",
            "by_setup", "by_session", "by_emotion", "mistakes",
        )},
        "recent_journal_rows": safe_rows,
        "goals": [
            {key: g.get(key) for key in ("period", "title", "start_date", "end_date", "target", "progress", "unit")}
            for g in profile.get("goals", []) if isinstance(g, dict)
        ],
    }, ensure_ascii=False, default=str)


def openai_response(question: str, context_json: str, api_key: str, model: str = DEFAULT_MODEL) -> str:
    """Make one explicit Responses API request; the function is never called at startup."""
    key = str(api_key or "").strip()
    if not key:
        raise ValueError("No OpenAI API key is configured.")
    payload = {
        "model": str(model or DEFAULT_MODEL),
        "instructions": (
            "You are a rigorous trading-plan and journal analyst. Use only supplied user data; "
            "distinguish observed metrics from hypotheses, show calculations when useful, and never promise profits "
            "or invent prices, stops, trades, or backtest results. Give a concise diagnosis, 2-4 actionable next steps, "
            "and state uncertainty or small sample size. Do not tell the user to increase risk to recover losses."
        ),
        "input": "User question:\n" + str(question)[:4000] + "\n\nSaved local trading context (JSON):\n" + str(context_json)[:22000],
        "max_output_tokens": 1100,
        "store": False,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            body = exc.read(4000).decode("utf-8", errors="replace")
            parsed = json.loads(body)
            detail = str((parsed.get("error") or {}).get("message") or "")
        except Exception:
            pass
        raise RuntimeError(f"OpenAI request failed (HTTP {exc.code}). {detail}".strip()) from exc
    output = str(result.get("output_text") or "").strip()
    if not output:
        parts = []
        for item in result.get("output", []):
            for part in item.get("content", []) or []:
                if part.get("type") == "output_text" and part.get("text"):
                    parts.append(part["text"])
        output = "\n".join(parts).strip()
    if not output:
        raise RuntimeError("The AI endpoint returned no text. Check API usage and model access.")
    return output
