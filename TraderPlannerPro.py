# Trader Planner Pro v2
# Windows 11 desktop trader workspace. Standard-library core; optional reportlab/openpyxl for exports.
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime, timedelta
import json, os, csv, webbrowser, urllib.request, urllib.parse

APP='Trader Planner Pro'
ROOT=os.path.join(os.path.expanduser('~'),'TraderPlannerPro')
os.makedirs(ROOT,exist_ok=True)
DB=os.path.join(ROOT,'data.json')
START=date.today()
DAYS=[START+timedelta(days=i) for i in range(30)]
FA=['دوشنبه','سه‌شنبه','چهارشنبه','پنجشنبه','جمعه','شنبه','یکشنبه']
SESSIONS=[('Sydney','22:00','07:00'),('Tokyo','00:00','09:00'),('London','08:00','17:00'),('New York','13:00','22:00')]
FOREX=['EURUSD','GBPUSD','USDJPY','XAUUSD','XAGUSD','HG=F','CL=F']
CRYPTO=['BTC-USD','ETH-USD','BNB-USD','SOL-USD','XRP-USD','DOGE-USD','ADA-USD','AVAX-USD','TRX-USD','LINK-USD']
FOREX_JOURNAL=['Date','Pair','Direction','Session','Timeframe','Entry','Stop Loss','Take Profit','Lot Size','Pips SL','Pips TP','Risk %','Risk $','R:R','Spread','Setup','Market Structure','Liquidity','Confluences','News','Emotion','Mistake','Result (R)','P&L','Lesson','Screenshot']
CRYPTO_JOURNAL=['Date','Coin/Pair','Position','Market Type','Exchange','Timeframe','Entry','Stop Loss','Take Profit','Position Size','Margin','Leverage','Risk %','Risk $','R:R','Funding Rate','Fees','Liquidation Price','Setup','Market Structure','Liquidity','Confluences','Emotion','Mistake','Result (R)','P&L','Lesson','Screenshot']
PLAN=['Markets','Timeframes','Allowed Setups','Entry Conditions','No-Trade Conditions','Risk Per Trade %','Daily Loss Limit %','Max Trades/Day','Exit Rules','Stop After Loss Rule','Psychology Rules','Monthly Goals']
CHECK=['Market direction/structure is clear','Valid entry zone','Setup is in Trading Plan','Risk is calculated','Stop Loss is defined before entry','R:R is acceptable','Important news checked','Mental state is calm','No FOMO / Revenge','No moving SL against the plan']
TASKS=[('07:00','Wake + water + morning light','Health'),('07:20','Breakfast','Food'),('07:50','Exercise 30–45 min','Fitness'),('08:40','Shower + desk preparation','Routine'),('09:00','MARK UP — structure, trend, liquidity, key zones','MARK UP'),('11:00','15 min break','Break'),('11:15','MARK UP — A/B scenarios + invalidation','MARK UP'),('13:00','Close charts + end markup','End'),('13:15','Lunch','Food'),('14:00','Recovery / short nap','Recovery'),('14:30','Review plan + prepare session','Preparation'),('15:30','TRADING — allowed setups only','TRADING'),('17:15','10 min break','Control'),('17:25','TRADING — continue session','TRADING'),('19:00','Hard stop + close platform','End'),('19:15','Dinner','Food'),('20:00','Leisure without charts','Leisure'),('21:15','Journal + screenshots + R + lessons','Journal'),('21:45','Study / light backtest','Learning'),('22:30','Screens off + wind down','Sleep'),('23:00','Sleep','Sleep')]

def defaults():
    return {'profile':{'name':'','trader_name':'','email':'','country':'','experience':'','style':'Day Trader','start_date':START.isoformat()},'theme':'dark','language':'fa','market_mode':'Forex','plan':{x:'' for x in PLAN},'check':{x:False for x in CHECK},'journals':{'Forex':[],'Crypto':[]},'tasks':{(START+timedelta(days=i)).isoformat():[{'time':t,'title':x,'cat':c,'done':False} for t,x,c in TASKS] for i in range(30)},'selected_day':START.isoformat(),'drive_folder':'','alarms':{}}

def load():
    try:
        with open(DB,'r',encoding='utf-8') as f: old=json.load(f)
    except Exception: old={}
    d=defaults()
    for k,v in old.items():
        if isinstance(v,dict) and isinstance(d.get(k),dict): d[k].update(v)
        else: d[k]=v
    return d

