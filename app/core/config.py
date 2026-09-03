from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

APP_NAME = "Trader Planner Pro"
APP_VERSION = "5.0.0-alpha.1"


@dataclass(frozen=True)
class AppConfig:
    data_dir: Path
    db_path: Path
    language: str = "fa"
    timezone: str = "Europe/Paris"

    @classmethod
    def from_environment(cls) -> "AppConfig":
        root = Path(os.getenv("TRADER_PLANNER_DATA_DIR", Path.home() / ".trader-planner-pro"))
        root.mkdir(parents=True, exist_ok=True)
        return cls(data_dir=root, db_path=root / "trader_planner.sqlite3")
