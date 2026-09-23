from __future__ import annotations

import asyncio
import json
import os
import threading
import urllib.request
from pathlib import Path

ROOT = Path.home() / "TraderPlannerPro"
AI_SECRET = ROOT / "openai_key.json"
OLLAMA_BASE = "http://localhost:11434/api"
DEFAULT_MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "xhigh"
MODEL_FALLBACKS = ("gpt-5.6-sol", "gpt-5.6-luna")
CHATGPT_WEB_URL = "https://chatgpt.com/"

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
        headers={"Content-Type": "application/json", "User-Agent": "TraderPlannerPro/8.3"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def ollama_status():
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE}/tags", headers={"User-Agent": "TraderPlannerPro/8.3"})
        with urllib.request.urlopen(req, timeout=2.5) as response:
            data = json.loads(response.read().decode("utf-8"))
        models = [m.get("name") for m in data.get("models", []) if isinstance(m, dict)]
        return True, models
    except Exception:
        return False, []


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


def agents_sdk_status():
    """Return whether the OpenAI Agents SDK is importable."""
    try:
        from agents import Agent, Runner, RunConfig, set_default_openai_key  # noqa: F401
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _agents_sdk_respond(role, user_message, context, history, model):
    """Run a real multi-agent handoff graph through the OpenAI Agents SDK."""
    from agents import Agent, Runner, RunConfig, set_default_openai_key

    api_key = _read_openai_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    set_default_openai_key(api_key, use_for_tracing=False)

    common = (
        "You are part of Trader Planner Pro, a desktop trading-workflow assistant. "
        "Never invent live prices or news. Never promise returns or personalized financial guarantees. "
        "Keep broad Smart Money/SMC frameworks distinct from named ICT models. "
        "Candlestick patterns are a separate technical-analysis family and must never be relabeled as ICT setups. "
        "Use the supplied app context and recent conversation. Answer in the user's language when possible."
    )
    names = {
        "form": "Form Coach",
        "strategy": "Strategy Coach",
        "psychology": "Trading Psychology Coach",
        "planner": "Routine Coach",
        "academy": "Academy Tutor",
        "product": "Product Strategist",
    }
    specialists = []
    for key, description in ROLES.items():
        if key == "orchestrator":
            continue
        specialists.append(
            Agent(
                name=names.get(key, key.title()),
                handoff_description=description,
                instructions=common + "\nSPECIALIST MISSION:\n" + description,
                model=model,
            )
        )
    master = Agent(
        name="Trader Planner Master Agent",
        handoffs=specialists,
        instructions=(
            common
            + "\nYou are the master router. Identify the user's intent, hand off to the most relevant specialist, "
              "then synthesize specialist output when the request spans domains. Return one clear response with "
              "assumptions, missing information and concrete next actions. Never claim tool access that is not in context."
        ),
        model=model,
    )
    recent = json.dumps(history[-8:], ensure_ascii=False)
    prompt = (
        "APP CONTEXT:\n" + str(context)
        + "\n\nRECENT CHAT:\n" + recent
        + "\n\nUSER QUESTION:\n" + user_message
        + "\n\nPREFERRED SPECIALIST:\n" + role
    )
    result = asyncio.run(
        Runner.run(
            master,
            prompt,
            max_turns=8,
            run_config=RunConfig(
                model=model,
                trace_include_sensitive_data=False,
            ),
        )
    )
    answer = str(getattr(result, "final_output", "") or "").strip()
    if not answer:
        raise RuntimeError("Agents SDK returned an empty response.")
    return answer


def cloud_status():
    key = _read_openai_key()
    sdk_ok, sdk_error = agents_sdk_status()
    if not key:
        return {"enabled": False, "agents_sdk": sdk_ok, "model": DEFAULT_MODEL,
                "message": "Add an OpenAI API key or enable Ollama.", "sdk_error": sdk_error}
    try:
        from openai import OpenAI  # noqa: F401
        return {"enabled": True, "agents_sdk": sdk_ok, "model": DEFAULT_MODEL,
                "message": "OpenAI cloud agent routing is ready.", "sdk_error": sdk_error}
    except Exception as exc:
        return {"enabled": False, "agents_sdk": sdk_ok, "model": DEFAULT_MODEL,
                "message": f"OpenAI SDK unavailable: {exc}", "sdk_error": sdk_error}


