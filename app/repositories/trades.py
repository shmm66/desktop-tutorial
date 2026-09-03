from __future__ import annotations

import sqlite3
from typing import Any

from app.core.models import Trade
from .base import Repository


class TradeRepository(Repository):
    def add(self, trade: Trade) -> int:
        fields = trade.__dataclass_fields__.keys()
        columns = ", ".join(fields)
        placeholders = ", ".join("?" for _ in fields)
        values = tuple(getattr(trade, field) for field in fields)
        cur = self.execute(f"INSERT INTO trades ({columns}) VALUES ({placeholders})", values)
        self.commit()
        return int(cur.lastrowid)

    def list_by_market(self, market: str) -> list[sqlite3.Row]:
        return list(self.execute("SELECT * FROM trades WHERE market = ? ORDER BY created_at DESC, id DESC", (market,)))

    def get(self, trade_id: int) -> sqlite3.Row | None:
        return self.execute("SELECT * FROM trades WHERE id = ?", (trade_id,)).fetchone()
