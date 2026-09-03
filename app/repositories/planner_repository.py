from __future__ import annotations

import json
import sqlite3
from datetime import date
from uuid import UUID

from app.domains.planner.models import DailyPlan, DailyTask


class PlannerRepository:
    """SQLite persistence for editable daily plans."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save(self, plan: DailyPlan) -> DailyPlan:
        payload = json.dumps(
            [{"id": str(task.id), "title": task.title, "start_time": task.start_time,
              "end_time": task.end_time, "category": task.category, "completed": task.completed}
             for task in plan.tasks],
            ensure_ascii=False,
        )
        self.conn.execute(
            """INSERT INTO daily_plans(plan_date, tasks_json, completed)
               VALUES (?, ?, ?)
               ON CONFLICT(plan_date) DO UPDATE SET
                 tasks_json=excluded.tasks_json,
                 completed=excluded.completed""",
            (plan.plan_date.isoformat(), payload,
             int(plan.completed_count == len(plan.tasks) and bool(plan.tasks))),
        )
        self.conn.commit()
        return plan

    def get(self, plan_date: date) -> DailyPlan | None:
        row = self.conn.execute(
            "SELECT plan_date, tasks_json FROM daily_plans WHERE plan_date = ?",
            (plan_date.isoformat(),),
        ).fetchone()
        if row is None:
            return None
        tasks = tuple(
            DailyTask(title=item["title"], start_time=item["start_time"], end_time=item["end_time"],
                      category=item.get("category", "routine"),
                      id=UUID(item["id"]), completed=bool(item.get("completed", False)))
            for item in json.loads(row["tasks_json"] or "[]")
        )
        return DailyPlan(plan_date, tasks)
