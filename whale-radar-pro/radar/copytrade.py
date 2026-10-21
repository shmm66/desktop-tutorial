"""Isolated-margin copy trading for Whale Radar Pro.

Live trading is deliberately fail-closed: an order is not sent unless the market,
available balance, isolated mode, leverage and protective stop can be verified.
The configured amount is a hard sizing budget; this module never transfers funds.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, ROUND_UP
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json
import os
import secrets
import time

import requests

from .bitunix import BASE_URL, make_signature
from .monitor import fill_identity
from .statement import record_note, record_stage, update_trade

SETTINGS_DEFAULTS: dict[str, Any] = {
    "authorized_capital_usdt": 20.0,
    "margin_per_trade_pct": 20.0,
    "max_total_loss_pct": 10.0,
    "max_leverage": 5,
    "live_copy_enabled": False,
}
RISK_PER_TRADE_MARGIN_FRACTION = 0.50
BOT_CLIENT_PREFIX = "WRP"


class CopyTradeError(RuntimeError):
    """An order was prevented or rejected by a safety guard."""


def _app_dir() -> Path:
    root = Path(os.environ.get("APPDATA", Path.home())) / "WhaleRadarPro"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: Path, value: Any) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    temp.replace(path)


def validate_settings(settings: dict[str, Any]) -> dict[str, Any]:
    value = dict(SETTINGS_DEFAULTS)
    value.update(settings or {})
    try:
        capital = float(value["authorized_capital_usdt"])
        allocation = float(value["margin_per_trade_pct"])
        loss = float(value["max_total_loss_pct"])
        leverage = int(value["max_leverage"])
    except (TypeError, ValueError, KeyError) as exc:
        raise ValueError("Capital, allocation, loss limit and leverage must be valid numbers.") from exc
    if capital <= 0:
        raise ValueError("Authorized futures capital must be greater than zero.")
    if not 0 < allocation <= 100:
        raise ValueError("Margin per trade must be greater than 0% and at most 100%.")
    if not 0 < loss <= 100:
        raise ValueError("Maximum total loss must be greater than 0% and at most 100%.")
    if not 1 <= leverage <= 5:
        raise ValueError("Maximum leverage must be between 1x and 5x for the built-in risk model.")
    value.update({
        "authorized_capital_usdt": capital,
        "margin_per_trade_pct": allocation,
        "max_total_loss_pct": loss,
        "max_leverage": leverage,
        "live_copy_enabled": bool(value.get("live_copy_enabled", False)),
    })
    return value


def load_copy_settings() -> dict[str, Any]:
    value = _read_json(_app_dir() / "copy_settings.json", {})
    if not isinstance(value, dict):
        value = {}
    try:
        return validate_settings(value)
    except ValueError:
        return dict(SETTINGS_DEFAULTS)


def save_copy_settings(settings: dict[str, Any]) -> dict[str, Any]:
    value = validate_settings(settings)
    _write_json(_app_dir() / "copy_settings.json", value)
    return value


def load_copy_state() -> dict[str, Any]:
    default = {
        "seen_fills": [],
        "active_trades": {},
        "closed_trades": [],
        "halted": False,
        "halt_reason": "",
        "started_at": int(time.time() * 1000),
    }
    state = _read_json(_app_dir() / "copy_state.json", default)
    if not isinstance(state, dict):
        state = default
    for key, fallback in default.items():
        if key not in state:
            state[key] = fallback
    return state


def save_copy_state(state: dict[str, Any]) -> None:
    state["seen_fills"] = list(dict.fromkeys(str(x) for x in state.get("seen_fills", [])))[-5000:]
    state["closed_trades"] = list(state.get("closed_trades", []))[-500:]
    _write_json(_app_dir() / "copy_state.json", state)


def reset_loss_halt() -> None:
    state = load_copy_state()
    if state.get("active_trades"):
        raise CopyTradeError("Close all tracked copy positions before resetting the loss stop.")
    state["halted"] = False
    state["halt_reason"] = ""
    state["started_at"] = int(time.time() * 1000)
    save_copy_state(state)


def interpret_fill(fill: dict[str, Any]) -> tuple[str, str] | None:
    """Return ('OPEN'/'CLOSE', 'LONG'/'SHORT') only for unambiguous HL actions."""
    direction = str(fill.get("dir") or "").strip().casefold()
    if direction == "open long":
        return "OPEN", "LONG"
    if direction == "open short":
        return "OPEN", "SHORT"
    if direction == "close long":
        return "CLOSE", "LONG"
    if direction == "close short":
        return "CLOSE", "SHORT"
    if "liquidat" in direction:
        return "LIQUIDATED", ""
    return None


def futures_symbol(coin: str) -> str:
    """Map a simple Hyperliquid base coin to the USDT-margined Bitunix symbol."""
    value = str(coin or "").strip().upper()
    if not value or not value.isalnum() or len(value) > 20:
        raise CopyTradeError("The Hyperliquid asset name cannot be mapped safely.")
    if value.endswith("USDT"):
        return value
    return value + "USDT"


def make_client_id(identity: str) -> str:
    return BOT_CLIENT_PREFIX + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]


class BitunixClient:
    """Signed Bitunix futures client. Only used after the user enables live copy."""

    def __init__(self, api_key: str, api_secret: str, timeout: float = 10.0):
        if not api_key.strip() or not api_secret.strip():
            raise CopyTradeError("Select a saved Bitunix API profile with valid credentials.")
        self.api_key = api_key.strip()
        self.api_secret = api_secret.strip()
        self.timeout = timeout

    @staticmethod
    def _canonical_query(params: dict[str, Any] | None) -> str:
        if not params:
            return ""
        return "".join(str(k) + str(params[k]) for k in sorted(params))

    def _private(self, method: str, path: str, params: dict[str, Any] | None = None,
                 body: dict[str, Any] | None = None) -> Any:
        params = dict(params or {})
        body_text = json.dumps(body, separators=(",", ":"), ensure_ascii=False) if body is not None else ""
        nonce = secrets.token_hex(8)
        timestamp = str(int(time.time() * 1000))
        signature = make_signature(
            nonce, timestamp, self.api_key, self.api_secret,
            self._canonical_query(params), body_text,
        )
        headers = {
            "api-key": self.api_key,
            "nonce": nonce,
            "timestamp": timestamp,
            "sign": signature,
            "language": "en-US",
            "Content-Type": "application/json",
            "User-Agent": "WhaleRadarPro/2.2",
        }
        url = BASE_URL + path
        try:
            response = requests.request(
                method.upper(), url, params=params or None,
                data=body_text if body is not None else None,
                headers=headers, timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise CopyTradeError("Bitunix request failed; no safe confirmation was received.") from exc
        if not isinstance(payload, dict):
            raise CopyTradeError("Bitunix returned an unexpected response.")
        code = payload.get("code")
        if str(code) != "0":
            # Never include or log API credentials in diagnostics.
            raise CopyTradeError("Bitunix rejected the request (code {0}): {1}".format(
                code, str(payload.get("msg") or payload.get("message") or "unknown error")[:240]
            ))
        return payload.get("data")

    @staticmethod
    def _public(path: str, params: dict[str, Any] | None = None) -> Any:
        try:
            response = requests.get(BASE_URL + path, params=params or None, timeout=8.0,
                                    headers={"User-Agent": "WhaleRadarPro/2.2"})
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise CopyTradeError("Could not verify current Bitunix market data.") from exc
        if not isinstance(payload, dict) or str(payload.get("code")) != "0":
            raise CopyTradeError("Bitunix market-data request was not successful.")
        return payload.get("data")

    def account(self) -> dict[str, Any]:
        data = self._private("GET", "/api/v1/futures/account", {"marginCoin": "USDT"})
        if isinstance(data, list) and data:
            data = data[0]
        if not isinstance(data, dict) or "available" not in data:
            raise CopyTradeError("Could not verify available USDT futures balance.")
        return data

    def positions(self, symbol: str | None = None) -> list[dict[str, Any]]:
        params = {"symbol": symbol} if symbol else {}
        data = self._private("GET", "/api/v1/futures/position/get_pending_positions", params)
        if data is None:
            return []
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        raise CopyTradeError("Bitunix returned an unexpected open-positions response.")

    def pending_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        params = {"symbol": symbol, "limit": 100} if symbol else {"limit": 100}
        data = self._private("GET", "/api/v1/futures/trade/get_pending_orders", params)
        if isinstance(data, dict):
            items = data.get("orderList", [])
            return [x for x in items if isinstance(x, dict)]
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        return []

    def margin_config(self, symbol: str) -> dict[str, Any]:
        data = self._private("GET", "/api/v1/futures/account/get_leverage_margin_mode",
                             {"symbol": symbol, "marginCoin": "USDT"})
        if not isinstance(data, dict):
            raise CopyTradeError("Could not verify isolated margin/leverage settings.")
        return data

    def change_margin_mode(self, symbol: str) -> Any:
        return self._private("POST", "/api/v1/futures/account/change_margin_mode", body={
            "marginMode": "ISOLATION", "symbol": symbol, "marginCoin": "USDT"
        })

    def change_leverage(self, symbol: str, leverage: int) -> Any:
        return self._private("POST", "/api/v1/futures/account/change_leverage", body={
            "symbol": symbol, "leverage": int(leverage), "marginCoin": "USDT"
        })

    def symbol_meta(self, symbol: str) -> dict[str, Any]:
        data = self._public("/api/v1/futures/market/trading_pairs", {"symbols": symbol})
        if not isinstance(data, list):
            raise CopyTradeError("Could not verify the Bitunix contract rules.")
        match = next((x for x in data if isinstance(x, dict) and str(x.get("symbol", "")).upper() == symbol), None)
        if not match:
            raise CopyTradeError("Bitunix does not list {0}; the trade was skipped.".format(symbol))
        if match.get("isApiSupported") is False or str(match.get("symbolStatus", "")).upper() != "OPEN":
            raise CopyTradeError("Bitunix API trading is unavailable for {0}; trade skipped.".format(symbol))
        return match

    def ticker(self, symbol: str) -> dict[str, Any]:
        data = self._public("/api/v1/futures/market/tickers", {"symbols": symbol})
        if not isinstance(data, list):
            raise CopyTradeError("Could not verify a current market price.")
        row = next((x for x in data if isinstance(x, dict) and str(x.get("symbol", "")).upper() == symbol), None)
        if not row:
            raise CopyTradeError("No current price was returned for {0}.".format(symbol))
        return row

    def place_order(self, body: dict[str, Any]) -> Any:
        return self._private("POST", "/api/v1/futures/trade/place_order", body=body)

    def close_position(self, position_id: str) -> Any:
        if not position_id:
            raise CopyTradeError("Cannot safely close a copy position without its Bitunix position ID.")
        return self._private("POST", "/api/v1/futures/trade/flash_close_position",
                             body={"positionId": str(position_id)})

    def order_detail(self, order_id: str) -> dict[str, Any] | None:
        data = self._private("GET", "/api/v1/futures/trade/get_order_detail", {"orderId": order_id})
        return data if isinstance(data, dict) else None

    def history_position(self, position_id: str) -> list[dict[str, Any]]:
        data = self._private("GET", "/api/v1/futures/position/get_history_positions",
                             {"positionId": position_id, "limit": 10})
        if isinstance(data, dict):
            rows = data.get("positionList", [])
            return [x for x in rows if isinstance(x, dict)]
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        return []

    def pending_tp_sl(self, symbol: str, position_id: str) -> list[dict[str, Any]]:
        params = {"symbol": symbol, "positionId": position_id, "limit": 100}
        data = self._private("GET", "/api/v1/futures/tpsl/get_pending_orders", params)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            rows = data.get("orderList", [])
            return [x for x in rows if isinstance(x, dict)]
        return []

    def confirm_stop_loss(self, symbol: str, position_id: str, order_id: str,
                          expected_price: float) -> bool | None:
        """Return True/False from exchange evidence; None means the check was unavailable."""
        price_tolerance = max(abs(expected_price) * 1e-6, 1e-8)
        tpsl_ok = False
        detail_ok = False
        lookup_failed = False
        if position_id:
            try:
                for row in self.pending_tp_sl(symbol, position_id):
                    same_position = str(row.get("positionId") or "") == position_id
                    sl_price = _safe_float(row.get("slPrice"))
                    if (same_position and sl_price is not None
                            and abs(sl_price - expected_price) <= price_tolerance
                            and str(row.get("slOrderType") or "").upper() == "MARKET"):
                        tpsl_ok = True
                        break
            except CopyTradeError:
                lookup_failed = True
        try:
            detail = self.order_detail(order_id) if order_id else None
            if detail:
                sl_price = _safe_float(detail.get("slPrice"))
                detail_ok = (
                    sl_price is not None
                    and abs(sl_price - expected_price) <= price_tolerance
                    and str(detail.get("slOrderType") or "").upper() == "MARKET"
                    and str(detail.get("slStopType") or "").upper() in {"MARK_PRICE", "LAST_PRICE", "MARK"}
                )
                # An order detail record is definitive for the attached stop parameters.
                if detail_ok:
                    return True
                # The detail endpoint responded but did not confirm the expected stop.
                return tpsl_ok
        except CopyTradeError:
            lookup_failed = True
        if tpsl_ok:
            return True
        return None if lookup_failed else False

def _safe_float(value: Any) -> float | None:
    try:
        parsed = float(value)
        return parsed if parsed == parsed and abs(parsed) != float("inf") else None
    except (TypeError, ValueError):
        return None



def _decimal_str(value: Decimal) -> str:
    return format(value.normalize(), "f")


def calculate_order_plan(margin_usdt: float, leverage: int, price: float,
                         side: str, base_precision: int, quote_precision: int,
                         min_trade_volume: float) -> dict[str, float | str]:
    """Size an isolated position and put its stop at a 50%-of-margin loss target."""
    if side not in ("LONG", "SHORT") or margin_usdt <= 0 or price <= 0 or leverage < 1:
        raise ValueError("Invalid side, margin, leverage, or market price.")
    if not 0 <= base_precision <= 12 or not 0 <= quote_precision <= 12:
        raise ValueError("Unsupported contract precision.")
    margin = Decimal(str(margin_usdt))
    px = Decimal(str(price))
    lev = Decimal(str(leverage))
    qty_step = Decimal("1").scaleb(-base_precision)
    raw_qty = (margin * lev) / px
    qty = raw_qty.quantize(qty_step, rounding=ROUND_DOWN)
    if qty <= 0 or qty < Decimal(str(min_trade_volume)):
        raise ValueError("The authorized margin is too small for this contract's minimum quantity.")
    notional = qty * px
    actual_margin = notional / lev
    risk_usdt = actual_margin * Decimal(str(RISK_PER_TRADE_MARGIN_FRACTION))
    move_fraction = risk_usdt / notional
    raw_stop = px * (Decimal("1") - move_fraction if side == "LONG" else Decimal("1") + move_fraction)
    price_step = Decimal("1").scaleb(-quote_precision)
    # Round toward entry so precision cannot increase the planned stop risk.
    stop = raw_stop.quantize(price_step, rounding=ROUND_UP if side == "LONG" else ROUND_DOWN)
    if stop <= 0 or (side == "LONG" and stop >= px) or (side == "SHORT" and stop <= px):
        raise ValueError("Could not create a valid stop price.")
    return {
        "qty": _decimal_str(qty),
        "entry_reference": float(px),
        "notional": float(notional),
        "margin": float(actual_margin),
        "risk_usdt": float(risk_usdt),
        "stop_price": _decimal_str(stop),
        "stop_distance_pct": float(move_fraction * 100),
    }


def _active_key(wallet: str, symbol: str, side: str) -> str:
    return "{0}:{1}:{2}".format(wallet.lower(), symbol, side)


def _seen(state: dict[str, Any], identity: str) -> bool:
    return identity in set(state.get("seen_fills", []))


def _remember(state: dict[str, Any], identity: str) -> None:
    state["seen_fills"] = list(state.get("seen_fills", [])) + [identity]


def calculate_risk_headroom(settings: dict[str, Any], state: dict[str, Any],
                            current_pnl: float, active_unrealized_pnl: float = 0.0) -> float:
    """Remaining stop-risk budget using realized PnL and worst-case stops for open positions."""
    max_loss = float(settings["authorized_capital_usdt"]) * float(settings["max_total_loss_pct"]) / 100.0
    active_risk = sum(float(r.get("risk_usdt", 0) or 0)
                      for r in state.get("active_trades", {}).values())
    # Do not count floating profit on an open trade as loss-budget headroom: it can vanish
    # before the exchange stop fills. Realized PnL remains included in current_pnl.
    realized_pnl = float(current_pnl) - float(active_unrealized_pnl)
    return max(0.0, max_loss + realized_pnl - active_risk)


def _tracked_pnl_components(client: BitunixClient, state: dict[str, Any]) -> tuple[float, float]:
    """Return (total bot PnL, unrealized PnL of currently open bot positions)."""
    total = 0.0
    active_unrealized = 0.0
    pending_ids: set[str] = set()
    positions = client.positions()
    position_by_id = {str(p.get("positionId")): p for p in positions if p.get("positionId")}
    for record in list(state.get("active_trades", {}).values()):
        pid = str(record.get("position_id") or "")
        if pid and pid in position_by_id:
            p = position_by_id[pid]
            pending_ids.add(pid)
            unrealized = float(p.get("unrealizedPNL") or 0)
            active_unrealized += unrealized
            total += float(p.get("realizedPNL") or 0) + unrealized
            total -= float(p.get("fee") or 0)
            total += float(p.get("funding") or 0)
    baseline = int(state.get("started_at") or 0)
    for record in list(state.get("closed_trades", [])):
        if int(record.get("created_at") or 0) < baseline:
            continue
        pid = str(record.get("position_id") or "")
        if not pid or pid in pending_ids:
            continue
        hist = client.history_position(pid)
        if hist:
            p = hist[0]
            total += float(p.get("realizedPNL") or 0)
            total -= float(p.get("fee") or 0)
            total += float(p.get("funding") or 0)
    return total, active_unrealized


def tracked_pnl(client: BitunixClient, state: dict[str, Any]) -> float:
    """Conservative PnL estimate from only position IDs stored by the copy bot."""
    return _tracked_pnl_components(client, state)[0]


def _reconcile_active(client: BitunixClient, state: dict[str, Any]) -> None:
    positions = client.positions()
    by_id = {str(p.get("positionId")): p for p in positions if p.get("positionId")}
    active = state.setdefault("active_trades", {})
    for key, record in list(active.items()):
        pid = str(record.get("position_id") or "")
        if pid and pid not in by_id:
            state.setdefault("closed_trades", []).append(record)
            active.pop(key, None)
            continue
        if not pid:
            symbol = str(record.get("symbol") or "")
            side = str(record.get("side") or "")
            matches = [p for p in positions if p.get("symbol") == symbol
                       and str(p.get("side", "")).upper() == side
                       and str(p.get("marginMode", "")).upper() == "ISOLATION"]
            if len(matches) == 1:
                record["position_id"] = str(matches[0].get("positionId") or "")
                record["last_position_margin"] = float(matches[0].get("margin") or record.get("margin", 0))
            elif len(matches) == 0 and record.get("order_id"):
                # Market order may already have stopped out before the next poll.
                detail = client.order_detail(str(record["order_id"]))
                if detail and str(detail.get("status", "")).upper() in ("FILLED", "CANCELED"):
                    state.setdefault("closed_trades", []).append(record)
                    active.pop(key, None)


def check_loss_circuit_breaker(client: BitunixClient, settings: dict[str, Any],
                               state: dict[str, Any]) -> str | None:
    # Once halted, never resume new entries automatically; keep retrying closes for any
    # still-confirmed bot position rather than dropping it from the tracking ledger.
    if state.get("halted"):
        try:
            _reconcile_active(client, state)
            for record in list(state.get("active_trades", {}).values()):
                pid = str(record.get("position_id") or "")
                if pid:
                    try:
                        client.close_position(pid)
                    except CopyTradeError:
                        # Preserve tracking and retry on the next monitoring cycle.
                        pass
            save_copy_state(state)
        except CopyTradeError:
            # Keep the halt active when the venue cannot be queried safely.
            pass
        return str(state.get("halt_reason") or "Copy trading is halted by the loss limit.")
    _reconcile_active(client, state)
    pnl = tracked_pnl(client, state)
    threshold = float(settings["authorized_capital_usdt"]) * float(settings["max_total_loss_pct"]) / 100.0
    if pnl <= -threshold:
        state["halted"] = True
        state["halt_reason"] = (
            "Loss limit reached: copy PnL {0:.4f} USDT, limit {1:.4f} USDT. "
            "New copy entries are disabled.".format(pnl, threshold)
        )
        for record in list(state.get("active_trades", {}).values()):
            pid = str(record.get("position_id") or "")
            if pid:
                try:
                    client.close_position(pid)
                except CopyTradeError:
                    # Preserve the record and retry the close on following monitoring cycles.
                    pass
        save_copy_state(state)
        return str(state["halt_reason"])
    save_copy_state(state)
    return None


def process_copy_fill(client: BitunixClient, fill: dict[str, Any], wallet: str,
                      settings: dict[str, Any], state: dict[str, Any]) -> str:
    """Process one fresh public fill. Repeated fills are deduplicated across restarts."""
    if not settings.get("live_copy_enabled"):
        return "Live copy is disabled in settings."
    identity = fill_identity(fill)
    if _seen(state, identity):
        return "Duplicate fill ignored."
    if state.get("halted"):
        return str(state.get("halt_reason") or "Copy trading is halted.")
    action = interpret_fill(fill)
    if action is None:
        _remember(state, identity)
        save_copy_state(state)
        return "Unsupported fill direction; no order sent."
    kind, side = action
    try:
        symbol = futures_symbol(str(fill.get("coin") or ""))
    except CopyTradeError as exc:
        _remember(state, identity)
        save_copy_state(state)
        return str(exc)

    loss_status = check_loss_circuit_breaker(client, settings, state)
    if loss_status:
        _remember(state, identity)
        save_copy_state(state)
        return loss_status

    key = _active_key(wallet, symbol, side)
    if kind in ("CLOSE", "LIQUIDATED"):
        candidates = []
        for trade_key, record in state.get("active_trades", {}).items():
            same_wallet = str(record.get("wallet", "")).lower() == wallet.lower()
            same_symbol = str(record.get("symbol", "")).upper() == symbol
            same_side = not side or str(record.get("side", "")).upper() == side
            if same_wallet and same_symbol and same_side:
                candidates.append((trade_key, record))
        if not candidates:
            _remember(state, identity)
            save_copy_state(state)
            return "Source close has no matching tracked copy position."
        for trade_key, record in candidates:
            pid = str(record.get("position_id") or "")
            if not pid:
                # Do not send an opposite-side order when the position ID is unknown.
                return "Close deferred: the copy position ID is not confirmed yet."
            client.close_position(pid)
            record["closed_by_source"] = True
            state.setdefault("closed_trades", []).append(record)
            state["active_trades"].pop(trade_key, None)
        _remember(state, identity)
        save_copy_state(state)
        return "Copied source close for {0}; Bitunix position close requested.".format(symbol)

    if kind != "OPEN":
        return "Unsupported action."
    if not fill.get("px") or not fill.get("sz"):
        _remember(state, identity)
        save_copy_state(state)
        return "Source fill is missing price or size; no order sent."
    if any(str(r.get("symbol", "")).upper() == symbol for r in state.get("active_trades", {}).values()):
        _remember(state, identity)
        save_copy_state(state)
        return "Another tracked copy position is already open for {0}; pyramiding skipped.".format(symbol)

    meta = client.symbol_meta(symbol)
    ticker = client.ticker(symbol)
    price = float(ticker.get("markPrice") or ticker.get("lastPrice") or 0)
    if price <= 0:
        raise CopyTradeError("No valid mark/last price; order not sent.")
    account = client.account()
    available = float(account.get("available") or 0)
    capital = float(settings["authorized_capital_usdt"])
    reserved = sum(float(r.get("margin", 0) or 0) for r in state.get("active_trades", {}).values())
    remaining_capital = capital - reserved

    # Keep both allocated margin and aggregate planned stop-risk within user limits.
    pnl_now, active_unrealized_pnl = _tracked_pnl_components(client, state)
    risk_budget = calculate_risk_headroom(settings, state, pnl_now, active_unrealized_pnl)
    requested_margin = capital * float(settings["margin_per_trade_pct"]) / 100.0
    max_margin_under_risk_budget = risk_budget / RISK_PER_TRADE_MARGIN_FRACTION
    margin = min(requested_margin, remaining_capital, available, max_margin_under_risk_budget)
    if margin <= 0:
        _remember(state, identity)
        save_copy_state(state)
        return "Authorized copy margin is exhausted or futures available balance is insufficient."
    # Never change margin/leverage if any manual position/order already uses the symbol.
    positions = client.positions(symbol)
    orders = client.pending_orders(symbol)
    if positions or orders:
        _remember(state, identity)
        save_copy_state(state)
        return "Bitunix already has a position or pending order for {0}; skipped to protect manual trades.".format(symbol)

    target_leverage = min(int(settings["max_leverage"]), int(meta.get("maxLeverage") or 1))
    if target_leverage < 1:
        raise CopyTradeError("Bitunix returned invalid leverage limits.")
    client.change_margin_mode(symbol)
    config = client.margin_config(symbol)
    if str(config.get("marginMode", "")).upper() != "ISOLATION":
        raise CopyTradeError("Bitunix did not confirm ISOLATED margin; no order was sent.")
    client.change_leverage(symbol, target_leverage)
    config = client.margin_config(symbol)
    if str(config.get("marginMode", "")).upper() != "ISOLATION":
        raise CopyTradeError("Isolated margin verification failed; no order was sent.")
    effective_leverage = int(config.get("leverage") or target_leverage)
    if effective_leverage != target_leverage:
        raise CopyTradeError("Bitunix did not apply the requested leverage; no order was sent.")

    try:
        plan = calculate_order_plan(
            margin, effective_leverage, price, side,
            int(meta.get("basePrecision") or 0), int(meta.get("quotePrecision") or 0),
            float(meta.get("minTradeVolume") or 0),
        )
    except ValueError as exc:
        _remember(state, identity)
        save_copy_state(state)
        return "Order skipped: {0}".format(exc)
    # Required margin after size precision must stay within both user caps.
    if float(plan["margin"]) > margin + 1e-8 or float(plan["margin"]) > remaining_capital + 1e-8:
        raise CopyTradeError("Calculated order exceeds the configured margin budget.")

    client_id = make_client_id(identity)
    order = {
        "symbol": symbol,
        "qty": str(plan["qty"]),
        "side": "BUY" if side == "LONG" else "SELL",
        "orderType": "MARKET",
        "tradeSide": "OPEN",
        "reduceOnly": False,
        "clientId": client_id,
        "slPrice": str(plan["stop_price"]),
        "slStopType": "MARK_PRICE",
        "slOrderType": "MARKET",
    }
    response = client.place_order(order)
    if not isinstance(response, dict) or not response.get("orderId"):
        raise CopyTradeError("Bitunix did not return an order ID; inspect order history before retrying.")
    order_id = str(response["orderId"])
    time.sleep(0.25)
    confirmed_positions = client.positions(symbol)
    position = next((p for p in confirmed_positions
                     if str(p.get("side", "")).upper() == side), None)
    if position:
        if str(position.get("marginMode", "")).upper() != "ISOLATION":
            try:
                client.close_position(str(position.get("positionId") or ""))
            finally:
                raise CopyTradeError("Emergency guard: position was not confirmed isolated; close requested.")
        position_id = str(position.get("positionId") or "")
    else:
        position_id = ""

    record = {
        "wallet": wallet,
        "symbol": symbol,
        "side": side,
        "order_id": order_id,
        "client_id": client_id,
        "position_id": position_id,
        "entry_reference": float(plan["entry_reference"]),
        "qty": str(plan["qty"]),
        "margin": float(plan["margin"]),
        "risk_usdt": float(plan["risk_usdt"]),
        "stop_price": str(plan["stop_price"]),
        "leverage": effective_leverage,
        "source_qty": float(fill.get("sz") or 0),
        "created_at": int(time.time() * 1000),
    }
    state.setdefault("active_trades", {})[key] = record
    _remember(state, identity)
    save_copy_state(state)
    return (
        "Copied {0} {1}: margin {2:.4f} USDT, isolated {3}x, stop {4} "
        "(planned risk {5:.4f} USDT, 50% of actual entry margin). "
        "Slippage/fees can make actual loss differ.".format(
            side, symbol, float(plan["margin"]), effective_leverage,
            plan["stop_price"], float(plan["risk_usdt"])
        )
    )
