# Trader Planner Pro V6 — stable daily planner + two-column trading journal
# Copyright (c) 2026 Seyed Hadi Mir Mohammad (سید هادی میر محمد), Gorgan, Iran.
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, timedelta, datetime
import json, os, csv

APP='Trader Planner Pro'
ROOT=os.path.join(os.path.expanduser('~'),'TraderPlannerPro')
DATA=os.path.join(ROOT,'data.json')
os.makedirs(ROOT,exist_ok=True)

TASKS=[('07:00','بیداری + آب + نور صبح','سلامت'),('07:15','صبحانه','غذا'),('07:45','ورزش / پیاده‌روی صبح 30–45 دقیقه','ورزش'),('08:35','دوش + آماده‌سازی میز','روتین'),('09:00','MARK UP — ساختار، روند، نقدینگی و نواحی','MARK UP'),('10:45','استراحت 15 دقیقه','استراحت'),('11:00','MARK UP — سناریوی A/B و نقاط ابطال','MARK UP'),('12:30','ثبت سناریو + بررسی خبرها','تحلیل'),('13:00','پایان MARK UP + بستن چارت','پایان'),('13:15','ناهار','غذا'),('14:00','استراحت / چرت کوتاه','ریکاوری'),('14:30','مرور پلن + آماده‌سازی سشن','آماده‌سازی'),('15:30','TRADING — فقط ستاپ‌های مجاز','TRADING'),('17:00','استراحت 10 دقیقه‌ای','کنترل'),('17:10','TRADING — ادامه سشن','TRADING'),('19:00','پایان قطعی ترید','پایان'),('19:15','شام','غذا'),('19:45','ورزش / پیاده‌روی عصر 30 دقیقه','ورزش'),('20:30','تفریح بدون چارت','تفریح'),('21:00','ژورنال + اسکرین‌شات + درس روز','ژورنال'),('21:40','مطالعه / بک‌تست سبک','یادگیری'),('22:30','خاموشی صفحه‌نمایش','خواب'),('23:30','خواب','خواب')]

PLAN=['بازارهای مجاز','تایم‌فریم‌های اصلی','ستاپ‌های مجاز','شرایط ورود','شرایط عدم ورود','حداکثر ریسک هر معامله (%)','حداکثر ضرر روزانه (%)','حداکثر معاملات روزانه','قانون خروج','قانون توقف بعد از باخت','قوانین روانشناسی','اهداف ماهانه']
CHECK=['جهت و ساختار بازار مشخص است','ناحیه ورود معتبر و تازه است','ستاپ مطابق Trading Plan است','ریسک و حجم محاسبه شده','حد ضرر قبل از ورود مشخص است','R:R قابل قبول است','خبر مهم بررسی شده است','حالت روانی مناسب است','FOMO / Revenge ندارم','بعد از ورود قانون را تغییر نمی‌دهم']
FIELDS=['Date','Symbol','Direction','Session','Timeframe','Entry','Stop Loss','Take Profit','Position Size','Risk %','Risk $','R:R','Setup','Market Structure','Liquidity','Entry Model','Emotion Before','Emotion After','Mistake','Result','Result (R)','P&L','Lesson','Screenshot']

COLORS={'bg':'#F7F4EE','panel':'#FFFFFF','panel2':'#EEF5F5','text':'#203040','muted':'#667784','accent':'#38B89C','line':'#D7E1E4','danger':'#C65B5B'}

def fresh():
    today=date.today(); tasks={}
    for i in range(90): tasks[(today+timedelta(i)).isoformat()]=[{'time':t,'title':x,'cat':c,'done':False} for t,x,c in TASKS]
    return {'version':6,'market':'Crypto','tasks':tasks,'journals':{'Forex':[],'Crypto':[]},'plan':{x:'' for x in PLAN},'check':{x:False for x in CHECK},'profile':{'name':'','timezone':'','account_currency':'USD','starting_balance':''}}

def load():
    db=fresh()
    try:
        with open(DATA,'r',encoding='utf-8') as f: old=json.load(f)
        for k,v in old.items():
            if isinstance(v,dict) and isinstance(db.get(k),dict): db[k].update(v)
            else: db[k]=v
    except Exception: pass
    for m in ('Forex','Crypto'): db['journals'].setdefault(m,[])
    db['version']=6
    return db
