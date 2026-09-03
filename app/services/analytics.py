from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable


@dataclass(frozen=True, slots=True)
class PerformanceSummary:
    trades: int
    wins: int
    losses: int
    win_rate: float
    net_r: float
    average_r: float


def summarize(results_r: Iterable[float]) -> PerformanceSummary:
    values = list(results_r)
    wins = sum(value > 0 for value in values)
    losses = sum(value < 0 for value in values)
    net_r = sum(values)
    return PerformanceSummary(
        trades=len(values),
        wins=wins,
        losses=losses,
        win_rate=(wins / len(values) * 100) if values else 0.0,
        net_r=net_r,
        average_r=mean(values) if values else 0.0,
    )
