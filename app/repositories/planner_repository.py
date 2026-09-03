from __future__ import annotations

import json
import sqlite3
from datetime import date
from uuid import UUID

from app.domains.planner.models import DailyPlan, DailyTask


class PlannerRepository:
    """SQLite persistence adapter for DailyPlan; no UI dependencies."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def get(self, plan_date: date) -> DailyPlan | None:
        row = self.conn.execute(
            "SELECT id, plan_date, tasks_json FROM daily_plans WHERE plan_date = ?",
            (plan_date.isoformat(),),
        ).fetchone()
        if row is None:
            return None
        tasks = tuple(self._task_from_dict(item) for item in json.loads(row["tasks_json"] or "[]"))
        return DailyPlan(plan_date=date.fromisoformat(row["plan_date"]), tasks=tasks, id=UUID(str(row["id"])) if self._is_uuid(row["id"]) else UUID(int=int(row["id"])))

    def save(self, plan: DailyPlan) -> DailyPlan:
        payload = json.dumps([self._task_to_dict(t) for t in plan.tasks], ensure_ascii=False, separators=(",", ":"))
        existing = self.conn.execute("SELECT id FROM daily_plans WHERE plan_date = ?", (plan.plan_date.isoformat(),)).fetchone()
        if existing is None:
            self.conn.execute(
                "INSERT INTO daily_plans(plan_date, tasks_json, completed) VALUES(?, ?, ?)",
                (plan.plan_date.isoformat(), payload, plan.completed_count),
            )
        else:
            self.conn.execute(
                "UPDATE daily_plans SET tasks_json = ?, completed = ? WHERE plan_date = ?",
                (payload, plan.completed_count, plan.plan_date.isoformat()),
            )
        self.conn.commit()
        return plan

    @staticmethod
    def _task_to_dict(task: DailyTask) -> dict[str, object]:
        return {"id": str(task.id), "title": task.title, "start_time": task.start_time, "end_time": task.end_time, "category": task.category, "completed": task.completed}

    @staticmethod
    def _task_from_dict(item: dict[str, object]) -> DailyTask:
        return DailyTask(title=str(item["title"]), start_time=str(item["start_time"]), end_time=str(item["end_time"]), category=str(item.get("category", "routine")), id=UUID(str(item["id"])), completed=bool(item.get("completed", False)))

    @staticmethod
    def _is_uuid(value: object) -> bool:
        try:
            UUID(str(value)); return True
        except (ValueError, AttributeError, TypeError):
            return False
