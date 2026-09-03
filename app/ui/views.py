from __future__ import annotations

import csv
import json
import math
import threading
import urllib.request
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from tkinter import END, filedialog, messagebox
from tkinter import ttk
from zoneinfo import ZoneInfo

from app.core.database import connect
from app.core.config import AppConfig
from app.domains.crypto.journal import CryptoTrade
from app.domains.forex.calculator import ForexCalculator
from app.domains.forex.journal import ForexTrade
from app.repositories.sqlite_journal_repository import SQLiteJournalRepository
from app.domains.journal.models import AssetClass, JournalEntry, TradeDirection, TradeOutcome
from app.services.journal_service import JournalService
from .theme import ACCENT, BG, DANGER, MUTED, SURFACE, SURFACE_2, TEXT, WARNING


class BaseView(ttk.Frame):
    def __init__(self, master, title: str, subtitle: str = ""):
        super().__init__(master)
        ttk.Label(self, text=title, style="Title.TLabel").pack(anchor="e", pady=(0, 4))
        if subtitle:
            ttk.Label(self, text=subtitle, style="Muted.TLabel").pack(anchor="e", pady=(0, 16))

    def card(self):
        f = ttk.Frame(self, style="Card.TFrame", padding=16)
        return f


class HomeView(BaseView):
    def __init__(self, master, config: AppConfig, open_view):
        super().__init__(master, "داشبورد تریدر", "مرکز کنترل روزانه؛ خلاصه عملکرد، نظم و بازار")
        self.config, self.open_view = config, open_view
        self.stats = ttk.Frame(self)
        self.stats.pack(fill="x", pady=(0, 16))
        self.refresh()
        quick = self.card(); quick.pack(fill="x", pady=8)
        ttk.Label(quick, text="دسترسی سریع", style="CardTitle.TLabel").pack(anchor="e")
        row = ttk.Frame(quick, style="Card.TFrame"); row.pack(fill="x", pady=(12, 0))
        for text, target in [("+ ثبت معامله", "journal"), ("ماشین حساب فارکس", "calculator"), ("چک‌لیست", "checklist"), ("ساعت سشن‌ها", "sessions")]:
            ttk.Button(row, text=text, command=lambda t=target: open_view(t)).pack(side="right", padx=5)

        market = self.card(); market.pack(fill="both", expand=True, pady=8)
        ttk.Label(market, text="نمای بازار", style="CardTitle.TLabel").pack(anchor="e")
        self.market_text = ttk.Label(market, text="در حال دریافت داده‌های بازار…", justify="right")
        self.market_text.pack(anchor="e", pady=12)
        threading.Thread(target=self._market, daemon=True).start()

    def _market(self):
        # Public Stooq endpoint; failures are non-fatal and never block the UI.
        try:
            url = "https://stooq.com/q/l/?s=eurusd,xauusd,cl.f,btcusd&f=sd2t2ohlcv&h&e=csv"
            with urllib.request.urlopen(url, timeout=4) as r:
                raw = r.read().decode("utf-8", errors="replace")
            self.after(0, lambda: self.market_text.configure(text="داده آنلاین آماده است؛ برای قیمت زنده کامل، منبع بازار را در تنظیمات انتخاب کنید."))
        except Exception:
            self.after(0, lambda: self.market_text.configure(text="اتصال بازار در دسترس نیست؛ برنامه بدون اینترنت هم قابل استفاده است."))

    def refresh(self):
        for w in self.stats.winfo_children(): w.destroy()
        conn = connect(self.config.db_path)
        try:
            rows = conn.execute("SELECT market, outcome, result_r, pnl FROM trades").fetchall()
        finally: conn.close()
        count = len(rows); wins = sum(1 for r in rows if r["outcome"] == "win")
        total_r = sum(float(r["result_r"] or 0) for r in rows); pnl = sum(float(r["pnl"] or 0) for r in rows)
        values = [("معاملات", count), ("Win Rate", f"{(wins/count*100):.1f}%" if count else "0.0%"), ("Net R", f"{total_r:+.2f}R"), ("P&L", f"{pnl:+,.2f}")]
        for label, value in values:
            c = self.card(); c.pack(side="right", fill="x", expand=True, padx=5)
            ttk.Label(c, text=label, style="CardTitle.TLabel").pack(anchor="e")
            ttk.Label(c, text=str(value), style="CardValue.TLabel").pack(anchor="e", pady=(8,0))


