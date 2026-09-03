import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta, timezone
import json, os, shutil, threading, urllib.request, urllib.parse, webbrowser

APP='TRADER PLANNER PRO'
DATA=os.path.join(os.path.expanduser('~'),'TraderPlannerPro','data.json')
ATT=os.path.join(os.path.expanduser('~'),'TraderPlannerPro','attachments')
os.makedirs(os.path.dirname(DATA),exist_ok=True); os.makedirs(ATT,exist_ok=True)
FF='https://www.forexfactory.com/calendar/'
DRIVE='https://drive.google.com/drive/my-drive'
FA=['دوشنبه','سه‌شنبه','چهارشنبه','پنجشنبه','جمعه','شنبه','یکشنبه']
TASKS=[('07:00','بیداری + آب + نور صبح','سلامت'),('07:20','صبحانه','غذا'),('07:50','ورزش 30–45 دقیقه','ورزش'),('08:40','دوش + آماده‌سازی میز','آماده‌سازی'),('09:00','MARK UP — ساختار، روند، نقدینگی، نواحی','MARK UP'),('10:45','استراحت 15 دقیقه','استراحت'),('11:00','MARK UP — سناریوی A/B و نقاط ابطال','MARK UP'),('12:30','ثبت سناریو + بررسی خبرها','تحلیل'),('13:00','پایان MARK UP + بستن چارت','پایان'),('13:15','ناهار','غذا'),('14:00','استراحت / چرت کوتاه','ریکاوری'),('14:30','مرور پلن + آماده‌سازی سشن','آماده‌سازی'),('15:30','TRADING — فقط ستاپ‌های مجاز','TRADING'),('17:00','استراحت 10 دقیقه‌ای','کنترل'),('17:10','TRADING — ادامه سشن','TRADING'),('19:00','پایان قطعی ترید','پایان'),('19:15','شام','غذا'),('20:00','تفریح بدون چارت','تفریح'),('21:00','ژورنال + اسکرین‌شات + درس روز','ژورنال'),('21:40','مطالعه / بک‌تست سبک','یادگیری'),('22:30','خاموشی صفحه‌نمایش','خواب'),('23:00','خواب','خواب')]
PLAN=['بازارهای مجاز','تایم‌فریم‌های اصلی','ستاپ‌های مجاز','شرایط ورود','شرایط عدم ورود','حداکثر ریسک هر معامله (%)','حداکثر ضرر روزانه (%)','حداکثر معاملات روزانه','قانون خروج','قانون توقف بعد از باخت','قوانین روانشناسی','اهداف ماهانه']
CHECK=['جهت و ساختار بازار مشخص است','ناحیه ورود معتبر و تازه است','ستاپ مطابق Trading Plan است','ریسک و حجم محاسبه شده','حد ضرر قبل از ورود مشخص است','R:R قابل قبول است','خبر مهم بررسی شده است','حالت روانی مناسب است','FOMO / Revenge ندارم','بعد از ورود قانون را تغییر نمی‌دهم']
FOREX=['Date','Pair','Direction','Session','Timeframe','Entry','Stop Loss','Take Profit','Lot Size','Risk %','Risk $','Pips SL','Pips TP','R:R','Spread','Setup','Market Structure','Liquidity','Entry Model','News','Emotion','Mistake','Result (R)','P&L','Lesson','Screenshot / Chart Link']
CRYPTO=['Date','Coin / Pair','Market Type','Exchange','Direction','Timeframe','Entry','Stop Loss','Take Profit','Position Size','Leverage','Margin','Risk %','Risk $','R:R','Funding Rate','Fees','Liquidation Price','Setup','Market Structure','Liquidity','Entry Model','Emotion','Mistake','Result (R)','P&L','Lesson','Screenshot / Chart Link']

def fresh():
 t={}; d=date.today()
 for i in range(30): t[(d+timedelta(i)).isoformat()]=[{'time':a,'title':b,'cat':c,'done':False} for a,b,c in TASKS]
 return {'language':'fa','theme':'dark','market':'Forex','drive_folder':'','timezone':'local','tasks':t,'plan':{x:'' for x in PLAN},'check':{x:False for x in CHECK},'journals':{'Forex':[],'Crypto':[]}}

