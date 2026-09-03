from __future__ import annotations

from datetime import date
from .models import DailyPlan, DailyTask


def default_trader_day(plan_date: date) -> DailyPlan:
    tasks = (
        DailyTask("Wake up + hydration", "07:30", "08:00", "health"),
        DailyTask("Breakfast", "08:00", "08:30", "nutrition"),
        DailyTask("Market preparation", "08:30", "09:00", "market"),
        DailyTask("Market analysis & markup", "09:00", "13:00", "market"),
        DailyTask("Lunch + screen break", "13:00", "14:00", "nutrition"),
        DailyTask("Exercise / walk", "14:00", "15:00", "health"),
        DailyTask("Pre-trade review + checklist", "15:00", "15:30", "trading"),
        DailyTask("Trading session", "15:30", "19:00", "trading"),
        DailyTask("Dinner", "19:30", "20:00", "nutrition"),
        DailyTask("Journal + daily review", "20:00", "20:30", "review"),
        DailyTask("Free time / family / hobby", "20:30", "22:30", "leisure"),
        DailyTask("Screen-off wind-down", "22:30", "23:00", "sleep"),
        DailyTask("Sleep", "23:00", "07:30", "sleep"),
    )
    return DailyPlan(plan_date, tasks)
