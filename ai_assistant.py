from __future__ import annotations

import json
import threading
import urllib.request
from datetime import datetime
from pathlib import Path


OLLAMA_BASE = "http://localhost:11434/api"
DEFAULT_MODEL = "gemma3:4b"
ROLES = {
    "form": "Form Coach: help the trader fill journal, plan and checklist fields with precise, concise prompts.",
    "strategy": "Strategy Coach: explain the app's ICT/SMC/candlestick rules exactly as documented; never invent a rule.",
    "psychology": "Trading Psychology Coach: help with FOMO, revenge trading, discipline, preparation and post-trade review without judging the person.",
    "planner": "Routine & Reminder Coach: organize the trader's day, sessions, review blocks and reminders.",
}


def _post_json(url, payload, timeout=25):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "TraderPlannerPro/7.5"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def ollama_status():
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE}/tags", headers={"User-Agent": "TraderPlannerPro/7.5"})
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


class AIOrchestrator:
    """Local-first multi-agent trader coach.

    It uses a local Ollama model when available and otherwise falls back to
    deterministic guidance based on the application's own forms/content.
    """

    def __init__(self, model=DEFAULT_MODEL):
        self.model = model
        self.roles = ROLES

    def status(self):
        online, models = ollama_status()
        return {"online": online, "models": models, "model": self.model}

    def _fallback(self, role, user_message, context):
        lower = f"{user_message} {context}".lower()
        if role == "form":
            return (
                "Form Coach\n"
                "1) Symbol: enter the exact instrument.\n"
                "2) Direction: LONG or SHORT.\n"
                "3) Entry/SL/TP: record the actual levels, not planned levels.\n"
                "4) Setup: choose the documented strategy/model.\n"
                "5) Lesson/Notes: write one concrete observation.\n"
                "Use the checklist before saving the trade."
            )
        if role == "strategy":
            if "engulf" in lower:
                return (
                    "Bullish/Bearish Engulfing is a candlestick reversal pattern. "
                    "The defining feature is the second candle's body overtaking the prior body; "
                    "do not replace it with an ICT setup. Use market context and confirmation."
                )
            return (
                "Strategy Coach\n"
                "Use the Academy definition shown in the app. Separate context, setup, trigger, "
                "invalidation and target. A pattern or ICT concept is not a guaranteed outcome."
            )
        if role == "psychology":
            return (
                "Psychology Coach\n"
                "Pause after a loss, name the emotion, check your written rules, and only continue "
                "when the checklist is satisfied. Track repeated FOMO/revenge triggers in Notes."
            )
        return (
            "Planner Coach\n"
            "Keep a fixed pre-market routine, a session-specific trading block, a hard stop time, "
            "and a post-trade journal block. Turn recurring tasks into reminders."
        )

    def respond(self, role, user_message, context="", callback=None):
        role = role if role in self.roles else "form"

        def worker():
            system = (
                "You are a practical assistant inside a desktop trading journal. "
                "Never claim certainty or guaranteed returns. "
                "Do not invent market data. "
                "Use only the supplied application context and documented strategy definitions. "
                f"Your role is: {self.roles[role]}"
            )
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": f"APP CONTEXT:\n{context}\n\nUSER:\n{user_message}"},
            ]
            try:
                online, models = ollama_status()
                model = self.model if self.model in models else (models[0] if models else self.model)
                if online and models:
                    answer = ollama_chat(model, messages)
                else:
                    answer = self._fallback(role, user_message, context)
            except Exception:
                answer = self._fallback(role, user_message, context)
            if callback:
                callback(answer)

        threading.Thread(target=worker, daemon=True).start()
