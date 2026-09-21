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
MODEL_FALLBACKS = ("gpt-5.6-sol", "gpt-5.6-luna")
CHATGPT_WEB_URL = "https://chatgpt.com/"

ROLES = {
    "orchestrator": (
        "Master Agent: route the request to the right specialist(s), synthesize their outputs, "
        "and answer with a clear next action. Preserve app context and do not invent missing data."
    ),
    "form": (
        "Form Coach: turn incomplete trading-plan/journal information into precise fields, "
        "ask for missing values only when necessary, and flag contradictions."
    ),
    "strategy": (
        "Strategy Coach: separate market context, structure, liquidity, setup, trigger, invalidation, "
        "target and risk. Keep Smart Money/SMC, named ICT models, and ordinary candlestick patterns distinct."
    ),
    "psychology": (
        "Trading Psychology Coach: help with FOMO, revenge trading, hesitation, discipline, preparation, "
        "and post-trade review using concrete routines rather than vague motivation."
    ),
    "planner": (
        "Routine Coach: organize pre-market preparation, sessions, risk stops, review blocks and reminders."
    ),
    "academy": (
        "Academy Tutor: teach concepts with exact terminology and anatomy. Smart Money/SMC is a broad "
        "framework; ICT is a family of named models; candlestick patterns are a separate technical language."
    ),
    "product": (
        "Product Strategist: propose concrete UX/UI, reliability and workflow improvements for Trader Planner Pro "
        "with emphasis on persistent navigation, clear states, fast actions, and testable behavior."
    ),
}

