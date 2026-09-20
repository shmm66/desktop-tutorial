from __future__ import annotations
import json, shutil, subprocess, threading, urllib.request
from datetime import datetime
from pathlib import Path

ROOT=Path.home()/"TraderPlannerPro"
AI_CACHE=ROOT/"ai_memory.json"
AGENTS={"planner":"Trading Planner Agent","strategy":"Strategy Coach Agent","psychology":"Psychology & Discipline Agent","journal":"Journal Coach Agent"}
SYSTEM_PROMPT=("You are Trader Planner Pro's local trading coach. Give educational, structured, risk-aware help. "
               "Do not promise profits or invent market data. Help users fill forms, follow their own plan, "
               "review routines, manage emotions, and create explicit checklists.")

def _load():
    try:
        d=json.loads(AI_CACHE.read_text(encoding="utf-8")); return d if isinstance(d,dict) else {}
    except Exception: return {}
def _save(d):
    try:
        AI_CACHE.parent.mkdir(parents=True,exist_ok=True); AI_CACHE.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
    except Exception: pass
def ollama_models():
    if not shutil.which("ollama"): return []
    try:
        p=subprocess.run(["ollama","list"],capture_output=True,text=True,timeout=5)
        return [line.split()[0] for line in p.stdout.splitlines()[1:] if line.split()]
    except Exception: return []
def fallback_response(agent,text,error=None):
    if agent=="psychology":
        return "Psychology coach:\n• Name the emotion before the trade.\n• State the rule you must not break.\n• Define your session stop condition.\n• Record one lesson after the trade."
    if agent=="strategy":
        return "Strategy coach:\nBias → Location → Liquidity → Trigger → Invalidation → Target → Risk.\nA missing step means the setup is incomplete."
    if agent=="journal":
        return "Journal coach:\nComplete Symbol, Direction, Timeframe, Entry, SL, TP, Setup, Emotion Before, Result and Lesson. Keep entries factual and repeatable."
    return "Planner coach:\nTurn the goal into a checklist, assign time, define the stop condition and schedule a review reminder."
def ask(agent,user_text,context=None,callback=None,model=None):
    models=[model] if model else ollama_models()
    selected=next((m for m in models if m),None)
    prompt=f"{SYSTEM_PROMPT}\nRole: {AGENTS.get(agent,AGENTS['planner'])}\nContext: {json.dumps(context or {},ensure_ascii=False)}\nUser: {user_text}"
    if not selected:
        ans=fallback_response(agent,user_text)
        _record(agent,user_text,ans)
        if callback: callback(ans)
        return {"mode":"fallback","model":None}
    def worker():
        try:
            body=json.dumps({"model":selected,"prompt":prompt,"stream":False}).encode()
            req=urllib.request.Request("http://127.0.0.1:11434/api/generate",data=body,headers={"Content-Type":"application/json"},method="POST")
            with urllib.request.urlopen(req,timeout=60) as res: ans=json.loads(res.read().decode()).get("response","").strip()
            if not ans: raise RuntimeError("Empty local model response")
        except Exception as exc:
            ans=fallback_response(agent,user_text,exc)
        _record(agent,user_text,ans)
        if callback: callback(ans)
    threading.Thread(target=worker,daemon=True).start()
    return {"mode":"ollama","model":selected}
def _record(agent,user,answer):
    d=_load(); d.setdefault("sessions",[]).append({"time":datetime.now().isoformat(timespec="seconds"),"agent":agent,"user":user,"answer":answer}); d["sessions"]=d["sessions"][-100:]; _save(d)
