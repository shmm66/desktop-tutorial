from __future__ import annotations

from dataclasses import replace
from datetime import date
from app.domains.planner.models import DailyPlan


class DailyPlannerService:
    def toggle_task(self, plan: DailyPlan, task_index: int) -> DailyPlan:
        if task_index < 0 or task_index >= len(plan.tasks):
            raise IndexError("task_index out of range")
        tasks = list(plan.tasks)
        tasks[task_index] = replace(tasks[task_index], completed=not tasks[task_index].completed)
        return replace(plan, tasks=tuple(tasks))

    def progress(self, plan: DailyPlan) -> dict[str, float | int]:
        return {"completed": plan.completed_count, "total": len(plan.tasks), "percent": plan.completion_percent}
