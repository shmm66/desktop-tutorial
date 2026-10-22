"""Resilient real-time Hyperliquid fills stream with automatic reconnects."""
from __future__ import annotations

import json
import queue
import threading
import time
from typing import Callable

import websocket

WS_URL = "wss://api.hyperliquid.xyz/ws"
SNAPSHOT_FRESH_MS = 90_000


class HyperliquidFillStream:
    """Subscribe to up to ten wallets and keep reconnecting until explicitly stopped.

    Snapshot history is used only for fills within the normal fresh-entry window.
    Older snapshot entries are ignored; entries received as live events are passed
    to the app for its independent stale-entry and risk checks.
    """

    def __init__(
        self,
        traders: list[tuple[str, str]],
        status_callback: Callable[[str], None] | None = None,
    ) -> None:
        if not traders:
            raise ValueError("At least one Hyperliquid trader must be selected.")
        if len(traders) > 10:
            raise ValueError("Hyperliquid supports at most 10 selected wallets in this monitor.")
        self._names_by_address = {address.lower(): name for name, address in traders}
        self._addresses = [address for _, address in traders]
        self._status_callback = status_callback
        self._queue: queue.Queue[tuple[str, str, dict]] = queue.Queue()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._ws: websocket.WebSocketApp | None = None
        self._ws_lock = threading.Lock()

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="hyperliquid-fill-stream", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        with self._ws_lock:
            ws = self._ws
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass

    def get_fill(self, timeout: float = 0.5) -> tuple[str, str, dict] | None:
        try:
            return self._queue.get(timeout=max(0.0, timeout))
        except queue.Empty:
            return None

    def _publish(self, message: str) -> None:
        callback = self._status_callback
        if callback is not None:
            try:
                callback(message)
            except Exception:
                pass

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        try:
            for address in self._addresses:
                ws.send(json.dumps({
                    "method": "subscribe",
                    "subscription": {"type": "userFills", "user": address},
                }))
            self._publish(
                "Hyperliquid live stream connected · monitoring {0} selected trader(s); "
                "automatic reconnect is enabled.".format(len(self._addresses))
            )
        except Exception as exc:
            self._publish("Hyperliquid subscription setup failed: {0}; reconnecting automatically.".format(exc))
            try:
                ws.close()
            except Exception:
                pass

    def _on_message(self, _ws: websocket.WebSocketApp, message: str) -> None:
        try:
            payload = json.loads(message)
            if not isinstance(payload, dict) or payload.get("channel") != "userFills":
                return
            data = payload.get("data")
            if not isinstance(data, dict):
                return
            address = str(data.get("user") or "").lower()
            name = self._names_by_address.get(address)
            fills = data.get("fills")
            if name is None or not isinstance(fills, list):
                return
            is_snapshot = bool(data.get("isSnapshot"))
            now_ms = int(time.time() * 1000)
            for raw_fill in fills:
                if not isinstance(raw_fill, dict):
                    continue
                fill = dict(raw_fill)
                if is_snapshot:
                    try:
                        fill_time = int(fill.get("time") or 0)
                    except (TypeError, ValueError):
                        fill_time = 0
                    # A reconnect snapshot may include old history. Never replay old
                    # entries; fresh snapshot fills still pass the app's stale-entry check.
                    if not fill_time or now_ms - fill_time > SNAPSHOT_FRESH_MS:
                        continue
                self._queue.put((name, address, fill))
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            self._publish("Ignored malformed Hyperliquid stream message: {0}".format(exc))

    def _on_error(self, _ws: websocket.WebSocketApp, error: object) -> None:
        if not self._stop.is_set():
            self._publish("Hyperliquid stream interrupted ({0}); reconnecting automatically.".format(error))

    def _on_close(self, _ws: websocket.WebSocketApp, _status_code: object, _message: object) -> None:
        if not self._stop.is_set():
            self._publish("Hyperliquid stream closed; reconnecting automatically.")

    def _run(self) -> None:
        delay = 1
        while not self._stop.is_set():
            opened_at = [0.0]

            def on_open(ws: websocket.WebSocketApp) -> None:
                opened_at[0] = time.monotonic()
                self._on_open(ws)

            ws = websocket.WebSocketApp(
                WS_URL,
                on_open=on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
            )
            with self._ws_lock:
                self._ws = ws
            try:
                ws.run_forever(ping_interval=20, ping_timeout=10)
            except Exception as exc:
                if not self._stop.is_set():
                    self._publish("Hyperliquid connection failed ({0}); reconnecting automatically.".format(exc))
            finally:
                with self._ws_lock:
                    if self._ws is ws:
                        self._ws = None
            if self._stop.is_set():
                break
            if opened_at[0] and time.monotonic() - opened_at[0] >= 30:
                delay = 1
            self._publish(
                "Hyperliquid disconnected · retrying in {0}s; selected wallets remain queued for reconnection.".format(delay)
            )
            if self._stop.wait(delay):
                break
            delay = min(30, delay * 2)
