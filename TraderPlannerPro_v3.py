import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta
import json, os, shutil, webbrowser, threading, csv, math

APP='Trader Planner Pro'
ROOT=os.path.join(os.path.expanduser('~'),'TraderPlannerPro'); os.makedirs(ROOT,exist_ok=True)
DATA=os.path.join(ROOT,'data.json'); ATT=os.path.join(ROOT,'attachments'); os.makedirs(ATT,exist_ok=True)
FF='https://www.forexfactory.com/calendar/'
FA=['دوشنبه','سه‌شنبه','چهارشنبه','پنجشنبه','جمعه','شنبه','یکشنبه']
TASKS=[('07:00','بیداری + آب + نور صبح','سلامت'),('07:20','صبحانه','غذا'),('07:50','ورزش 30–45 دقیقه','ورزش'),('08:40','دوش + آماده‌سازی میز','روتین'),('09:00','MARK UP — ساختار، روند، نقدینگی و نواحی','MARK UP'),('10:45','استراحت 15 دقیقه','استراحت'),('11:00','MARK UP — سناریوی A/B و نقاط ابطال','MARK UP'),('12:30','ثبت سناریو + بررسی خبرها','تحلیل'),('13:00','پایان MARK UP + بستن چارت','پایان'),('13:15','ناهار','غذا'),('14:00','استراحت / چرت کوتاه','ریکاوری'),('14:30','مرور پلن + آماده‌سازی سشن','آماده‌سازی'),('15:30','TRADING — فقط ستاپ‌های مجاز','TRADING'),('17:00','استراحت 10 دقیقه‌ای','کنترل'),('17:10','TRADING — ادامه سشن','TRADING'),('19:00','پایان قطعی ترید','پایان'),('19:15','شام','غذا'),('20:00','تفریح بدون چارت','تفریح'),('21:00','ژورنال + اسکرین‌شات + درس روز','ژورنال'),('21:40','مطالعه / بک‌تست سبک','یادگیری'),('22:30','خاموشی صفحه‌نمایش','خواب'),('23:00','خواب','خواب')]
PLAN=['بازارهای مجاز','تایم‌فریم‌های اصلی','ستاپ‌های مجاز','شرایط ورود','شرایط عدم ورود','حداکثر ریسک هر معامله (%)','حداکثر ضرر روزانه (%)','حداکثر معاملات روزانه','قانون خروج','قانون توقف بعد از باخت','قوانین روانشناسی','اهداف ماهانه']
CHECK=['جهت و ساختار بازار مشخص است','ناحیه ورود معتبر و تازه است','ستاپ مطابق Trading Plan است','ریسک و حجم محاسبه شده','حد ضرر قبل از ورود مشخص است','R:R قابل قبول است','خبر مهم بررسی شده است','حالت روانی مناسب است','FOMO / Revenge ندارم','بعد از ورود قانون را تغییر نمی‌دهم']
FJ=['Date','Pair','Direction','Session','Timeframe','Entry','Stop Loss','Take Profit','Lot Size','Risk %','Risk $','Pips SL','Pips TP','R:R','Spread','Setup','Market Structure','Liquidity','Entry Model','News','Emotion','Mistake','Result (R)','P&L','Lesson','Screenshot']
CJ=['Date','Coin / Pair','Market Type','Exchange','Direction','Timeframe','Entry','Stop Loss','Take Profit','Position Size','Leverage','Margin','Risk %','Risk $','R:R','Funding Rate','Fees','Liquidation Price','Setup','Market Structure','Liquidity','Entry Model','Emotion','Mistake','Result (R)','P&L','Lesson','Screenshot']

DEFAULT_PROFILE={'name':'','title':'','email':'','country':'','timezone':'','experience':'','style':'Day Trader','broker':'','account_type':'','account_currency':'USD','starting_balance':'','report_note':''}
def fresh():
 d=date.today(); tasks={}
 for i in range(30): tasks[(d+timedelta(i)).isoformat()]=[{'time':a,'title':b,'cat':c,'done':False} for a,b,c in TASKS]
 return {'version':3,'language':'fa','theme':'dark','market':'Forex','profile':DEFAULT_PROFILE.copy(),'tasks':tasks,'plan':{x:'' for x in PLAN},'check':{x:False for x in CHECK},'journals':{'Forex':[],'Crypto':[]},'drive_folder':''}
def load():
 try:
  with open(DATA,'r',encoding='utf8') as f: d=json.load(f)
 except: d={}
 b=fresh();
 for k,v in d.items():
  if isinstance(v,dict) and isinstance(b.get(k),dict): b[k].update(v)
  else: b[k]=v
 b['profile']={**DEFAULT_PROFILE,**b.get('profile',{})}; b['journals'].setdefault('Forex',[]); b['journals'].setdefault('Crypto',[]); return b
