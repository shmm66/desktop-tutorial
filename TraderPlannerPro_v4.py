# Trader Planner Pro V5
# Copyright (c) 2026 Seyed Hadi Mir Mohammad (سید هادی میر محمد), Gorgan, Iran.
# Free to use and fork; original project copyright and attribution must remain intact.

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta
import json, os, csv, webbrowser

APP = "Trader Planner Pro"
AUTHOR = "Seyed Hadi Mir Mohammad"
TELEGRAM = "@Hadimm66"
ROOT = os.path.join(os.path.expanduser("~"), "TraderPlannerPro")
os.makedirs(ROOT, exist_ok=True)
DATA = os.path.join(ROOT, "data.json")

TASKS = [("07:00","بیداری + آب + نور صبح","سلامت"),("07:15","صبحانه","غذا"),("07:45","ورزش / پیاده‌روی صبح 30–45 دقیقه","ورزش"),("08:35","دوش + آماده‌سازی میز","روتین"),("09:00","MARK UP — ساختار، روند، نقدینگی و نواحی","MARK UP"),("10:45","استراحت 15 دقیقه","استراحت"),("11:00","MARK UP — سناریوی A/B و نقاط ابطال","MARK UP"),("12:30","ثبت سناریو + بررسی خبرها","تحلیل"),("13:00","پایان MARK UP + بستن چارت","پایان"),("13:15","ناهار","غذا"),("14:00","استراحت / چرت کوتاه","ریکاوری"),("14:30","مرور پلن + آماده‌سازی سشن","آماده‌سازی"),("15:30","TRADING — فقط ستاپ‌های مجاز","TRADING"),("17:00","استراحت 10 دقیقه‌ای","کنترل"),("17:10","TRADING — ادامه سشن","TRADING"),("19:00","پایان قطعی ترید","پایان"),("19:15","شام","غذا"),("19:45","ورزش / پیاده‌روی عصر 30 دقیقه","ورزش"),("20:30","تفریح بدون چارت","تفریح"),("21:00","ژورنال + اسکرین‌شات + درس روز","ژورنال"),("21:40","مطالعه / بک‌تست سبک","یادگیری"),("22:30","خاموشی صفحه‌نمایش","خواب"),("23:30","خواب","خواب")]
PLAN = ["بازارهای مجاز","تایم‌فریم‌های اصلی","ستاپ‌های مجاز","شرایط ورود","شرایط عدم ورود","حداکثر ریسک هر معامله (%)","حداکثر ضرر روزانه (%)","حداکثر معاملات روزانه","قانون خروج","قانون توقف بعد از باخت","قوانین روانشناسی","اهداف ماهانه"]
CHECK = ["جهت و ساختار بازار مشخص است","ناحیه ورود معتبر و تازه است","ستاپ مطابق Trading Plan است","ریسک و حجم محاسبه شده","حد ضرر قبل از ورود مشخص است","R:R قابل قبول است","خبر مهم بررسی شده است","حالت روانی مناسب است","FOMO / Revenge ندارم","بعد از ورود قانون را تغییر نمی‌دهم"]
FIELDS = ["Date","Pair","Direction","Session","Timeframe","Entry","Stop Loss","Take Profit","Position Size","Risk %","Risk $","R:R","Setup","Market Structure","Liquidity","Entry Model","Emotion","Mistake","Result (R)","P&L","Lesson","Screenshot"]

def fresh():
    today=date.today(); tasks={}
    for i in range(60):
        d=(today+timedelta(i)).isoformat(); tasks[d]=[{"time":t,"title":x,"cat":c,"done":False} for t,x,c in TASKS]
    return {"version":5,"market":"Crypto","tasks":tasks,"journals":{"Forex":[],"Crypto":[]},"plan":{x:"" for x in PLAN},"check":{x:False for x in CHECK},"profile":{"name":"","timezone":"","account_currency":"USD","starting_balance":""}}

