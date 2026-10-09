from __future__ import annotations

import asyncio
import json
import os
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path.home() / "TraderPlannerPro"
AI_SECRET = ROOT / "openai_key.json"
OLLAMA_BASE = "http://localhost:11434/api"
DEFAULT_MODEL = os.getenv("TRADER_PLANNER_AI_MODEL", "gpt-5.6-sol")
REASONING_EFFORT = "high"
MODEL_FALLBACKS = ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna")

# Keep the application shell light: the Agents SDK is imported only when a
# cloud response is requested, not while the desktop window is booting.
AGENT_SDK_AVAILABLE = False
_AGENT_SDK_CHECKED = False
_AGENT_SDK_LOCK = threading.Lock()
Agent = ModelSettings = Runner = Reasoning = None

# Status widgets must never wait for a local HTTP request. Probe Ollama in a
# daemon thread and let the UI read the last known result immediately.
_OLLAMA_STATUS_LOCK = threading.Lock()
_OLLAMA_STATUS_CACHE = {
    "checked_at": 0.0,
    "online": False,
    "models": [],
    "refreshing": False,
}
CHATGPT_WEB_URL = "https://chatgpt.com/"


def _ensure_agents_sdk() -> bool:
    global Agent, ModelSettings, Runner, Reasoning
    global AGENT_SDK_AVAILABLE, _AGENT_SDK_CHECKED
    if _AGENT_SDK_CHECKED:
        return AGENT_SDK_AVAILABLE
    with _AGENT_SDK_LOCK:
        if _AGENT_SDK_CHECKED:
            return AGENT_SDK_AVAILABLE
        try:
            from agents import Agent as _Agent, ModelSettings as _ModelSettings, Runner as _Runner
            from openai.types.shared import Reasoning as _Reasoning
            Agent, ModelSettings, Runner, Reasoning = _Agent, _ModelSettings, _Runner, _Reasoning
            AGENT_SDK_AVAILABLE = True
        except Exception:
            Agent = ModelSettings = Runner = Reasoning = None
            AGENT_SDK_AVAILABLE = False
        _AGENT_SDK_CHECKED = True
    return AGENT_SDK_AVAILABLE

ROLES = {
    "orchestrator": "Master Agent: triage the question, use the right specialist, connect the journal, strategy, psychology and Academy context, and produce one actionable answer.",
    "form": "Form Coach: fill forms step-by-step, detect missing fields and convert context into concise journal/checklist entries.",
    "strategy": "Strategy Coach: explain only documented strategy definitions, separate context/setup/trigger/invalidation/target, and never invent a rule.",
    "psychology": "Trading Psychology Coach: help with FOMO, revenge trading, discipline, preparation and post-trade review without judging the person.",
    "planner": "Routine Coach: organize the trader's daily routine, sessions, review blocks, reminders and stop times.",
    "academy": "Academy Tutor: teach Smart Money, ICT and candlestick concepts using the app's source-backed Academy definitions and clearly separate the families.",
    "product": "Product Strategist: propose concrete UI/UX/product improvements for Trader Planner Pro, prioritizing clarity, speed, accessibility and trading workflow.",
}


def _post_json(url, payload, timeout=25):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "TraderPlannerPro/8.2"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def ollama_status():
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE}/tags", headers={"User-Agent": "TraderPlannerPro/7.8"})
        with urllib.request.urlopen(req, timeout=2.5) as response:
            data = json.loads(response.read().decode("utf-8"))
        models = [m.get("name") for m in data.get("models", []) if isinstance(m, dict)]
        return True, models
    except Exception:
        return False, []


def _refresh_ollama_status() -> None:
    try:
        online, models = ollama_status()
    except Exception:
        online, models = False, []
    with _OLLAMA_STATUS_LOCK:
        _OLLAMA_STATUS_CACHE["online"] = bool(online)
        _OLLAMA_STATUS_CACHE["models"] = list(models or [])
        _OLLAMA_STATUS_CACHE["checked_at"] = time.monotonic()
        _OLLAMA_STATUS_CACHE["refreshing"] = False


