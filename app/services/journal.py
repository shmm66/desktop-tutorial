from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

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
    def __init__(self, repository: JournalRepository) -> None:
        self.repository = repository

    def record(self, entry: JournalEntry) -> JournalEntry:
        return self.repository.save(entry)

    def get(self, entry_id: UUID) -> JournalEntry | None:
        return self.repository.get(entry_id)

    def entries(self, asset_class: AssetClass | None = None) -> list[JournalEntry]:
        return self.repository.list(asset_class.value if asset_class else None)

    def remove(self, entry_id: UUID) -> bool:
        return self.repository.delete(entry_id)

    def summary(self, asset_class: AssetClass | None = None) -> JournalSummary:
        entries = self.entries(asset_class)
        gross = sum((e.gross_pnl() for e in entries), Decimal("0"))
        net = sum((e.net_pnl() for e in entries), Decimal("0"))
        winners = sum(1 for e in entries if e.net_pnl() > 0)
        losers = sum(1 for e in entries if e.net_pnl() < 0)
        return JournalSummary(len(entries), winners, losers, gross, net)
