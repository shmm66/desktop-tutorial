from datetime import date

from app.core.database import connect, initialize
from app.core.migrations import migrate
from app.domains.planner.default_schedule import default_trader_day
from app.repositories.planner_repository import PlannerRepository


def test_planner_round_trip_persists_completion(tmp_path):
    db = tmp_path / "planner.sqlite"
    initialize(db)
    conn = connect(db)
    try:
        assert migrate(conn) == 3
        repository = PlannerRepository(conn)
        plan = default_trader_day(date(2026, 9, 3))
        tasks = list(plan.tasks)
        from dataclasses import replace
        saved = replace(plan, tasks=tuple(replace(task, completed=(i == 2)) for i, task in enumerate(tasks)))
        repository.save(saved)
        loaded = repository.get(plan.plan_date)
        assert loaded is not None
        assert loaded.completed_count == 1
        assert loaded.tasks[2].title == "Breakfast"
    finally:
        conn.close()