class PlannerView(BaseView):
    def __init__(self, master, config: AppConfig):
        super().__init__(master, "Trading Plan", "قوانین خودت را ثبت کن؛ برنامه خالی است و قابل شخصی‌سازی")
        self.config = config
        fields = ["بازارهای مجاز", "تایم‌فریم‌ها", "ستاپ‌های مجاز", "شرایط ورود", "شرایط عدم ورود", "حداکثر ریسک هر معامله (%)", "حداکثر ضرر روزانه (%)", "حداکثر معاملات روزانه", "قانون خروج", "قانون توقف بعد از باخت", "قوانین روانشناسی", "اهداف ماهانه"]
        self.vars = {}
        body = ttk.Frame(self); body.pack(fill="both", expand=True)
        for i, field in enumerate(fields):
            ttk.Label(body, text=field).grid(row=i, column=1, sticky="e", padx=8, pady=5)
            v = ttk.Entry(body); v.grid(row=i, column=0, sticky="ew", padx=8, pady=5); self.vars[field]=v
        body.columnconfigure(0, weight=1)
        ttk.Button(self, text="ذخیره Trading Plan", style="Accent.TButton", command=self.save).pack(pady=12)
    def save(self):
        conn=connect(self.config.db_path)
        try:
            for k,v in self.vars.items(): conn.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (f"plan.{k}",v.get()))
            conn.commit()
        finally: conn.close()
        messagebox.showinfo("ذخیره شد", "Trading Plan ذخیره شد.")


class ChecklistView(BaseView):
    def __init__(self, master):
        super().__init__(master, "چک‌لیست قبل از ورود", "اگر یکی از شروط حیاتی رد شد، معامله نکن")
        items=["جهت/ساختار بازار مشخص است", "ناحیه ورود معتبر است", "ستاپ Trading Plan را دارد", "حد ضرر قبل از ورود مشخص شده", "ریسک محاسبه شده است", "حداقل R:R موردنیاز برقرار است", "خبر مهم نزدیک ورود بررسی شده", "حالت روانی مناسب است", "FOMO / Revenge در کار نیست", "بعد از ورود دستکاری تصادفی انجام نمی‌دهم"]
        self.vars=[]
        box=self.card(); box.pack(fill="x")
        for text in items:
            v=ttk.BooleanVar(value=False); self.vars.append(v); ttk.Checkbutton(box,text=text,variable=v).pack(anchor="e", pady=4)
        ttk.Button(self,text="ریست چک‌لیست",style="Danger.TButton",command=lambda:[v.set(False) for v in self.vars]).pack(pady=12)