DB=load()
def save():
 tmp=DATA+'.tmp';
 with open(tmp,'w',encoding='utf8') as f: json.dump(DB,f,ensure_ascii=False,indent=2)
 os.replace(tmp,DATA)
def num(v):
 try:return float(str(v).replace(',',''))
 except:return 0.0

def export_csv(rows,path):
 keys=FJ if rows and 'Pair' in rows[0] else CJ
 with open(path,'w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore'); w.writeheader(); w.writerows(rows)

class App(tk.Tk):
 def __init__(self):
  super().__init__(); self.title(APP); self.geometry('1500x940'); self.minsize(1180,760); self.cur='home'; self.market=DB['market']; self.day=date.today().isoformat(); self.vars=[]; self.apply_theme(); self.shell(); self.show('home'); self.after(1000,self.clock)
 def apply_theme(self):
  dark=DB.get('theme','dark')=='dark'; self.bg='#070d19' if dark else '#eef3f8'; self.panel='#0e182a' if dark else '#fff'; self.panel2='#14223a' if dark else '#e9eff6'; self.fg='#eef5ff' if dark else '#172235'; self.muted='#91a5c6' if dark else '#64748b'; self.acc='#42d9b5'; self.red='#ed6b7d'; self.gold='#f2c96b'; self.line='#243754' if dark else '#d5deea'; self.configure(bg=self.bg); s=ttk.Style(self); s.theme_use('clam'); s.configure('Treeview',background=self.panel2,fieldbackground=self.panel2,foreground=self.fg,rowheight=32,borderwidth=0); s.map('Treeview',background=[('selected','#1e476b')]); s.configure('TCombobox',fieldbackground=self.panel2,background=self.panel2,foreground=self.fg)
 def shell(self):
  top=tk.Frame(self,bg=self.bg); top.pack(fill='x',padx=18,pady=12); tk.Button(top,text='☰',command=self.toggle,bg=self.panel,fg=self.fg,relief='flat',font=('Segoe UI',18,'bold'),width=3).pack(side='left'); tk.Label(top,text=APP,bg=self.bg,fg=self.acc,font=('Segoe UI',24,'bold')).pack(side='left',padx=14); self.clocklabel=tk.Label(top,bg=self.bg,fg=self.fg,font=('Segoe UI',11,'bold')); self.clocklabel.pack(side='right'); self.marketbtn=tk.Button(top,text=self.market,command=self.change_market,bg=self.panel2,fg=self.fg,relief='flat',font=('Segoe UI',10,'bold'),padx=14,pady=7); self.marketbtn.pack(side='right',padx=15)
  self.content=tk.Frame(self,bg=self.bg); self.content.pack(fill='both',expand=True,padx=16); self.bottom=tk.Frame(self,bg=self.panel); self.bottom.pack(fill='x',side='bottom'); self.menu_frame=tk.Frame(self,bg=self.panel,width=330); self.menu_frame.place(x=-340,y=0,relheight=1); self.menu_frame.lift(); self.make_menu(); self.make_ticker()
 def make_menu(self):
  tk.Label(self.menu_frame,text='TRADER PLANNER PRO',bg=self.panel,fg=self.acc,font=('Segoe UI',17,'bold')).pack(anchor='w',padx=22,pady=24)
  items=[('⌂  Home','home'),('◫  برنامه روزانه','daily'),('◈  Trading Plan','plan'),('✓  Checklist','check'),('▣  Journal','journal'),('◉  مدیریت ریسک','risk'),('◷  ساعت بازارها','sessions'),('🐂  ⚔  🐻  Forex Factory','ff'),('▥  گزارش‌ها و خروجی','reports'),('⚙  تنظیمات','settings')]
  for t,k in items: tk.Button(self.menu_frame,text=t,command=lambda x=k:self.go(x),anchor='w',bg=self.panel,fg=self.fg,activebackground=self.panel2,activeforeground=self.acc,relief='flat',font=('Segoe UI',11),padx=22,pady=11).pack(fill='x')
 def make_ticker(self):
  for w in self.bottom.winfo_children(): w.destroy()
  mode=self.market; names=['EURUSD','GBPUSD','USDJPY','XAUUSD','XAGUSD','WTI'] if mode=='Forex' else ['BTC','ETH','BNB','SOL','XRP','DOGE','ADA','AVAX','TRX','LINK','BTC.D','USDT.D']
  for n in names: tk.Label(self.bottom,text=f'{n}   —   --',bg=self.panel,fg=self.fg,font=('Segoe UI',9,'bold'),padx=14,pady=8).pack(side='left')
 def toggle(self): self.menu_frame.place_configure(x=0 if self.menu_frame.winfo_x()<0 else -340)
 def go(self,k): self.toggle(); self.show(k)
 def show(self,k): self.cur=k; self.clear(); getattr(self,k)()
 def clear(self):
  for w in self.content.winfo_children(): w.destroy()
 def title(self,a,b=''):
  tk.Label(self.content,text=a,bg=self.bg,fg=self.fg,font=('Segoe UI',21,'bold')).pack(anchor='e',pady=(10,2))
  if b: tk.Label(self.content,text=b,bg=self.bg,fg=self.muted,font=('Segoe UI',10)).pack(anchor='e',pady=(0,12))
 def card(self,p): return tk.Frame(p,bg=self.panel,highlightbackground=self.line,highlightthickness=1)
 def btn(self,p,t,cmd,primary=False,danger=False): return tk.Button(p,text=t,command=cmd,bg=self.acc if primary else self.red if danger else self.panel2,fg='#06131c' if primary else self.fg,relief='flat',font=('Segoe UI',10,'bold'),padx=13,pady=8)
 def clock(self): self.clocklabel.config(text=datetime.now().strftime('%Y-%m-%d  |  %H:%M:%S')); self.after(1000,self.clock)
 def home(self):
  self.title('داشبورد حرفه‌ای','مرکز کنترل کامل فرایند ترید، زندگی، ریسک و سوابق حرفه‌ای')
  p=DB['profile']; name=p.get('name') or 'Trader'; tk.Label(self.content,text=f'خوش آمدی، {name}',bg=self.bg,fg=self.acc,font=('Segoe UI',14,'bold')).pack(anchor='e',padx=10)
  trades=DB['journals'][self.market]; rs=[num(x.get('Result (R)')) for x in trades]; wins=sum(r>0 for r in rs); net=sum(rs); done=sum(x['done'] for x in DB['tasks'].get(self.day,[])); total=len(DB['tasks'].get(self.day,[]))
  row=tk.Frame(self.content,bg=self.bg); row.pack(fill='x',pady=12)
  for a,b in [('معاملات',len(trades)),('Win Rate',f'{wins/len(rs)*100:.1f}%' if rs else '0%'),('Net R',f'{net:.2f} R'),('پیشرفت امروز',f'{done/total*100:.0f}%' if total else '0%'),('بازار فعال',self.market)]:
   c=self.card(row); c.pack(side='left',fill='both',expand=True,padx=4); tk.Label(c,text=a,bg=self.panel,fg=self.muted).pack(anchor='w',padx=16,pady=(12,2)); tk.Label(c,text=b,bg=self.panel,fg=self.fg,font=('Segoe UI',18,'bold')).pack(anchor='w',padx=16,pady=(0,12))
  mid=tk.Frame(self.content,bg=self.bg); mid.pack(fill='both',expand=True); l=self.card(mid); l.pack(side='left',fill='both',expand=True,padx=(0,6)); r=self.card(mid); r.pack(side='left',fill='both',expand=True,padx=(6,0))
  tk.Label(l,text='Equity / عملکرد',bg=self.panel,fg=self.fg,font=('Segoe UI',14,'bold')).pack(anchor='e',padx=18,pady=15); self.chart=tk.Canvas(l,bg=self.panel2,height=250,highlightthickness=0); self.chart.pack(fill='both',expand=True,padx=18,pady=10); self.draw_chart(rs)
  tk.Label(r,text='امروز',bg=self.panel,fg=self.fg,font=('Segoe UI',14,'bold')).pack(anchor='e',padx=18,pady=15)
  for x in DB['tasks'].get(self.day,[])[:12]: tk.Label(r,text=f'{"✓" if x["done"] else "○"}  {x["time"]}   {x["title"]}',bg=self.panel,fg=self.muted if x['done'] else self.fg,anchor='e').pack(fill='x',padx=18,pady=3)
  self.btn(r,'ثبت معامله جدید',lambda:self.go('journal'),True).pack(anchor='e',padx=18,pady=12)
 def draw_chart(self,rs):
  self.chart.delete('all'); w=max(600,self.chart.winfo_width()); h=250; vals=[0]
  for x in rs: vals.append(vals[-1]+x)
  if len(vals)<2: self.chart.create_text(w//2,h//2,text='پس از ثبت معاملات، نمودار عملکرد اینجا نمایش داده می‌شود',fill=self.muted,font=('Segoe UI',11)); return
  mn,mx=min(vals),max(vals); span=max(1,mx-mn); pts=[]
  for i,v in enumerate(vals): pts += [25+i*(w-50)/(len(vals)-1),h-25-(v-mn)/span*(h-50)]
  self.chart.create_line(*pts,fill=self.acc,width=3,smooth=True); self.chart.create_text(25,15,text=f'{vals[-1]:.2f} R',fill=self.fg,anchor='w',font=('Segoe UI',11,'bold'))
 def change_market(self): self.market='Crypto' if self.market=='Forex' else 'Forex'; DB['market']=self.market; save(); self.marketbtn.config(text=self.market); self.make_ticker(); self.show(self.cur)
 def daily(self):
  self.title('برنامه روزانه ۳۰ روزه','هر فعالیت قابل تیک، افزودن و جابه‌جایی است')
  wrap=tk.Frame(self.content,bg=self.bg); wrap.pack(fill='both',expand=True); left=self.card(wrap); left.pack(side='left',fill='y',padx=(0,6)); right=self.card(wrap); right.pack(side='left',fill='both',expand=True,padx=(6,0))
  lb=tk.Listbox(left,bg=self.panel2,fg=self.fg,selectbackground='#1e476b',bd=0,width=25,font=('Segoe UI',10)); lb.pack(fill='both',expand=True,padx=12,pady=12); self.lb=lb
  start=date.today()
  for i in range(30): d=start+timedelta(i); lb.insert('end',f'{d.isoformat()}  {FA[d.weekday()]}')
  idx=max(0,(datetime.fromisoformat(self.day).date()-start).days); lb.selection_set(idx); lb.bind('<<ListboxSelect>>',lambda e:self.select_day(lb))
  self.daytree=ttk.Treeview(right,columns=('time','title','cat','done'),show='headings');
  for c,h,w in [('time','زمان',85),('title','فعالیت',620),('cat','دسته',130),('done','وضعیت',80)]: self.daytree.heading(c,text=h); self.daytree.column(c,width=w,anchor='e')
  self.daytree.pack(fill='both',expand=True,padx=15,pady=15); self.daytree.bind('<Double-1>',self.toggle_task)
  bar=tk.Frame(right,bg=self.panel); bar.pack(fill='x',padx=15,pady=(0,12)); self.btn(bar,'＋ فعالیت',self.add_task,True).pack(side='left'); self.btn(bar,'↑',lambda:self.move_task(-1)).pack(side='left',padx=4); self.btn(bar,'↓',lambda:self.move_task(1)).pack(side='left'); self.btn(bar,'حذف',self.delete_task,False,True).pack(side='left',padx=4); self.render_day()
 def select_day(self,lb):
  s=lb.curselection();
  if s:self.day=(date.today()+timedelta(s[0])).isoformat(); self.render_day()
 def render_day(self):
  if not hasattr(self,'daytree'):return
  self.daytree.delete(*self.daytree.get_children())
  for i,x in enumerate(DB['tasks'].get(self.day,[])): self.daytree.insert('','end',iid=str(i),values=(x['time'],x['title'],x['cat'],'✓' if x['done'] else '○'))
 def toggle_task(self,e=None):
  s=self.daytree.selection();
  if s:
   i=int(s[0]); DB['tasks'][self.day][i]['done']=not DB['tasks'][self.day][i]['done']; save(); self.render_day()
 def add_task(self):
  w=tk.Toplevel(self); w.title('فعالیت جدید'); w.geometry('430x260'); w.configure(bg=self.panel); vals=[]
  for lab in ['زمان','فعالیت','دسته']: tk.Label(w,text=lab,bg=self.panel,fg=self.fg).pack(anchor='e',padx=20,pady=(10,2)); e=tk.Entry(w,bg=self.panel2,fg=self.fg,insertbackground=self.fg,relief='flat'); e.pack(fill='x',padx=20); vals.append(e)
  self.btn(w,'ذخیره',lambda:(DB['tasks'][self.day].append({'time':vals[0].get(),'title':vals[1].get(),'cat':vals[2].get(),'done':False}),save(),w.destroy(),self.render_day()),True).pack(pady=15)
 def move_task(self,d):
  s=self.daytree.selection();
  if not s:return
  i=int(s[0]); a=DB['tasks'][self.day]; j=i+d
  if 0<=j<len(a): a[i],a[j]=a[j],a[i]; save(); self.render_day(); self.daytree.selection_set(str(j))
 def delete_task(self):
  s=self.daytree.selection();
  if s and messagebox.askyesno('حذف','این فعالیت حذف شود؟'): del DB['tasks'][self.day][int(s[0])]; save(); self.render_day()
 def plan(self): self.form_page('Trading Plan',PLAN,'plan','ذخیره Trading Plan')
 def form_page(self,title,fields,store,save_text):
  self.title(title,'فیلدها عمداً قابل شخصی‌سازی هستند؛ مقدار پیش‌فرض فقط عنوان است')
  frame=self.card(self.content); frame.pack(fill='both',expand=True,padx=8,pady=5); canvas=tk.Canvas(frame,bg=self.panel,highlightthickness=0); scroll=tk.Scrollbar(frame,command=canvas.yview); inner=tk.Frame(canvas,bg=self.panel); canvas.create_window((0,0),window=inner,anchor='nw'); canvas.configure(yscrollcommand=scroll.set); canvas.pack(side='left',fill='both',expand=True); scroll.pack(side='right',fill='y'); entries=[]
  for i,f in enumerate(fields):
   tk.Label(inner,text=f,bg=self.panel,fg=self.fg,font=('Segoe UI',10,'bold')).grid(row=i,column=1,sticky='e',padx=20,pady=7); e=tk.Entry(inner,bg=self.panel2,fg=self.fg,insertbackground=self.fg,relief='flat',font=('Segoe UI',10)); e.grid(row=i,column=0,sticky='ew',padx=20,pady=7,ipady=7); e.insert(0,DB[store].get(f,'')); entries.append((f,e))
  inner.grid_columnconfigure(0,weight=1); inner.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
  self.btn(self.content,save_text,lambda:[DB[store].__setitem__(f,e.get()) for f,e in entries] and (save(),messagebox.showinfo('ذخیره شد','اطلاعات ذخیره شد')),True).pack(pady=10)
 def check(self):
  self.title('Trading Checklist','قبل از هر ورود، همه موارد لازم را تأیید کن')
  box=self.card(self.content); box.pack(fill='x',padx=10,pady=8)
  vars=[]
  for i,f in enumerate(CHECK): v=tk.BooleanVar(value=DB['check'].get(f,False)); tk.Checkbutton(box,text=f,variable=v,command=lambda f=f,v=v:(DB['check'].__setitem__(f,v.get()),save()),bg=self.panel,fg=self.fg,selectcolor=self.panel2,activebackground=self.panel,activeforeground=self.fg,anchor='e').pack(fill='x',padx=20,pady=7); vars.append(v)
  self.btn(self.content,'Reset Checklist',lambda:(DB['check'].update({x:False for x in CHECK}),save(),self.show('check')),False,True).pack(pady=10)
 def journal(self):
  self.title(f'Journal — {self.market}','ژورنال‌ها کاملاً مستقل هستند و فرم تخصصی هر بازار نمایش داده می‌شود')
  top=tk.Frame(self.content,bg=self.bg); top.pack(fill='x'); self.btn(top,'＋ ثبت معامله',self.new_trade,True).pack(side='left'); self.btn(top,'خروجی CSV',self.export_market).pack(side='left',padx=6); self.btn(top,'گزارش کامل',self.report_dialog).pack(side='left')
  cols=FJ if self.market=='Forex' else CJ; view=['Date',('Pair' if self.market=='Forex' else 'Coin / Pair'),'Direction','Result (R)','P&L','Setup','Lesson']; tree=ttk.Treeview(self.content,columns=view,show='headings');
  for c in view: tree.heading(c,text=c); tree.column(c,width=150,anchor='center')
  tree.pack(fill='both',expand=True,pady=12); self.jtree=tree
  for i,x in enumerate(DB['journals'][self.market]): tree.insert('','end',iid=str(i),values=[x.get(c,'') for c in view])
  tree.bind('<Double-1>',lambda e:self.edit_trade())
 def new_trade(self): self.trade_form()
 def edit_trade(self):
  s=getattr(self,'jtree',None).selection();
  if s:self.trade_form(int(s[0]))
 def trade_form(self,idx=None):
  cols=FJ if self.market=='Forex' else CJ; old=DB['journals'][self.market][idx] if idx is not None else {'Date':date.today().isoformat(),'Direction':'Long' if self.market=='Crypto' else 'Buy'}; w=tk.Toplevel(self); w.title(f'{self.market} Journal'); w.geometry('900x760'); w.configure(bg=self.panel)
  canvas=tk.Canvas(w,bg=self.panel,highlightthickness=0); scr=tk.Scrollbar(w,command=canvas.yview); inner=tk.Frame(canvas,bg=self.panel); canvas.create_window((0,0),window=inner,anchor='nw'); canvas.configure(yscrollcommand=scr.set); canvas.pack(side='left',fill='both',expand=True); scr.pack(side='right',fill='y')
  es={}
  for i,c in enumerate(cols):
   tk.Label(inner,text=c,bg=self.panel,fg=self.fg,font=('Segoe UI',9,'bold')).grid(row=i,column=1,sticky='e',padx=18,pady=5); e=tk.Entry(inner,bg=self.panel2,fg=self.fg,insertbackground=self.fg,relief='flat'); e.grid(row=i,column=0,sticky='ew',padx=18,pady=5,ipady=5); e.insert(0,str(old.get(c,''))); es[c]=e
  inner.grid_columnconfigure(0,weight=1); inner.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
  def save_trade():
   rec={c:e.get() for c,e in es.items()}; rec['Screenshot']=self.attach_screenshot(rec.get('Screenshot',''))
   if idx is None: DB['journals'][self.market].append(rec)
   else: DB['journals'][self.market][idx]=rec
   save(); w.destroy(); self.show('journal')
  self.btn(w,'ذخیره معامله',save_trade,True).pack(pady=10)
 def attach_screenshot(self,current=''):
  if not current:return ''
  return current
 def export_market(self):
  rows=DB['journals'][self.market]; path=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('Excel CSV','*.csv')],initialfile=f'{self.market}_Journal.csv')
  if path: export_csv(rows,path); messagebox.showinfo('Export','فایل CSV ساخته شد.')
 def risk(self):
  self.title('Risk Manager','محاسبه سریع ریسک معامله؛ اعداد را وارد کن')
  c=self.card(self.content); c.pack(fill='x',padx=10,pady=10); fields=['Account Balance','Risk %','Entry Price','Stop Loss Price','Pip/Point Value']; es={}
  for i,f in enumerate(fields): tk.Label(c,text=f,bg=self.panel,fg=self.fg).grid(row=i,column=1,padx=20,pady=8,sticky='e'); e=tk.Entry(c,bg=self.panel2,fg=self.fg,insertbackground=self.fg,relief='flat'); e.grid(row=i,column=0,padx=20,pady=8,sticky='ew'); es[f]=e
  c.grid_columnconfigure(0,weight=1); out=tk.Label(c,text='—',bg=self.panel,fg=self.acc,font=('Segoe UI',15,'bold')); out.grid(row=5,column=0,columnspan=2,pady=15)
  def calc():
   bal=num(es['Account Balance'].get()); rp=num(es['Risk %'].get()); en=num(es['Entry Price'].get()); sl=num(es['Stop Loss Price'].get()); pv=num(es['Pip/Point Value'].get()); risk=bal*rp/100; dist=abs(en-sl); out.config(text=f'Risk $: {risk:.2f}    |    Distance: {dist:.5g}    |    Points value: {pv:.5g}')
  self.btn(c,'محاسبه',calc,True).grid(row=6,column=0,columnspan=2,pady=8)
 def sessions(self):
  self.title('Market Sessions','ساعت‌ها بر اساس UTC نمایش داده می‌شوند و با ساعت محلی سیستم همگام هستند')
  c=self.card(self.content); c.pack(fill='x',padx=10,pady=10); self.session_clock=tk.Label(c,text='--:--:--',bg=self.panel,fg=self.acc,font=('Segoe UI',42,'bold')); self.session_clock.pack(pady=20); self.session_sub=tk.Label(c,text='',bg=self.panel,fg=self.fg,font=('Segoe UI',15)); self.session_sub.pack(pady=10)
  for n,a,b in [('Sydney','22:00','07:00'),('Tokyo','00:00','09:00'),('London','08:00','17:00'),('New York','13:00','22:00')]: tk.Label(c,text=f'{n:<12} {a}  →  {b} UTC',bg=self.panel2,fg=self.fg,font=('Segoe UI',13,'bold'),padx=18,pady=10).pack(fill='x',padx=30,pady=4)
  self.session_tick()
 def session_tick(self):
  if self.cur!='sessions':return
  n=datetime.utcnow(); m=n.hour*60+n.minute; ss=[('Sydney',1320,420),('Tokyo',0,540),('London',480,1020),('New York',780,1260)]; act=[x for x,a,b in ss if (a<=m<b if a<b else m>=a or m<b)]; self.session_clock.config(text=n.strftime('%H:%M:%S')); self.session_sub.config(text='  •  '.join(act) if act else 'Market closed'); self.after(1000,self.session_tick)
 def ff(self):
  self.title('Forex Factory','تقویم اقتصادی را مستقیماً در مرورگر باز کن')
  c=self.card(self.content); c.pack(fill='both',expand=True,padx=10,pady=10); tk.Label(c,text='🐂   ⚔   🐻',bg=self.panel,fg=self.gold,font=('Segoe UI',40,'bold')).pack(pady=45); tk.Label(c,text='Forex Factory Economic Calendar',bg=self.panel,fg=self.fg,font=('Segoe UI',18,'bold')).pack(); self.btn(c,'باز کردن Forex Factory',lambda:webbrowser.open(FF),True).pack(pady=25)
 def reports(self):
  self.title('گزارش‌ها و سوابق حرفه‌ای','خروجی کامل برای آرشیو، رزومه و سابقه کاری — همراه نمودار عملکرد')
  c=self.card(self.content); c.pack(fill='x',padx=10,pady=10)
  for text,cmd in [('PDF کامل',lambda:self.export_report('pdf')),('Excel کامل',lambda:self.export_report('xlsx')),('CSV Forex',lambda:self.save_csv_for('Forex')),('CSV Crypto',lambda:self.save_csv_for('Crypto'))]: self.btn(c,text,cmd,True if 'کامل' in text else False).pack(side='left',padx=8,pady=18)
  tk.Label(c,text='پروفایل گزارش از Settings خوانده می‌شود و نام/عنوان شما روی گزارش ثبت خواهد شد.',bg=self.panel,fg=self.muted).pack(anchor='e',padx=18,pady=10)
 def save_csv_for(self,market):
  p=filedialog.asksaveasfilename(defaultextension='.csv',initialfile=f'{market}_Journal.csv');
  if p: export_csv(DB['journals'][market],p)
 def report_dialog(self): self.show('reports')
 def export_report(self,kind):
  p=filedialog.asksaveasfilename(defaultextension='.pdf' if kind=='pdf' else '.xlsx',initialfile=f'TraderPlannerPro_{self.market}_Report')
  if not p:return
  try:
   if kind=='pdf': self.make_pdf(p)
   else:self.make_xlsx(p)
   messagebox.showinfo('موفق','گزارش حرفه‌ای ساخته شد.')
  except Exception as e: messagebox.showerror('خطا',f'برای خروجی {kind} کتابخانه لازم نصب نیست یا خطایی رخ داد:\n{e}')
 def make_pdf(self,path):
  from reportlab.lib.pagesizes import A4, landscape
  from reportlab.pdfgen import canvas
  from reportlab.lib.units import mm
  c=canvas.Canvas(path,pagesize=landscape(A4)); W,H=landscape(A4); p=DB['profile']; name=p.get('name') or 'Trader'; c.setFont('Helvetica-Bold',22); c.drawString(25*mm,H-25*mm,'TRADER PLANNER PRO'); c.setFont('Helvetica-Bold',16); c.drawRightString(W-25*mm,H-25*mm,f'{name} — {self.market}'); c.setFont('Helvetica',10); c.drawString(25*mm,H-34*mm,f"{p.get('title','')} | {p.get('country','')} | {p.get('experience','')} | Generated {datetime.now():%Y-%m-%d}")
  rows=DB['journals'][self.market]; rs=[num(x.get('Result (R)')) for x in rows]; c.setFont('Helvetica-Bold',13); c.drawString(25*mm,H-50*mm,'Performance Summary'); c.setFont('Helvetica',11); c.drawString(25*mm,H-59*mm,f'Trades: {len(rows)}   Win Rate: {(sum(r>0 for r in rs)/len(rs)*100 if rs else 0):.1f}%   Net R: {sum(rs):.2f}'); vals=[0];
  for r in rs: vals.append(vals[-1]+r)
  x0,y0=25*mm,H-105*mm; cw,ch=W-50*mm,55*mm; c.rect(x0,y0,cw,ch,stroke=1,fill=0); 
  if len(vals)>1:
   mn,mx=min(vals),max(vals); sp=max(1,mx-mn); pts=[]
   for i,v in enumerate(vals): pts.append((x0+5*mm+i*(cw-10*mm)/(len(vals)-1),y0+5*mm+(v-mn)/sp*(ch-10*mm)))
   c.setLineWidth(2); c.setStrokeColorRGB(.25,.75,.65)
   for a,b in zip(pts,pts[1:]): c.line(*a,*b)
  c.setFillColorRGB(0,0,0); c.setFont('Helvetica-Bold',12); c.drawString(25*mm,y0-12*mm,'Journal Records'); y= y0-20*mm; c.setFont('Helvetica',7); keys=['Date','Pair' if self.market=='Forex' else 'Coin / Pair','Direction','Result (R)','P&L','Setup']; c.drawString(25*mm,y,' | '.join(keys)); y-=5*mm
  for r in rows[-22:]:
   c.drawString(25*mm,y,' | '.join(str(r.get(k,''))[:24] for k in keys)); y-=4.5*mm
   if y<12*mm:c.showPage(); y=H-25*mm
  c.save()
 def make_xlsx(self,path):
  from openpyxl import Workbook
  from openpyxl.styles import Font,PatternFill,Alignment
  from openpyxl.chart import LineChart,Reference
  wb=Workbook(); ws=wb.active; ws.title='Profile'; p=DB['profile']; ws.append(['TRADER PLANNER PRO']); ws.append([])
  for k,v in p.items():ws.append([k,v])
  for market in ['Forex','Crypto']:
   ws=wb.create_sheet(market); cols=FJ if market=='Forex' else CJ; ws.append(cols)
   for cell in ws[1]: cell.font=Font(bold=True); cell.fill=PatternFill('solid',fgColor='16324F'); cell.font=Font(color='FFFFFF',bold=True)
   for r in DB['journals'][market]: ws.append([r.get(k,'') for k in cols])
   if ws.max_row>1:
    c=wb.create_sheet(market+' Performance'); c.append(['Trade','Result R','Equity R']) ; eq=0
    for i,r in enumerate(DB['journals'][market],1): eq+=num(r.get('Result (R)')); c.append([i,num(r.get('Result (R)')),eq])
    chart=LineChart(); chart.title='Equity Curve'; chart.y_axis.title='R'; chart.x_axis.title='Trade'; chart.add_data(Reference(c,min_col=3,min_row=1,max_row=c.max_row),titles_from_data=True); chart.set_categories(Reference(c,min_col=1,min_row=2,max_row=c.max_row)); c.add_chart(chart,'E2')
  wb.save(path)
 def settings(self):
  self.title('تنظیمات','زبان، ظاهر، پروفایل حرفه‌ای و Google Drive')
  c=self.card(self.content); c.pack(fill='both',expand=True,padx=10,pady=10)
  fields=list(DEFAULT_PROFILE.keys()); es={}
  for i,f in enumerate(fields):
   tk.Label(c,text=f,bg=self.panel,fg=self.fg).grid(row=i,column=1,sticky='e',padx=20,pady=5); e=tk.Entry(c,bg=self.panel2,fg=self.fg,insertbackground=self.fg,relief='flat'); e.grid(row=i,column=0,sticky='ew',padx=20,pady=5); e.insert(0,DB['profile'].get(f,'')); es[f]=e
  c.grid_columnconfigure(0,weight=1)
  tk.Label(c,text='Language',bg=self.panel,fg=self.fg).grid(row=0,column=3,padx=15); lang=ttk.Combobox(c,values=['فارسی','English'],state='readonly'); lang.set('فارسی' if DB['language']=='fa' else 'English'); lang.grid(row=0,column=2,padx=15)
  tk.Label(c,text='Theme',bg=self.panel,fg=self.fg).grid(row=1,column=3,padx=15); theme=ttk.Combobox(c,values=['Dark','Light'],state='readonly'); theme.set('Dark' if DB['theme']=='dark' else 'Light'); theme.grid(row=1,column=2,padx=15)
  tk.Label(c,text='Google Drive synced folder',bg=self.panel,fg=self.fg).grid(row=2,column=3,padx=15); drive=tk.Entry(c,bg=self.panel2,fg=self.fg,insertbackground=self.fg,relief='flat'); drive.insert(0,DB.get('drive_folder','')); drive.grid(row=2,column=2,padx=15); self.btn(c,'انتخاب پوشه',lambda:drive.insert(0,filedialog.askdirectory() or '')).grid(row=2,column=1,padx=8)
  def save_settings():
   for k,e in es.items():DB['profile'][k]=e.get()
   DB['language']='fa' if lang.get()=='فارسی' else 'en'; DB['theme']='dark' if theme.get()=='Dark' else 'light'; DB['drive_folder']=drive.get(); save(); self.apply_theme(); messagebox.showinfo('ذخیره','تنظیمات ذخیره شد. برای اعمال کامل ظاهر، برنامه را دوباره باز کن.')
  self.btn(c,'ذخیره تنظیمات',save_settings,True).grid(row=len(fields)+1,column=0,columnspan=4,pady=18)
  self.btn(c,'باز کردن Google Drive',lambda:webbrowser.open('https://drive.google.com/drive/my-drive')).grid(row=len(fields)+2,column=0,columnspan=4,pady=5)

if __name__=='__main__': App().mainloop()
