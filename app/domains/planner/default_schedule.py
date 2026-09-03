from __future__ import annotations

from datetime import date
from .models import DailyPlan, DailyTask


def default_trader_day(plan_date: date) -> DailyPlan:
    """Balanced default day; every item remains editable by the user."""
    tasks = (
        DailyTask("Wake up + hydration", "07:30", "08:00", "health"),
        DailyTask("Morning walk / light exercise", "08:00", "08:30", "health"),
        DailyTask("Breakfast", "08:30", "09:00", "nutrition"),
        DailyTask("Market analysis & markup", "09:00", "13:00", "market"),
        DailyTask("Lunch + screen break", "13:00", "14:00", "nutrition"),
        DailyTask("Recovery / personal time", "14:00", "14:45", "rest"),
        DailyTask("Pre-trade review + checklist", "14:45", "15:30", "trading"),
        DailyTask("Trading session", "15:30", "19:00", "trading"),
        DailyTask("Evening walk / exercise", "19:00", "19:30", "health"),
        DailyTask("Dinner", "19:30", "20:15", "nutrition"),
        DailyTask("Journal + daily review", "20:15", "20:45", "review"),
        DailyTask("Free time / family / hobby", "20:45", "22:30", "leisure"),
        DailyTask("Screen-free wind-down", "22:30", "23:30", "sleep"),
        DailyTask("Sleep", "23:30", "07:30", "sleep"),
    )
    return DailyPlan(plan_date, tasks)
