from __future__ import annotations

from dataclasses import replace
from datetime import date

from app.domains.planner.models import DailyPlan
from app.repositories.planner_repository import PlannerRepository


class DailyPlannerService:
    def __init__(self, repository: PlannerRepository) -> None:
        self.repository = repository

    def load_or_create(self, plan_date: date) -> DailyPlan:
        from app.domains.planner.default_schedule import default_trader_day
        return self.repository.get(plan_date) or self.repository.save(default_trader_day(plan_date))

    def toggle_task(self, plan: DailyPlan, task_index: int) -> DailyPlan:
        if not 0 <= task_index < len(plan.tasks):
            raise IndexError("task_index out of range")
        tasks = list(plan.tasks)
        tasks[task_index] = replace(tasks[task_index], completed=not tasks[task_index].completed)
        return self.repository.save(replace(plan, tasks=tuple(tasks)))

    def progress(self, plan: DailyPlan) -> dict[str, float | int]:
        return {"completed": plan.completed_count, "total": len(plan.tasks), "percent": plan.completion_percent}