def _cached_ollama_status():
    now = time.monotonic()
    with _OLLAMA_STATUS_LOCK:
        stale = now - float(_OLLAMA_STATUS_CACHE["checked_at"]) >= 20.0
        if stale and not _OLLAMA_STATUS_CACHE["refreshing"]:
            _OLLAMA_STATUS_CACHE["refreshing"] = True
            try:
                threading.Thread(
                    target=_refresh_ollama_status,
                    name="TraderPlannerOllamaStatus",
                    daemon=True,
                ).start()
            except Exception:
                _OLLAMA_STATUS_CACHE["refreshing"] = False
        return bool(_OLLAMA_STATUS_CACHE["online"]), list(_OLLAMA_STATUS_CACHE["models"])


def ollama_chat(model, messages):
    data = _post_json(
        f"{OLLAMA_BASE}/chat",
        {"model": model, "messages": messages, "stream": False},
        timeout=90,
    )
    return ((data.get("message") or {}).get("content") or "").strip()


def _read_openai_key():
    env = os.getenv("OPENAI_API_KEY", "").strip()
    if env:
        return env
    try:
        payload = json.loads(AI_SECRET.read_text(encoding="utf-8"))
        return str(payload.get("api_key") or "").strip()
    except Exception:
        return ""


def save_openai_key(api_key: str):
    key = str(api_key or "").strip()
    if not key:
        raise ValueError("API key cannot be empty.")
    ROOT.mkdir(parents=True, exist_ok=True)
    AI_SECRET.write_text(json.dumps({"api_key": key}, ensure_ascii=False), encoding="utf-8")
    try:
        os.chmod(AI_SECRET, 0o600)
    except OSError:
        pass


def clear_openai_key():
    try:
        AI_SECRET.unlink(missing_ok=True)
    except OSError:
        pass


def cloud_status():
    # This check is intentionally local-only. Importing OpenAI/Agents merely to
    # paint a status badge made cold startup slower; the SDK initializes on the
    # first actual cloud request instead.
    key = _read_openai_key()
    if not key:
        return {
            "enabled": False,
            "model": DEFAULT_MODEL,
            "message": "Add an OpenAI API key or enable Ollama.",
            "agents_sdk": AGENT_SDK_AVAILABLE,
        }
    return {
        "enabled": True,
        "model": DEFAULT_MODEL,
        "message": "Cloud agent will initialize on the first request.",
        "agents_sdk": AGENT_SDK_AVAILABLE,
    }


