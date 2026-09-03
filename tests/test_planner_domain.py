from datetime import date
from app.domains.planner.models import DailyPlan, DailyTask
from app.services.planner import DailyPlannerService


def test_daily_plan_tracks_completion() -> None:
    plan = DailyPlan(date(2026, 9, 3), (DailyTask("Market markup", "09:00", "13:00", "market"), DailyTask("Trading", "15:30", "19:00", "trading")))
    updated = DailyPlannerService().toggle_task(plan, 0)
    assert updated.completed_count == 1
    assert updated.completion_percent == 50.0
