from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class UserSettings:
    language: str = "fa"
    theme: str = "dark"
    market_mode: str = "forex"
    google_drive_folder: str = ""

    def validate(self) -> None:
        if self.language not in {"fa", "en"}:
            raise ValueError("language must be fa or en")
        if self.theme not in {"dark", "light", "system"}:
            raise ValueError("invalid theme")
        if self.market_mode not in {"forex", "crypto"}:
            raise ValueError("market_mode must be forex or crypto")
        if self.google_drive_folder and not Path(self.google_drive_folder).is_absolute():
            raise ValueError("google_drive_folder must be an absolute path")
