"""Persistent copy-trade lifecycle history and printable performance statements."""
from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any
import csv
import json
import os
import webbrowser


STAGE_LABELS = {
    "pending": "Pending",
    "order_confirmed": "Order confirmed",
    "position_opened": "Position opened",
    "stop_confirmed": "Stop-loss confirmed",
    "closed": "Closed",
    "failed": "Failed",
}
STAGE_ORDER = {name: index for index, name in enumerate(STAGE_LABELS)}


def _app_dir() -> Path:
    root = Path(os.environ.get("APPDATA", Path.home())) / "WhaleRadarPro"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _history_path() -> Path:
    return _app_dir() / "copy_trade_history.json"


def _now_ms() -> int:
    return int(datetime.now().timestamp() * 1000)


def format_time(value: Any) -> str:
    try:
        stamp = int(value or 0) / 1000
        return datetime.fromtimestamp(stamp).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError, OverflowError):
        return "—"


def _read_history() -> list[dict[str, Any]]:
    try:
        data = json.loads(_history_path().read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
    except (OSError, json.JSONDecodeError):
        pass
    return []


def _write_history(rows: list[dict[str, Any]]) -> None:
    path = _history_path()
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(rows[-5000:], indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


def list_history() -> list[dict[str, Any]]:
    return sorted(_read_history(), key=lambda row: int(row.get("created_at") or 0), reverse=True)


def get_trade(trade_id: str) -> dict[str, Any] | None:
    return next((row for row in _read_history() if row.get("trade_id") == trade_id), None)


def ensure_trade(trade_id: str, trader_name: str, wallet: str, fill: dict[str, Any]) -> dict[str, Any]:
    rows = _read_history()
    existing = next((row for row in rows if row.get("trade_id") == trade_id), None)
    if existing:
        return existing
    direction = str(fill.get("dir") or "Unknown")
    side = "LONG" if direction.casefold().endswith("long") else (
        "SHORT" if direction.casefold().endswith("short") else "—"
    )
    coin = str(fill.get("coin") or "Unknown")
    now = _now_ms()
    row = {
        "trade_id": trade_id,
        "trader_name": trader_name,
        "wallet": wallet,
        "source_action": direction,
        "coin": coin,
        "symbol": coin.upper() + "USDT" if coin and coin.isalnum() else coin.upper(),
        "side": side,
        "status": "pending",
        "status_label": STAGE_LABELS["pending"],
        "created_at": now,
        "updated_at": now,
        "source_time": int(fill.get("time") or now),
        "source_price": _to_float(fill.get("px")),
        "source_qty": _to_float(fill.get("sz")),
        "order_id": "",
        "position_id": "",
        "client_id": "",
        "entry_price": None,
        "qty": None,
        "margin": None,
        "risk_usdt": None,
        "leverage": None,
        "stop_price": None,
        "realized_pnl": None,
        "fees": None,
        "funding": None,
        "close_reason": "",
        "error": "",
        "notes": [],
        "stages": [{
            "stage": "pending", "label": STAGE_LABELS["pending"], "at": now,
            "message": "Fresh Hyperliquid fill detected; copy eligibility checks started."
        }],
    }
    rows.append(row)
    _write_history(rows)
    return row


def _to_float(value: Any) -> float | None:
    try:
        number = float(value)
        return number if number == number and abs(number) != float("inf") else None
    except (TypeError, ValueError):
        return None


def update_trade(trade_id: str, fields: dict[str, Any] | None = None) -> dict[str, Any] | None:
    rows = _read_history()
    row = next((item for item in rows if item.get("trade_id") == trade_id), None)
    if row is None:
        return None
    for key, value in (fields or {}).items():
        if key in {"trade_id", "stages", "notes"}:
            continue
        row[key] = value
    row["updated_at"] = _now_ms()
    _write_history(rows)
    return row


def record_stage(trade_id: str, stage: str, message: str = "",
                 fields: dict[str, Any] | None = None) -> dict[str, Any] | None:
    if stage not in STAGE_LABELS:
        raise ValueError("Unknown copy-trade lifecycle stage: " + stage)
    rows = _read_history()
    row = next((item for item in rows if item.get("trade_id") == trade_id), None)
    if row is None:
        return None
    now = _now_ms()
    if fields:
        for key, value in fields.items():
            if key not in {"trade_id", "stages", "notes"}:
                row[key] = value
    stages = row.setdefault("stages", [])
    # Preserve the full path while avoiding repeated duplicate stage stamps.
    if not stages or stages[-1].get("stage") != stage or stage in {"failed", "closed"}:
        stages.append({"stage": stage, "label": STAGE_LABELS[stage], "at": now, "message": message})
    elif message:
        stages[-1]["message"] = message
        stages[-1]["at"] = now
    row["status"] = stage
    row["status_label"] = STAGE_LABELS[stage]
    row["updated_at"] = now
    if stage == "closed":
        row["closed_at"] = now
        if not row.get("close_reason"):
            row["close_reason"] = message or "No open position found during reconciliation."
    if stage == "failed":
        row["error"] = message
    if message and stage not in {"failed", "closed"}:
        row.setdefault("notes", []).append({"at": now, "message": message})
        row["notes"] = row["notes"][-100:]
    _write_history(rows)
    return row


def record_note(trade_id: str, message: str) -> None:
    rows = _read_history()
    row = next((item for item in rows if item.get("trade_id") == trade_id), None)
    if row is None:
        return
    row.setdefault("notes", []).append({"at": _now_ms(), "message": str(message)})
    row["notes"] = row["notes"][-100:]
    row["updated_at"] = _now_ms()
    _write_history(rows)


def summarize_history(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = rows if rows is not None else list_history()
    closed = [row for row in rows if row.get("status") == "closed"]
    with_pnl = [row for row in closed if _to_float(row.get("realized_pnl")) is not None]
    pnls = [_to_float(row.get("realized_pnl")) or 0.0 for row in with_pnl]
    wins = sum(1 for value in pnls if value > 0)
    losses = sum(1 for value in pnls if value < 0)
    return {
        "total": len(rows),
        "closed": len(closed),
        "open": sum(1 for row in rows if row.get("status") in {
            "pending", "order_confirmed", "position_opened", "stop_confirmed"
        }),
        "failed": sum(1 for row in rows if row.get("status") == "failed"),
        "with_pnl": len(with_pnl),
        "wins": wins,
        "losses": losses,
        "win_rate": (wins / len(with_pnl) * 100.0) if with_pnl else None,
        "net_pnl": sum(pnls) if pnls else 0.0,
        "gross_profit": sum(value for value in pnls if value > 0),
        "gross_loss": sum(value for value in pnls if value < 0),
        "average_pnl": (sum(pnls) / len(pnls)) if pnls else None,
    }


def _svg_per_trade(rows: list[dict[str, Any]], width: int = 900, height: int = 260) -> str:
    closed = [r for r in rows if r.get("status") == "closed" and _to_float(r.get("realized_pnl")) is not None]
    closed = list(reversed(closed[-40:]))
    if not closed:
        return '<div class="empty-chart">No confirmed closed-trade P&amp;L data yet.</div>'
    values = [_to_float(row.get("realized_pnl")) or 0 for row in closed]
    low, high = min([0.0] + values), max([0.0] + values)
    span = max(high - low, 0.000001)
    margin_left, margin_right, margin_top, margin_bottom = 55, 20, 18, 35
    plot_w, plot_h = width - margin_left - margin_right, height - margin_top - margin_bottom
    baseline = margin_top + (high / span) * plot_h
    bar_w = max(3, plot_w / len(values) * 0.55)
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Realized PnL by closed trade">']
    parts.append(f'<line x1="{margin_left}" y1="{baseline:.2f}" x2="{width-margin_right}" y2="{baseline:.2f}" stroke="#7b8797" stroke-dasharray="4 4"/>')
    for index, value in enumerate(values):
        x = margin_left + (index + .5) * plot_w / len(values) - bar_w / 2
        y_value = margin_top + (high - value) / span * plot_h
        y = min(y_value, baseline)
        h = max(1, abs(baseline - y_value))
        label = escape(str(closed[index].get("symbol") or closed[index].get("coin") or "Trade"))
        color = "#16856a" if value >= 0 else "#c44747"
        parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{h:.2f}" fill="{color}" rx="2"><title>{label}: {value:.4f} USDT</title></rect>')
    parts.append(f'<text x="8" y="{margin_top+8}" fill="currentColor" font-size="11">{high:.3f}</text>')
    parts.append(f'<text x="8" y="{height-margin_bottom}" fill="currentColor" font-size="11">{low:.3f}</text>')
    parts.append("</svg>")
    return "".join(parts)


def _svg_equity_curve(rows: list[dict[str, Any]], width: int = 900, height: int = 260) -> str:
    closed = [r for r in rows if r.get("status") == "closed" and _to_float(r.get("realized_pnl")) is not None]
    closed = list(reversed(closed[-100:]))
    if not closed:
        return '<div class="empty-chart">Cumulative curve appears after the first closed trade with P&amp;L.</div>'
    cumulative = []
    total = 0.0
    for row in closed:
        total += _to_float(row.get("realized_pnl")) or 0.0
        cumulative.append(total)
    low, high = min([0.0] + cumulative), max([0.0] + cumulative)
    span = max(high - low, 0.000001)
    ml, mr, mt, mb = 55, 20, 18, 30
    pw, ph = width-ml-mr, height-mt-mb
    points = []
    for i, val in enumerate(cumulative):
        x = ml + (i * pw / max(1, len(cumulative)-1))
        y = mt + (high-val)/span*ph
        points.append((x,y))
    d = " ".join(("M" if i == 0 else "L") + f" {x:.2f} {y:.2f}" for i,(x,y) in enumerate(points))
    zero_y = mt + (high/span)*ph
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Cumulative realized PnL equity curve">']
    parts.append(f'<line x1="{ml}" y1="{zero_y:.2f}" x2="{width-mr}" y2="{zero_y:.2f}" stroke="#7b8797" stroke-dasharray="4 4"/>')
    parts.append(f'<path d="{d}" fill="none" stroke="#16856a" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')
    for x,y in points:
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3" fill="#16856a"/>')
    parts.append(f'<text x="8" y="{mt+8}" fill="currentColor" font-size="11">{high:.3f}</text>')
    parts.append(f'<text x="8" y="{height-mb}" fill="currentColor" font-size="11">{low:.3f}</text>')
    parts.append("</svg>")
    return "".join(parts)


def build_statement_html(rows: list[dict[str, Any]] | None = None) -> str:
    rows = list_history() if rows is None else rows
    stats = summarize_history(rows)
    money = lambda value: "—" if _to_float(value) is None else f'{float(value):+.4f}'
    win = "—" if stats["win_rate"] is None else f'{stats["win_rate"]:.2f}%'
    table_rows = []
    for row in sorted(rows, key=lambda r: int(r.get("created_at") or 0)):
        event_list = row.get("stages", [])
        trail = " → ".join(str(e.get("label") or e.get("stage")) for e in event_list if isinstance(e, dict))
        notes = " | ".join(str(n.get("message") or "") for n in row.get("notes", []) if isinstance(n, dict))
        table_rows.append(
            "<tr>"
            f"<td>{escape(format_time(row.get('created_at')))}</td>"
            f"<td>{escape(str(row.get('trader_name') or '—'))}<small>{escape(str(row.get('wallet') or ''))}</small></td>"
            f"<td>{escape(str(row.get('symbol') or row.get('coin') or '—'))}</td>"
            f"<td>{escape(str(row.get('side') or '—'))}</td>"
            f"<td><strong>{escape(str(row.get('status_label') or STAGE_LABELS.get(str(row.get('status')), 'Unknown')))}</strong><small>{escape(trail)}</small></td>"
            f"<td>{escape(str(row.get('qty') or '—'))}</td>"
            f"<td>{money(row.get('margin'))}</td>"
            f"<td>{escape(str(row.get('leverage') or '—'))}x</td>"
            f"<td>{escape(str(row.get('stop_price') or '—'))}</td>"
            f"<td>{money(row.get('realized_pnl'))}</td>"
            f"<td>{escape(str(row.get('order_id') or '—'))}<small>{escape(str(row.get('position_id') or ''))}</small></td>"
            f"<td>{escape(str(row.get('error') or notes or '—'))}</td>"
            "</tr>"
        )
    if not table_rows:
        table_rows = ['<tr><td colspan="12" class="empty">No copy trades have been recorded yet.</td></tr>']
    built_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Whale Radar Pro — Copy Trade Statement</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{{--ink:#182334;--muted:#65738a;--line:#dce3ec;--panel:#f4f7fb;--green:#16856a;--red:#c44747}}
*{{box-sizing:border-box}}body{{font:12px/1.45 Arial,Segoe UI,sans-serif;color:var(--ink);margin:22px}}
h1{{font-size:25px;margin:0}}h2{{font-size:15px;margin:20px 0 8px}}.top{{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;border-bottom:2px solid var(--ink);padding-bottom:13px}}
.muted{{color:var(--muted)}}.kpis{{display:grid;grid-template-columns:repeat(5,minmax(100px,1fr));gap:8px;margin:15px 0}}
.kpi{{background:var(--panel);border:1px solid var(--line);border-radius:7px;padding:10px}}.kpi span{{display:block;color:var(--muted);font-size:10px}}.kpi strong{{display:block;font-size:17px;margin-top:3px;overflow-wrap:anywhere}}
.charts{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.chart{{border:1px solid var(--line);border-radius:8px;padding:9px;min-width:0}}.chart h2{{margin:0}}svg{{width:100%;height:auto;display:block;margin-top:6px}}.empty-chart{{height:120px;display:flex;align-items:center;justify-content:center;color:var(--muted);text-align:center}}
table{{width:100%;border-collapse:collapse;font-size:9px;table-layout:auto}}thead{{display:table-header-group}}th{{background:#e9eef5;text-align:left;font-weight:700}}th,td{{border:1px solid var(--line);padding:5px;vertical-align:top;overflow-wrap:anywhere}}small{{display:block;color:var(--muted);font-size:8px;margin-top:2px;max-width:180px;overflow-wrap:anywhere}}.empty{{text-align:center;padding:22px;color:var(--muted)}}
.notice{{margin-top:13px;padding:9px;border:1px solid var(--line);color:var(--muted);border-radius:6px}}.actions{{margin:14px 0}}button{{border:0;border-radius:6px;background:var(--ink);color:white;padding:9px 13px;cursor:pointer}}
@page{{size:A4 landscape;margin:8mm}}@media print{{body{{margin:0;font-size:9px}}.actions{{display:none}}h1{{font-size:18px}}h2{{font-size:12px}}.kpi{{padding:5px}}.kpi strong{{font-size:13px}}.charts{{gap:6px}}.chart{{break-inside:avoid;padding:5px}}svg{{max-height:145px}}table{{font-size:7px}}th,td{{padding:3px}}tr{{break-inside:avoid}}.notice{{font-size:8px}}}}
</style></head><body>
<div class="actions"><button onclick="window.print()">Print / Save as PDF</button> <span class="muted">Choose a printer or “Save as PDF” in the print dialog.</span></div>
<div class="top"><div><h1>Copy Trade Statement</h1><div class="muted">Whale Radar Pro · Bitunix Futures · lifecycle and performance report</div></div><div class="muted">Generated: {escape(built_at)}<br>Records: {stats["total"]}</div></div>
<div class="kpis">
<div class="kpi"><span>Total records</span><strong>{stats["total"]}</strong></div>
<div class="kpi"><span>Closed positions</span><strong>{stats["closed"]}</strong></div>
<div class="kpi"><span>Open / pending</span><strong>{stats["open"]}</strong></div>
<div class="kpi"><span>Realized net P&amp;L (known)</span><strong>{stats["net_pnl"]:+.4f} USDT</strong></div>
<div class="kpi"><span>Win rate (closed with P&amp;L)</span><strong>{win}</strong></div>
</div>
<div class="charts">
<section class="chart"><h2>Cumulative realized P&amp;L (USDT)</h2>{_svg_equity_curve(rows)}</section>
<section class="chart"><h2>Realized P&amp;L per closed trade (USDT)</h2>{_svg_per_trade(rows)}</section>
</div>
<h2>Complete copy-trade ledger</h2>
<table><thead><tr><th>Detected at</th><th>Source trader / wallet</th><th>Market</th><th>Side</th><th>Current status / lifecycle stages</th><th>Quantity</th><th>Margin</th><th>Leverage</th><th>Stop price</th><th>Realized P&amp;L</th><th>Order / Position ID</th><th>Failure / notes</th></tr></thead>
<tbody>{''.join(table_rows)}</tbody></table>
<div class="notice">Status meanings are based on stored evidence: Order confirmed = Bitunix returned an order ID; Position opened = an actual position ID was returned by the open-position query; Stop-loss confirmed = the stop parameters were found in Bitunix order details or pending TP/SL data; Closed = the position was no longer present in open positions. P&amp;L is shown only when retrieved or confirmed; — means unknown, not zero. Risk controls cannot guarantee an exact maximum loss during gaps, slippage, liquidation, or exchange/API outages.</div>
</body></html>"""


def export_statement_html(path: str | Path, rows: list[dict[str, Any]] | None = None,
                          open_browser: bool = True) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_statement_html(rows), encoding="utf-8")
    if open_browser:
        webbrowser.open(target.resolve().as_uri())
    return target


def export_statement_csv(path: str | Path, rows: list[dict[str, Any]] | None = None) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = list_history() if rows is None else rows
    columns = [
        "created_at", "updated_at", "closed_at", "trader_name", "wallet", "symbol", "side",
        "source_action", "status_label", "order_id", "position_id", "qty", "margin",
        "leverage", "risk_usdt", "stop_price", "entry_price", "realized_pnl", "fees",
        "funding", "error", "stages", "notes",
    ]
    with target.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in sorted(rows, key=lambda item: int(item.get("created_at") or 0)):
            shaped = dict(row)
            for field in ("created_at", "updated_at", "closed_at"):
                shaped[field] = format_time(row.get(field)) if row.get(field) else ""
            shaped["stages"] = " | ".join(
                "{0}: {1} ({2})".format(item.get("label") or item.get("stage"),
                                        item.get("message") or "", format_time(item.get("at")))
                for item in row.get("stages", []) if isinstance(item, dict))
            shaped["notes"] = " | ".join(
                "{0}: {1}".format(format_time(item.get("at")), item.get("message") or "")
                for item in row.get("notes", []) if isinstance(item, dict))
            writer.writerow(shaped)
    return target