def _fallback(role, user_message, context):
    """Give concrete, structured next steps when no live model is configured."""
    message = str(user_message or "").strip()
    lower = f"{message} {context}".lower()
    is_fa = any("\\u0600" <= character <= "\\u06ff" for character in message)
    market_line = next((line.strip() for line in str(context).splitlines() if line.lower().startswith("market:")), "")
    profile_line = next((line.strip() for line in str(context).splitlines() if line.lower().startswith("profile:")), "")
    context_tail = " | ".join(value for value in (market_line, profile_line) if value)
    if role == "orchestrator":
        if any(token in lower for token in ("fvg","bos","ict","smc","order block","liquidity","ستاپ","ایمبالانس","نقدینگی")): role = "strategy"
        elif any(token in lower for token in ("journal","ژورنال","trade log","معامله")): role = "form"
        elif any(token in lower for token in ("fomo","revenge","فومو","انتقام","روانشناسی")): role = "psychology"
        elif any(token in lower for token in ("routine","روتین","برنامه روزانه")): role = "planner"
    if role == "strategy":
        if is_fa:
            return ("بررسی ساختاری ستاپ — راهنمای آفلاین\n" + (context_tail + chr(10) if context_tail else "") +
                "۱) زمینه: بایاس و ساختار تایم‌فریم بالاتر را مشخص کن؛ بدون نماد و تایم‌فریم بازار را فرض نمی‌کنم.\n"
                "۲) ستاپ: ناحیه نقدینگی، سقف/کف مهم و FVG یا Order Block را روی نمودار علامت بزن.\n"
                "۳) تریگر: جابه‌جایی قوی، بسته‌شدن معتبر کندل و برگشت به ناحیه را جداگانه تأیید کن.\n"
                "۴) ابطال: حد ضرر باید پشت ساختاری باشد که فرض معامله را باطل می‌کند.\n"
                "۵) هدف: نقدینگی یا سقف/کف بعدی را مشخص کن و R:R را پیش از ورود حساب کن.\n"
                "۶) ریسک: اگر چک‌لیست ناقص است یا نسبت سود به زیان با قانونت سازگار نیست، ورود نکن.\n"
                "برای تحلیل مشخص، نماد، تایم‌فریم‌ها و تصویر نمودار را بفرست. این پاسخ سیگنال زنده نیست.")
        return ("Structured Strategy Review (offline guide)\n" + (context_tail + chr(10) if context_tail else "") +
            "1) Context: define higher-timeframe bias and structure; I will not assume them without symbol/timeframe data.\n"
            "2) Setup: mark liquidity, important swing levels, and the FVG or order-block area.\n"
            "3) Trigger: confirm displacement, a valid close through structure, and the planned retrace.\n"
            "4) Invalidation: place the stop beyond the structure that invalidates the thesis.\n"
            "5) Target: identify the next liquidity pool/swing and calculate R:R before entry.\n"
            "6) Risk: skip the trade if the checklist is incomplete or R:R violates your rules.\n"
            "For a specific review, provide symbol, timeframes and a chart screenshot. This is not a live signal.")
    if role == "form":
        if is_fa: return "مربی فرم معامله — موارد لازم\nنماد و بازار | جهت | تایم‌فریم | مدل ستاپ | دلیل ورود | ورود | حد ضرر | هدف | R:R | درصد ریسک\nموارد اجباری چک‌لیست را پیش از ذخیره بررسی کن؛ پس از معامله نتیجه برحسب R، احساسات و یک درس قابل اجرا را ثبت کن."
        return "Trade Form Coach — required fields\nSymbol/market | direction | timeframes | setup model | entry rationale | entry | stop | target | R:R | risk %\nCheck required checklist items before saving; afterward, record result in R, emotions and one actionable lesson."
    if role == "psychology":
        if is_fa: return "چک‌لیست روانشناسی قبل از ورود\n۱) آیا ستاپ طبق پلن است؟ ۲) آیا خبر مهم نزدیک است؟ ۳) آیا حد ضرر و ریسک مشخص‌اند؟\n۴) آیا برای جبران ضرر عجله داری؟ ۵) آیا از جا ماندن از حرکت می‌ترسی؟\nاگر پاسخ ۴ یا ۵ مثبت است، ۱۰ دقیقه مکث کن و سپس چک‌لیست را دوباره بررسی کن."
        return "Pre-trade psychology checklist\n1) Is the setup in your plan? 2) Is major news imminent? 3) Are stop and risk defined?\n4) Are you rushing to recover a loss? 5) Are you afraid of missing the move?\nIf 4 or 5 is yes, pause for 10 minutes and repeat your checklist before entering."
    if role == "planner":
        return "روتین پیشنهادی: بررسی خبرها → تعیین بایاس و نواحی → انتظار برای تریگر → توقف در سقف ریسک روز → ثبت تصویر و نتیجه در ژورنال." if is_fa else "Suggested routine: check the news calendar → set bias and zones → wait for the trigger → stop at the daily risk limit → save a chart screenshot and journal the result."
    if role == "academy":
        return "آکادمی آفلاین: SMC چارچوب کلی ساختار بازار و نقدینگی است؛ ICT مدل‌ها و نام‌گذاری‌های مشخص خود را دارد؛ الگوی کندلی به‌تنهایی تریگر کامل نیست. زمینه، محل وقوع و ابطال را هم بررسی کن." if is_fa else "Offline Academy: SMC is a broad market-structure/liquidity framework; ICT has named models and terminology; a candlestick pattern alone is not a complete trigger. Check context, location and invalidation."
    if role == "product":
        return "اقدام‌های مشخص: اول خطاهای شروع را از روی لاگ قابل تکرار رفع کن؛ وضعیت ذخیره را واضح نشان بده؛ سپس نمودار، تصویر و قابلیت‌های سنگین را فقط هنگام نیاز بارگذاری کن." if is_fa else "Concrete product actions: fix repeatable startup errors from logs first; expose save/error states clearly; then lazy-load expensive chart, image and AI features only when requested."
    if is_fa: return "دستیار داخلی آفلاین\nبرای ساخت چک‌لیست و فرم کمک می‌کنم، اما تحلیل واقعی نمودار به نماد، تایم‌فریم و تصویر/داده جاری نیاز دارد. برای پاسخ مولد ابری، کلید API را در تنظیمات ثبت کن؛ برای مدل محلی، Ollama باید نصب و اجرا باشد."
    return "Built-in offline assistant\nI can structure a checklist and trade form, but chart analysis requires the symbol, timeframe and current chart/data. For generative cloud replies, save an API key in Settings; for a local model, Ollama must be installed and running."


