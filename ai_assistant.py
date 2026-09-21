from __future__ import annotations

import json
import os
import threading
import urllib.request
from pathlib import Path

ROOT = Path.home() / "TraderPlannerPro"
AI_SECRET = ROOT / "openai_key.json"

OLLAMA_BASE = "http://localhost:11434/api"
DEFAULT_MODEL = "gpt-5.6-sol"
MODEL_FALLBACKS = ("gpt-5.6-sol", "gpt-5.6-luna")
CHATGPT_WEB_URL = "https://chatgpt.com/"

ROLES = {
    "orchestrator": "Master Agent: route the request, combine journal, strategy, psychology, planner and Academy context, then answer clearly.",
    "form": "Form Coach: turn messy information into completed plan/checklist/journal fields and point out missing values.",
    "strategy": "Strategy Coach: separate context, setup, trigger, invalidation and target; never invent a rule.",
    "psychology": "Trading Psychology Coach: help with FOMO, revenge trading, discipline, preparation and post-trade review.",
    "planner": "Routine Coach: organize pre-market, sessions, review blocks, stop times and reminders.",
    "academy": "Academy Tutor: teach broad SMC/Smart Money concepts separately from named ICT models and candlestick patterns.",
    "product": "Product Strategist: propose concrete UI/UX improvements for Trader Planner Pro with emphasis on clarity, speed and reliability.",
}

SYSTEM_BASE = (
    "You are the Master Agent inside Trader Planner Pro. "
    "Be precise and practical. Never invent live market data, never promise returns, and never claim certainty. "
    "Use only supplied app context for journal/profile/market values. "
    "Keep Smart Money/SMC, named ICT models, and ordinary candlestick patterns clearly separated. "
    "When a user asks about a setup, structure your answer as context -> setup -> trigger -> invalidation -> target -> risk. "
    "When asked about the app, propose a concrete workflow and UI action. "
)

def _post_json(url, payload, timeout=25):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "TraderPlannerPro/8.1.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def ollama_status():
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE}/tags", headers={"User-Agent": "TraderPlannerPro/8.1.0"})
        with urllib.request.urlopen(req, timeout=2.5) as response:
            data = json.loads(response.read().decode("utf-8"))
        models = [m.get("name") for m in data.get("models", []) if isinstance(m, dict)]
        return True, [m for m in models if m]
    except Exception:
        return False, []

def ollama_chat(model, messages):
    data = _post_json(
        f"{OLLAMA_BASE}/chat",
        {"model": model, "messages": messages, "stream": False},
        timeout=90,
    )
    return str(((data.get("message") or {}).get("content") or "")).strip()

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
    key = _read_openai_key()
    if not key:
        return {"enabled": False, "model": DEFAULT_MODEL, "provider": "none"}
    try:
        import openai  # noqa: F401
        return {"enabled": True, "model": DEFAULT_MODEL, "provider": "openai"}
    except Exception:
        return {"enabled": False, "model": DEFAULT_MODEL, "provider": "missing_sdk"}

def _fallback(role, user_message, context):
    lower = f"{user_message} {context}".lower()
    if role == "form":
        return (
            "Form Coach\n"
            "1) Symbol / market / direction\n"
            "2) Context + structure + liquidity\n"
            "3) Setup + trigger\n"
            "4) Entry / SL / TP / size / risk\n"
            "5) Psychology + result + lesson\n"
            "Fill missing values before saving."
        )
    if role == "strategy":
        if "engulf" in lower:
            return "Bullish Engulfing and Bearish Engulfing are candlestick patterns, not ICT setup names. Use trend/level/context plus confirmation."
        return "Strategy Coach: separate context -> setup -> trigger -> invalidation -> target. Use the exact Academy definition for the selected model."
    if role == "psychology":
        return "Psychology check: pause -> name the emotion -> verify the checklist -> verify risk -> only then act. Record repeated FOMO/revenge triggers in the journal."
    if role == "planner":
        return "Routine: pre-market markup -> news -> session block -> hard stop -> journal -> review. Convert recurring actions into reminders."
    if role == "academy":
        return "Academy Tutor: Smart Money/SMC is a broad framework; ICT is a family of named models; candlestick patterns are a separate technical language. Keep their terminology and visuals separate."
    if role == "product":
        return "Product Strategist: prioritize persistent navigation, explicit live/cache/offline states, fast in-app actions, strong empty/error states, and a journal -> review -> improvement loop."
    return (
        "Master Agent: I will route this question through the correct specialist and use the app context. "
        "Ask me about your plan, journal, Academy, psychology, reminders or app workflow."
    )

