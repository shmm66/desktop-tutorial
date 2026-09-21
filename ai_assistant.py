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
DEFAULT_MODEL = "gpt-5.6-luna"
REASONING_EFFORT = "high"

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
        headers={"Content-Type": "application/json", "User-Agent": "TraderPlannerPro/7.8"},
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
    key = _read_openai_key()
    if not key:
        return {"enabled": False, "model": DEFAULT_MODEL}
    try:
        import agents  # noqa: F401
        return {"enabled": True, "model": DEFAULT_MODEL}
    except Exception:
        return {"enabled": False, "model": DEFAULT_MODEL}


def _fallback(role, user_message, context):
    lower = f"{user_message} {context}".lower()
    if role == "orchestrator":
        return (
            "Master Agent\\n"
            "I will break the request into context, setup, trigger, invalidation, target, risk and next action. "
            "I will keep SMC, ICT and candlestick terminology separate and only use supplied live-data context."
        )
    if role == "form":
        return (
            "Form Coach\n"
            "• Symbol / market / direction\n"
            "• Entry / SL / TP / position size\n"
            "• Setup + market structure + liquidity\n"
            "• Emotion before/during/after\n"
            "• Result in R + lesson\n"
            "Complete the checklist before saving."
        )
    if role == "strategy":
        if "engulf" in lower:
            return (
                "This is a candlestick pattern, not an ICT model. "
                "Bullish engulfing and bearish engulfing are separate patterns. "
                "Use context and confirmation rather than treating the pattern as a standalone signal."
            )
        return (
            "Strategy Coach\n"
            "Separate: context → setup → trigger → invalidation → target. "
            "Use only the documented Academy definition for the selected model."
        )
    if role == "psychology":
        return (
            "Psychology Coach\n"
            "Pause → name the emotion → check the rules → check risk → act only if the checklist passes. "
            "Record repeated FOMO/revenge triggers in the journal."
        )
    if role == "planner":
        return (
            "Routine Coach\n"
            "Pre-market markup → news check → trading block → hard stop → journal → review. "
            "Convert recurring items into reminders."
        )
    if role == "academy":
        return (
            "Academy Tutor\n"
            "Smart Money is a broad framework; ICT uses its own named models and terminology. "
            "Read the exact source visual and the definition shown in the selected Academy card."
        )
    return (
        "Product Strategist\n"
        "Prioritize a calm dashboard, fewer clicks, clear state badges, responsive cards, "
        "strong empty/error states, and a fast journal → review → improvement loop."
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

    def status(self):
        ollama_online, ollama_models = ollama_status()
        cloud = cloud_status()
        return {
            "online": cloud["enabled"] or ollama_online,
            "cloud": cloud["enabled"],
            "ollama": ollama_online,
            "models": ollama_models,
            "model": cloud["model"] if cloud["enabled"] else (ollama_models[0] if ollama_models else self.model),
        }

    def _build_cloud_agents(self):
        if self._cloud_agents is not None:
            return self._cloud_agents
        from agents import Agent

        common = (
            "You are inside Trader Planner Pro, a trading journal/academy desktop app. "
            "Never promise returns or invent market data. "
            "Use the supplied app context. Be precise. "
            "Keep broad Smart Money/SMC concepts distinct from named ICT models. "
            "Candlestick patterns must not be relabeled as ICT setups. "
        )
        try:
            from agents import ModelSettings
            from openai.types.shared import Reasoning
            model_settings = ModelSettings(
                reasoning=Reasoning(effort=REASONING_EFFORT),
                verbosity="low",
            )
        except Exception:
            model_settings = None

        specialists = {}
        for key, instruction in ROLES.items():
            kwargs = {
                "name": key.replace("_", " ").title() + " Agent",
                "model": self.model,
                "instructions": common + instruction,
            }
            if model_settings is not None:
                kwargs["model_settings"] = model_settings
            specialists[key] = Agent(**kwargs)

        triage_kwargs = {
            "name":"Trader Planner Master Agent",
            "model":self.model,
            "instructions":(
                common
                + "Route the request to the most appropriate specialist. "
                  "You may hand off form, strategy, psychology, planner, academy, or product requests. "
                  "For product requests, propose concrete improvements and explain why they help workflow. "
                  "Return one clear, practical answer with no made-up facts."
            ),
            "handoffs":list(specialists.values()),
        }
        if model_settings is not None:
            triage_kwargs["model_settings"] = model_settings
        triage = Agent(**triage_kwargs)
        specialists["orchestrator"] = triage
        self._cloud_agents = specialists
        return specialists

    def _cloud_respond(self, role, user_message, context):
        api_key = _read_openai_key()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        os.environ["OPENAI_API_KEY"] = api_key
        from agents import Runner

        agents_map = self._build_cloud_agents()
        agent = agents_map.get("orchestrator") if role in {"orchestrator","product"} else agents_map.get(role, agents_map["orchestrator"])
        result = asyncio.run(
            Runner.run(
                agent,
                f"APP CONTEXT:\n{context}\n\nUSER QUESTION:\n{user_message}",
                max_turns=6,
            )
        )
        return str(result.final_output or "").strip()

    def respond(self, role, user_message, context="", callback=None):
        role = role if role in self.roles else "form"

        def worker():
            answer = None
            try:
                if cloud_status()["enabled"]:
                    answer = self._cloud_respond(role, user_message, context)
            except Exception:
                answer = None

            if not answer:
                try:
                    online, models = ollama_status()
                    model = self.model
                    if online and models:
                        model = model if model in models else models[0]
                        answer = ollama_chat(
                            model,
                            [
                                {
                                    "role": "system",
                                    "content": (
                                        "You are a practical assistant inside a trading journal. "
                                        "Use only supplied context. Never guarantee outcomes. "
                                        f"Your role: {self.roles[role]}"
                                    ),
                                },
                                {
                                    "role": "user",
                                    "content": f"APP CONTEXT:\n{context}\n\nUSER:\n{user_message}",
                                },
                            ],
                        )
                except Exception:
                    answer = None

            if not answer:
                answer = _fallback(role, user_message, context)

            if callback:
                callback(answer)

        threading.Thread(target=worker, name="TraderPlannerAI", daemon=True).start()
