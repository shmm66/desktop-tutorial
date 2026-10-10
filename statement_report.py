from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _num(value):
    try:
        raw = str(value if value is not None else "").strip().replace(",", "")
        return float(raw) if raw not in {"", "—", "-", "N/A", "n/a"} else 0.0
    except (TypeError, ValueError, OverflowError):
        return 0.0


def summarize(rows):
    results = [_num(row.get("Result (R)")) for row in rows if isinstance(row, dict)]
    wins = sum(1 for x in results if x > 0)
    losses = sum(1 for x in results if x < 0)
    flat = len(results) - wins - losses
    gross_profit = sum(x for x in results if x > 0)
    gross_loss = sum(x for x in results if x < 0)
    net_r = sum(results)
    avg_r = net_r / len(results) if results else 0.0
    profit_factor = gross_profit / abs(gross_loss) if gross_loss else math.inf if gross_profit else 0.0
    return {
        "trades": len(results),
        "wins": wins,
        "losses": losses,
        "flat": flat,
        "win_rate": wins / len(results) * 100 if results else 0.0,
        "gross_profit_r": gross_profit,
        "gross_loss_r": gross_loss,
        "net_r": net_r,
        "avg_r": avg_r,
        "profit_factor": profit_factor,
    }


def _font(size, bold=False):
    candidates = (
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_statement_chart(rows, market, profile_name, stats, timestamp):
    width, height = 1600, 1040
    image = Image.new("RGB", (width, height), "#F4F7FB")
    draw = ImageDraw.Draw(image)
    title_font = _font(44, True)
    header_font = _font(24, True)
    body_font = _font(21)
    small_font = _font(17)
    metric_font = _font(28, True)

    # Header
    draw.rounded_rectangle((32, 28, width - 32, 152), radius=28, fill="#0B1728")
    draw.text((68, 48), "TRADER PLANNER PRO", font=small_font, fill="#46E2C2")
    draw.text((68, 77), "Trading Performance Statement", font=title_font, fill="#F6F9FC")
    draw.text((width - 68, 70), timestamp, font=body_font, fill="#B8C7D8", anchor="ra")
    draw.text((68, 166), f"Profile: {profile_name}    •    Market: {market}", font=body_font, fill="#42536A")

    # KPI cards
    items = [
        ("TRADES", str(stats["trades"]), "#087E8B"),
        ("WIN RATE", f'{stats["win_rate"]:.1f}%', "#0B8F71"),
        ("NET R", f'{stats["net_r"]:+.2f} R', "#A56C10" if stats["net_r"] >= 0 else "#C04455"),
        ("AVG R", f'{stats["avg_r"]:+.2f} R', "#6355B7" if stats["avg_r"] >= 0 else "#C04455"),
        ("PROFIT FACTOR", "INF" if math.isinf(stats["profit_factor"]) else f'{stats["profit_factor"]:.2f}', "#1D69A7"),
    ]
    left, gap, card_w = 32, 14, (width - 64 - 4 * 14) // 5
    for i, (label, value, accent) in enumerate(items):
        x = left + i * (card_w + gap)
        draw.rounded_rectangle((x, 212, x + card_w, 308), radius=20, fill="#FFFFFF", outline="#DCE5EF", width=2)
        draw.rounded_rectangle((x, 212, x + 9, 308), radius=4, fill=accent)
        draw.text((x + 24, 228), label, font=small_font, fill="#64758B")
        draw.text((x + 24, 262), value, font=metric_font, fill="#16263B")

    # Last 20 trades
    chart_box = (32, 330, 980, 720)
    draw.rounded_rectangle(chart_box, radius=24, fill="#FFFFFF", outline="#DCE5EF", width=2)
    draw.text((58, 350), "TRADE RESULTS • R MULTIPLE", font=header_font, fill="#15283E")
    results = [_num(row.get("Result (R)")) for row in rows if isinstance(row, dict)][-20:]
    if not results:
        draw.text((500, 520), "No trade results recorded yet", font=body_font, fill="#7A899D", anchor="mm")
    else:
        plot_l, plot_r, plot_t, plot_b = 86, 950, 410, 654
        lo, hi = min(results + [0.0]), max(results + [0.0])
        pad = max(0.25, (hi - lo) * 0.12)
        lo, hi = lo - pad, hi + pad
        def y_map(value):
            return plot_b - (value - lo) * (plot_b - plot_t) / max(0.001, hi - lo)
        for tick in range(5):
            yy = plot_t + tick * (plot_b - plot_t) / 4
            draw.line((plot_l, yy, plot_r, yy), fill="#E7EDF4", width=2)
        zero = y_map(0.0)
        draw.line((plot_l, zero, plot_r, zero), fill="#8192A7", width=3)
        slot = (plot_r - plot_l) / len(results)
        bar_w = max(8, min(28, slot * 0.62))
        for i, value in enumerate(results):
            cx = plot_l + slot * (i + 0.5)
            yy = y_map(value)
            color = "#19A886" if value > 0 else "#E16D78" if value < 0 else "#8A9BAE"
            draw.rounded_rectangle((cx - bar_w / 2, min(zero, yy), cx + bar_w / 2, max(zero, yy) + 1),
                                   radius=5, fill=color)
            if len(results) <= 12:
                draw.text((cx, plot_b + 16), str(i + 1), font=small_font, fill="#718197", anchor="mt")

    # Outcome distribution
    pie_box = (1000, 330, width - 32, 720)
    draw.rounded_rectangle(pie_box, radius=24, fill="#FFFFFF", outline="#DCE5EF", width=2)
    draw.text((1028, 350), "OUTCOME MIX", font=header_font, fill="#15283E")
    center = (1190, 535)
    radius = 112
    counts = [stats["wins"], stats["losses"], stats["flat"]]
    colors = ["#16A47F", "#E16D78", "#94A3B8"]
    total = sum(counts)
    if total:
        angle = -90.0
        for count, color in zip(counts, colors):
            extent = 360.0 * count / total
            if extent > 0:
                draw.pieslice((center[0] - radius, center[1] - radius,
                               center[0] + radius, center[1] + radius),
                              start=angle, end=angle + extent, fill=color, outline="#FFFFFF", width=4)
            angle += extent
        inner = 62
        draw.ellipse((center[0]-inner, center[1]-inner, center[0]+inner, center[1]+inner), fill="#FFFFFF")
        draw.text(center, str(total), font=metric_font, fill="#15283E", anchor="mm")
    else:
        draw.ellipse((center[0]-radius, center[1]-radius, center[0]+radius, center[1]+radius),
                     fill="#E6ECF3")
        draw.text(center, "0", font=metric_font, fill="#64758B", anchor="mm")

    legend_x, legend_y = 1350, 456
    for i, (label, count, color) in enumerate(zip(("Wins", "Losses", "Flat"), counts, colors)):
        y = legend_y + i * 62
        draw.rounded_rectangle((legend_x, y + 5, legend_x + 20, y + 25), radius=5, fill=color)
        pct = count / total * 100 if total else 0
        draw.text((legend_x + 34, y), f"{label}: {count}", font=body_font, fill="#2C3F55")
        draw.text((legend_x + 34, y + 28), f"{pct:.1f}%", font=small_font, fill="#78879A")

    # Transparent metric definitions and disclaimer
    draw.rounded_rectangle((32, 742, width - 32, 978), radius=24, fill="#FFFFFF", outline="#DCE5EF", width=2)
    draw.text((58, 762), "RISK & PERFORMANCE DETAILS", font=header_font, fill="#15283E")
    pf = "INF" if math.isinf(stats["profit_factor"]) else f'{stats["profit_factor"]:.2f}'
    detail_specs = [
        ("Gross profit", f'{stats["gross_profit_r"]:+.2f} R'),
        ("Gross loss", f'{stats["gross_loss_r"]:+.2f} R'),
        ("Profit factor", pf),
        ("Closed trades", str(stats["trades"])),
        ("Winning trades", str(stats["wins"])),
        ("Losing trades", str(stats["losses"])),
    ]
    for i, (label, value) in enumerate(detail_specs):
        col, row = i % 3, i // 3
        x, y = 60 + col * 500, 820 + row * 68
        draw.text((x, y), label, font=small_font, fill="#6F7F93")
        draw.text((x, y + 26), value, font=header_font, fill="#243A52")
    draw.text((58, 990), "Descriptive historical statistics only • Not a forecast or guarantee of future results.",
              font=small_font, fill="#718197")
    return image


def create_statement(rows, market, profile_name, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp_dt = datetime.now()
    stamp = stamp_dt.strftime("%Y%m%d_%H%M%S_%f")
    timestamp = stamp_dt.strftime("%Y-%m-%d %H:%M")
    png_path = out_dir / f"TradingStatement_{market}_{stamp}.png"
    pdf_path = out_dir / f"TradingStatement_{market}_{stamp}.pdf"

    stats = summarize(rows)
    chart = _draw_statement_chart(rows, market, profile_name, stats, timestamp)
    chart.save(png_path, format="PNG", optimize=True)

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    pdf = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4
    pdf.setTitle(f"Trading Statement • {profile_name} • {market}")

    pdf.setFillColorRGB(0.04, 0.09, 0.16)
    pdf.roundRect(30, height - 100, width - 60, 66, 12, fill=1, stroke=0)
    pdf.setFillColorRGB(0.96, 0.98, 0.99)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(44, height - 60, "Trader Planner Pro • Trading Statement")
    pdf.setFillColorRGB(0.26, 0.88, 0.74)
    pdf.setFont("Helvetica", 9)
    pdf.drawString(44, height - 82, f"{profile_name}  •  {market}  •  {timestamp}")

    metric_items = [
        ("Trades", stats["trades"]),
        ("Win Rate", f'{stats["win_rate"]:.1f}%'),
        ("Net R", f'{stats["net_r"]:+.2f}'),
        ("Average R", f'{stats["avg_r"]:+.2f}'),
        ("Profit Factor", "INF" if math.isinf(stats["profit_factor"]) else f'{stats["profit_factor"]:.2f}'),
    ]
    y = height - 132
    gap = 8
    card_w = (width - 60 - gap * 4) / 5
    for i, (label, value) in enumerate(metric_items):
        x = 30 + i * (card_w + gap)
        pdf.setFillColorRGB(0.94, 0.96, 0.98)
        pdf.roundRect(x, y - 48, card_w, 42, 8, fill=1, stroke=0)
        pdf.setFillColorRGB(0.35, 0.41, 0.49)
        pdf.setFont("Helvetica", 7)
        pdf.drawString(x + 7, y - 22, label)
        pdf.setFillColorRGB(0.08, 0.15, 0.24)
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(x + 7, y - 39, str(value))

    from reportlab.lib.colors import HexColor
    pdf.setFillColor(HexColor("#718197"))
    pdf.setFont("Helvetica", 8)
    pdf.drawString(30, 74, "Generated locally. Historical statistics are descriptive and not performance guarantees.")
    pdf.drawImage(ImageReader(str(png_path)), 30, 100, width=width - 60, height=height - 300,
                  preserveAspectRatio=True, anchor="c", mask="auto")
    pdf.save()
    return {"pdf": pdf_path, "png": png_path, "stats": stats}
