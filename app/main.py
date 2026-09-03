from __future__ import annotations

from app.core.config import AppConfig
from app.core.database import connect, initialize
from app.core.migrations import migrate
from app.ui.shell import run


def main() -> None:
    config = AppConfig.from_environment()
    initialize(config.db_path)
    conn = connect(config.db_path)
    try:
        migrate(conn)
    finally:
        conn.close()
    run(config)


if __name__ == "__main__":
    main()