def load():
 try:
  with open(DATA,'r',encoding='utf8') as f: d=json.load(f)
  base=fresh(); base.update(d); base['journals'].setdefault('Forex',[]); base['journals'].setdefault('Crypto',[]); return base
 except: return fresh()
DB=load()
def save():
 with open(DATA+'.tmp','w',encoding='utf8') as f: json.dump(DB,f,ensure_ascii=False,indent=2)
 os.replace(DATA+'.tmp',DATA)
def get(url):
 r=urllib.request.Request(url,headers={'User-Agent':'TraderPlannerPro/2.0'})
 with urllib.request.urlopen(r,timeout=8) as x: return json.loads(x.read().decode())
def browse(url): webbrowser.open(url)

class App(tk.Tk):
 def __init__(self):
  super().__init__(); self.title(APP); self.geometry('1450x900'); self.minsize(1100,720); self.cur='home'; self.day=date.today().isoformat(); self.market=DB['market']; self.menu=False; self.apply_colors(); self.shell(); self.home(); self.clock(); self.live()
 def apply_colors(self):
  dark=DB.get('theme','dark')=='dark'; self.bg='#08101f' if dark else '#f3f6fa'; self.panel='#0f1a2d' if dark else '#fff'; self.panel2='#14233b' if dark else '#e9eef5'; self.fg='#edf4ff' if dark else '#182235'; self.muted='#91a4c4' if dark else '#64748b'; self.acc='#43d6b1'; self.red='#ed6b83'; self.line='#263958' if dark else '#d7e0eb'; self.ent='#0b1628' if dark else '#f7f9fc'; self.configure(bg=self.bg)
 def shell(self):
  top=tk.Frame(self,bg=self.bg); top.pack(fill='x'); tk.Button(top,text='☰',command=self.toggle,bg=self.panel,fg=self.fg,relief='flat',font=('Segoe UI',18,'bold'),width=3).pack(side='left',padx=14,pady=10); tk.Label(top,text=APP,bg=self.bg,fg=self.acc,font=('Segoe UI',24,'bold')).pack(side='left'); self.marketbtn=tk.Button(top,text=self.market,command=self.change_market,bg=self.panel2,fg=self.fg,relief='flat',font=('Segoe UI',10,'bold')); self.marketbtn.pack(side='right',padx=10); self.cl=tk.Label(top,bg=self.bg,fg=self.fg,font=('Segoe UI',11,'bold')); self.cl.pack(side='right',padx=20)
  self.content=tk.Frame(self,bg=self.bg); self.content.pack(fill='both',expand=True,padx=14); self.ticker=tk.Frame(self,bg=self.panel); self.ticker.pack(side='bottom',fill='x'); self.menu_frame=tk.Frame(self,bg=self.panel,width=330); self.menu_frame.place(x=-340,y=0,relheight=1); self.menu_frame.lift(); self.menu_items()
 def menu_items(self):
  tk.Label(self.menu_frame,text=APP,bg=self.panel,fg=self.acc,font=('Segoe UI',17,'bold')).pack(anchor='w',padx=22,pady=25)
  for text,key in [('⌂  Home','home'),('◫  برنامه روزانه','daily'),('◈  Trading Plan','plan'),('✓  Checklist','check'),('▣  Journal','journal'),('◉  مدیریت ریسک','risk'),('◷  ساعت بازارها','sessions'),('🐂 🐻  Forex Factory','ff'),('⚙  تنظیمات','settings')]: tk.Button(self.menu_frame,text=text,command=lambda k=key:self.go(k),anchor='w',bg=self.panel,fg=self.fg,activebackground=self.panel2,activeforeground=self.acc,relief='flat',font=('Segoe UI',11),padx=22,pady=11).pack(fill='x')
 def toggle(self): self.menu=not self.menu; self.menu_frame.place_configure(x=0 if self.menu else -340)
 def go(self,k): self.toggle(); self.cur=k; self.clear(); getattr(self,k)()
 def clear(self):
  for w in self.content.winfo_children(): w.destroy()
 def title(self,a,b=''):
  tk.Label(self.content,text=a,bg=self.bg,fg=self.fg,font=('Segoe UI',21,'bold')).pack(anchor='e',pady=(14,2));
  if b: tk.Label(self.content,text=b,bg=self.bg,fg=self.muted,font=('Segoe UI',10)).pack(anchor='e',pady=(0,10))
 def card(self,p): return tk.Frame(p,bg=self.panel,highlightbackground=self.line,highlightthickness=1)
 def btn(self,p,text,cmd,primary=False,danger=False):
  bg=self.acc if primary else self.red if danger else self.panel2; fg='#06131c' if primary else self.fg; return tk.Button(p,text=text,command=cmd,bg=bg,fg=fg,activebackground=bg,activeforeground=fg,relief='flat',font=('Segoe UI',10,'bold'),padx=12,pady=8)
 def home(self):
  self.title('داشبورد تریدر','تمام وضعیت روز، ریسک، ژورنال، سشن‌ها و بازار در یک صفحه')
  row=tk.Frame(self.content,bg=self.bg); row.pack(fill='x')
  done=sum(x['done'] for x in DB['tasks'].get(self.day,[])); total=len(DB['tasks'].get(self.day,[])); vals=[('پیشرفت امروز',f'{done/total*100:.0f}%' if total else '0%'),('معاملات',str(len(DB['journals'][self.market]))),('بازار',self.market),('تاریخ',self.day)]
  for a,b in vals:
   c=self.card(row); c.pack(side='left',fill='both',expand=True,padx=4); tk.Label(c,text=a,bg=self.panel,fg=self.muted).pack(anchor='w',padx=16,pady=(12,2)); tk.Label(c,text=b,bg=self.panel,fg=self.fg,font=('Segoe UI',18,'bold')).pack(anchor='w',padx=16,pady=(0,12))
  mid=tk.Frame(self.content,bg=self.bg); mid.pack(fill='both',expand=True,pady=12)
  l=self.card(mid); l.pack(side='left',fill='both',expand=True,padx=(0,6)); r=self.card(mid); r.pack(side='left',fill='both',expand=True,padx=(6,0))
  tk.Label(l,text='ساعت سشن‌ها',bg=self.panel,fg=self.muted).pack(anchor='e',padx=20,pady=(18,2)); self.big=tk.Label(l,text='',bg=self.panel,fg=self.acc,font=('Segoe UI',30,'bold')); self.big.pack(anchor='e',padx=20); self.sub=tk.Label(l,text='',bg=self.panel,fg=self.fg,font=('Segoe UI',10)); self.sub.pack(anchor='e',padx=20,pady=4); self.cv=tk.Canvas(l,height=100,bg=self.panel,highlightthickness=0); self.cv.pack(fill='x',padx=20,pady=12); self.btn(l,'باز کردن Forex Factory',lambda:browse(FF),True).pack(anchor='e',padx=20)
  tk.Label(r,text='اقدامات سریع',bg=self.panel,fg=self.muted).pack(anchor='e',padx=20,pady=(18,8));
  for t,k in [('＋ ثبت معامله','journal'),('Trading Plan','plan'),('Checklist','check'),('مدیریت ریسک','risk')]: self.btn(r,t,lambda x=k:self.go(x)).pack(fill='x',padx=20,pady=5)
  tk.Label(self.content,text='آخرین معاملات',bg=self.bg,fg=self.fg,font=('Segoe UI',12,'bold')).pack(anchor='e'); tr=ttk.Treeview(self.content,columns=('d','s','x','r','p'),show='headings',height=4)
  for c,h in zip(tr['columns'],['Date','Symbol','Direction','R','P&L']): tr.heading(c,text=h); tr.column(c,width=170,anchor='center')
  tr.pack(fill='x',pady=5)
  sym='Pair' if self.market=='Forex' else 'Coin / Pair'
  for x in DB['journals'][self.market][-4:][::-1]: tr.insert('','end',values=(x.get('Date',''),x.get(sym,''),x.get('Direction',''),x.get('Result (R)',''),x.get('P&L','')))
 def clock(self):
  n=datetime.now().astimezone(); self.cl.config(text=n.strftime('%Y-%m-%d  |  %H:%M:%S'))
  if self.cur=='home':
   u=n.astimezone(timezone.utc); m=u.hour*60+u.minute+u.second/60; ss=[('Sydney',1320,420),('Tokyo',0,540),('London',420,960),('New York',780,1320)]; act=[x for x,a,b in ss if (m>=a or m<b) if a>b or m<b] if False else [x for x,a,b in ss if (m>=a and m<b) if a<b else (m>=a or m<b)]
   self.big.config(text=' + '.join(act) if act else 'Market closed'); self.sub.config(text='Live UTC session clock')
   if hasattr(self,'cv'):
    self.cv.delete('all'); w=max(500,self.cv.winfo_width()); self.cv.create_line(10,50,w-10,50,fill=self.line,width=12)
    for x,a,b in ss:
     xx=10+a/1440*(w-20); yy=10+(b if b>=a else 1440)/1440*(w-20); self.cv.create_line(xx,50,yy,50,fill=self.acc if x in act else self.panel2,width=18); self.cv.create_text((xx+yy)/2,50,text=x,fill=self.fg,font=('Segoe UI',8,'bold'))
  self.after(1000,self.clock)
 def change_market(self): self.market='Crypto' if self.market=='Forex' else 'Forex'; DB['market']=self.market; save(); self.marketbtn.config(text=self.market); self.clear(); getattr(self,self.cur)(); self.live()
 def live(self): threading.Thread(target=self.data,daemon=True).start()
 def data(self):
  out=[]
  try:
   if self.market=='Crypto':
    d=get('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1'); g=get('https://api.coingecko.com/api/v3/global')['data']['market_cap_percentage']; out=[(x['symbol'].upper(),x['current_price'],x.get('price_change_percentage_24h')) for x in d]+[('BTC.D',g.get('btc'),None),('USDT.D',g.get('usdt'),None)]
   else:
    sy={'EUR/USD':'EURUSD=X','GBP/USD':'GBPUSD=X','USD/JPY':'JPY=X','XAU/USD':'GC=F','XAG/USD':'SI=F','Copper':'HG=F','WTI':'CL=F','AAPL':'AAPL','MSFT':'MSFT','NVDA':'NVDA','AMZN':'AMZN','GOOGL':'GOOGL','META':'META','TSLA':'TSLA','AVGO':'AVGO','JPM':'JPM','BRK-B':'BRK-B'}
    for name,s in sy.items():
     try:
      q=get('https://query1.finance.yahoo.com/v8/finance/chart/'+urllib.parse.quote(s,safe=''))['chart']['result'][0]['meta']; out.append((name,q.get('regularMarketPrice'),q.get('regularMarketChangePercent')))
     except: pass
  except: pass
  self.after(0,lambda:self.ticker_view(out))
 def ticker_view(self,out):
  for w in self.ticker.winfo_children(): w.destroy()
  tk.Label(self.ticker,text='CRYPTO' if self.market=='Crypto' else 'FOREX • METALS • ENERGY • STOCKS',bg=self.panel,fg=self.acc,font=('Segoe UI',9,'bold')).pack(side='left',padx=10)
  for n,p,c in out[:14]:
   f=tk.Frame(self.ticker,bg=self.panel); f.pack(side='left',padx=6,pady=5); tk.Label(f,text=n,bg=self.panel,fg=self.muted,font=('Segoe UI',8,'bold')).pack(side='left'); tk.Label(f,text=' '+('—' if p is None else f'{p:,.2f}'),bg=self.panel,fg=self.fg,font=('Segoe UI',8)).pack(side='left');
   if c is not None: tk.Label(f,text=f' {c:+.2f}%',bg=self.panel,fg=self.acc if c>=0 else self.red,font=('Segoe UI',8,'bold')).pack(side='left')
  self.btn(self.ticker,'↻',self.live).pack(side='right',padx=8,pady=4)
 def daily(self):
  self.title('برنامه روزانه ۳۰ روزه','فعالیت‌ها قابل افزودن، ویرایش، حذف و جابه‌جایی هستند')
  b=tk.Frame(self.content,bg=self.bg); b.pack(fill='both',expand=True); left=self.card(b); left.config(width=250); left.pack(side='left',fill='y',padx=(0,8)); lb=tk.Listbox(left,bg=self.ent,fg=self.fg,selectbackground='#1d4260',borderwidth=0); lb.pack(fill='both',expand=True,padx=10,pady=10); self.lb=lb
  for i in range(30): d=date.today()+timedelta(i); lb.insert('end',f'{d.isoformat()}  •  {FA[d.weekday()]}')
  lb.selection_set(0); lb.bind('<<ListboxSelect>>',lambda e:self.pickday()); self.btn(left,'＋ افزودن',self.add_task,True).pack(fill='x',padx=10,pady=4); self.btn(left,'حذف',self.del_task,False,True).pack(fill='x',padx=10,pady=4)
  right=self.card(b); right.pack(side='left',fill='both',expand=True,padx=(8,0)); self.tt=ttk.Treeview(right,columns=('time','title','cat','done'),show='headings');
  for c,h,w in [('time','زمان',90),('title','فعالیت',550),('cat','دسته',130),('done','✓',50)]: self.tt.heading(c,text=h); self.tt.column(c,width=w,anchor='center')
  self.tt.pack(fill='both',expand=True,padx=12,pady=12); self.tt.bind('<Double-1>',lambda e:self.toggle_task()); self.btn(right,'↑',lambda:self.move(-1)).pack(side='left',padx=12,pady=8); self.btn(right,'↓',lambda:self.move(1)).pack(side='left',pady=8); self.render_tasks()
 def pickday(self):
  if self.lb.curselection(): self.day=(date.today()+timedelta(self.lb.curselection()[0])).isoformat(); self.render_tasks()
 def render_tasks(self):
  self.tt.delete(*self.tt.get_children());
  for i,x in enumerate(DB['tasks'][self.day]): self.tt.insert('','end',iid=str(i),values=(x['time'],x['title'],x['cat'],'✓' if x['done'] else '○'))
 def sel(self): return int(self.tt.selection()[0]) if self.tt.selection() else None
 def toggle_task(self):
  i=self.sel();
  if i is not None: DB['tasks'][self.day][i]['done']=not DB['tasks'][self.day][i]['done']; save(); self.render_tasks()
 def move(self,d):
  i=self.sel(); a=DB['tasks'][self.day]
  if i is not None and 0<=i+d<len(a): a[i],a[i+d]=a[i+d],a[i]; save(); self.render_tasks(); self.tt.selection_set(str(i+d))
 def add_task(self): self.task_dialog()
 def task_dialog(self):
  w=tk.Toplevel(self); w.title('Activity'); w.geometry('430x250'); w.configure(bg=self.panel); e=[]
  for lab in ['زمان','فعالیت','دسته']:
   tk.Label(w,text=lab,bg=self.panel,fg=self.fg).pack(anchor='e',padx=20,pady=(10,0)); q=tk.Entry(w,bg=self.ent,fg=self.fg,insertbackground=self.fg,relief='flat');q.pack(fill='x',padx=20);e.append(q)
  self.btn(w,'افزودن',lambda:(DB['tasks'][self.day].append({'time':e[0].get(),'title':e[1].get(),'cat':e[2].get(),'done':False}),save(),self.render_tasks(),w.destroy()),True).pack(pady=15)
 def del_task(self):
  i=self.sel();
  if i is not None: DB['tasks'][self.day].pop(i); save(); self.render_tasks()
 def plan(self):
  self.title('Trading Plan','فیلدهای پیش‌فرض را خودت کامل کن؛ ذخیره خودکار است'); box=self.card(self.content);box.pack(fill='both',expand=True,padx=8); self.pv={}
  for i,x in enumerate(PLAN): tk.Label(box,text=x,bg=self.panel,fg=self.fg,width=30,anchor='e').grid(row=i,column=1,padx=12,pady=5); e=tk.Entry(box,bg=self.ent,fg=self.fg,insertbackground=self.fg,relief='flat');e.grid(row=i,column=0,sticky='ew',padx=12,pady=5);e.insert(0,DB['plan'].get(x,''));e.bind('<KeyRelease>',lambda ev:self.save_plan());self.pv[x]=e
  box.columnconfigure(0,weight=1)
 def save_plan(self):
  for k,e in self.pv.items(): DB['plan'][k]=e.get()
  save()
 def check(self):
  self.title('Checklist','قبل از هر ورود بررسی کن'); box=self.card(self.content);box.pack(fill='x',padx=8,pady=8); self.cvrs=[]
  for x in CHECK:
   v=tk.BooleanVar(value=DB['check'].get(x,False));self.cvrs.append((x,v));tk.Checkbutton(box,text=x,variable=v,command=self.save_check,bg=self.panel,fg=self.fg,selectcolor=self.ent,activebackground=self.panel,anchor='e').pack(fill='x',padx=18,pady=5)
  self.btn(self.content,'ریست',self.reset_check,False,True).pack(pady=10)
 def save_check(self): DB['check']={x:v.get() for x,v in self.cvrs};save()
 def reset_check(self):
  for _,v in self.cvrs:v.set(False)
  self.save_check()
 def journal(self):
  self.title('Trading Journal','Forex و Crypto کاملاً مستقل با فرم تخصصی جداگانه'); bar=tk.Frame(self.content,bg=self.bg);bar.pack(fill='x'); self.jm=ttk.Combobox(bar,values=['Forex','Crypto'],state='readonly',width=12);self.jm.set(self.market);self.jm.pack(side='right');self.jm.bind('<<ComboboxSelected>>',lambda e:self.change_journal())
  box=self.card(self.content);box.pack(fill='x',pady=8);self.jv={}; fields=FOREX if self.market=='Forex' else CRYPTO
  for i,x in enumerate(fields): r=i//4;c=i%4;tk.Label(box,text=x,bg=self.panel,fg=self.muted,font=('Segoe UI',8)).grid(row=r*2,column=c,sticky='e',padx=7,pady=(5,1));e=tk.Entry(box,bg=self.ent,fg=self.fg,insertbackground=self.fg,relief='flat');e.grid(row=r*2+1,column=c,sticky='ew',padx=7,pady=(1,5));self.jv[x]=e
  for c in range(4): box.columnconfigure(c,weight=1)
  a=tk.Frame(self.content,bg=self.bg);a.pack(fill='x');self.btn(a,'＋ ثبت معامله',self.add_trade,True).pack(side='right',padx=4);self.btn(a,'📷 تصویر / Google Drive',self.attach).pack(side='right',padx=4)
  self.jt=ttk.Treeview(self.content,columns=('d','s','dir','rr','r','p'),show='headings',height=8); 
  for c,h in zip(self.jt['columns'],['Date','Symbol','Direction','R:R','R','P&L']):self.jt.heading(c,text=h);self.jt.column(c,width=160,anchor='center')
  self.jt.pack(fill='both',expand=True,pady=6);self.render_journal()
 def change_journal(self): self.market=self.jm.get();DB['market']=self.market;save();self.clear();self.journal();self.live()
 def add_trade(self):
  t={k:e.get().strip() for k,e in self.jv.items()};t['Date']=t.get('Date') or date.today().isoformat();DB['journals'][self.market].append(t);save();self.render_journal()
 def render_journal(self):
  self.jt.delete(*self.jt.get_children());s='Pair' if self.market=='Forex' else 'Coin / Pair'
  for t in DB['journals'][self.market]:self.jt.insert('','end',values=(t.get('Date',''),t.get(s,''),t.get('Direction',''),t.get('R:R',''),t.get('Result (R)',''),t.get('P&L','')))
 def attach(self):
  p=filedialog.askopenfilename(filetypes=[('Images','*.png *.jpg *.jpeg *.webp'),('All','*.*')]);
  if not p:return
  shutil.copy2(p,os.path.join(ATT,os.path.basename(p))); folder=DB.get('drive_folder','');
  if folder and os.path.isdir(folder):
   try:shutil.copy2(p,os.path.join(folder,os.path.basename(p)))
   except:pass
  browse(folder if folder.startswith('http') else DRIVE);messagebox.showinfo('Google Drive','تصویر در پوشه محلی برنامه ذخیره شد. برای آپلود مستقیم، Google Drive for Desktop را نصب و پوشه آن را در تنظیمات انتخاب کن.')
 def risk(self):
  self.title('مدیریت ریسک','حجم معامله بر اساس ریسک ثابت');box=self.card(self.content);box.pack(fill='x',padx=8);self.rv={}
  for i,x in enumerate(['Account Balance','Risk %','Entry Price','Stop Loss Price','Pip/Point Value']):tk.Label(box,text=x,bg=self.panel,fg=self.fg).grid(row=i,column=1,padx=15,pady=9);e=tk.Entry(box,bg=self.ent,fg=self.fg,insertbackground=self.fg,relief='flat');e.grid(row=i,column=0,sticky='ew',padx=15,pady=9);self.rv[x]=e
  box.columnconfigure(0,weight=1);self.rr=tk.Label(box,text='—',bg=self.panel,fg=self.acc,font=('Segoe UI',16,'bold'));self.rr.grid(row=5,column=1);self.btn(box,'محاسبه',self.calc,True).grid(row=5,column=0,pady=12)
 def calc(self):
  try:b=float(self.rv['Account Balance'].get());r=float(self.rv['Risk %'].get())/100;e=float(self.rv['Entry Price'].get());s=float(self.rv['Stop Loss Price'].get());v=float(self.rv['Pip/Point Value'].get());money=b*r;size=money/(abs(e-s)*v);self.rr.config(text=f'Risk $ {money:.2f}  |  Units {size:.4f}')
  except:self.rr.config(text='مقادیر عددی معتبر وارد کن')
 def sessions(self):
  self.title('ساعت بازارهای مالی','ساعت‌ها UTC هستند و ساعت سیستم بالا به‌صورت زنده نمایش داده می‌شود');g=tk.Frame(self.content,bg=self.bg);g.pack(fill='x',pady=10)
  for n,a,b in [('Sydney','22:00','07:00'),('Tokyo','00:00','09:00'),('London','07:00','16:00'),('New York','13:00','22:00')]:
   c=self.card(g);c.pack(side='left',fill='both',expand=True,padx=5);tk.Label(c,text=n,bg=self.panel,fg=self.fg,font=('Segoe UI',16,'bold')).pack(pady=15);tk.Label(c,text=f'{a} → {b}',bg=self.panel,fg=self.acc,font=('Segoe UI',24,'bold')).pack(pady=8);tk.Label(c,text='UTC',bg=self.panel,fg=self.muted).pack(pady=(0,15))
 def ff(self):
  self.title('Forex Factory','تقویم اقتصادی زنده در مرورگر؛ سایت اصلی برای خبرها و اثرگذاری');c=self.card(self.content);c.pack(fill='x',pady=20);tk.Label(c,text='🐂  VS  🐻',bg=self.panel,fg=self.acc,font=('Segoe UI',38,'bold')).pack(pady=25);tk.Label(c,text='Bulls vs Bears',bg=self.panel,fg=self.fg,font=('Segoe UI',16,'bold')).pack();self.btn(c,'باز کردن Forex Factory',lambda:browse(FF),True).pack(pady=20)
 def settings(self):
  self.title('تنظیمات','زبان، ظاهر، بازار پیش‌فرض و اتصال به Google Drive');c=self.card(self.content);c.pack(fill='x',padx=8);self.settings_entries={}
  for i,(lab,val) in enumerate([('Language / زبان','English' if DB['language']=='en' else 'فارسی / Persian'),('Theme','Dark' if DB['theme']=='dark' else 'Light'),('Drive folder',DB.get('drive_folder',''))]):
   tk.Label(c,text=lab,bg=self.panel,fg=self.fg).grid(row=i,column=1,sticky='e',padx=15,pady=12);e=tk.Entry(c,bg=self.ent,fg=self.fg,insertbackground=self.fg,relief='flat');e.insert(0,val);e.grid(row=i,column=0,sticky='ew',padx=15,pady=12);self.settings_entries[lab]=e
  c.columnconfigure(0,weight=1);self.btn(c,'انتخاب پوشه Drive',lambda:self.pick_drive()).grid(row=2,column=2,padx=8);self.btn(c,'ذخیره',self.save_settings,True).grid(row=3,column=0,pady=15)
 def pick_drive(self):
  p=filedialog.askdirectory();
  if p:self.settings_entries['Drive folder'].delete(0,'end');self.settings_entries['Drive folder'].insert(0,p)
 def save_settings(self):
  DB['language']='en' if self.settings_entries['Language / زبان'].get()=='English' else 'fa';DB['theme']='dark' if self.settings_entries['Theme'].get()=='Dark' else 'light';DB['drive_folder']=self.settings_entries['Drive folder'].get();save();messagebox.showinfo('Saved','Settings saved. Restart the app to apply theme/language.')

if __name__=='__main__': App().mainloop()