DB=load()

def save():
    tmp=DATA+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(DB,f,ensure_ascii=False,indent=2)
    os.replace(tmp,DATA)

def num(v):
    try:return float(str(v).replace(',','').strip())
    except Exception:return 0.0

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title(APP+' V6'); self.geometry('1480x920'); self.minsize(1050,700); self.configure(bg=COLORS['bg'])
        self.market=DB.get('market','Crypto'); self.day=date.today().isoformat(); self.vars=[]
        self.style=ttk.Style(self); self.style.theme_use('clam'); self.style.configure('Treeview',background=COLORS['panel'],fieldbackground=COLORS['panel'],foreground=COLORS['text'],rowheight=34); self.style.configure('TCombobox',fieldbackground=COLORS['panel2'],background=COLORS['panel2'],foreground=COLORS['text']); self.style.configure('TScrollbar',background=COLORS['panel2'])
        self.build_shell(); self.show('home'); self.after(500,self.clock)
    def build_shell(self):
        top=tk.Frame(self,bg=COLORS['bg']); top.pack(fill='x',padx=18,pady=12)
        tk.Button(top,text='☰',command=self.toggle_menu,bg=COLORS['panel'],fg=COLORS['text'],relief='flat',font=('Segoe UI',18,'bold'),width=3).pack(side='left')
        tk.Label(top,text=APP,bg=COLORS['bg'],fg=COLORS['accent'],font=('Segoe UI',23,'bold')).pack(side='left',padx=14)
        self.clock_label=tk.Label(top,bg=COLORS['bg'],fg=COLORS['text'],font=('Segoe UI',10,'bold')); self.clock_label.pack(side='right')
        self.market_btn=tk.Button(top,text=self.market,command=self.change_market,bg=COLORS['panel2'],fg=COLORS['text'],relief='flat',font=('Segoe UI',10,'bold'),padx=16,pady=8); self.market_btn.pack(side='right',padx=14)
        self.content=tk.Frame(self,bg=COLORS['bg']); self.content.pack(fill='both',expand=True,padx=16)
        self.menu=tk.Frame(self,bg=COLORS['panel'],width=300); self.menu.place(x=-310,y=0,relheight=1); self.menu_open=False
        tk.Label(self.menu,text='TRADER PLANNER PRO',bg=COLORS['panel'],fg=COLORS['accent'],font=('Segoe UI',17,'bold')).pack(anchor='w',padx=22,pady=24)
        for text,key in [('⌂  Home','home'),('◫  برنامه روزانه','daily'),('◈  Trading Plan','plan'),('✓  Checklist','check'),('▣  Journal','journal'),('⚙  تنظیمات','settings')]:
            tk.Button(self.menu,text=text,command=lambda k=key:self.go(k),anchor='w',bg=COLORS['panel'],fg=COLORS['text'],activebackground=COLORS['panel2'],relief='flat',font=('Segoe UI',11),padx=22,pady=11).pack(fill='x')
    def toggle_menu(self): self.menu.place_configure(x=0 if not self.menu_open else -310); self.menu_open=not self.menu_open
    def go(self,k):
        if self.menu_open:self.toggle_menu()
        self.show(k)
    def show(self,k):
        self.cur=k
        for w in self.content.winfo_children(): w.destroy()
        getattr(self,k)()
    def clock(self): self.clock_label.config(text=datetime.now().strftime('%Y-%m-%d  |  %H:%M:%S')); self.after(500,self.clock)
    def heading(self,a,b=''):
        tk.Label(self.content,text=a,bg=COLORS['bg'],fg=COLORS['text'],font=('Segoe UI',21,'bold')).pack(anchor='e',pady=(8,2))
        if b: tk.Label(self.content,text=b,bg=COLORS['bg'],fg=COLORS['muted'],font=('Segoe UI',10)).pack(anchor='e',pady=(0,10))
    def card(self,p): return tk.Frame(p,bg=COLORS['panel'],highlightbackground=COLORS['line'],highlightthickness=1)
    def button(self,p,text,cmd,primary=False): return tk.Button(p,text=text,command=cmd,bg=COLORS['accent'] if primary else COLORS['panel2'],fg=COLORS['text'],relief='flat',font=('Segoe UI',10,'bold'),padx=13,pady=8)
    def change_market(self): self.market='Forex' if self.market=='Crypto' else 'Crypto'; DB['market']=self.market; save(); self.market_btn.config(text=self.market); self.show(self.cur)
    def home(self):
        self.heading('داشبورد','مرکز کنترل نظم روزانه و عملکرد معامله‌گری')
        rows=DB['journals'][self.market]; rs=[num(r.get('Result (R)')) for r in rows]; tasks=DB['tasks'].setdefault(self.day,[]); done=sum(bool(x.get('done')) for x in tasks)
        cards=[('معاملات',len(rows)),('Win Rate',f'{sum(r>0 for r in rs)/len(rs)*100:.1f}%' if rs else '0%'),('Net R',f'{sum(rs):.2f} R'),('پیشرفت امروز',f'{done/len(tasks)*100:.0f}%' if tasks else '0%'),('بازار فعال',self.market)]
        row=tk.Frame(self.content,bg=COLORS['bg']); row.pack(fill='x',pady=8)
        for a,b in cards:
            c=self.card(row); c.pack(side='left',fill='both',expand=True,padx=4); tk.Label(c,text=a,bg=COLORS['panel'],fg=COLORS['muted']).pack(anchor='w',padx=15,pady=(11,2)); tk.Label(c,text=b,bg=COLORS['panel'],fg=COLORS['text'],font=('Segoe UI',17,'bold')).pack(anchor='w',padx=15,pady=(0,11))
        self.button(self.content,'＋ ثبت معامله جدید',self.add_trade,True).pack(anchor='e',pady=10)
    def daily(self):
        self.heading('برنامه روزانه','تیک‌ها فوراً در data.json ذخیره می‌شوند و بعد از بستن برنامه باقی می‌مانند')
        nav=tk.Frame(self.content,bg=COLORS['bg']); nav.pack(fill='x',pady=4); self.button(nav,'روز قبل',lambda:self.shift_day(-1)).pack(side='left'); tk.Label(nav,text=self.day,bg=COLORS['bg'],fg=COLORS['text'],font=('Segoe UI',12,'bold')).pack(side='left',padx=16); self.button(nav,'روز بعد',lambda:self.shift_day(1)).pack(side='left')
        tasks=DB['tasks'].setdefault(self.day,[])
        if not tasks: tasks[:]=[{'time':t,'title':x,'cat':c,'done':False} for t,x,c in TASKS]; save()
        done=sum(bool(x.get('done')) for x in tasks); tk.Label(nav,text=f'{done}/{len(tasks)} انجام شد  |  {done/len(tasks)*100:.0f}%',bg=COLORS['bg'],fg=COLORS['accent'],font=('Segoe UI',11,'bold')).pack(side='right')
        box=tk.Frame(self.content,bg=COLORS['bg']); box.pack(fill='both',expand=True,pady=10); cv=tk.Canvas(box,bg=COLORS['bg'],highlightthickness=0); sb=ttk.Scrollbar(box,orient='vertical',command=cv.yview); inner=tk.Frame(cv,bg=COLORS['bg']); win=cv.create_window((0,0),window=inner,anchor='nw'); inner.bind('<Configure>',lambda e:cv.configure(scrollregion=cv.bbox('all'))); cv.bind('<Configure>',lambda e:cv.itemconfigure(win,width=e.width)); cv.configure(yscrollcommand=sb.set); cv.pack(side='left',fill='both',expand=True); sb.pack(side='right',fill='y')
        for i,x in enumerate(tasks):
            row=tk.Frame(inner,bg=COLORS['panel'],highlightbackground=COLORS['line'],highlightthickness=1); row.pack(fill='x',pady=3)
            v=tk.BooleanVar(value=bool(x.get('done')))
            cb=tk.Checkbutton(row,variable=v,command=lambda i=i,v=v:self.toggle_task(i,v),bg=COLORS['panel'],fg=COLORS['text'],selectcolor=COLORS['panel2'],activebackground=COLORS['panel'],anchor='w'); cb.pack(side='left',padx=12,pady=8)
            tk.Label(row,text=x['time'],bg=COLORS['panel'],fg=COLORS['accent'],font=('Segoe UI',11,'bold'),width=8).pack(side='left')
            tk.Label(row,text=x['title'],bg=COLORS['panel'],fg=COLORS['muted'] if x.get('done') else COLORS['text'],font=('Segoe UI',10),anchor='e').pack(side='right',fill='x',expand=True,padx=14)
            tk.Label(row,text=x['cat'],bg=COLORS['panel'],fg=COLORS['muted'],width=14,anchor='e').pack(side='right')
    def toggle_task(self,i,v): DB['tasks'][self.day][i]['done']=bool(v.get()); save(); self.show('daily')
    def shift_day(self,n): self.day=(date.fromisoformat(self.day)+timedelta(days=n)).isoformat(); self.show('daily')
    def journal(self):
        self.heading(f'Journal — {self.market}','فرم دو ستونه، سریع و کامل؛ هر بازار داده‌های مستقل خودش را دارد')
        bar=tk.Frame(self.content,bg=COLORS['bg']); bar.pack(fill='x'); self.button(bar,'＋ ثبت معامله',self.add_trade,True).pack(side='left',padx=4); self.button(bar,'خروجی CSV',self.export_journal).pack(side='left',padx=4)
        rows=DB['journals'][self.market]; tree=ttk.Treeview(self.content,columns=('date','symbol','direction','entry','sl','tp','r','pnl','setup','lesson'),show='headings'); heads={'date':'Date','symbol':'Symbol','direction':'Direction','entry':'Entry','sl':'SL','tp':'TP','r':'Result R','pnl':'P&L','setup':'Setup','lesson':'Lesson'}
        for k,h in heads.items():tree.heading(k,text=h); tree.column(k,width=110 if k not in ('setup','lesson') else 180)
        tree.pack(fill='both',expand=True,pady=10)
        for r in rows: tree.insert('','end',values=tuple(r.get(k,'') for k in ('Date','Symbol','Direction','Entry','Stop Loss','Take Profit','Result (R)','P&L','Setup','Lesson')))
        tree.bind('<Double-1>',lambda e:self.edit_selected(tree))
        tk.Label(self.content,text='دابل‌کلیک روی معامله = ویرایش',bg=COLORS['bg'],fg=COLORS['muted']).pack(anchor='e')
    def field(self,p,label,value='',kind='entry',values=None):
        f=tk.Frame(p,bg=COLORS['panel']); f.pack(fill='x',pady=4)
        tk.Label(f,text=label,bg=COLORS['panel'],fg=COLORS['muted'],width=20,anchor='e').pack(side='right',padx=8)
        if kind=='combo': w=ttk.Combobox(f,values=values or [],state='readonly',width=27); w.set(value or ((values or [''])[0])); w.pack(side='right',padx=8)
        elif kind=='text': w=tk.Text(f,bg=COLORS['panel2'],fg=COLORS['text'],insertbackground=COLORS['text'],relief='flat',height=3,width=30); w.insert('1.0',value); w.pack(side='right',padx=8)
        else: w=tk.Entry(f,bg=COLORS['panel2'],fg=COLORS['text'],insertbackground=COLORS['text'],relief='flat',width=30); w.insert(0,value); w.pack(side='right',padx=8)
        return w
    def add_trade(self,existing=None,index=None):
        win=tk.Toplevel(self); win.title(f'{self.market} — '+('ویرایش معامله' if existing else 'ثبت معامله جدید')); win.geometry('1120x760'); win.minsize(900,650); win.configure(bg=COLORS['bg']); win.transient(self); win.grab_set()
        tk.Label(win,text=f'{self.market} Journal',bg=COLORS['bg'],fg=COLORS['accent'],font=('Segoe UI',19,'bold')).pack(anchor='e',padx=22,pady=(16,2)); tk.Label(win,text='فرم سریع دو ستونه — اطلاعات را وارد کن و ذخیره بزن',bg=COLORS['bg'],fg=COLORS['muted']).pack(anchor='e',padx=22,pady=(0,10))
        outer=tk.Frame(win,bg=COLORS['bg']); outer.pack(fill='both',expand=True,padx=18); left=self.card(outer); right=self.card(outer); left.pack(side='left',fill='both',expand=True,padx=(0,7),pady=4); right.pack(side='left',fill='both',expand=True,padx=(7,0),pady=4)
        old=existing or {}; widgets={}
        basic=['Date','Symbol','Direction','Session','Timeframe','Entry','Stop Loss','Take Profit','Position Size','Risk %','Risk $','R:R']; analysis=['Setup','Market Structure','Liquidity','Entry Model','Emotion Before','Emotion After','Mistake','Result','Result (R)','P&L','Lesson','Screenshot']
        for f in basic: widgets[f]=self.field(left,f,old.get(f,self.day) if f=='Date' else old.get(f,''),'combo' if f in ('Direction','Session') else 'entry', {'Direction':['Buy','Sell'],'Session':['Asia','London','New York','Overlap','Other']}.get(f))
        for f in analysis: widgets[f]=self.field(right,f,old.get(f,''),'combo' if f=='Result' else 'text' if f in ('Setup','Market Structure','Liquidity','Entry Model','Mistake','Lesson') else 'entry', ['Win','Loss','BE'] if f=='Result' else None)
        btn=tk.Frame(win,bg=COLORS['bg']); btn.pack(fill='x',padx=18,pady=12)
        def get(w): return w.get('1.0','end').strip() if isinstance(w,tk.Text) else w.get().strip()
        def commit():
            row={f:get(w) for f,w in widgets.items()}
            if not row['Symbol']: messagebox.showwarning('ثبت معامله','Symbol / Pair را وارد کن.',parent=win); return
            try:
                if row['Entry'] and row['Stop Loss'] and row['Take Profit']: pass
            except Exception: pass
            if existing is not None: DB['journals'][self.market][index]=row
            else: DB['journals'][self.market].append(row)
            save(); win.destroy(); self.show('journal')
        self.button(btn,'ذخیره معامله',commit,True).pack(side='left'); self.button(btn,'انصراف',win.destroy).pack(side='left',padx=8)
    def edit_selected(self,tree):
        sel=tree.selection()
        if not sel:return
        idx=tree.index(sel[0]); self.add_trade(DB['journals'][self.market][idx],idx)
    def export_journal(self):
        path=filedialog.asksaveasfilename(defaultextension='.csv',initialfile=f'{self.market}_Journal.csv',filetypes=[('CSV','*.csv')])
        if not path:return
        with open(path,'w',newline='',encoding='utf-8-sig') as f: w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(DB['journals'][self.market])
        messagebox.showinfo('خروجی','فایل CSV ذخیره شد.')
    def plan(self):
        self.heading('Trading Plan','قوانین خودت را وارد و ذخیره کن'); box=self.card(self.content); box.pack(fill='both',expand=True,pady=10); self.vars=[]
        for k in PLAN: self.vars.append((k,self.field(box,k,DB['plan'].get(k,''))))
        self.button(box,'ذخیره Trading Plan',self.save_plan,True).pack(anchor='e',padx=15,pady=12)
    def save_plan(self):
        for k,w in self.vars: DB['plan'][k]=w.get().strip()
        save(); messagebox.showinfo('ذخیره شد','Trading Plan ذخیره شد.')
    def check(self):
        self.heading('Checklist','قبل از ورود، همه موارد لازم را بررسی کن'); box=self.card(self.content); box.pack(fill='both',expand=True,pady=10)
        for k in CHECK:
            v=tk.BooleanVar(value=bool(DB['check'].get(k))); tk.Checkbutton(box,text=k,variable=v,command=lambda k=k,v=v:self.set_check(k,v),bg=COLORS['panel'],fg=COLORS['text'],selectcolor=COLORS['panel2'],activebackground=COLORS['panel'],anchor='e',padx=18,pady=10).pack(fill='x')
    def set_check(self,k,v): DB['check'][k]=bool(v.get()); save()
    def settings(self):
        self.heading('تنظیمات','اطلاعات کاربر'); box=self.card(self.content); box.pack(fill='x',pady=20); name=self.field(box,'نام',DB['profile'].get('name','')); tz=self.field(box,'Timezone',DB['profile'].get('timezone','')); bal=self.field(box,'Starting Balance',DB['profile'].get('starting_balance',''))
        def commit(): DB['profile'].update({'name':name.get().strip(),'timezone':tz.get().strip(),'starting_balance':bal.get().strip()}); save(); messagebox.showinfo('ذخیره شد','تنظیمات ذخیره شد.')
        self.button(box,'ذخیره تنظیمات',commit,True).pack(anchor='e',padx=14,pady=14)
    def edit_dummy(self): pass

if __name__=='__main__': App().mainloop()