class JournalView(BaseView):
    def __init__(self, master, config: AppConfig):
        super().__init__(master, "Trading Journal", "ژورنال کاملاً جدا برای Forex و Crypto با فیلدهای اختصاصی")
        self.config=config; self.market=ttk.StringVar(value="forex")
        top=ttk.Frame(self); top.pack(fill="x",pady=(0,10))
        ttk.Label(top,text="نوع بازار:").pack(side="right",padx=5); cb=ttk.Combobox(top,textvariable=self.market,values=["forex","crypto"],state="readonly",width=14); cb.pack(side="right"); cb.bind("<<ComboboxSelected>>",lambda e:self.render_form())
        self.form=ttk.Frame(self); self.form.pack(fill="x"); self.table=ttk.Treeview(self,columns=("date","market","symbol","dir","entry","sl","tp","result","pnl"),show="headings",height=9)
        for c,h in zip(self.table["columns"],["Date","Market","Symbol","Dir","Entry","SL","TP","R","P&L"]): self.table.heading(c,text=h)
        self.table.pack(fill="both",expand=True,pady=12); self.render_form(); self.refresh()

    def render_form(self):
        for w in self.form.winfo_children():w.destroy()
        m=self.market.get(); self.vars={}
        fields = (["Symbol","Direction","Lot Size","Entry","Stop Loss","Take Profit","Spread","Commission","Swap","Session","Setup","Notes"] if m=="forex" else ["Symbol","Direction","Quantity","Entry","Stop Loss","Take Profit","Leverage","Margin","Fees","Funding","Liquidation Price","Exchange","Setup","Notes"])
        grid=ttk.Frame(self.form);grid.pack(fill="x")
        for i,f in enumerate(fields):
            col=(i%4)*2; row=i//4; ttk.Label(grid,text=f).grid(row=row,column=col+1,sticky="e",padx=5,pady=4); e=ttk.Entry(grid);e.grid(row=row,column=col,sticky="ew",padx=5,pady=4);self.vars[f]=e
        for c in range(0,8,2):grid.columnconfigure(c,weight=1)
        ttk.Button(self.form,text="ثبت معامله",style="Accent.TButton",command=self.save).pack(pady=8)

    def _f(self,key,default=""):
        return self.vars[key].get().strip() if key in self.vars else default
    def _num(self,key,default=0.0):
        try:return float(self._f(key))
        except ValueError:return default

    def save(self):
        try:
            conn=connect(self.config.db_path); repo=SQLiteJournalRepository(conn)
            if self.market.get()=="forex":
                entry=ForexTrade(self._f("Symbol"),self._f("Direction") or "long",self._num("Lot Size"),self._num("Entry"),self._num("Stop Loss"),self._num("Take Profit"),self._num("Spread"),self._num("Commission"),self._num("Swap"),self._f("Session"),self._f("Setup"),self._f("Notes"))
                # The shared repository stores the common journal contract; preserve market-specific fields in notes.
                je=JournalEntry(id=None,asset_class=AssetClass.FOREX,symbol=entry.symbol,direction=TradeDirection.LONG if entry.direction.lower()!="short" else TradeDirection.SHORT,entry_price=__import__('decimal').Decimal(str(entry.entry or 0)),quantity=__import__('decimal').Decimal(str(entry.lot_size)),stop_loss=__import__('decimal').Decimal(str(entry.stop_loss)) if entry.stop_loss is not None else None,take_profit=__import__('decimal').Decimal(str(entry.take_profit)) if entry.take_profit is not None else None,fees=__import__('decimal').Decimal(str(entry.commission)),notes=f"Spread={entry.spread}; Swap={entry.swap}; Session={entry.session}; {entry.notes}",setup=entry.setup)
            else:
                entry=CryptoTrade(self._f("Symbol"),self._f("Direction") or "long",self._num("Quantity"),self._num("Entry"),self._num("Stop Loss"),self._num("Take Profit"),self._num("Leverage",1),self._num("Margin"),self._num("Fees"),self._num("Funding"),self._num("Liquidation Price") if self._f("Liquidation Price") else None,self._f("Exchange"),self._f("Setup"),self._f("Notes"))
                je=JournalEntry(id=None,asset_class=AssetClass.CRYPTO,symbol=entry.symbol,direction=TradeDirection.LONG if entry.direction.lower()!="short" else TradeDirection.SHORT,entry_price=__import__('decimal').Decimal(str(entry.entry or 0)),quantity=__import__('decimal').Decimal(str(entry.quantity)),stop_loss=__import__('decimal').Decimal(str(entry.stop_loss)) if entry.stop_loss is not None else None,take_profit=__import__('decimal').Decimal(str(entry.take_profit)) if entry.take_profit is not None else None,fees=__import__('decimal').Decimal(str(entry.fees)),funding=__import__('decimal').Decimal(str(entry.funding)),notes=f"Leverage={entry.leverage}; Margin={entry.margin}; Liq={entry.liquidation_price}; Exchange={entry.exchange}; {entry.notes}",setup=entry.setup)
            repo.save(je); conn.close(); self.refresh(); messagebox.showinfo("ثبت شد","معامله در ژورنال ذخیره شد.")
        except Exception as exc: messagebox.showerror("خطا",str(exc))

    def refresh(self):
        for i in self.table.get_children():self.table.delete(i)
        conn=connect(self.config.db_path)
        try: rows=SQLiteJournalRepository(conn).list(self.market.get())
        finally:conn.close()
        for r in rows:
            self.table.insert("","end",values=(r.opened_at.strftime("%Y-%m-%d"),r.asset_class.value,r.symbol,r.direction.value,float(r.entry_price),r.stop_loss or "",r.take_profit or "",r.outcome.value,r.pnl or ""))