def _academy_knowledge_answer(query: str):
    """Offline retrieval from the app's curated Academy corpus."""
    try:
        from academy_content import SMART_MONEY_STRATEGIES, ICT_STRATEGIES, CANDLE_PLAYBOOK, GLOSSARY
    except Exception:
        return None
    q = str(query or "").strip().lower()
    if not q:
        return None

    candidates = []
    for item in list(SMART_MONEY_STRATEGIES) + list(ICT_STRATEGIES):
        blob = " ".join(str(item.get(k, "")) for k in ("name_en", "name_fa", "summary_en", "summary_fa"))
        if any(token and token in blob.lower() for token in (q, q.replace("?", ""), " ".join(q.split()[:3]))):
            candidates.append(("strategy", item))

    for name_en, name_fa, summary_fa in CANDLE_PLAYBOOK:
        if q in name_en.lower() or q in name_fa.lower() or q in summary_fa.lower():
            candidates.append(("candle", {
                "name_en": name_en,
                "name_fa": name_fa,
                "summary_fa": summary_fa,
                "summary_en": summary_fa,
            }))

    for item in GLOSSARY:
        blob = " ".join(str(item.get(k, "")) for k in ("term", "fa", "en", "meaning_en", "meaning_fa", "usage_en", "usage_fa"))
        if q and q in blob.lower():
            candidates.append(("glossary", item))

    if not candidates:
        return None

    kind, item = candidates[0]
    if kind == "strategy":
        lines_en = item.get("steps_en") or []
        lines_fa = item.get("steps_fa") or []
        return {
            "kind": "academy",
            "title": item.get("name_en", ""),
            "fa_title": item.get("name_fa", item.get("name_en", "")),
            "summary": item.get("summary_en", ""),
            "summary_fa": item.get("summary_fa", item.get("summary_en", "")),
            "steps": lines_en,
            "steps_fa": lines_fa,
            "risk": item.get("risk_en", ""),
            "risk_fa": item.get("risk_fa", item.get("risk_en", "")),
        }
    if kind == "candle":
        return {
            "kind": "candle",
            "title": item.get("name_en", ""),
            "fa_title": item.get("name_fa", item.get("name_en", "")),
            "summary": item.get("summary_en", ""),
            "summary_fa": item.get("summary_fa", ""),
            "steps": [],
            "steps_fa": [],
            "risk": "Candlestick evidence is context-dependent; do not treat one pattern as a complete trading setup.",
            "risk_fa": "الگوی کندلی به‌تنهایی ستاپ کامل نیست؛ کانتکست و تأیید را بررسی کن.",
        }
    return {
        "kind": "glossary",
        "title": item.get("term", ""),
        "fa_title": item.get("fa", item.get("term", "")),
        "summary": item.get("meaning_en", ""),
        "summary_fa": item.get("meaning_fa", item.get("meaning_en", "")),
        "steps": [item.get("usage_en", "")] if item.get("usage_en") else [],
        "steps_fa": [item.get("usage_fa", "")] if item.get("usage_fa") else [],
        "risk": "",
        "risk_fa": "",
    }


def _render_offline_knowledge(answer, role, language="fa"):
    if not isinstance(answer, dict):
        return None
    use_fa = str(language).lower().startswith("fa")
    title = answer.get("fa_title") if use_fa else answer.get("title")
    summary = answer.get("summary_fa") if use_fa else answer.get("summary")
    steps = answer.get("steps_fa") if use_fa else answer.get("steps")
    risk = answer.get("risk_fa") if use_fa else answer.get("risk")
    lines = [str(title or "Academy").strip(), "", str(summary or "").strip()]
    if steps:
        lines += ["", "مراحل:" if use_fa else "Steps:"]
        for n, step in enumerate(steps, 1):
            if str(step).strip():
                lines.append(f"{n}. {step}")
    if risk:
        lines += ["", "نکته/ابطال:" if use_fa else "Risk / invalidation:", str(risk)]
    if role not in ("academy", "strategy", "orchestrator"):
        lines += ["", "این پاسخ از حافظه آموزشی داخلی برنامه آمده و داده زنده بازار نیست." if use_fa else
                  "This answer comes from the app's curated Academy corpus; it is not live market data."]
    return "\n".join(x for x in lines if x is not None)


