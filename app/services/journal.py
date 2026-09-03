from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.domains.journal.models import AssetClass, JournalEntry
from app.repositories.journal_repository import JournalRepository


@dataclass(frozen=True)
class JournalSummary:
    trades: int
    winners: int
    losers: int
    gross_pnl: Decimal
    net_pnl: Decimal


class JournalService:
    """Application use-cases for journal records; persistence is injected."""

    def __init__(self, repository: JournalRepository) -> None:
        self.repository = repository

    def record(self, entry: JournalEntry) -> JournalEntry:
        return self.repository.save(entry)

    def get(self, entry_id: str) -> JournalEntry | None:
        return self.repository.get(entry_id)

    def entries(self, asset_class: AssetClass | None = None) -> list[JournalEntry]:
        return self.repository.list(asset_class.value if asset_class else None)

    def remove(self, entry_id: str) -> bool:
        return self.repository.delete(entry_id)

    def summary(self, asset_class: AssetClass | None = None) -> JournalSummary:
        entries = self.entries(asset_class)
        closed = [entry for entry in entries if entry.net_pnl is not None]
        gross = sum((entry.gross_pnl or Decimal("0") for entry in closed), Decimal("0"))
        net = sum((entry.net_pnl or Decimal("0") for entry in closed), Decimal("0"))
        winners = sum(1 for entry in closed if (entry.net_pnl or Decimal("0")) > 0)
        losers = sum(1 for entry in closed if (entry.net_pnl or Decimal("0")) < 0)
        return JournalSummary(len(entries), winners, losers, gross, net)
