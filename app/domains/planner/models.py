from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DailyTask:
    title: str
    start_time: str
    end_time: str
    category: str = "routine"
    id: UUID = field(default_factory=uuid4)
    completed: bool = False


@dataclass(frozen=True)
class DailyPlan:
    plan_date: date
    tasks: tuple[DailyTask, ...]
    id: UUID = field(default_factory=uuid4)

    @property
    def completed_count(self) -> int:
        return sum(task.completed for task in self.tasks)

    @property
    def completion_percent(self) -> float:
        return (self.completed_count / len(self.tasks) * 100) if self.tasks else 0.0