db=load()
def save():
    with open(DB,'w',encoding='utf-8') as f: json.dump(db,f,ensure_ascii=False,indent=2)

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title(APP); self.geometry('1440x900'); self.minsize(1150,720); self.market=db['market_mode']; self.page='home'; self.day=0
        self.colors(); self.make_header(); self.make_body(); self.show('home'); self.tick()
    def colors(self):
        dark=db.get('theme','dark')=='dark'; self.bg='#08101f' if dark else '#eef2f7'; self.card='#101b30' if dark else '#ffffff'; self.card2='#14233d' if dark else '#f5f7fa'; self.fg='#f2f6ff' if dark else '#152033'; self.muted='#91a1bf' if dark else '#637083'; self.accent='#55d6b5'; self.red='#ef6b7a'; self.gold='#f1c96b'
        self.configure(bg=self.bg)
        s=ttk.Style(self); s.theme_use('clam'); s.configure('TCombobox',fieldbackground=self.card2,background=self.card2,foreground=self.fg); s.configure('Treeview',background=self.card2,fieldbackground=self.card2,foreground=self.fg,rowheight=34,borderwidth=0); s.map('Treeview',background=[('selected','#1e4269')]); s.configure('TNotebook',background=self.bg,borderwidth=0)
    def make_header(self):
        h=tk.Frame(self,bg=self.bg); h.pack(fill='x',padx=22,pady=16)
        tk.Button(h,text='☰',font=('Segoe UI',18,'bold'),command=self.menu,bd=0,bg=self.card,fg=self.fg,width=3).pack(side='left',padx=(0,12))
        tk.Label(h,text='TRADER PLANNER PRO',font=('Segoe UI',25,'bold'),fg=self.accent,bg=self.bg).pack(side='left')
        self.clock=tk.Label(h,bg=self.bg,fg=self.fg,font=('Segoe UI',12,'bold')); self.clock.pack(side='right')
    def make_body(self):
        self.content=tk.Frame(self,bg=self.bg); self.content.pack(fill='both',expand=True,padx=18,pady=(0,18))
    def clear(self):
        for w in self.content.winfo_children(): w.destroy()
    def menu(self):
        m=tk.Toplevel(self); m.title('Menu'); m.geometry('310x610'); m.configure(bg=self.card); m.transient(self)
        items=[('⌂  Home','home'),('📅  Daily Planner','daily'),('📋  Trading Plan','plan'),('☑  Checklist','check'),('📒  Journal','journal'),('🧮  Risk Manager','risk'),('◷  Market Sessions','sessions'),('📰  Forex Factory','ff'),('📈  Performance & Reports','reports'),('📡  Radar','radar'),('⚙  Settings','settings')]
        for text,key in items: tk.Button(m,text=text,command=lambda k=key:(m.destroy(),self.show(k)),anchor='e',font=('Segoe UI',11,'bold'),bg=self.card2,fg=self.fg,activebackground='#1e4269',activeforeground='white',bd=0,padx=18,pady=12).pack(fill='x',padx=14,pady=4)
    def show(self,page):
        self.page=page; self.clear(); getattr(self,'page_'+page)()
    def titlebar(self,title,subtitle=''):
        f=tk.Frame(self.content,bg=self.bg); f.pack(fill='x',pady=(5,16)); tk.Label(f,text=title,font=('Segoe UI',21,'bold'),bg=self.bg,fg=self.fg).pack(anchor='e');
        if subtitle: tk.Label(f,text=subtitle,bg=self.bg,fg=self.muted,font=('Segoe UI',10)).pack(anchor='e',pady=3)
    def card(self,parent):
        f=tk.Frame(parent,bg=self.card); f.pack(fill='both',expand=True,padx=8,pady=8); return f
    def metric(self,p,text,value):
        f=tk.Frame(p,bg=self.card2); f.pack(side='left',fill='both',expand=True,padx=5); tk.Label(f,text=text,bg=self.card2,fg=self.muted,font=('Segoe UI',10)).pack(pady=(12,3)); tk.Label(f,text=value,bg=self.card2,fg=self.fg,font=('Segoe UI',20,'bold')).pack(pady=(0,12))
    def page_home(self):
        self.titlebar('داشبورد معامله‌گر','نمای کلی کل فرایند — برنامه، ریسک، ژورنال و عملکرد')
        prof=db['profile']; name=prof.get('name') or 'Trader'; tk.Label(self.content,text=f'سلام {name} 👋',bg=self.bg,fg=self.accent,font=('Segoe UI',14,'bold')).pack(anchor='e',padx=15)
        stats=tk.Frame(self.content,bg=self.bg); stats.pack(fill='x',pady=10)
        trades=sum(len(v) for v in db['journals'].values()); rs=[]
        for v in db['journals'].values():
            for t in v:
                try: rs.append(float(t.get('Result (R)',0)))
                except: pass
        wins=sum(1 for r in rs if r>0); total=sum(rs) if rs else 0
        for a,b in [('معاملات',trades),('Win Rate',f'{wins/len(rs)*100:.1f}%' if rs else '0%'),('Net R',f'{total:.2f} R'),('بازار فعال',self.market),('برنامه',f'{sum(1 for x in db["plan"].values() if x)}/{len(PLAN)}')]: self.metric(stats,a,b)
        row=tk.Frame(self.content,bg=self.bg); row.pack(fill='both',expand=True)
        left=self.card(row); right=self.card(row)
        tk.Label(left,text='امروز',bg=self.card,fg=self.fg,font=('Segoe UI',15,'bold')).pack(anchor='e',padx=18,pady=12)
        today=db['tasks'].get(date.today().isoformat(),[]); done=sum(x.get('done',False) for x in today); tk.Label(left,text=f'{done}/{len(today)} فعالیت انجام شده',bg=self.card,fg=self.accent,font=('Segoe UI',13,'bold')).pack(anchor='e',padx=18)
        for x in today[:9]: tk.Label(left,text=f'{"✓" if x["done"] else "○"}  {x["time"]}   {x["title"]}',bg=self.card,fg=self.fg if not x['done'] else self.muted,anchor='e').pack(fill='x',padx=18,pady=4)
        tk.Button(left,text='باز کردن برنامه روزانه',command=lambda:self.show('daily'),bg=self.accent,fg='#071018',bd=0,padx=15,pady=8).pack(pady=12)
        tk.Label(right,text='خلاصه عملکرد',bg=self.card,fg=self.fg,font=('Segoe UI',15,'bold')).pack(anchor='e',padx=18,pady=12)
        self.chart= tk.Canvas(right,bg=self.card2,highlightthickness=0,height=220); self.chart.pack(fill='x',padx=18,pady=10); self.draw_equity(rs)
        tk.Label(right,text='توجه: داده‌های بازار فقط برای نمایش و نیازمند تأیید منبع/کارگزار هستند.',bg=self.card,fg=self.muted).pack(anchor='e',padx=18,pady=8)
    def draw_equity(self,rs):
        self.chart.delete('all'); w=self.chart.winfo_reqwidth() or 800; h=220; vals=[0];
        for r in rs: vals.append(vals[-1]+r)
        if len(vals)<2: self.chart.create_text(400,110,text='هنوز داده‌ای برای نمودار عملکرد ثبت نشده',fill=self.muted,font=('Segoe UI',12)); return
        mn,mx=min(vals),max(vals); span=max(1,mx-mn); pts=[]
        for i,v in enumerate(vals): pts += [20+i*(w-40)/max(1,len(vals)-1), h-20-(v-mn)/span*(h-40)]
        self.chart.create_line(*pts,fill=self.accent,width=3,smooth=True); self.chart.create_text(45,20,text=f'{vals[-1]:.2f} R',fill=self.fg,anchor='w',font=('Segoe UI',11,'bold'))
    def page_daily(self):
        self.titlebar('برنامه روزانه ۳۰ روزه','قابل ویرایش و جابه‌جایی — مارک‌آپ 09:00 تا 13:00 | ترید 15:30 تا 19:00')
        outer=tk.Frame(self.content,bg=self.bg); outer.pack(fill='both',expand=True)
        side=self.card(outer); side.config(width=250); side.pack_propagate(False)
        tk.Label(side,text='تقویم ۳۰ روزه',bg=self.card,fg=self.fg,font=('Segoe UI',14,'bold')).pack(pady=10)
        self.daylist=tk.Listbox(side,bg=self.card2,fg=self.fg,selectbackground='#1e4269',bd=0,font=('Segoe UI',10)); self.daylist.pack(fill='both',expand=True,padx=12); self.daylist.bind('<<ListboxSelect>>',self.pick_day)
        for i,d in enumerate(DAYS): self.daylist.insert('end',f'{d.isoformat()}  {FA[d.weekday()]}')
        self.daylist.selection_set(self.day); self.daylist.activate(self.day)
        main=self.card(outer); self.daytree=ttk.Treeview(main,columns=('time','task','cat','done'),show='headings');
        for c,h,w in [('time','زمان',90),('task','فعالیت',650),('cat','دسته',130),('done','وضعیت',90)]: self.daytree.heading(c,text=h); self.daytree.column(c,width=w,anchor='e')
        self.daytree.pack(fill='both',expand=True,padx=14,pady=14); self.daytree.bind('<Double-1>',self.toggle_task)
        self.render_day()
        b=tk.Frame(main,bg=self.card); b.pack(fill='x',padx=14,pady=(0,12)); tk.Button(b,text='+ فعالیت',command=self.add_task,bg=self.accent,fg='#071018',bd=0,padx=15,pady=7).pack(side='left',padx=4); tk.Button(b,text='↕ جابه‌جایی',command=self.move_task,bg=self.card2,fg=self.fg,bd=0,padx=15,pady=7).pack(side='left',padx=4)
    def render_day(self):
        self.daytree.delete(*self.daytree.get_children()); d=DAYS[self.day]; self.daytitle_text=d.isoformat()
        for i,x in enumerate(db['tasks'].get(d.isoformat(),[])): self.daytree.insert('', 'end', iid=str(i),values=(x['time'],x['title'],x['cat'],'✓' if x['done'] else '○'))
    def pick_day(self,e=None):
        s=self.daylist.curselection();
        if s: self.day=s[0]; self.render_day()
    def toggle_task(self,e=None):
        s=self.daytree.selection();
        if not s:return
        i=int(s[0]); d=DAYS[self.day].isoformat(); db['tasks'][d][i]['done']=not db['tasks'][d][i]['done']; save(); self.render_day()
    def add_task(self):
        d=DAYS[self.day].isoformat(); db['tasks'].setdefault(d,[]).append({'time':'','title':'فعالیت جدید','cat':'Custom','done':False}); save(); self.render_day()
    def move_task(self):
        s=self.daytree.selection();
        if not s:return
        i=int(s[0]); arr=db['tasks'][DAYS[self.day].isoformat()];
        if i>0: arr[i-1],arr[i]=arr[i],arr[i-1]; save(); self.render_day(); self.daytree.selection_set(str(i-1))
    def page_plan(self):
        self.titlebar('Trading Plan','فیلدها عمداً عمومی و قابل تکمیل توسط خود کاربر هستند')
        grid=tk.Frame(self.content,bg=self.bg); grid.pack(fill='both',expand=True,padx=20)
        self.planvars={}
        for i,f in enumerate(PLAN):
            tk.Label(grid,text=f,bg=self.bg,fg=self.fg,font=('Segoe UI',10,'bold')).grid(row=i,column=1,sticky='e',padx=10,pady=6); e=tk.Entry(grid,bg=self.card2,fg=self.fg,insertbackground=self.fg,bd=0); e.grid(row=i,column=0,sticky='ew',padx=10,pady=5); e.insert(0,db['plan'].get(f,'')); self.planvars[f]=e
        grid.columnconfigure(0,weight=1); tk.Button(self.content,text='💾 ذخیره پلن',command=self.save_plan,bg=self.accent,fg='#071018',bd=0,padx=20,pady=8).pack(pady=12)
    def save_plan(self):
        db['plan']={k:v.get().strip() for k,v in self.planvars.items()}; save(); messagebox.showinfo('Saved','Trading Plan saved.')
    def page_check(self):
        self.titlebar('Trade Checklist','قبل از هر ورود، موارد لازم را تیک بزن')
        box=self.card(self.content); self.cvars=[]
        for x in CHECK:
            v=tk.BooleanVar(value=db['check'].get(x,False)); self.cvars.append((x,v)); tk.Checkbutton(box,text=x,variable=v,command=self.save_check,bg=self.card,fg=self.fg,selectcolor=self.card2,activebackground=self.card,activeforeground=self.fg,anchor='e').pack(fill='x',padx=30,pady=7)
        tk.Button(self.content,text='Reset',command=self.reset_check,bg=self.red,fg='white',bd=0,padx=20,pady=8).pack(pady=10)
    def save_check(self): db['check']={x:v.get() for x,v in self.cvars}; save()
    def reset_check(self):
        for _,v in self.cvars:v.set(False)
        self.save_check()
    def page_journal(self):
        self.titlebar('Trading Journal','دو دیتابیس مستقل برای Forex و Crypto — ساختار تخصصی هر بازار')
        top=tk.Frame(self.content,bg=self.bg); top.pack(fill='x'); tk.Label(top,text='Market',bg=self.bg,fg=self.muted).pack(side='right'); box=ttk.Combobox(top,values=['Forex','Crypto'],state='readonly',width=12); box.set(self.market); box.pack(side='right',padx=8); box.bind('<<ComboboxSelected>>',lambda e:self.set_market(box.get()))
        form=self.card(self.content); fields=FOREX_JOURNAL if self.market=='Forex' else CRYPTO_JOURNAL; self.jv={}
        for i,f in enumerate(fields):
            r=i//4*2; c=i%4; tk.Label(form,text=f,bg=self.card,fg=self.muted,font=('Segoe UI',9)).grid(row=r,column=c,sticky='e',padx=7,pady=(7,1)); e=tk.Entry(form,bg=self.card2,fg=self.fg,insertbackground=self.fg,bd=0); e.grid(row=r+1,column=c,sticky='ew',padx=7,pady=(1,6)); self.jv[f]=e
        for c in range(4): form.columnconfigure(c,weight=1)
        btn=tk.Frame(self.content,bg=self.bg); btn.pack(fill='x'); tk.Button(btn,text='＋ ثبت معامله',command=self.add_trade,bg=self.accent,fg='#071018',bd=0,padx=18,pady=8).pack(side='left',padx=8); tk.Button(btn,text='📷 انتخاب Screenshot',command=self.choose_image,bg=self.card2,fg=self.fg,bd=0,padx=18,pady=8).pack(side='left',padx=8); tk.Button(btn,text='Export',command=lambda:self.export_market(self.market),bg=self.card2,fg=self.fg,bd=0,padx=18,pady=8).pack(side='left',padx=8)
        self.jtree=ttk.Treeview(self.content,columns=('date','symbol','dir','rr','r','pnl','setup'),show='headings');
        for c,h in zip(self.jtree['columns'],['Date','Symbol','Direction','R:R','R','P&L','Setup']): self.jtree.heading(c,text=h); self.jtree.column(c,width=125)
        self.jtree.pack(fill='both',expand=True,pady=10); self.render_journal()
    def set_market(self,m): self.market=m; db['market_mode']=m; save(); self.show('journal')
    def choose_image(self):
        p=filedialog.askopenfilename(title='Screenshot',filetypes=[('Images','*.png *.jpg *.jpeg *.webp'),('All files','*.*')]);
        if p and 'Screenshot' in self.jv: self.jv['Screenshot'].delete(0,'end'); self.jv['Screenshot'].insert(0,p)
    def add_trade(self):
        t={k:v.get().strip() for k,v in self.jv.items()}; t['Date']=t.get('Date') or date.today().isoformat(); db['journals'][self.market].append(t); save(); self.render_journal()
        for v in self.jv.values(): v.delete(0,'end')
        self.jv['Date'].insert(0,date.today().isoformat()); messagebox.showinfo('ثبت شد','معامله با موفقیت ذخیره شد.')
    def render_journal(self):
        self.jtree.delete(*self.jtree.get_children())
        for t in db['journals'][self.market]: self.jtree.insert('','end',values=(t.get('Date',''),t.get('Pair',t.get('Coin/Pair','')),t.get('Direction',t.get('Position','')),t.get('R:R',''),t.get('Result (R)',''),t.get('P&L',''),t.get('Setup','')))
    def page_risk(self):
        self.titlebar('Risk Manager','محاسبه حجم/ریسک — عددها را با قوانین کارگزار خود تطبیق دهید')
        box=self.card(self.content); self.rv={}; fields=['Account Balance','Risk %','Entry Price','Stop Loss Price','Pip/Point Value']
        for i,f in enumerate(fields):
            tk.Label(box,text=f,bg=self.card,fg=self.muted).grid(row=i,column=1,sticky='e',padx=15,pady=10); e=tk.Entry(box,bg=self.card2,fg=self.fg,insertbackground=self.fg,bd=0); e.grid(row=i,column=0,sticky='ew',padx=15,pady=10); self.rv[f]=e
        box.columnconfigure(0,weight=1); self.riskout=tk.Label(box,text='—',bg=self.card,fg=self.accent,font=('Segoe UI',18,'bold')); self.riskout.grid(row=6,column=0,columnspan=2,pady=15); tk.Button(box,text='محاسبه',command=self.calc_risk,bg=self.accent,fg='#071018',bd=0,padx=20,pady=8).grid(row=5,column=0,columnspan=2)
    def calc_risk(self):
        try:
            bal=float(self.rv['Account Balance'].get()); rp=float(self.rv['Risk %'].get())/100; entry=float(self.rv['Entry Price'].get()); sl=float(self.rv['Stop Loss Price'].get()); pv=float(self.rv['Pip/Point Value'].get()); risk=bal*rp; distance=abs(entry-sl); size=risk/(distance*pv) if distance*pv else 0; self.riskout.config(text=f'Risk $: {risk:.2f}   |   Distance: {distance:.5f}   |   Size: {size:.4f}')
        except: self.riskout.config(text='ورودی‌ها را به عدد تبدیل کنید')
    def page_sessions(self):
        self.titlebar('Market Sessions','ساعت‌ها بر اساس زمان محلی/UTC ابزار شما نمایش داده می‌شوند؛ DST می‌تواند زمان‌ها را تغییر دهد')
        wrap=tk.Frame(self.content,bg=self.bg); wrap.pack(fill='both',expand=True)
        now=datetime.now().strftime('%H:%M:%S'); tk.Label(wrap,text=now,font=('Segoe UI',42,'bold'),bg=self.card,fg=self.accent).pack(fill='x',pady=15)
        for name,a,b in SESSIONS:
            f=self.card(wrap); f.pack(fill='x',expand=False); tk.Label(f,text=f'🐂 {name}',font=('Segoe UI',20,'bold'),bg=self.card,fg=self.fg).pack(side='left',padx=25,pady=18); tk.Label(f,text=f'{a}  →  {b}',font=('Segoe UI',24,'bold'),bg=self.card,fg=self.accent).pack(side='right',padx=25,pady=18)
    def page_ff(self):
        self.titlebar('Forex Factory','تقویم اخبار در مرورگر باز می‌شود — اتصال مستقیم به اینترنت')
        f=self.card(self.content); tk.Label(f,text='🐂  VS  🐻',font=('Segoe UI',44,'bold'),bg=self.card,fg=self.gold).pack(pady=35); tk.Label(f,text='BULL  vs  BEAR',font=('Segoe UI',22,'bold'),bg=self.card,fg=self.fg).pack(pady=5); tk.Button(f,text='باز کردن Forex Factory Calendar',command=lambda:webbrowser.open('https://www.forexfactory.com/calendar'),bg=self.accent,fg='#071018',bd=0,padx=25,pady=12,font=('Segoe UI',12,'bold')).pack(pady=30); tk.Label(f,text='برای داده‌های اخبار، مرورگر شما از سایت رسمی استفاده می‌کند.',bg=self.card,fg=self.muted).pack()