class AIOrchestrator:
    """Multi-provider, multi-agent trader assistant.

    Priority: OpenAI Agents SDK when configured, then local Ollama, then a
    deterministic built-in assistant. The chat UI remains usable in all modes.
    """

    def __init__(self, model=DEFAULT_MODEL):
        self.model = model
        self.roles = ROLES
        self._cloud_agents = None
        self.last_error = ""
        self.history = []
        self.active_role = "orchestrator"

    def status(self):
        ollama_online, ollama_models = _cached_ollama_status()
        cloud = cloud_status()
        return {
            "online": cloud["enabled"] or ollama_online,
            "agents_sdk": bool(cloud.get("agents_sdk")),
            "cloud": cloud["enabled"],
            "agents_sdk": AGENT_SDK_AVAILABLE,
            "ollama": ollama_online,
            "web": True,
            "models": ollama_models,
            "model": cloud["model"] if cloud["enabled"] else (ollama_models[0] if ollama_models else self.model),
            "last_error": self.last_error,
        }

    def _build_cloud_agents(self):
        if self._cloud_agents is not None:
            return self._cloud_agents
        if not _ensure_agents_sdk():
            raise RuntimeError("OpenAI Agents SDK is not installed or could not be loaded.")
        common = (
            "You are a production-grade specialist inside Trader Planner Pro. "
            "Use the supplied app context as the source of truth. "
            "Never invent live market data, never promise returns, and never provide personalized financial guarantees. "
            "Keep Smart Money Concepts as a broad framework, ICT as its named model/terminology family, "
            "and candlestick patterns as a separate technical-analysis family. "
            "When the user asks about a setup, structure the answer as context, setup, trigger, invalidation, target and risk. "
            "When evidence is missing, say exactly what is missing."
        )
        settings = ModelSettings(
            reasoning=Reasoning(mode="pro", effort=REASONING_EFFORT, context="all_turns"),
            verbosity="medium",
        )
        specialists = {}
        for key, instruction in self.roles.items():
            if key == "orchestrator":
                continue
            specialists[key] = Agent(
                name={
                    "form":"Form Coach","strategy":"Strategy Coach","psychology":"Psychology Coach",
                    "planner":"Routine Coach","academy":"Academy Tutor","product":"Product Strategist",
                }.get(key, key.title()),
                handoff_description=instruction,
                instructions=common + "\nSPECIALIST MISSION:\n" + instruction,
                model=self.model,
                model_settings=settings,
            )
        master = Agent(
            name="Trader Planner Master Agent",
            handoff_description=self.roles["orchestrator"],
            instructions=(
                common
                + "\nYou are the master router. Decide which specialist should own the user's turn, "
                  "then hand off to that specialist. Do not answer with a generic placeholder when a specialist can handle the request."
            ),
            model=self.model,
            model_settings=settings,
            handoffs=list(specialists.values()),
        )
        self._cloud_agents = {"master": master, **specialists}
        return self._cloud_agents

    def _cloud_respond(self, role, user_message, context):
        api_key = _read_openai_key()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        if not _ensure_agents_sdk():
            raise RuntimeError("OpenAI Agents SDK is not installed or could not be loaded.")

        # The Agents SDK reads OPENAI_API_KEY when the provider/client is resolved.
        os.environ["OPENAI_API_KEY"] = api_key
        agents = self._build_cloud_agents()
        active = agents.get(role) if role in agents and role != "orchestrator" else agents["master"]
        recent = json.dumps(self.history[-8:], ensure_ascii=False)
        prompt = (
            "APP CONTEXT:\n" + context +
            "\n\nRECENT CHAT:\n" + recent +
            "\n\nUSER QUESTION:\n" + user_message
        )
        result = Runner.run_sync(active, prompt)
        answer = str(getattr(result, "final_output", "") or "").strip()
        if not answer:
            raise RuntimeError("Agents SDK returned an empty response.")
        return answer

    def respond(self, role, user_message, context="", callback=None):
        # Master router chooses a specialist from the user's wording.
        if role == "orchestrator":
            text_l = str(user_message or "").lower()
            if any(k in text_l for k in ("فرم","چک لیست","checklist","journal","پلن","form")):
                role = "form"
            elif any(k in text_l for k in ("فومو","fomo","revenge","روان","احساس","discipline","نظم")):
                role = "psychology"
            elif any(k in text_l for k in ("کندل","engulf","doji","hammer","morning star")):
                role = "academy"
            elif any(k in text_l for k in ("ict","smc","fvg","order block","liquidity","ستاپ","نمودار")):
                role = "strategy"
            elif any(k in text_l for k in ("طراحی","ui","ux","ارتقا","بهبود","محصول")):
                role = "product"
        role = role if role in self.roles else "orchestrator"
        self.active_role = role
        user_message = str(user_message or "").strip()
        if not user_message:
            return

        # Keep the last few turns so the agent can answer follow-up questions
        # instead of treating every message as an unrelated one.
        self.history.append({"role": "user", "content": user_message})
        self.history = self.history[-10:]

        def worker():
            answer = None
            self.last_error = ""
            try:
                if cloud_status()["enabled"]:
                    answer = self._cloud_respond(role, user_message, context)
            except Exception as exc:
                self.last_error = f"Cloud Agent: {type(exc).__name__}: {exc}"

            if not answer:
                try:
                    online, models = ollama_status()
                    if online and models:
                        preferred = [m for m in MODEL_FALLBACKS if m in models]
                        model = preferred[0] if preferred else models[0]
                        recent = json.dumps(self.history[-8:], ensure_ascii=False)
                        answer = ollama_chat(
                            model,
                            [
                                {
                                    "role": "system",
                                    "content": (
                                        "You are the local specialist assistant inside Trader Planner Pro. "
                                        "Use only the supplied app context. Never guarantee outcomes. "
                                        f"Specialist role: {self.roles[role]}\n"
                                        "Recent conversation is supplied as JSON and should be treated as conversation context."
                                    ),
                                },
                                {
                                    "role": "user",
                                    "content": f"APP CONTEXT:\n{context}\n\nRECENT CHAT:\n{recent}\n\nUSER:\n{user_message}",
                                },
                            ],
                        )
                except Exception as exc:
                    self.last_error = f"Local AI: {type(exc).__name__}: {exc}"

            if not answer:
                answer = _fallback(role, user_message, context)
                if not self.last_error:
                    self.last_error = "No live AI provider configured; using offline assistant."

            self.history.append({"role": "assistant", "content": answer})
            self.history = self.history[-10:]
            if callback:
                callback(answer)

        threading.Thread(target=worker, name="TraderPlannerAI", daemon=True).start()