def _fallback(role, user_message, context):
    lower = f"{user_message} {context}".lower()
    # The offline knowledge agent makes the AI genuinely useful without an API key.
    language = "fa" if any("\u0600" <= ch <= "\u06FF" for ch in str(user_message)) else "en"
    knowledge = _academy_knowledge_answer(user_message)
    rendered = _render_offline_knowledge(knowledge, role, language)
    if rendered:
        return rendered

    if role == "orchestrator":
        if any(k in lower for k in ("fill", "form", "فرم", "پلن", "checklist", "چک")):
            return (
                "AI Command Center\n"
                "برای تکمیل فرم: بازار و جهت → ستاپ → ساختار → نقدینگی → Entry/SL/TP → ریسک → وضعیت روانی → نتیجه/درس. "
                "هر فیلدی که از داده فعلی قابل استنباط نباشد عمداً خالی می‌ماند."
                if language == "fa" else
                "AI Command Center\n"
                "For form completion: market/direction → setup → structure → liquidity → Entry/SL/TP → risk → psychology → result/lesson. "
                "Fields that cannot be inferred from the current app data remain blank."
            )
        if any(k in lower for k in ("psychology", "fomo", "revenge", "روان", "فومو", "انتقام")):
            return (
                "AI Command Center\n"
                "قانون دو دقیقه: توقف → نام‌گذاری احساس → بررسی چک‌لیست → بررسی ریسک → فقط در صورت عبور از قوانین اقدام کن."
                if language == "fa" else
                "AI Command Center\n"
                "Two-minute rule: pause → name the emotion → check the checklist → verify risk → act only after the rules pass."
            )
        return (
            "AI Command Center\n"
            "دستیار آفلاین فعال است. درباره ستاپ، اصطلاحات آکادمی، فرم ترید، ریسک، روانشناسی یا روتین سؤال بپرس."
            if language == "fa" else
            "AI Command Center\n"
            "The offline assistant is active. Ask about Academy setups, terminology, trading forms, risk, psychology or routine."
        )
    if role == "form":
        return (
            "Form Coach\n"
            "می‌توانم بر اساس داده فعلی برنامه و ژورنال، فیلدهای قابل استنتاج را پیشنهاد کنم؛ موارد نامطمئن را حدس نمی‌زنم.\n"
            "برای شروع: «فرم معامله امروز را از اطلاعات فعلی پر کن.»"
            if language == "fa" else
            "Form Coach\n"
            "I can suggest fields inferable from the current plan and journal while leaving uncertain fields untouched.\n"
            "Try: “Fill today's trade form from the current data.”"
        )
    if role == "strategy":
        if "engulf" in lower:
            return (
                "این الگو Candlestick است، نه مدل ICT. Bullish Engulfing و Bearish Engulfing مستقل از مدل‌های ICT آموزش داده می‌شوند؛ "
                "برای استفاده، کانتکست، سطح، تأیید و ابطال را جداگانه بررسی کن."
            )
        return (
            "Strategy Coach\n"
            "SMC: نقدینگی/ساختار/OB/FVG را به‌عنوان چارچوب بررسی کن. "
            "ICT: از نام و منطق همان مدل مشخص استفاده کن. "
            "قبل از ورود: context → setup → trigger → invalidation → target."
        )
    if role == "psychology":
        return (
            "Psychology Coach\n"
            "توقف → نام احساس → بررسی قانون → بررسی ریسک → تصمیم. "
            "FOMO و Revenge باید به‌عنوان رویداد ژورنال ثبت و برایشان Reminders ساخته شود."
        )
    if role == "planner":
        return (
            "Routine Coach\n"
            "پیش‌گشایش → خبر → محدوده‌های مهم → سناریو → اجرای محدود → توقف اجباری → ژورنال → مرور."
        )
    if role == "academy":
        return (
            "Academy Tutor\n"
            "در آکادمی، SMC یک چارچوب عمومی ساختار/نقدینگی است؛ ICT مجموعه مدل‌های نام‌گذاری‌شده با منطق مشخص است؛ "
            "Candlestick خانواده‌ای جداست. برای اصطلاح دقیق سؤال کن تا از بانک داخلی تعریف و مراحل آن را بازیابی کنم."
        )
    return (
        "Product Strategist\n"
        "اولویت‌های محصول: حالت‌های خالی/خطا با راهنمای واضح، ناوبری پایدار، کارت‌های شیشه‌ای سبک، "
        "جستجوی آکادمی با تصویر اختصاصی، و حلقه Journal → Review → Improvement."
    )


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

    def status(self):
        ollama_online, ollama_models = ollama_status()
        cloud = cloud_status()
        return {
            "online": cloud["enabled"] or ollama_online,
            "cloud": cloud["enabled"],
            "agents_sdk": cloud.get("agents_sdk", False),
            "ollama": ollama_online,
            "web": True,
            "models": ollama_models,
            "model": cloud["model"] if cloud["enabled"] else (ollama_models[0] if ollama_models else self.model),
            "last_error": self.last_error,
            "message": cloud.get("message", ""),
        }

    def _cloud_respond(self, role, user_message, context):
        api_key = _read_openai_key()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        from openai import OpenAI

        client = OpenAI(api_key=api_key, timeout=45.0)
        common = (
            "You are Trader Planner Pro's master trading assistant. "
            "Operate as a precise agent: inspect the supplied app context, identify the user intent, "
            "apply the selected specialist role, and return a practical answer. "
            "Never invent market data, never promise returns, and never give personalized financial guarantees. "
            "Keep broad Smart Money/SMC concepts distinct from named ICT models. "
            "Candlestick patterns must never be relabeled as ICT setups. "
        )
        specialist = self.roles.get(role, self.roles["orchestrator"])
        recent = json.dumps(self.history[-8:], ensure_ascii=False)
        response = client.responses.create(
            model=self.model,
            instructions=common + "\nSPECIALIST ROLE:\n" + specialist,
            input=(
                "APP CONTEXT:\n" + context +
                "\n\nRECENT CHAT:\n" + recent +
                "\n\nUSER QUESTION:\n" + user_message
            ),
        )
        answer = str(getattr(response, "output_text", "") or "").strip()
        if not answer:
            raise RuntimeError("OpenAI returned an empty response.")
        return answer

    def respond(self, role, user_message, context="", callback=None):
        role = role if role in self.roles else "form"
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
                cloud = cloud_status()
                if cloud.get("enabled") and cloud.get("agents_sdk"):
                    answer = _agents_sdk_respond(role, user_message, context, self.history, self.model)
                elif cloud.get("enabled"):
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