def load():
    try:
        with open(DATA,"r",encoding="utf-8") as f: old=json.load(f)
    except Exception: old={}
    db=fresh()
    for k,v in old.items():
        if isinstance(v,dict) and isinstance(db.get(k),dict): db[k].update(v)
        else: db[k]=v
    db.setdefault("journals",{"Forex":[],"Crypto":[]}); db["journals"].setdefault("Forex",[]); db["journals"].setdefault("Crypto",[])
    return db
DB=load()

def save():
    tmp=DATA+".tmp"
    with open(tmp,"w",encoding="utf-8") as f: json.dump(DB,f,ensure_ascii=False,indent=2)
    os.replace(tmp,DATA)

def num(v):
    try:return float(str(v).replace(",","").strip())
    except Exception:return 0.0

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title(APP); self.geometry("1500x940"); self.minsize(1100,720)
        self.bg="#070d19"; self.panel="#0e182a"; self.panel2="#14223a"; self.fg="#eef5ff"; self.muted="#91a5c6"; self.acc="#42d9b5"; self.line="#243754"
        self.market=DB.get("market","Crypto"); self.day=date.today().isoformat(); self.vars=[]; self.menu_open=False
        self.style=ttk.Style(self); self.style.theme_use("clam"); self.style.configure("Treeview",background=self.panel2,fieldbackground=self.panel2,foreground=self.fg,rowheight=32); self.style.map("Treeview",background=[("selected","#1e476b")])
        self._shell(); self.show("home"); self.after(500,self._clock)
    def _shell(self):
        top=tk.Frame(self,bg=self.bg); top.pack(fill="x",padx=18,pady=12); tk.Button(top,text="☰",command=self.toggle_menu,bg=self.panel,fg=self.fg,relief="flat",font=("Segoe UI",18,"bold"),width=3).pack(side="left")
        tk.Label(top,text=APP,bg=self.bg,fg=self.acc,font=("Segoe UI",24,"bold")).pack(side="left",padx=14); self.clock_label=tk.Label(top,bg=self.bg,fg=self.fg,font=("Segoe UI",11,"bold")); self.clock_label.pack(side="right")
        self.market_btn=tk.Button(top,text=self.market,command=self.change_market,bg=self.panel2,fg=self.fg,relief="flat",font=("Segoe UI",10,"bold"),padx=14,pady=7); self.market_btn.pack(side="right",padx=15)
        self.content=tk.Frame(self,bg=self.bg); self.content.pack(fill="both",expand=True,padx=16); self.menu=tk.Frame(self,bg=self.panel,width=330); self.menu.place(x=-340,y=0,relheight=1); self.menu.lift(); self._make_menu()
    def _make_menu(self):
        tk.Label(self.menu,text="TRADER PLANNER PRO",bg=self.panel,fg=self.acc,font=("Segoe UI",17,"bold")).pack(anchor="w",padx=22,pady=24)
        for text,key in [("⌂  Home","home"),("◫  برنامه روزانه","daily"),("◈  Trading Plan","plan"),("✓  Checklist","check"),("▣  Journal","journal"),("◉  مدیریت ریسک","risk"),("◷  ساعت بازارها","sessions"),("🐂  Forex Factory","ff"),("▥  گزارش‌ها و خروجی","reports"),("⚙  تنظیمات","settings")]:
            tk.Button(self.menu,text=text,command=lambda k=key:self.go(k),anchor="w",bg=self.panel,fg=self.fg,activebackground=self.panel2,activeforeground=self.acc,relief="flat",font=("Segoe UI",11),padx=22,pady=11).pack(fill="x")
        tk.Label(self.menu,text=f"© {AUTHOR}\n{TELEGRAM}",bg=self.panel,fg=self.muted,justify="left",font=("Segoe UI",9)).pack(side="bottom",anchor="w",padx=22,pady=20)
    def toggle_menu(self): self.menu.place_configure(x=0 if not self.menu_open else -340); self.menu_open=not self.menu_open
    def go(self,key):
        if self.menu_open:self.toggle_menu()
        self.show(key)
    def show(self,key):
        self.cur=key
        for w in self.content.winfo_children():w.destroy()
        getattr(self,key)()
    def _clock(self): self.clock_label.config(text=datetime.now().strftime("%Y-%m-%d  |  %H:%M:%S")); self.after(500,self._clock)
    def title(self,a,b=""):
        tk.Label(self.content,text=a,bg=self.bg,fg=self.fg,font=("Segoe UI",21,"bold")).pack(anchor="e",pady=(10,2))
        if b:tk.Label(self.content,text=b,bg=self.bg,fg=self.muted,font=("Segoe UI",10)).pack(anchor="e",pady=(0,12))
    def card(self,p):return tk.Frame(p,bg=self.panel,highlightbackground=self.line,highlightthickness=1)
    def button(self,p,text,cmd,primary=False):return tk.Button(p,text=text,command=cmd,bg=self.acc if primary else self.panel2,fg="#06131c" if primary else self.fg,relief="flat",font=("Segoe UI",10,"bold"),padx=13,pady=8)
    def change_market(self):
        self.market="Forex" if self.market=="Crypto" else "Crypto"; DB["market"]=self.market; save(); self.market_btn.config(text=self.market); self.show(self.cur)
    def home(self):
        self.title("داشبورد حرفه‌ای","مرکز کنترل ترید، نظم روزانه و عملکرد"); name=DB["profile"].get("name") or "Trader"; tk.Label(self.content,text=f"خوش آمدی، {name}",bg=self.bg,fg=self.acc,font=("Segoe UI",14,"bold")).pack(anchor="e",padx=10)
        rows=DB["journals"][self.market]; rs=[num(x.get("Result (R)")) for x in rows]; wins=sum(x>0 for x in rs); tasks=DB["tasks"].setdefault(self.day,[]); done=sum(bool(x.get("done")) for x in tasks)
        row=tk.Frame(self.content,bg=self.bg); row.pack(fill="x",pady=12)
        for a,b in [("معاملات",len(rows)),("Win Rate",f"{wins/len(rs)*100:.1f}%" if rs else "0%"),("Net R",f"{sum(rs):.2f} R"),("پیشرفت امروز",f"{done/len(tasks)*100:.0f}%" if tasks else "0%"),("بازار فعال",self.market)]:
            c=self.card(row); c.pack(side="left",fill="both",expand=True,padx=4); tk.Label(c,text=a,bg=self.panel,fg=self.muted).pack(anchor="w",padx=16,pady=(12,2)); tk.Label(c,text=b,bg=self.panel,fg=self.fg,font=("Segoe UI",18,"bold")).pack(anchor="w",padx=16,pady=(0,12))
        body=tk.Frame(self.content,bg=self.bg); body.pack(fill="both",expand=True); left=self.card(body); left.pack(side="left",fill="both",expand=True,padx=(0,6)); right=self.card(body); right.pack(side="left",fill="both",expand=True,padx=(6,0))
        tk.Label(left,text="Equity / عملکرد",bg=self.panel,fg=self.fg,font=("Segoe UI",14,"bold")).pack(anchor="e",padx=18,pady=15); canvas=tk.Canvas(left,bg=self.panel2,highlightthickness=0); canvas.pack(fill="both",expand=True,padx=18,pady=10)
        if rs:
            vals=[0]
            for r in rs:vals.append(vals[-1]+r)
            def draw(_=None):
                canvas.delete("all"); w=max(canvas.winfo_width(),400); h=max(canvas.winfo_height(),240); lo,hi=min(vals),max(vals); span=max(1,hi-lo); pts=[]
                for i,v in enumerate(vals):pts += [25+i*(w-50)/max(1,len(vals)-1),h-25-(v-lo)/span*(h-50)]
                canvas.create_line(*pts,fill=self.acc,width=3,smooth=True); canvas.create_text(25,15,text=f"{vals[-1]:.2f} R",fill=self.fg,anchor="w",font=("Segoe UI",11,"bold"))
            canvas.bind("<Configure>",draw); draw()
        else:canvas.create_text(300,130,text="پس از ثبت معامله، عملکرد اینجا نمایش داده می‌شود",fill=self.muted,font=("Segoe UI",11))
        tk.Label(right,text="برنامه امروز",bg=self.panel,fg=self.fg,font=("Segoe UI",14,"bold")).pack(anchor="e",padx=18,pady=15)
        for x in tasks[:12]:tk.Label(right,text=f'{"✓" if x["done"] else "○"}  {x["time"]}   {x["title"]}',bg=self.panel,fg=self.muted if x["done"] else self.fg,anchor="e").pack(fill="x",padx=18,pady=3)
        self.button(right,"باز کردن Journal",lambda:self.show("journal"),True).pack(anchor="e",padx=18,pady=12)
    def daily(self):
        self.title("برنامه روزانه","تیک بزن؛ وضعیت در داشبورد ذخیره می‌شود"); nav=tk.Frame(self.content,bg=self.bg); nav.pack(fill="x"); self.button(nav,"روز قبل",lambda:self._shift_day(-1)).pack(side="left",padx=4); tk.Label(nav,text=self.day,bg=self.bg,fg=self.fg,font=("Segoe UI",12,"bold")).pack(side="left",padx=14); self.button(nav,"روز بعد",lambda:self._shift_day(1)).pack(side="left",padx=4)
        box=tk.Frame(self.content,bg=self.bg); box.pack(fill="both",expand=True,pady=12); canvas=tk.Canvas(box,bg=self.bg,highlightthickness=0); scroll=ttk.Scrollbar(box,orient="vertical",command=canvas.yview); inner=tk.Frame(canvas,bg=self.bg); inner.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all"))); canvas.create_window((0,0),window=inner,anchor="nw"); canvas.configure(yscrollcommand=scroll.set); canvas.pack(side="left",fill="both",expand=True); scroll.pack(side="right",fill="y")
        tasks=DB["tasks"].setdefault(self.day,[])
        if not tasks:tasks[:] = [{"time":t,"title":x,"cat":c,"done":False} for t,x,c in TASKS]; save()
        for i,x in enumerate(tasks):
            v=tk.BooleanVar(value=bool(x.get("done"))); tk.Checkbutton(inner,text=f'{x["time"]}   {x["title"]}   [{x["cat"]}]',variable=v,command=lambda i=i,v=v:self._toggle_task(tasks,i,v),bg=self.panel,fg=self.fg,selectcolor=self.panel2,activebackground=self.panel,activeforeground=self.acc,anchor="e",padx=14,pady=9).pack(fill="x",pady=2)
    def _toggle_task(self,tasks,i,var):tasks[i]["done"]=bool(var.get()); save()
    def _shift_day(self,n):self.day=(date.fromisoformat(self.day)+timedelta(days=n)).isoformat(); self.show("daily")
    def _entry(self,p,label,default="",width=32):
        f=tk.Frame(p,bg=self.panel); f.pack(fill="x",padx=12,pady=4); tk.Label(f,text=label,bg=self.panel,fg=self.muted,width=18,anchor="e").pack(side="right"); e=tk.Entry(f,bg=self.panel2,fg=self.fg,insertbackground=self.fg,relief="flat",width=width); e.insert(0,default); e.pack(side="right",padx=8); return e
    def journal(self):
        self.title(f"Journal — {self.market}","هر معامله را ثبت کن؛ داده محلی و قابل خروجی است"); bar=tk.Frame(self.content,bg=self.bg); bar.pack(fill="x",pady=4); self.button(bar,"＋ ثبت معامله",self.add_trade,True).pack(side="left",padx=4); self.button(bar,"CSV خروجی",self.export_journal).pack(side="left",padx=4)
        tree=ttk.Treeview(self.content,columns=("date","pair","dir","r","pnl","setup","lesson"),show="headings"); heads={"date":"Date","pair":"Pair","dir":"Direction","r":"Result (R)","pnl":"P&L","setup":"Setup","lesson":"Lesson"}
        for k,h in heads.items():tree.heading(k,text=h); tree.column(k,width=150)
        tree.pack(fill="both",expand=True,pady=8)
        for r in DB["journals"][self.market]:tree.insert("","end",values=(r.get("Date",""),r.get("Pair",""),r.get("Direction",""),r.get("Result (R)",""),r.get("P&L",""),r.get("Setup",""),r.get("Lesson","")))
    def add_trade(self):
        win=tk.Toplevel(self); win.title("ثبت معامله جدید"); win.geometry("720x760"); win.configure(bg=self.panel); win.transient(self); win.grab_set(); canvas=tk.Canvas(win,bg=self.panel,highlightthickness=0); canvas.pack(side="left",fill="both",expand=True); sb=ttk.Scrollbar(win,orient="vertical",command=canvas.yview); sb.pack(side="right",fill="y"); canvas.configure(yscrollcommand=sb.set); form=tk.Frame(canvas,bg=self.panel); canvas.create_window((0,0),window=form,anchor="nw"); form.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all"))); entries={}
        for f in FIELDS:entries[f]=self._entry(form,f,self.day if f=="Date" else "")
        def save_trade():
            row={f:e.get().strip() for f,e in entries.items()}
            if not row["Pair"]:messagebox.showwarning("ثبت معامله","Pair / Coin را وارد کن.",parent=win); return
            DB["journals"][self.market].append(row); save(); win.destroy(); self.show("journal")
        self.button(form,"ذخیره معامله",save_trade,True).pack(pady=18)
    def export_journal(self):self._report_csv(self.market)
    def _report_csv(self,market):
        path=filedialog.asksaveasfilename(defaultextension=".csv",initialfile=f"{market}_Report.csv",filetypes=[("CSV","*.csv")]);
        if not path:return
        with open(path,"w",newline="",encoding="utf-8-sig") as f:w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="ignore"); w.writeheader(); w.writerows(DB["journals"][market])
        messagebox.showinfo("گزارش","گزارش CSV ذخیره شد.")
    def plan(self):
        self.title("Trading Plan","قوانین شخصی را ذخیره کن"); box=self.card(self.content); box.pack(fill="both",expand=True,pady=10)
        self.vars=[]
        for key in PLAN:
            f=tk.Frame(box,bg=self.panel); f.pack(fill="x",padx=14,pady=5); tk.Label(f,text=key,bg=self.panel,fg=self.muted,width=30,anchor="e").pack(side="right"); e=tk.Entry(f,bg=self.panel2,fg=self.fg,insertbackground=self.fg,relief="flat"); e.insert(0,DB["plan"].get(key,"")); e.pack(side="right",fill="x",expand=True,padx=8); self.vars.append((key,e))
        self.button(box,"ذخیره Trading Plan",self.save_plan,True).pack(anchor="e",padx=16,pady=15)
    def save_plan(self):
        for k,e in self.vars:DB["plan"][k]=e.get().strip()
        self.vars=[]; save(); messagebox.showinfo("ذخیره شد","Trading Plan ذخیره شد.")
    def check(self):
        self.title("Checklist","قبل از ورود همه موارد ضروری را بررسی کن"); box=self.card(self.content); box.pack(fill="both",expand=True,pady=10)
        for key in CHECK:
            v=tk.BooleanVar(value=bool(DB["check"].get(key))); tk.Checkbutton(box,text=key,variable=v,command=lambda k=key,v=v:self._set_check(k,v),bg=self.panel,fg=self.fg,selectcolor=self.panel2,activebackground=self.panel,activeforeground=self.acc,anchor="e",padx=18,pady=10).pack(fill="x")
        self.button(self.content,"پاک کردن Checklist",self.reset_check).pack(anchor="e",pady=10)
    def _set_check(self,k,v):DB["check"][k]=bool(v.get()); save()
    def reset_check(self):DB["check"]={x:False for x in CHECK}; save(); self.show("check")
    def risk(self):
        self.title("مدیریت ریسک","محاسبه ساده حجم/ریسک"); box=self.card(self.content); box.pack(fill="x",pady=20); bal=self._entry(box,"Account Balance","10000"); risk=self._entry(box,"Risk %","1"); stop=self._entry(box,"Stop Distance","100"); out=tk.Label(box,text="Risk Amount: —",bg=self.panel,fg=self.acc,font=("Segoe UI",15,"bold")); out.pack(pady=18)
        def calc():
            amount=num(bal.get())*num(risk.get())/100; out.config(text=f"Risk Amount: {amount:.2f}   |   Approx. Units: {amount/num(stop.get()):.4f}" if num(stop.get()) else f"Risk Amount: {amount:.2f}")
        self.button(box,"محاسبه",calc,True).pack(anchor="e",padx=12,pady=12)
    def sessions(self):
        self.title("ساعت بازارها","بازه‌های رایج بازار");
        for name,a,b in [("Tokyo","00:00","09:00"),("London","08:00","17:00"),("New York","13:00","22:00")]:
            c=self.card(self.content); c.pack(fill="x",pady=6); tk.Label(c,text=f"{name}    {a} — {b}",bg=self.panel,fg=self.fg,font=("Segoe UI",14,"bold")).pack(anchor="e",padx=18,pady=14)
    def ff(self):
        self.title("Forex Factory","تقویم خبرها در مرورگر باز می‌شود"); self.button(self.content,"باز کردن Forex Factory",lambda:webbrowser.open("https://www.forexfactory.com/calendar/"),True).pack(anchor="e",pady=20)
    def reports(self):
        self.title("گزارش‌ها و خروجی","خروجی‌ها از Journal فعلی ساخته می‌شوند"); box=self.card(self.content); box.pack(fill="x",pady=20); self.button(box,"CSV Crypto",lambda:self._report_csv("Crypto")).pack(side="left",padx=8,pady=18); self.button(box,"CSV Forex",lambda:self._report_csv("Forex")).pack(side="left",padx=8,pady=18); self.button(box,"گزارش TXT",self._report_txt,True).pack(side="left",padx=8,pady=18)
    def _report_txt(self):
        path=filedialog.asksaveasfilename(defaultextension=".txt",initialfile="TraderPlanner_Report.txt",filetypes=[("Text","*.txt")]);
        if not path:return
        rows=DB["journals"][self.market]; rs=[num(x.get("Result (R)")) for x in rows]
        with open(path,"w",encoding="utf-8") as f:f.write(f"{APP}\nAuthor: {AUTHOR}\nTelegram: {TELEGRAM}\nMarket: {self.market}\nTrades: {len(rows)}\nNet R: {sum(rs):.2f}\n")
        messagebox.showinfo("گزارش","گزارش TXT ذخیره شد.")
    def settings(self):
        self.title("تنظیمات","اطلاعات کاربر و مالکیت پروژه"); box=self.card(self.content); box.pack(fill="x",pady=20); name=self._entry(box,"نام",DB["profile"].get("name","")); tz=self._entry(box,"Timezone",DB["profile"].get("timezone","")); bal=self._entry(box,"Starting Balance",DB["profile"].get("starting_balance",""))
        def save_settings():DB["profile"].update({"name":name.get().strip(),"timezone":tz.get().strip(),"starting_balance":bal.get().strip()}); save(); messagebox.showinfo("ذخیره شد","تنظیمات ذخیره شد.")
        self.button(box,"ذخیره تنظیمات",save_settings,True).pack(anchor="e",padx=12,pady=14); tk.Label(self.content,text=f"© 2026 {AUTHOR} — Gorgan, Iran\nTelegram: {TELEGRAM}\nFree software • Fork permitted • Keep original attribution",bg=self.bg,fg=self.muted,font=("Segoe UI",10),justify="right").pack(anchor="e",pady=20)

if __name__=="__main__": App().mainloop()
