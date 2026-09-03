from __future__ import annotations

import sqlite3
from typing import Callable

Migration = Callable[[sqlite3.Connection], None]


def migration_1(conn: sqlite3.Connection) -> None:
    from .database import SCHEMA
    conn.executescript(SCHEMA)


MIGRATIONS: dict[int, Migration] = {1: migration_1}


def migrate(conn: sqlite3.Connection) -> int:
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    current = conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()[0]
    for version in sorted(MIGRATIONS):
        if version <= current:
            continue
        with conn:
            MIGRATIONS[version](conn)
            conn.execute("INSERT INTO schema_migrations(version) VALUES (?)", (version,))
        current = version
    return current