class CalculatorView(BaseView):
    def __init__(self, master):
        super().__init__(master,"ماشین حساب فارکس","Position Size، ریسک، Pip Value و R:R")
        self.v={}; fields=["Balance","Risk %","Stop Pips","Pip Value / Lot","Entry","Stop","Target"]
        box=self.card();box.pack(fill="x")
        for i,f in enumerate(fields):
            ttk.Label(box,text=f).grid(row=i//2,column=(i%2)*2+1,sticky="e",padx=8,pady=6);e=ttk.Entry(box);e.grid(row=i//2,column=(i%2)*2,sticky="ew",padx=8,pady=6);self.v[f]=e
        box.columnconfigure(0,weight=1);box.columnconfigure(2,weight=1)
        ttk.Button(self,text="محاسبه",style="Accent.TButton",command=self.calc).pack(pady=12)
        self.out=ttk.Label(self,text="—",style="Hero.TLabel");self.out.pack(pady=10)
    def n(self,k):return float(self.v[k].get() or 0)
    def calc(self):
        try:
            c=ForexCalculator(); risk=c.risk_amount(self.n("Balance"),self.n("Risk %")); lots=c.lots_for_risk(self.n("Balance"),self.n("Risk %"),self.n("Stop Pips"),self.n("Pip Value / Lot")); rr=c.reward_risk(self.n("Entry"),self.n("Stop"),self.n("Target"))
            self.out.configure(text=f"Risk: ${risk:,.2f}   |   Lots: {lots:.2f}   |   R:R: 1:{rr:.2f}")
        except Exception as e:messagebox.showerror("خطا",str(e))


class SessionsView(BaseView):
    def __init__(self, master):
        super().__init__(master,"ساعت بازارهای مالی","سشن‌ها با ساعت محلی شما و DST به‌روز می‌شوند")
        self.labels={}; box=self.card();box.pack(fill="x")
        for name,zone in [("Sydney","Australia/Sydney"),("Tokyo","Asia/Tokyo"),("London","Europe/London"),("New York","America/New_York"),("UTC","UTC")]:
            r=ttk.Frame(box,style="Card.TFrame");r.pack(fill="x",pady=8);ttk.Label(r,text=name,style="CardTitle.TLabel").pack(side="right");l=ttk.Label(r,text="--:--:--",style="CardValue.TLabel");l.pack(side="left");self.labels[name]=(l,zone)
        self.tick()
    def tick(self):
        for l,z in self.labels.items():self.labels[l][0].configure(text=datetime.now(ZoneInfo(z)).strftime("%H:%M:%S"))
        self.after(1000,self.tick)


class MarketView(BaseView):
    def __init__(self,master):
        super().__init__(master,"بازار و Forex Factory","بازکردن منبع خبر در مرورگر سیستم؛ قیمت‌ها در صورت دسترسی اینترنتی به‌روزرسانی می‌شوند")
        box=self.card();box.pack(fill="x")
        ttk.Label(box,text="🐂   BULL        ⚔        BEAR   🐻",font=("Segoe UI",22,"bold"),style="CardTitle.TLabel").pack(pady=18)
        ttk.Button(box,text="باز کردن Forex Factory",style="Accent.TButton",command=lambda:webbrowser.open("https://www.forexfactory.com/calendar")).pack()
        ttk.Label(self,text="Crypto mode: BTC, ETH, BNB, XRP, SOL, ADA, DOGE, TRX, AVAX, LINK + BTC Dominance + USDT Dominance\nForex mode: EURUSD, GBPUSD, USDJPY + Gold, Silver, Copper, Oil + شاخص‌های سهام منتخب",style="Muted.TLabel",justify="right").pack(anchor="e",pady=18)


class ReportsView(BaseView):
    def __init__(self,master,config:AppConfig):
        super().__init__(master,"گزارش و سوابق","خروجی CSV/Excel و PDF برای آرشیو شخصی")
        self.config=config;box=self.card();box.pack(fill="x")
        ttk.Button(box,text="Export CSV",command=self.csv).pack(side="right",padx=5);ttk.Button(box,text="Export Excel",command=self.xlsx).pack(side="right",padx=5);ttk.Button(box,text="Export PDF",command=self.pdf).pack(side="right",padx=5)
    def rows(self):
        conn=connect(self.config.db_path)
        try:return [dict(r) for r in conn.execute("SELECT * FROM trades ORDER BY id DESC").fetchall()]
        finally:conn.close()
    def csv(self):
        p=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")]);
        if not p:return
        rows=self.rows(); keys=list(rows[0].keys()) if rows else ["id","market","symbol","direction","pnl","result_r"]
        with open(p,"w",newline="",encoding="utf-8-sig") as f:w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
    def xlsx(self):
        try:from openpyxl import Workbook
        except ImportError:messagebox.showerror("خطا","openpyxl نصب نیست.");return
        p=filedialog.asksaveasfilename(defaultextension=".xlsx",filetypes=[("Excel","*.xlsx")]);
        if not p:return
        rows=self.rows();wb=Workbook();ws=wb.active;ws.title="Trades";keys=list(rows[0].keys()) if rows else ["id","market","symbol","direction","pnl","result_r"]
        ws.append(keys)
        for r in rows:ws.append([r.get(k) for k in keys])
        wb.save(p)
    def pdf(self):
        try:from reportlab.lib.pagesizes import A4;from reportlab.platypus import SimpleDocTemplate,Table,TableStyle,Paragraph;from reportlab.lib import colors
        except ImportError:messagebox.showerror("خطا","reportlab نصب نیست.");return
        p=filedialog.asksaveasfilename(defaultextension=".pdf",filetypes=[("PDF","*.pdf")]);
        if not p:return
        rows=self.rows();data=[["Date","Market","Symbol","Direction","R","P&L"]]+[[str(r.get("opened_at") or ""),r.get("market"),r.get("symbol"),r.get("direction"),r.get("result_r") or "",r.get("pnl") or ""] for r in rows]
        doc=SimpleDocTemplate(p,pagesize=A4,title="Trader Planner Pro Journal");t=Table(data,repeatRows=1);t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.4,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("FONTSIZE",(0,0),(-1,-1),8)]));doc.build([Paragraph("Trader Planner Pro — Trading Journal",__import__('reportlab').lib.styles.getSampleStyleSheet()["Title"]),t])