def page_reports(self):
        self.titlebar('Performance & Reports','خروجی برای آرشیو سوابق کار — PDF شامل نمودار عملکرد و XLSX_INCLUDEd خام')
        f=self.card(self.content); tk.Label(f,text='گزارش جامع',font=('Segoe UI',18,'bold'),bg=self.card,fg=self.fg).pack(pady=25); tk.Label(f,text='نام معامله‌گر: '+(db['profile'].get('name') or '—'),bg=self.card,fg=self.muted).pack(pady=4); tk.Button(f,text='📄 خروجی PDF با نمودار',command=self.export_pdf,bg=self.accent,fg='#071018',bd=0,padx=25,pady=10).pack(pady=12); tk.Button(f,text='📊 خروجی Excel / CSV',command=lambda:self.export_market(self.market),bg=self.card2,fg=self.fg,bd=0,padx=25,pady=10).pack(pady=12); tk.Label(f,text='فایل PDF برای ارائه/رزومه و فایل Excel برای آرشیو و تحلیل قابل استفاده است.',bg=self.card,fg=self.muted).pack(pady=15)
    def page_radar(self):
        self.titlebar('Market Radar',' reaiscan رسمی بازار — سیگنال‌های معاملاتی Opportunities')
        # instructions / status area
        top=self.card(self.content); tk.Label(top,text='رادار بازار',bg=self.card,fg=self.fg,font=('Segoe UI',18,'bold')).pack(anchor='e',padx=18,pady=12)
        self.radar_status=tk.Label(top,text='',bg=self.card,fg=self.muted,font=('Segoe UI',12)); self.radar_status.pack(anchor='e',padx=18,pady=4)
        # controls
        ctrl=self.card(self.content); tk.Label(ctrl,text='بازار',bg=self.card,fg=self.muted).pack(side='right'); box=ttk.Combobox(ctrl,values=['Forex','Crypto'],state='readonly',width=12); box.set(self.market); box.pack(side='right',padx=8); box.bind('<<ComboboxSelected>>',lambda e:self.set_market_radar(e))
        # signals table
        table=self.card(self.content); columns=('symbol','price','change','trend','rsi','setup','score'); self.radar_tree=ttk.Treeview(table,columns=columns,show='headings'); [self.radar_tree.heading(c,text=c) or self.radar_tree.column(c,width=100,anchor='e') for c in columns]; self.radar_tree.pack(fill='both',expand=True,pady=10)
        # refresh button
        btn=tk.Frame(self.content,bg=self.bg); btn.pack(fill='x'); tk.Button(btn,text='🔄 refresh radar',command=self.refresh_radar,bg=self.accent,fg='#071018',bd=0,padx=20,pady=8).pack(side='left',padx=8); tk.Button(btn,text='Export CSV',command=self.export_radar_csv,bg=self.card2,fg=self.fg,bd=0,padx=18,pady=8).pack(side='left',padx=8)
        # initial load
        self.refresh_radar()
    def set_market_radar(self,m): self.market=m; db['market_mode']=m; save(); self.refresh_radar()
    def refresh_radar(self):
        self.radar_status.config(text='در حال scan...'); self.radar_tree.delete(*self.radar_tree.get_children())
        from app.services.radar_service import scan_radar, RadarSignal
        result=scan_radar('Forex' if self.market=='Forex' else 'Crypto')
        self.radar_status.config(text=result.message)
        if result.signals:
            for s in result.signals:
                trend_txt='صعودی' if s.trend=='bullish' else ('نزولی' if s.trend=='bearish' else 'تعادل')
                rsi_txt=str(s.rsi) if s.rsi is not None else '—'
                self.radar_tree.insert('', 'end',values=(s.symbol,s.price,rsi_txt,trend_txt,s.setup,f'{s.score:.2f}'))
        else:
            self.radar_tree.insert('', 'end',values=('—','—','—','—','—','—'))
    def export_radar_csv(self):
        import csv, filedialog
        path=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')],initialfile='radar_signals.csv')
        if not path:return
        from app.services.radar_service import RadarSignal
        selected=self.radar_tree.get_children()
        rows=[['Symbol','Price','Change %','Trend','Setup','Score']]
        for s in selected:
            rows.append(list(self.radar_tree.item(s)['values']))
        with open(path,'w',newline='',encoding='utf-8-sig') as f:
            w=csv.writer(f); w.writerows(rows)
        messagebox.showinfo('Export complete',path)
    def export_market(self,market):
        path=filedialog.asksaveasfilename(defaultextension='.xlsx',filetypes=[('Excel','*.xlsx'),('CSV','*.csv')],initialfile=f'{market}_Journal.xlsx');
        if not path:return
        rows=db['journals'][market]; fields=FOREX_JOURNAL if market=='Forex' else CRYPTO_JOURNAL
        if path.lower().endswith('.csv'):
            with open(path,'w',newline='',encoding='utf-8-sig') as f: w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
        else:
            try:
                from openpyxl import Workbook
                wb=Workbook(); ws=wb.active; ws.title=market; ws.append(fields)
                for t in rows: ws.append([t.get(x,'') for x in fields])
                for col in ws.columns: ws.column_dimensions[col[0].column_letter].width=min(28,max(12,max(len(str(c.value or '')) for c in col)+2))
                wb.save(path)
            except ImportError:
                messagebox.showerror('Excel export','برای XLSX باید openpyxl نصب باشد. CSV را می‌توانید همین حالا خروجی بگیرید.'); return
        messagebox.showinfo('Export complete',path)
    def export_pdf(self):
        path=filedialog.asksaveasfilename(defaultextension='.pdf',filetypes=[('PDF','*.pdf')],initialfile='TraderPlannerPro_Report.pdf');
        if not path:return
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            styles=getSampleStyleSheet(); story=[Paragraph('TRADER PLANNER PRO — Trading Performance Report',styles['Title']),Spacer(1,12),Paragraph('Trader: '+(db['profile'].get('name') or 'Trader'),styles['Heading2']),Paragraph('Report date: '+date.today().isoformat(),styles['Normal']),Spacer(1,15)]
            for market in ['Forex','Crypto']:
                data=[['Date','Symbol','Dir','R:R','R','P&L']]
                for t in db['journals'][market]: data.append([t.get('Date',''),t.get('Pair',t.get('Coin/Pair','')),t.get('Direction',t.get('Position','')),t.get('R:R',''),t.get('Result (R)',''),t.get('P&L','')])
                story += [Paragraph(market,styles['Heading2']),Table(data,repeatRows=1,style=TableStyle([('GRID',(0,0),(-1,-1),.4,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('FONTSIZE',(0,0),(-1,-1),7)])),Spacer(1,15)]
            SimpleDocTemplate(path,pagesize=A4,rightMargin=28,leftMargin=28,topMargin=28,bottomMargin=28).build(story); messagebox.showinfo('PDF complete',path)
        except ImportError: messagebox.showerror('PDF export','برای PDF باید reportlab نصب باشد.')
    def page_settings(self):
        self.titlebar('Settings','اطلاعات هویتی ساده برای نام‌گذاری گزارش‌ها — بدون درخواست اطلاعات حساس')
        f=self.card(self.content); self.pv={}
        fields=[('name','نام و نام خانوادگی'),('trader_name','نام تریدر / برند'),('email','ایمیل اختیاری'),('country','کشور'),('experience','سابقه / تجربه'),('style','سبک معامله‌گری')]
        for i,(k,label) in enumerate(fields):
            tk.Label(f,text=label,bg=self.card,fg=self.fg).grid(row=i,column=1,sticky='e',padx=20,pady=8); e=tk.Entry(f,bg=self.card2,fg=self.fg,insertbackground=self.fg,bd=0); e.grid(row=i,column=0,sticky='ew',padx=20,pady=8); e.insert(0,db['profile'].get(k,'')); self.pv[k]=e
        f.columnconfigure(0,weight=1); tk.Button(f,text='ذخیره پروفایل',command=self.save_profile,bg=self.accent,fg='#071018',bd=0,padx=20,pady=8).grid(row=6,column=0,columnspan=2,pady=15)
        tk.Label(f,text='Language',bg=self.card,fg=self.fg).grid(row=7,column=1,sticky='e',padx=20,pady=8); lang=ttk.Combobox(f,values=['فارسی','English'],state='readonly'); lang.set('فارسی' if db.get('language')=='fa' else 'English'); lang.grid(row=7,column=0,sticky='w',padx=20); lang.bind('<<ComboboxSelected>>',lambda e:self.set_lang(lang.get()))
        tk.Button(f,text='Open Google Drive folder',command=self.open_drive,bg=self.card2,fg=self.fg,bd=0,padx=20,pady=8).grid(row=8,column=0,pady=10); tk.Button(f,text='انتخاب پوشه Google Drive برای Screenshot',command=self.select_drive,bg=self.card2,fg=self.fg,bd=0,padx=20,pady=8).grid(row=8,column=1,pady=10)
    def save_profile(self): db['profile'].update({k:v.get().strip() for k,v in self.pv.items()}); save(); messagebox.showinfo('Saved','Profile saved.')
    def set_lang(self,x): db['language']='fa' if x=='فارسی' else 'en'; save(); messagebox.showinfo('Language','زبان ذخیره شد. برای ترجمه کامل UI، برنامه را دوباره اجرا کنید.')
    def select_drive(self):
        p=filedialog.askdirectory(title='Google Drive Desktop folder');
        if p: db['drive_folder']=p; save(); messagebox.showinfo('Google Drive','پوشه ذخیره شد. Screenshotها را می‌توانید در این پوشه نگهداری کنید.')
    def open_drive(self):
        p=db.get('drive_folder','');
        if p and os.path.exists(p): os.startfile(p)
        else: webbrowser.open('https://drive.google.com/')
    def tick(self):
        self.clock.config(text=datetime.now().strftime('%Y-%m-%d   %H:%M:%S')); self.after(1000,self.tick)

if __name__=='__main__':
    save(); App().mainloop()
