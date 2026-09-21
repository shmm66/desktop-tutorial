from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def summarize(rows):
    results = [_num(row.get("Result (R)")) for row in rows]
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


def create_statement(rows, market, profile_name, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    png_path = out_dir / f"TradingStatement_{market}_{stamp}.png"
    pdf_path = out_dir / f"TradingStatement_{market}_{stamp}.pdf"

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    stats = summarize(rows)
    results = [_num(row.get("Result (R)")) for row in rows]
    labels = [str(i + 1) for i in range(len(results))]

    fig = plt.figure(figsize=(12, 8))
    ax1 = fig.add_axes([0.08, 0.42, 0.88, 0.48])
    ax1.bar(labels[-20:] or ["—"], results[-20:] or [0])
    ax1.axhline(0, linewidth=1)
    ax1.set_title(f"{market} • Trade R Results")
    ax1.set_ylabel("R")

    ax2 = fig.add_axes([0.08, 0.08, 0.34, 0.24])
    ax2.pie(
        [stats["wins"], stats["losses"], stats["flat"]],
        labels=["Wins", "Losses", "Flat"],
        autopct="%1.0f%%",
    )
    ax2.set_title("Outcome Mix")

    ax3 = fig.add_axes([0.55, 0.08, 0.40, 0.24])
    keys = ["Trades", "Win Rate %", "Net R", "Avg R"]
    values = [stats["trades"], stats["win_rate"], stats["net_r"], stats["avg_r"]]
    ax3.bar(keys, values)
    ax3.set_title("Performance Snapshot")
    ax3.tick_params(axis="x", rotation=25)

    fig.suptitle(
        f"Trader Planner Pro — Trading Statement\n"
        f"{profile_name} • {market} • {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        fontsize=15,
        fontweight="bold",
    )
    fig.savefig(png_path, dpi=160, bbox_inches="tight")
    plt.close(fig)

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    pdf = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4
    pdf.setTitle(f"Trading Statement • {profile_name} • {market}")

    y = height - 42
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(36, y, "Trader Planner Pro — Trading Statement")
    y -= 22
    pdf.setFont("Helvetica", 10)
    pdf.drawString(36, y, f"Profile: {profile_name}    Market: {market}")
    y -= 28

    metrics = [
        ("Trades", stats["trades"]),
        ("Win Rate", f"{stats['win_rate']:.1f}%"),
        ("Net R", f"{stats['net_r']:.2f}"),
        ("Average R", f"{stats['avg_r']:.2f}"),
        ("Profit Factor", "∞" if math.isinf(stats["profit_factor"]) else f"{stats['profit_factor']:.2f}"),
    ]
    x = 36
    for label, value in metrics:
        pdf.setFillColorRGB(0.95, 0.96, 0.98)
        pdf.roundRect(x, y - 22, 96, 46, 8, fill=1, stroke=0)
        pdf.setFillColorRGB(0.15, 0.18, 0.22)
        pdf.setFont("Helvetica", 8)
        pdf.drawString(x + 8, y + 8, label)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(x + 8, y - 7, str(value))
        x += 108

    y -= 82
    image = ImageReader(str(png_path))
    pdf.drawImage(image, 36, 90, width=width - 72, height=420, preserveAspectRatio=True, anchor="c", mask="auto")

    pdf.setFont("Helvetica-Oblique", 8)
    pdf.setFillColorRGB(0.35, 0.38, 0.42)
    pdf.drawString(36, 42, "Generated locally by Trader Planner Pro. Metrics are descriptive and not performance guarantees.")
    pdf.save()

    return {"pdf": pdf_path, "png": png_path, "stats": stats}