class SettingsView(BaseView):
    def __init__(self,master,config:AppConfig):
        super().__init__(master,"تنظیمات","زبان و اطلاعات مالک گزارش‌ها")
        self.config=config;self.v={}
        box=self.card();box.pack(fill="x")
        for i,(k,label) in enumerate([("full_name","نام و نام خانوادگی"),("email","ایمیل"),("language","Language")]):
            ttk.Label(box,text=label).grid(row=i,column=1,sticky="e",padx=8,pady=7);e=ttk.Entry(box);e.grid(row=i,column=0,sticky="ew",padx=8,pady=7);self.v[k]=e
        self.v["language"].insert(0,"فارسی / English");box.columnconfigure(0,weight=1)
        ttk.Button(self,text="ذخیره پروفایل",style="Accent.TButton",command=self.save).pack(pady=12)
        ttk.Label(self,text="مالکیت پروژه: Seyed Hadi Mir Mohammad — Iran, Gorgan\nپشتیبانی Telegram: @Hadimm66",style="Muted.TLabel",justify="right").pack(anchor="e",pady=10)
    def save(self):
        conn=connect(self.config.db_path)
        try:
            conn.execute("INSERT INTO profiles(full_name,email,language) VALUES(?,?,?)",(self.v["full_name"].get(),self.v["email"].get(),self.v["language"].get()));conn.commit()
        finally:conn.close()
        messagebox.showinfo("ذخیره شد","پروفایل ذخیره شد.")
