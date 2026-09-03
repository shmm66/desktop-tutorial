from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.domains.journal.models import JournalEntry


class JournalRepository(Protocol):
    def save(self, entry: JournalEntry) -> JournalEntry: ...
    def get(self, entry_id: UUID) -> JournalEntry | None: ...
    def list(self, asset_class: str | None = None) -> list[JournalEntry]: ...
    def delete(self, entry_id: UUID) -> bool: ...


class InMemoryJournalRepository:
    """Deterministic repository for UI/application tests; persistence is injected later."""

    def __init__(self) -> None:
        self._items: dict[UUID, JournalEntry] = {}

    def save(self, entry: JournalEntry) -> JournalEntry:
        self._items[entry.id] = entry
        return entry

    def get(self, entry_id: UUID) -> JournalEntry | None:
        return self._items.get(entry_id)

    def list(self, asset_class: str | None = None) -> list[JournalEntry]:
        values = list(self._items.values())
        if asset_class is None:
            return values
        return [item for item in values if item.asset_class.value == asset_class]

    def delete(self, entry_id: UUID) -> bool:
        return self._items.pop(entry_id, None) is not None