SYSTEM_BASE = (
    "You are the AI system inside Trader Planner Pro. "
    "Be precise, practical and evidence-aware. Never invent live market values, never promise returns, "
    "and never claim certainty. Use only supplied app context for journal/profile/market values. "
    "When discussing trading setups, use context -> setup -> trigger -> invalidation -> target -> risk. "
    "Keep Smart Money/SMC, named ICT models, and candlestick patterns clearly separated. "
    "When the user asks about the app, give concrete in-app actions. "
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
        req = urllib.request.Request(
            f"{OLLAMA_BASE}/tags",
            headers={"User-Agent": "TraderPlannerPro/8.1.0"},
        )
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
            return (
                "Bullish Engulfing and Bearish Engulfing are candlestick patterns, not ICT setup names. "
                "Use trend/level/context plus a separately defined confirmation rule."
            )
        return (
            "Strategy Coach: separate context -> setup -> trigger -> invalidation -> target. "
            "Use the exact Academy definition for the selected model."
        )
    if role == "psychology":
        return (
            "Psychology check: pause -> name the emotion -> verify the checklist -> verify risk -> only then act. "
            "Record repeated FOMO/revenge triggers in the journal."
        )
    if role == "planner":
        return (
            "Routine: pre-market markup -> news -> session block -> hard stop -> journal -> review. "
            "Convert recurring actions into reminders."
        )
    if role == "academy":
        return (
            "Academy Tutor: Smart Money/SMC is a broad framework; ICT is a family of named models; "
            "candlestick patterns are separate. Keep their terminology and visuals separate."
        )
    if role == "product":
        return (
            "Product Strategist: prioritize persistent navigation, explicit live/cache/offline states, "
            "fast in-app actions, strong empty/error states, and a journal -> review -> improvement loop."
        )
    return (
        "Master Agent is in offline mode. Ask about your plan, journal, Academy, psychology, reminders or app workflow."
    )

def _responses_response(model, system_text, user_text):
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
    return (getattr(response, "output_text", "") or "").strip()

def _agents_response(model, system_text, user_text, role):
    """
    Real multi-agent orchestration using the OpenAI Agents SDK.

    A manager agent keeps synthesis control while specialist agents are exposed
    as tools, so a single user request can consult strategy + psychology +
    planner + Academy without losing the app-wide context.
    """
    from agents import Agent, Runner

    def specialist(name, specialist_key):
        return Agent(
            name=name,
            model=model,
            instructions=system_text + "\nSPECIALIST ROLE: " + ROLES[specialist_key],
        )

    specialists = {
        "form": specialist("Form Coach", "form"),
        "strategy": specialist("Strategy Coach", "strategy"),
        "psychology": specialist("Psychology Coach", "psychology"),
        "planner": specialist("Routine Coach", "planner"),
        "academy": specialist("Academy Tutor", "academy"),
        "product": specialist("Product Strategist", "product"),
    }

    toolset = [
        specialists["form"].as_tool(
            tool_name="consult_form_coach",
            tool_description="Consult the Form Coach to structure or complete plan/journal fields.",
        ),
        specialists["strategy"].as_tool(
            tool_name="consult_strategy_coach",
            tool_description="Consult the Strategy Coach about setup, structure, liquidity, trigger and risk.",
        ),
        specialists["psychology"].as_tool(
            tool_name="consult_psychology_coach",
            tool_description="Consult the Psychology Coach about discipline, FOMO, revenge and routines.",
        ),
        specialists["planner"].as_tool(
            tool_name="consult_routine_coach",
            tool_description="Consult the Routine Coach about schedules, sessions and reminders.",
        ),
        specialists["academy"].as_tool(
            tool_name="consult_academy_tutor",
            tool_description="Consult the Academy Tutor about exact concepts and terminology.",
        ),
        specialists["product"].as_tool(
            tool_name="consult_product_strategist",
            tool_description="Consult the Product Strategist about Trader Planner Pro UX/reliability improvements.",
        ),
    ]

    manager = Agent(
        name="Trader Planner Pro Master Agent",
        model=model,
        instructions=(
            system_text
            + "\nYou are the final synthesis agent. Choose specialist tools as needed, not automatically all at once. "
              "Use the user's requested role as a routing hint, but you may consult multiple specialists when the "
              "question crosses domains. Never reveal internal tool routing unless asked. Produce one coherent answer."
        ),
        tools=toolset,
    )

    async def run():
        result = await Runner.run(
            manager,
            input=(
                f"REQUESTED ROLE: {role}\n\n"
                f"APP CONTEXT:\n{user_text}"
            ),
            max_turns=10,
        )
        return str(result.final_output or "").strip()

    return asyncio.run(run())

class AIOrchestrator:
    """Reliable multi-agent AI with cloud, local, and offline recovery.

    Provider priority:
      1. OpenAI Agents SDK manager + specialist agents.
      2. OpenAI Responses API fallback.
      3. Local Ollama.
      4. Built-in offline guidance.

    A configured API key is required for cloud AI; the app never silently
    claims that offline guidance is generative cloud AI.
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
            "agents": bool(cloud["enabled"]),
            "models": ollama_models,
            "model": cloud["model"] if cloud["enabled"] else (ollama_models[0] if ollama_models else self.model),
            "provider": "OpenAI Multi-Agent" if cloud["enabled"] else ("Ollama" if ollama_online else "Offline"),
            "last_provider": self.last_provider,
            "last_error": self.last_error,
        }

    def respond(self, role, user_message, context="", callback=None):
        role = role if role in self.roles else "orchestrator"
        user_message = str(user_message or "").strip()
        if not user_message:
            return

        self.history.append({"role": "user", "content": user_message})
        self.history = self.history[-10:]
        recent = json.dumps(self.history[-8:], ensure_ascii=False)
        combined_context = (
            f"{context}\n\nRECENT CHAT:\n{recent}\n\nUSER REQUEST:\n{user_message}"
        )

        def worker():
            answer = None
            self.last_error = ""
            self.last_provider = "none"

            cloud = cloud_status()
            if cloud["enabled"]:
                role_text = self.roles.get(role, self.roles["orchestrator"])
                system_text = SYSTEM_BASE + "\nCURRENT ROUTING ROLE: " + role_text
                try:
                    answer = _agents_response(self.model, system_text, combined_context, role)
                    if answer:
                        self.last_provider = f"OpenAI Multi-Agent • {self.model}"
                except Exception as exc:
                    self.last_error = f"Agents SDK: {type(exc).__name__}: {exc}"

                if not answer:
                    for model in (self.model,) + tuple(m for m in MODEL_FALLBACKS if m != self.model):
                        try:
                            answer = _responses_response(model, system_text, combined_context)
                            if answer:
                                self.last_provider = f"OpenAI Responses • {model}"
                                break
                        except Exception as exc:
                            self.last_error = f"OpenAI Responses: {type(exc).__name__}: {exc}"

            if not answer:
                try:
                    online, models = ollama_status()
                    if online and models:
                        preferred = [m for m in MODEL_FALLBACKS if m in models]
                        local_model = preferred[0] if preferred else models[0]
                        answer = ollama_chat(
                            local_model,
                            [
                                {
                                    "role": "system",
                                    "content": SYSTEM_BASE + self.roles.get(role, self.roles["orchestrator"]),
                                },
                                {
                                    "role": "user",
                                    "content": combined_context,
                                },
                            ],
                        )
                        if answer:
                            self.last_provider = f"Ollama • {local_model}"
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

        threading.Thread(target=worker, name="TraderPlannerAIMaster", daemon=True).start()