def _openai_response(model, system_text, user_text):
    from openai import OpenAI
    client = OpenAI(api_key=_read_openai_key(), timeout=90)
    response = client.responses.create(
        model=model,
        reasoning={"effort": "high"},
        input=[
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ],
    )
    text = getattr(response, "output_text", "") or ""
    return text.strip()

class AIOrchestrator:
    """Reliable local-first Master Agent.

    Provider priority:
      1. OpenAI Responses API with GPT-5.6 Sol when a user API key is configured.
      2. GPT-5.6 Luna on a temporary model fallback if Sol is unavailable.
      3. Local Ollama if installed.
      4. Built-in offline guidance.

    The UI remains usable in every state and reports the actual provider.
    """

    def __init__(self, model=DEFAULT_MODEL):
        self.model = model
        self.roles = ROLES
        self.last_error = ""
        self.history = []
        self.last_provider = "none"

    def status(self):
        cloud = cloud_status()
        ollama_online, ollama_models = ollama_status()
        return {
            "online": bool(cloud["enabled"] or ollama_online),
            "cloud": bool(cloud["enabled"]),
            "ollama": bool(ollama_online),
            "web": True,
            "models": ollama_models,
            "model": cloud["model"] if cloud["enabled"] else (ollama_models[0] if ollama_models else self.model),
            "provider": "OpenAI" if cloud["enabled"] else ("Ollama" if ollama_online else "Offline"),
            "last_provider": self.last_provider,
            "last_error": self.last_error,
        }

    def _cloud_respond(self, role, user_message, context):
        role_text = self.roles.get(role, self.roles["orchestrator"])
        recent = json.dumps(self.history[-8:], ensure_ascii=False)
        prompt = (
            f"APP CONTEXT:\n{context}\n\n"
            f"SPECIALIST ROLE:\n{role_text}\n\n"
            f"RECENT CHAT:\n{recent}\n\n"
            f"USER QUESTION:\n{user_message}"
        )
        answer = _openai_response(
            self.model,
            SYSTEM_BASE + role_text,
            prompt,
        )
        if not answer:
            raise RuntimeError("OpenAI returned an empty response.")
        return answer

    def respond(self, role, user_message, context="", callback=None):
        role = role if role in self.roles else "orchestrator"
        user_message = str(user_message or "").strip()
        if not user_message:
            return

        self.history.append({"role": "user", "content": user_message})
        self.history = self.history[-10:]

        def worker():
            answer = None
            self.last_error = ""
            self.last_provider = "none"

            cloud = cloud_status()
            if cloud["enabled"]:
                for model in (self.model,) + tuple(m for m in MODEL_FALLBACKS if m != self.model):
                    try:
                        answer = self._cloud_respond(role, user_message, context)
                        if answer:
                            self.last_provider = f"OpenAI • {model}"
                            break
                    except Exception as exc:
                        self.last_error = f"OpenAI: {type(exc).__name__}: {exc}"

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
                                    "content": SYSTEM_BASE + self.roles.get(role, self.roles["orchestrator"]),
                                },
                                {
                                    "role": "user",
                                    "content": (
                                        f"APP CONTEXT:\n{context}\n\n"
                                        f"RECENT CHAT:\n{recent}\n\n"
                                        f"USER:\n{user_message}"
                                    ),
                                },
                            ],
                        )
                        if answer:
                            self.last_provider = f"Ollama • {model}"
                except Exception as exc:
                    self.last_error = f"Ollama: {type(exc).__name__}: {exc}"

            if not answer:
                answer = _fallback(role, user_message, context)
                self.last_provider = "Offline built-in"
                if not self.last_error:
                    self.last_error = "No live AI provider is configured."

            self.history.append({"role": "assistant", "content": answer})
            self.history = self.history[-10:]
            if callback:
                callback(answer)

        threading.Thread(target=worker, name="TraderPlannerAI", daemon=True).start()
