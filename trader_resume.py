"""Local, journal-grounded trader performance résumé exporter."""
from __future__ import annotations
import math
from datetime import datetime
from pathlib import Path
from journal_agent import analyse_journal
from statement_report import create_statement

def _safe(value) -> str:
    return str(value if value is not None else "—").encode("cp1252", "replace").decode("cp1252")

def _wrap(text: str, font: str, size: float, max_width: float) -> list[str]:
    from reportlab.pdfbase.pdfmetrics import stringWidth
    lines, current = [], ""
    for word in _safe(text).split():
        candidate = f"{current} {word}".strip()
        if current and stringWidth(candidate, font, size) > max_width:
            lines.append(current); current = word
        else:
            current = candidate
    if current: lines.append(current)
    return lines or [""]

def _paragraph(pdf, text: str, x: float, y: float, max_width: float,
               size=8.5, leading=11, color=None) -> float:
    from reportlab.lib.colors import HexColor
    pdf.setFont("Helvetica", size); pdf.setFillColor(color or HexColor("#34465D"))
    for line in _wrap(text, "Helvetica", size, max_width):
        pdf.drawString(x, y, line); y -= leading
    return y - 3

def build_trader_resume(rows, profile: dict, market: str, out_dir):
    """Create a two-page PDF résumé and matching outcome chart from saved trades."""
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    profile = profile or {}
    name = str(profile.get("name") or "Trader Profile")
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    stats = analyse_journal(rows)
    report = create_statement(rows, market, name, out_dir,
                              document_title="Trader Performance Resume", file_prefix="TraderResume")
    pdf_path = report["pdf"]; width, height = A4
    pdf = canvas.Canvas(str(pdf_path), pagesize=A4)
    pdf.setTitle(f"Trader Performance Resume - {_safe(name)} - {_safe(market)}")
    dark, cyan = HexColor("#0B1728"), HexColor("#27BFA5")
    ink, muted, white = HexColor("#17283C"), HexColor("#687B92"), HexColor("#FFFFFF")
    pdf.setFillColor(dark); pdf.roundRect(28,height-118,width-56,86,12,fill=1,stroke=0)
    pdf.setFillColor(cyan); pdf.setFont("Helvetica-Bold",8)
    pdf.drawString(44,height-52,"TRADER PLANNER PRO | PERFORMANCE DOSSIER")
    pdf.setFillColor(white); pdf.setFont("Helvetica-Bold",21); pdf.drawString(44,height-79,_safe(name)[:42])
    pdf.setFillColor(HexColor("#B9C8D8")); pdf.setFont("Helvetica",9)
    pdf.drawRightString(width-44,height-102,f"{_safe(market)} | {datetime.now().strftime('%Y-%m-%d')}")
    metadata=f"Profile: {_safe(name)} | Market: {_safe(market)} | Starting balance: {_safe(profile.get('initial_balance','—'))} {_safe(profile.get('currency','USD'))}"
    pdf.setFillColor(ink); pdf.setFont("Helvetica",8); pdf.drawString(34,height-139,metadata[:100])
    metrics=[
      ("TRADES",str(stats["count"])),("WIN RATE",f'{stats["win_rate"]:.1f}%'),
      ("NET RESULT",f'{stats["net_r"]:+.2f} R'),("EXPECTANCY",f'{stats["expectancy_r"]:+.2f} R'),
      ("PROFIT FACTOR","INF" if math.isinf(stats["profit_factor"]) else f'{stats["profit_factor"]:.2f}'),
      ("MAX DRAWDOWN",f'{stats["max_drawdown_r"]:.2f} R')]
    gap=8; card_w=(width-68-2*gap)/3; top=height-160
    for i,(label,value) in enumerate(metrics):
      col,row=i%3,i//3; x,y=34+col*(card_w+gap),top-row*57
      pdf.setFillColor(HexColor("#F0F4F8")); pdf.roundRect(x,y-42,card_w,48,7,fill=1,stroke=0)
      pdf.setFillColor(muted); pdf.setFont("Helvetica-Bold",7); pdf.drawString(x+9,y-11,label)
      pdf.setFillColor(ink); pdf.setFont("Helvetica-Bold",13); pdf.drawString(x+9,y-31,value)
    y=top-134; pdf.setFillColor(ink); pdf.setFont("Helvetica-Bold",11); pdf.drawString(34,y,"Observed strengths"); y-=18
    strengths=[]
    setups=[g for g in stats.get("by_setup",[]) if g.get("name") and g["name"]!="Unspecified" and g["count"]>0]
    sessions=[g for g in stats.get("by_session",[]) if g.get("name") and g["name"]!="Unspecified" and g["count"]>0]
    if setups:
      b=max(setups,key=lambda g:(g["avg_r"],g["count"]))
      strengths.append(f'Highest average setup: {b["name"]} ({b["avg_r"]:+.2f} R over {b["count"]} trades; win rate {b["win_rate"]:.1f}%).')
    if sessions:
      b=max(sessions,key=lambda g:(g["avg_r"],g["count"]))
      strengths.append(f'Highest average session: {b["name"]} ({b["avg_r"]:+.2f} R over {b["count"]} trades).')
    if stats["avg_win_r"]: strengths.append(f'Average recorded win: {stats["avg_win_r"]:+.2f} R.')
    if not strengths: strengths.append("Not enough labeled trades to identify a reliable setup or session edge yet.")
    for p in strengths: y=_paragraph(pdf,p,42,y,width-84,color=ink)
    y-=3; pdf.setFillColor(ink); pdf.setFont("Helvetica-Bold",11); pdf.drawString(34,y,"Risk flags and data quality"); y-=17
    risks=[f'Average loss: {stats["avg_loss_r"]:+.2f} R; longest losing streak: {stats["max_losing_streak"]}.']
    if stats["missing_r_count"]: risks.append(f'{stats["missing_r_count"]} trade(s) have no Result (R); they count as zero for R calculations and should be completed.')
    if stats["mistakes"]:
      mistake,count=stats["mistakes"][0]; risks.append(f'Most frequent recorded mistake: "{mistake}" ({count} times).')
    if stats["count"]<20: risks.append(f'Sample-size caution: only {stats["count"]} trades; patterns are preliminary until a larger sample is available.')
    if stats["expectancy_r"]<=0 and stats["count"]: risks.append("The sample does not show positive expectancy. Review entries, stops and execution before increasing risk.")
    elif stats["expectancy_r"]>0: risks.append("Positive historical expectancy is descriptive only; confirm on new trades before changing risk.")
    for p in risks: y=_paragraph(pdf,p,42,y,width-84,size=8,leading=10,color=ink)
    y-=2; pdf.setFillColor(ink); pdf.setFont("Helvetica-Bold",11); pdf.drawString(34,y,"Recommended next actions"); y-=16
    for p in ("Record date, setup, session, emotion, mistakes and Result (R) for every closed trade.",
              "Compare setup and session results using fixed rules; avoid conclusions from tiny samples.",
              "Audit drawdown periods and repeated mistakes before changing position size."):
      y=_paragraph(pdf,"- "+p,42,y,width-84,size=8,leading=10,color=ink)
    pdf.setFillColor(muted); pdf.setFont("Helvetica",7); pdf.drawString(34,24,"Generated locally. Historical statistics are not a forecast or guarantee.")
    pdf.showPage()
    pdf.setFillColor(dark); pdf.roundRect(28,height-66,width-56,38,9,fill=1,stroke=0)
    pdf.setFillColor(white); pdf.setFont("Helvetica-Bold",13); pdf.drawString(42,height-51,"Performance Charts & Trade Outcomes")
    pdf.drawImage(ImageReader(str(report["png"])),30,58,width=width-60,height=height-152,preserveAspectRatio=True,anchor="c",mask="auto")
    pdf.setFillColor(muted); pdf.setFont("Helvetica",7); pdf.drawString(34,24,"Charts summarize recorded outcomes; missing R values are identified in the data-quality note.")
    pdf.save()
    return {"pdf":pdf_path,"png":report["png"],"stats":stats}
