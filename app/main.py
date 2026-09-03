from __future__ import annotations

from app.core.config import AppConfig
from app.core.database import initialize
from app.ui.shell import run


def main() -> None:
    config = AppConfig.from_environment()
    initialize(config.db_path)
    run(config)


if __name__ == "__main__":
    main()
