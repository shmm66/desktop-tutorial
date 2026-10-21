"""Local API profile metadata; secrets are delegated to the OS credential store."""
import json
import os
from pathlib import Path
from typing import Any

import keyring

SERVICE = "WhaleRadarPro"


def _data_path() -> Path:
    root = Path(os.environ.get("APPDATA", Path.home())) / "WhaleRadarPro"
    root.mkdir(parents=True, exist_ok=True)
    return root / "profiles.json"


def _read() -> list[dict[str, str]]:
    path = _data_path()
    if not path.exists():
        return []
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _write(profiles: list[dict[str, str]]) -> None:
    path = _data_path()
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(profiles, indent=2), encoding="utf-8")
    temp.replace(path)


def list_profiles() -> list[dict[str, str]]:
    return [{"name": p["name"], "exchange": p.get("exchange", "Bitunix"), "key_hint": p.get("key_hint", "")}
            for p in _read()]


def save_profile(name: str, api_key: str, api_secret: str, exchange: str = "Bitunix") -> None:
    name, api_key, api_secret = name.strip(), api_key.strip(), api_secret.strip()
    if not name or not api_key or not api_secret:
        raise ValueError("Profile name, API key, and API secret are required")
    profiles = _read()
    old = next((p for p in profiles if p["name"].casefold() == name.casefold()), None)
    if old and old.get("exchange", "Bitunix") != exchange:
        keyring.delete_password(SERVICE, f"{old['exchange']}:{old['name']}:key")
        keyring.delete_password(SERVICE, f"{old['exchange']}:{old['name']}:secret")
    keyring.set_password(SERVICE, f"{exchange}:{name}:key", api_key)
    keyring.set_password(SERVICE, f"{exchange}:{name}:secret", api_secret)
    record = {"name": name, "exchange": exchange, "key_hint": f"…{api_key[-4:]}"}
    profiles = [p for p in profiles if p["name"].casefold() != name.casefold()]
    profiles.append(record)
    _write(profiles)


def get_profile_secrets(name: str) -> tuple[str, str]:
    record = next((p for p in _read() if p["name"].casefold() == name.casefold()), None)
    if not record:
        raise KeyError(f"Unknown API profile: {name}")
    exchange = record.get("exchange", "Bitunix")
    key = keyring.get_password(SERVICE, f"{exchange}:{name}:key")
    secret = keyring.get_password(SERVICE, f"{exchange}:{name}:secret")
    if not key or not secret:
        raise RuntimeError("Credentials are missing from the operating system credential store")
    return key, secret


def delete_profile(name: str) -> None:
    record = next((p for p in _read() if p["name"].casefold() == name.casefold()), None)
    if not record:
        return
    exchange = record.get("exchange", "Bitunix")
    for kind in ("key", "secret"):
        try:
            keyring.delete_password(SERVICE, f"{exchange}:{name}:{kind}")
        except keyring.errors.PasswordDeleteError:
            pass
    _write([p for p in _read() if p["name"].casefold() != name.casefold()])
