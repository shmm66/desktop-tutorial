from datetime import date

from app.core.database import connect, initialize
from app.domains.planner.default_schedule import default_trader_day
from app.repositories.planner_repository import PlannerRepository
from app.services.planner import DailyPlannerService


def test_daily_plan_round_trip_and_toggle(tmp_path):
    db = tmp_path / "planner.db"
    initialize(db)
    conn = connect(db)
    try:
        repo = PlannerRepository(conn)
        service = DailyPlannerService(repo)
        plan = service.load_or_create(date(2026, 9, 3))
        assert len(plan.tasks) >= 10
        assert plan.completed_count == 0
        updated = service.toggle_task(plan, 0)
        assert updated.completed_count == 1
        reloaded = repo.get(plan.plan_date)
        assert reloaded is not None
        assert reloaded.tasks[0].completed is True
        assert reloaded.completion_percent > 0
    finally:
        conn.close()


def test_default_schedule_has_morning_and_evening_exercise_and_2330_sleep():
    plan = default_trader_day(date(2026, 9, 3))
    health = [task.title for task in plan.tasks if task.category == "health"]
    assert any("Morning" in title for title in health)
    assert any("Evening" in title for title in health)
    sleep = next(task for task in plan.tasks if task.title == "Sleep")
    assert sleep.start_time == "23:30"
    assert sleep.end_time == "07:30"
