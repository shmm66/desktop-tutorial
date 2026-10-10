"""Fast, local and deterministic performance analysis for Trader Planner Pro.

No network calls, API keys, model downloads or background workers are used.
All metrics are computed from the selected profile's saved journal rows.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from math import inf, isfinite


def _number(value) -> float:
    try:
        text = str(value if value is not None else "").strip().replace(",", "")
        if not text or text in {"—", "-", "N/A", "n/a"}:
            return 0.0
        result = float(text)
        return result if isfinite(result) else 0.0
    except (TypeError, ValueError, OverflowError):
        return 0.0


def _r_value(row: dict) -> tuple[float, bool]:
    raw = row.get("Result (R)", row.get("R", ""))
    missing = raw is None or not str(raw).strip()
    return _number(raw), missing


def _classify(row: dict, r_value: float) -> str:
    if r_value > 0:
        return "win"
    if r_value < 0:
        return "loss"
    result = str(row.get("Result", "")).strip().lower()
    if result in {"win", "won", "winner"}:
        return "win"
    if result in {"loss", "lost", "loser"}:
        return "loss"
    pnl = _number(row.get("P&L", 0))
    if pnl > 0:
        return "win"
    if pnl < 0:
        return "loss"
    return "breakeven"


def _group_summary(groups: dict) -> list[dict]:
    result = []
    for name, vals in groups.items():
        rs = vals["rs"]
        count = vals["count"]
        result.append({
            "name": name,
            "count": count,
            "wins": vals["wins"],
            "win_rate": vals["wins"] / count * 100.0 if count else 0.0,
            "net_r": sum(rs),
            "avg_r": sum(rs) / count if count else 0.0,
        })
    return sorted(result, key=lambda x: (x["net_r"], x["count"]), reverse=True)


def analyse_journal(rows) -> dict:
    """Return auditable statistics; blank R fields are never inferred as a profit."""
    trades = [dict(row) for row in (rows or []) if isinstance(row, dict)]
    # Drawdown/equity curves must follow trade dates, not the current display order.
    def date_order(row):
        raw = str(row.get("Date") or "").strip()[:10]
        try:
            from datetime import date
            return date.fromisoformat(raw).toordinal()
        except (TypeError, ValueError):
            return 0
    trades.sort(key=date_order)
    values = []
    outcomes = []
    missing_r = 0
    cumulative = 0.0
    peak = 0.0
    max_drawdown = 0.0
    equity_curve = [0.0]
    max_losing_streak = 0
    losing_streak = 0
    setup_groups, session_groups, emotion_groups = {}, {}, {}
    mistakes = Counter()

    for row in trades:
        r, missing = _r_value(row)
        if missing:
            missing_r += 1
        values.append(r)
        outcome = _classify(row, r)
        outcomes.append(outcome)
        cumulative += r
        peak = max(peak, cumulative)
        max_drawdown = max(max_drawdown, peak - cumulative)
        equity_curve.append(cumulative)
        if outcome == "loss":
            losing_streak += 1
            max_losing_streak = max(max_losing_streak, losing_streak)
        else:
            losing_streak = 0

        setup = str(row.get("Setup") or "Unspecified").strip() or "Unspecified"
        session = str(row.get("Session") or "Unspecified").strip() or "Unspecified"
        emotion = str(row.get("Emotion During") or row.get("Emotion Before") or "Unspecified").strip() or "Unspecified"
        for groups, name in ((setup_groups, setup), (session_groups, session), (emotion_groups, emotion)):
            group = groups.setdefault(name, {"count": 0, "wins": 0, "rs": []})
            group["count"] += 1
            group["wins"] += int(outcome == "win")
            group["rs"].append(r)

        mistake = str(row.get("Mistake") or "").strip()
        if mistake and mistake.lower() not in {"none", "no", "none recorded", "—", "-"}:
            mistakes[mistake] += 1

    wins = outcomes.count("win")
    losses = outcomes.count("loss")
    breakeven = outcomes.count("breakeven")
    gross_profit = sum(v for v in values if v > 0)
    gross_loss = sum(-v for v in values if v < 0)
    count = len(trades)
    net_r = sum(values)
    profit_factor = gross_profit / gross_loss if gross_loss else (inf if gross_profit > 0 else 0.0)
    win_values = [v for v, outcome in zip(values, outcomes) if outcome == "win" and v > 0]
    loss_values = [v for v, outcome in zip(values, outcomes) if outcome == "loss" and v < 0]

    return {
        "count": count,
        "wins": wins,
        "losses": losses,
        "breakeven": breakeven,
        "win_rate": wins / count * 100.0 if count else 0.0,
        "net_r": net_r,
        "expectancy_r": net_r / count if count else 0.0,
        "avg_win_r": sum(win_values) / len(win_values) if win_values else 0.0,
        "avg_loss_r": sum(loss_values) / len(loss_values) if loss_values else 0.0,
        "gross_profit_r": gross_profit,
        "gross_loss_r": gross_loss,
        "profit_factor": profit_factor,
        "max_drawdown_r": max_drawdown,
        "max_losing_streak": max_losing_streak,
        "missing_r_count": missing_r,
        "equity_curve": equity_curve,
        "by_setup": _group_summary(setup_groups),
        "by_session": _group_summary(session_groups),
        "by_emotion": _group_summary(emotion_groups),
        "mistakes": mistakes.most_common(8),
    }
