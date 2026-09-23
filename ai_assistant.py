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
