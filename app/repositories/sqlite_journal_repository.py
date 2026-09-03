from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from decimal import Decimal

from app.domains.journal.models import AssetClass, JournalEntry, TradeDirection, TradeOutcome


class SQLiteJournalRepository:
    """SQLite-backed JournalRepository implementation for production use."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> JournalEntry:
        opened_at = datetime.fromisoformat(row["opened_at"]) if row["opened_at"] else datetime.now().astimezone()
        return JournalEntry(
            id=str(row["id"]),
            asset_class=AssetClass(row["market"]),
            symbol=row["symbol"],
            direction=TradeDirection(row["direction"]),
            entry_price=Decimal(str(row["entry_price"])),
            quantity=Decimal(str(row["quantity"])),
            opened_at=opened_at,
            stop_loss=Decimal(str(row["stop_loss"])) if row["stop_loss"] is not None else None,
            take_profit=Decimal(str(row["take_profit"])) if row["take_profit"] is not None else None,
            exit_price=Decimal(str(row["exit_price"])) if row["exit_price"] is not None else None,
            fees=Decimal(str(row["fees"] or 0)),
            funding=Decimal(str(row["funding"] or 0)),
            outcome=TradeOutcome(row["outcome"] or "open"),
            setup=row["setup"] or "",
            thesis=row["thesis"] or "",
            emotion=row["emotion"] or "",
            notes=row["notes"] or "",
            image_refs=json.loads(row["image_refs"] or "[]"),
        )

    def save(self, entry: JournalEntry) -> JournalEntry:
        payload = (
            entry.asset_class.value, entry.symbol.strip(), entry.direction.value,
            float(entry.entry_price), float(entry.stop_loss) if entry.stop_loss is not None else None,
            float(entry.take_profit) if entry.take_profit is not None else None,
            float(entry.exit_price) if entry.exit_price is not None else None,
            float(entry.fees), float(entry.quantity), float(entry.funding), entry.outcome.value,
            entry.setup, entry.thesis, entry.emotion, entry.notes,
            json.dumps(entry.image_refs, ensure_ascii=False), entry.opened_at.isoformat(),
        )
        if entry.id is None:
            cursor = self.connection.execute(
                """INSERT INTO trades
                (market, symbol, direction, entry_price, stop_loss, take_profit, exit_price,
                 fees, quantity, funding, outcome, setup, thesis, emotion, notes, image_refs, opened_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", payload,
            )
            entry.id = str(cursor.lastrowid)
        else:
            self.connection.execute(
                """UPDATE trades SET market=?, symbol=?, direction=?, entry_price=?, stop_loss=?,
                 take_profit=?, exit_price=?, fees=?, quantity=?, funding=?, outcome=?, setup=?,
                 thesis=?, emotion=?, notes=?, image_refs=?, opened_at=? WHERE id=?""",
                payload + (int(entry.id),),
            )
        self.connection.commit()
        return entry

    def get(self, entry_id: str) -> JournalEntry | None:
        row = self.connection.execute("SELECT * FROM trades WHERE id=?", (int(entry_id),)).fetchone()
        return self._row_to_entry(row) if row else None

    def list(self, asset_class: str | None = None) -> list[JournalEntry]:
        if asset_class is None:
            rows = self.connection.execute("SELECT * FROM trades ORDER BY id DESC").fetchall()
        else:
            rows = self.connection.execute(
                "SELECT * FROM trades WHERE market=? ORDER BY id DESC", (asset_class,)
            ).fetchall()
        return [self._row_to_entry(row) for row in rows]

    def delete(self, entry_id: str) -> bool:
        cursor = self.connection.execute("DELETE FROM trades WHERE id=?", (int(entry_id),))
        self.connection.commit()
        return cursor.rowcount > 0
