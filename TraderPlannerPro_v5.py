# Trader Planner Pro V6
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, timedelta, datetime
import json, os, csv, webbrowser
APP='Trader Planner Pro'; VERSION=6
ROOT=os.path.join(os.path.expanduser('~'),'TraderPlannerPro'); os.makedirs(ROOT,exist_ok=True); DATA=os.path.join(ROOT,'data.json')
TASKS=[('07:00','بیداری + آب + نور صبح','سلامت'),('07:15','صبحانه','غذا'),('07:45','ورزش / پیاده‌روی صبح 30–45 دقیقه','ورزش'),('08:35','دوش + آماده‌سازی میز','روتین'),('09:00','MARK UP — ساختار، روند، نقدینگی و نواحی','MARK UP'),('10:45','استراحت 15 دقیقه','استراحت'),('11:00','MARK UP — سناریوی A/B و نقاط ابطال','MARK UP'),('12:30','ثبت سناریو + بررسی خبرها','تحلیل'),('13:00','پایان MARK UP + بستن چارت','پایان'),('13:15','ناهار','غذا'),('14:00','استراحت / چرت کوتاه','ریکاوری'),('14:30','مرور پلن + آماده‌سازی سشن','آماده‌سازی'),('15:30','TRADING — فقط ستاپ‌های مجاز','TRADING'),('17:00','استراحت 10 دقیقه‌ای','کنترل'),('17:10','TRADING — ادامه سشن','TRADING'),('19:00','پایان قطعی ترید','پایان'),('19:15','شام','غذا'),('19:45','ورزش / پیاده‌روی عصر 30 دقیقه','ورزش'),('20:30','تفریح بدون چارت','تفریح'),('21:00','ژورنال + اسکرین‌شات + درس روز','ژورنال'),('21:40','مطالعه / بک‌تست سبک','یادگیری'),('22:30','خاموشی صفحه‌نمایش','خواب'),('23:30','خواب','خواب')]
PLAN=['بازارهای مجاز','تایم‌فریم‌های اصلی','ستاپ‌های مجاز','شرایط ورود','شرایط عدم ورود','حداکثر ریسک هر معامله (%)','حداکثر ضرر روزانه (%)','حداکثر معاملات روزانه','قانون خروج','قانون توقف بعد از باخت','قوانین روانشناسی','اهداف ماهانه']
CHECK=['جهت و ساختار بازار مشخص است','ناحیه ورود معتبر و تازه است','ستاپ مطابق Trading Plan است','ریسک و حجم محاسبه شده','حد ضرر قبل از ورود مشخص است','R:R قابل قبول است','خبر مهم بررسی شده است','حالت روانی مناسب است','FOMO / Revenge ندارم','بعد از ورود قانون را تغییر نمی‌دهم']
FIELDS=['Date','Pair / Coin','Direction','Session','Timeframe','Entry','Stop Loss','Take Profit','Position Size','Risk %','Risk $','R:R','Setup','Market Structure','Liquidity','Entry Model','Emotion Before','Emotion During','Emotion After','Mistake','Result','Result (R)','P&L','Lesson','Screenshot']
CHOICES={'Direction':['Buy / Long','Sell / Short'],'Session':['Asia','London','New York','London + New York','Other'],'Timeframe':['1m','3m','5m','15m','30m','1H','4H','Daily'],'Result':['Win','Loss','Break Even','Open']}
def fresh():
    t=date.today(); tasks={}
    for i in range(60): tasks[(t+timedelta(i)).isoformat()]=[{'time':a,'title':b,'cat':c,'done':False} for a,b,c in TASKS]
    return {'version':VERSION,'market':'Crypto','tasks':tasks,'journals':{'Forex':[],'Crypto':[]},'plan':{x:'' for x in PLAN},'check':{x:False for x in CHECK},'profile':{'name':'','timezone':'','account_currency':'USD','starting_balance':''}}
def load():
    try:
        with open(DATA,encoding='utf-8') as f: old=json.load(f)
    except Exception: old={}
    db=fresh()
    for k,v in old.items():
        if isinstance(v,dict) and isinstance(db.get(k),dict): db[k].update(v)
        else: db[k]=v
    db['version']=VERSION; db.setdefault('journals',{'Forex':[],'Crypto':[]}); db['journals'].setdefault('Forex',[]); db['journals'].setdefault('Crypto',[]); db.setdefault('tasks',{})
    return db
DB=load()
def save():
    tmp=DATA+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(DB,f,ensure_ascii=False,indent=2)
    os.replace(tmp,DATA)
def num(v):
    try:return float(str(v).replace(',','').strip())
    except:return 0.0
class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title(APP+' V6'); self.geometry('1500x940'); self.minsize(1100,720); self.bg='#070d19'; self.panel='#0e182a'; self.panel2='#14223a'; self.fg='#eef5ff'; self.muted='#91a5c6'; self.acc='#42d9b5'; self.line='#243754'; self.market=DB.get('market','Crypto'); self.day=date.today().isoformat(); self.menu_open=False
        s=ttk.Style(self); s.theme_use('clam'); s.configure('Treeview',background=self.panel2,fieldbackground=self.panel2,foreground=self.fg,rowheight=34); s.map('Treeview',background=[('selected','#1e476b')]); self._shell(); self.show('home'); self.after(500,self._clock)
    def _shell(self):
        top=tk.Frame(self,bg=self.bg); top.pack(fill='x',padx=18,pady=12); tk.Button(top,text='☰',command=self.toggle_menu,bg=self.panel,fg=self.fg,relief='flat',font=('Segoe UI',18,'bold'),width=3).pack(side='left'); tk.Label(top,text='TRADER PLANNER PRO',bg=self.bg,fg=self.acc,font=('Segoe UI',23,'bold')).pack(side='left',padx=14); self.clock=tk.Label(top,bg=self.bg,fg=self.fg,font=('Segoe UI',11,'bold')); self.clock.pack(side='right'); self.market_btn=tk.Button(top,text=self.market,command=self.change_market,bg=self.panel2,fg=self.fg,relief='flat',font=('Segoe UI',10,'bold'),padx=14,pady=7); self.market_btn.pack(side='right',padx=15); self.content=tk.Frame(self,bg=self.bg); self.content.pack(fill='both',expand=True,padx=16); self.menu=tk.Frame(self,bg=self.panel,width=330); self.menu.place(x=-340,y=0,relheight=1); self.menu.lift()
        for text,key in [('⌂  Home','home'),('◫  برنامه روزانه','daily'),('◈  Trading Plan','plan'),('✓  Checklist','check'),('▣  Journal','journal'),('◉  مدیریت ریسک','risk'),('◷  ساعت بازارها','sessions'),('🐂  Forex Factory','ff'),('▥  گزارش‌ها و خروجی','reports'),('⚙  تنظیمات','settings')]: tk.Button(self.menu,text=text,command=lambda k=key:self.go(k),anchor='w',bg=self.panel,fg=self.fg,activebackground=self.panel2,activeforeground=self.acc,relief='flat',font=('Segoe UI',11),padx=22,pady=11).pack(fill='x')
    def toggle_menu(self): self.menu.place_configure(x=0 if not self.menu_open else -340); self.menu_open=not self.menu_open
    def go(self,k):
        if self.menu_open:self.toggle_menu()
        self.show(k)
    def show(self,k):
        self.cur=k
        for w in self.content.winfo_children():w.destroy()
        getattr(self,k)()
    def _clock(self): self.clock.config(text=datetime.now().strftime('%Y-%m-%d  |  %H:%M:%S')); self.after(500,self._clock)
    def title(self,a,b=''):
        tk.Label(self.content,text=a,bg=self.bg,fg=self.fg,font=('Segoe UI',21,'bold')).pack(anchor='e',pady=(10,2))
        if b:tk.Label(self.content,text=b,bg=self.bg,fg=self.muted,font=('Segoe UI',10)).pack(anchor='e',pady=(0,12))
    def card(self,p): return tk.Frame(p,bg=self.panel,highlightbackground=self.line,highlightthickness=1)
    def button(self,p,text,cmd,primary=False): return tk.Button(p,text=text,command=cmd,bg=self.acc if primary else self.panel2,fg='#06131c' if primary else self.fg,relief='flat',font=('Segoe UI',10,'bold'),padx=13,pady=8,cursor='hand2')
    def change_market(self): self.market='Forex' if self.market=='Crypto' else 'Crypto'; DB['market']=self.market; save(); self.market_btn.config(text=self.market); self.show(self.cur)
    def home(self):
        self.title('داشبورد حرفه‌ای','مرکز کنترل نظم روزانه و عملکرد معاملات'); rows=DB['journals'][self.market]; rs=[num(x.get('Result (R)')) for x in rows]; wins=sum(x>0 for x in rs); tasks=DB['tasks'].setdefault(self.day,[]); done=sum(bool(x.get('done')) for x in tasks); bar=tk.Frame(self.content,bg=self.bg); bar.pack(fill='x',pady=10)
        for a,b in [('معاملات',len(rows)),('Win Rate',f'{wins/len(rs)*100:.1f}%' if rs else '0%'),('Net R',f'{sum(rs):.2f} R'),('پیشرفت امروز',f'{done/len(tasks)*100:.0f}%' if tasks else '0%'),('بازار فعال',self.market)]:
            c=self.card(bar); c.pack(side='left',fill='both',expand=True,padx=4); tk.Label(c,text=a,bg=self.panel,fg=self.muted).pack(anchor='w',padx=16,pady=(12,2)); tk.Label(c,text=b,bg=self.panel,fg=self.fg,font=('Segoe UI',18,'bold')).pack(anchor='w',padx=16,pady=(0,12))
        body=tk.Frame(self.content,bg=self.bg); body.pack(fill='both',expand=True); left=self.card(body); right=self.card(body); left.pack(side='left',fill='both',expand=True,padx=(0,6)); right.pack(side='left',fill='both',expand=True,padx=(6,0)); tk.Label(left,text='عملکرد / Net R',bg=self.panel,fg=self.fg,font=('Segoe UI',14,'bold')).pack(anchor='e',padx=18,pady=15); cv=tk.Canvas(left,bg=self.panel2,highlightthickness=0); cv.pack(fill='both',expand=True,padx=18,pady=10)
        if rs:
            vals=[0]
            for r in rs: vals.append(vals[-1]+r)
            def draw(_=None):
                cv.delete('all'); w=max(cv.winfo_width(),400); h=max(cv.winfo_height(),240); lo,hi=min(vals),max(vals); span=max(1,hi-lo); pts=[]
                for i,v in enumerate(vals): pts += [25+i*(w-50)/max(1,len(vals)-1),h-25-(v-lo)/span*(h-50)]
                cv.create_line(*pts,fill=self.acc,width=3,smooth=True); cv.create_text(25,15,text=f'{vals[-1]:.2f} R',fill=self.fg,anchor='w',font=('Segoe UI',11,'bold'))
            cv.bind('<Configure>',draw); draw()
        else: cv.create_text(300,130,text='بعد از ثبت معامله، عملکرد اینجا نمایش داده می‌شود',fill=self.muted)
        tk.Label(right,text='برنامه امروز',bg=self.panel,fg=self.fg,font=('Segoe UI',14,'bold')).pack(anchor='e',padx=18,pady=15)
        for x in tasks[:14]: tk.Label(right,text=('✓' if x.get('done') else '○')+'  '+x['time']+'   '+x['title'],bg=self.panel,fg=self.muted if x.get('done') else self.fg,anchor='e').pack(fill='x',padx=18,pady=3)
        self.button(right,'باز کردن Journal',lambda:self.show('journal'),True).pack(anchor='e',padx=18,pady=12)
    def daily(self):
        self.title('برنامه روزانه','تیک‌ها فوری ذخیره می‌شوند'); nav=tk.Frame(self.content,bg=self.bg); nav.pack(fill='x'); self.button(nav,'روز قبل',lambda:self._shift(-1)).pack(side='left',padx=4); tk.Label(nav,text=self.day,bg=self.bg,fg=self.fg,font=('Segoe UI',12,'bold')).pack(side='left',padx=14); self.button(nav,'روز بعد',lambda:self._shift(1)).pack(side='left',padx=4); tasks=DB['tasks'].setdefault(self.day,[])
        if not tasks: tasks.extend([{'time':a,'title':b,'cat':c,'done':False} for a,b,c in TASKS]); save()
        done=sum(bool(x.get('done')) for x in tasks); h=self.card(self.content); h.pack(fill='x',pady=10); tk.Label(h,text=f'پیشرفت: {done}/{len(tasks)}  ({done/len(tasks)*100:.0f}%)',bg=self.panel,fg=self.acc,font=('Segoe UI',13,'bold')).pack(anchor='e',padx=16,pady=12)
        box=tk.Frame(self.content,bg=self.bg); box.pack(fill='both',expand=True); cv=tk.Canvas(box,bg=self.bg,highlightthickness=0); sb=ttk.Scrollbar(box,orient='vertical',command=cv.yview); inner=tk.Frame(cv,bg=self.bg); inner.bind('<Configure>',lambda e:cv.configure(scrollregion=cv.bbox('all'))); cv.create_window((0,0),window=inner,anchor='nw'); cv.configure(yscrollcommand=sb.set); cv.pack(side='left',fill='both',expand=True); sb.pack(side='right',fill='y')
        for i,x in enumerate(tasks):
            v=tk.BooleanVar(value=bool(x.get('done'))); tk.Checkbutton(inner,text=f"{x['time']}   {x['title']}   [{x['cat']}]",variable=v,command=lambda i=i,v=v,tasks=tasks:self._toggle_task(tasks,i,v),bg=self.panel,fg=self.fg,selectcolor=self.panel2,activebackground=self.panel,activeforeground=self.acc,anchor='e',padx=14,pady=10,relief='flat').pack(fill='x',pady=2)
    def _toggle_task(self,tasks,i,v): tasks[i]['done']=bool(v.get()); save(); self.show('daily')
    def _shift(self,n): self.day=(date.fromisoformat(self.day)+timedelta(n)).isoformat(); self.show('daily')
    def journal(self):
        self.title(f'Journal — {self.market}','فرم دو ستونه حرفه‌ای؛ Double-click برای ویرایش و Delete برای حذف'); bar=tk.Frame(self.content,bg=self.bg); bar.pack(fill='x',pady=4); self.button(bar,'＋ ثبت معامله جدید',self.add_trade,True).pack(side='left',padx=4); self.button(bar,'CSV خروجی',self.export_journal).pack(side='left',padx=4); tree=ttk.Treeview(self.content,columns=('date','pair','dir','tf','result','r','pnl','setup'),show='headings')
        for k,h in {'date':'Date','pair':'Pair / Coin','dir':'Direction','tf':'TF','result':'Result','r':'R','pnl':'P&L','setup':'Setup'}.items(): tree.heading(k,text=h); tree.column(k,width=130,anchor='center')
        tree.pack(fill='both',expand=True,pady=8)
        for idx,r in enumerate(DB['journals'][self.market]): tree.insert('','end',iid=str(idx),values=(r.get('Date',''),r.get('Pair / Coin',r.get('Pair','')),r.get('Direction',''),r.get('Timeframe',''),r.get('Result',''),r.get('Result (R)',''),r.get('P&L',''),r.get('Setup','')))
        tree.bind('<Double-1>',lambda e:self.edit_selected(tree)); tree.bind('<Delete>',lambda e:self.delete_selected(tree)); tk.Label(self.content,text='Double-click = ویرایش   |   Delete = حذف',bg=self.bg,fg=self.muted).pack(anchor='e')
    def add_trade(self): self.trade_form(None)
    def edit_selected(self,tree):
        s=tree.selection()
        if s:self.trade_form(int(s[0]))
    def delete_selected(self,tree):
        s=tree.selection()
        if s and messagebox.askyesno('حذف معامله','این معامله حذف شود؟'): del DB['journals'][self.market][int(s[0])]; save(); self.show('journal')
    def trade_form(self,index):
        win=tk.Toplevel(self); win.title(('ویرایش' if index is not None else 'ثبت')+' معامله — '+self.market); win.geometry('1080x820'); win.configure(bg=self.panel); win.minsize(900,700); win.transient(self); win.grab_set(); outer=tk.Frame(win,bg=self.panel); outer.pack(fill='both',expand=True,padx=18,pady=18); tk.Label(outer,text=f'Journal {self.market}',bg=self.panel,fg=self.acc,font=('Segoe UI',18,'bold')).pack(anchor='e',pady=(0,12)); data=DB['journals'][self.market][index].copy() if index is not None else {}; cols=tk.Frame(outer,bg=self.panel); cols.pack(fill='both',expand=True); left=self.card(cols); right=self.card(cols); left.pack(side='left',fill='both',expand=True,padx=(0,7)); right.pack(side='left',fill='both',expand=True,padx=(7,0)); widgets={}
        groups1=[('TRADE INFO',['Date','Pair / Coin','Direction','Session','Timeframe']),('ENTRY & RISK',['Entry','Stop Loss','Take Profit','Position Size','Risk %','Risk $','R:R']),('ANALYSIS',['Setup','Market Structure','Liquidity','Entry Model'])]; groups2=[('PSYCHOLOGY',['Emotion Before','Emotion During','Emotion After','Mistake']),('RESULT',['Result','Result (R)','P&L','Lesson','Screenshot'])]
        def build(parent,groups):
            for title,fields in groups:
                tk.Label(parent,text=title,bg=self.panel,fg=self.acc,font=('Segoe UI',11,'bold')).pack(anchor='e',padx=14,pady=(14,5))
                for f in fields:
                    row=tk.Frame(parent,bg=self.panel); row.pack(fill='x',padx=10,pady=4); tk.Label(row,text=f,bg=self.panel,fg=self.muted,width=17,anchor='e').pack(side='right'); val=data.get(f,''); val=self.day if f=='Date' and not val else val
                    if f in CHOICES: w=ttk.Combobox(row,values=CHOICES[f],state='readonly',width=27); w.set(val); w.pack(side='right',padx=8); widgets[f]=w
                    elif f in ('Setup','Market Structure','Liquidity','Entry Model','Emotion Before','Emotion During','Emotion After','Mistake','Lesson'): w=tk.Text(row,height=2,width=29,bg=self.panel2,fg=self.fg,insertbackground=self.fg,relief='flat',wrap='word'); w.insert('1.0',val); w.pack(side='right',padx=8); widgets[f]=w
                    else: w=tk.Entry(row,bg=self.panel2,fg=self.fg,insertbackground=self.fg,relief='flat',width=30); w.insert(0,val); w.pack(side='right',padx=8); widgets[f]=w
        build(left,groups1); build(right,groups2)
        def browse():
            p=filedialog.askopenfilename(parent=win,filetypes=[('Images','*.png *.jpg *.jpeg *.webp'),('All files','*.*')]);
            if p: widgets['Screenshot'].delete(0,'end'); widgets['Screenshot'].insert(0,p)
        self.button(right,'انتخاب Screenshot',browse).pack(anchor='e',padx=18,pady=5)
        def value(f): w=widgets[f]; return w.get('1.0','end-1c').strip() if isinstance(w,tk.Text) else w.get().strip()
        def save_trade():
            row={f:value(f) for f in FIELDS}
            if not row['Date'] or not row['Pair / Coin']: messagebox.showwarning('اطلاعات ناقص','Date و Pair / Coin الزامی هستند.',parent=win); return
            if num(row['Risk %'])<0 or num(row['Risk $'])<0: messagebox.showwarning('ریسک نامعتبر','مقادیر ریسک نمی‌توانند منفی باشند.',parent=win); return
            if index is None: DB['journals'][self.market].append(row)
            else: DB['journals'][self.market][index]=row
            save(); win.destroy(); self.show('journal')
        self.button(outer,'💾 ذخیره معامله',save_trade,True).pack(anchor='e',pady=14)
    def export_journal(self):
        path=filedialog.asksaveasfilename(defaultextension='.csv',initialfile=f'{self.market}_Journal.csv',filetypes=[('CSV','*.csv')]);
        if not path:return
        with open(path,'w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction='ignore'); w.writeheader(); w.writerows(DB['journals'][self.market])
        messagebox.showinfo('گزارش','CSV ذخیره شد.')
    def plan(self):
        self.title('Trading Plan','قوانین شخصی را ثبت و ذخیره کن'); box=self.card(self.content); box.pack(fill='both',expand=True,pady=10); self.planvars=[]
        for k in PLAN: e=tk.Entry(box,bg=self.panel2,fg=self.fg,insertbackground=self.fg,relief='flat'); e.insert(0,DB['plan'].get(k,'')); e.pack(fill='x',padx=16,pady=4); self.planvars.append((k,e))
        self.button(box,'ذخیره Trading Plan',self.save_plan,True).pack(anchor='e',padx=16,pady=15)
    def save_plan(self):
        for k,e in self.planvars: DB['plan'][k]=e.get().strip()
        save(); messagebox.showinfo('ذخیره شد','Trading Plan ذخیره شد.')
    def check(self):
        self.title('Checklist','قبل از ورود همه موارد را بررسی کن'); box=self.card(self.content); box.pack(fill='both',expand=True,pady=10)
        for k in CHECK:
            v=tk.BooleanVar(value=bool(DB['check'].get(k))); tk.Checkbutton(box,text=k,variable=v,command=lambda k=k,v=v:self._set_check(k,v),bg=self.panel,fg=self.fg,selectcolor=self.panel2,activebackground=self.panel,activeforeground=self.acc,anchor='e',padx=18,pady=10).pack(fill='x')
        self.button(self.content,'پاک کردن Checklist',self.reset_check).pack(anchor='e',pady=10)
    def _set_check(self,k,v): DB['check'][k]=bool(v.get()); save()
    def reset_check(self): DB['check']={x:False for x in CHECK}; save(); self.show('check')
    def risk(self):
        self.title('مدیریت ریسک','محاسبه مقدار ریسک و حجم تقریبی'); box=self.card(self.content); box.pack(fill='x',pady=20); bal=self._entry(box,'Account Balance','10000'); risk=self._entry(box,'Risk %','1'); stop=self._entry(box,'Stop Distance','100'); out=tk.Label(box,text='Risk Amount: —',bg=self.panel,fg=self.acc,font=('Segoe UI',15,'bold')); out.pack(pady=18)
        def calc(): amount=num(bal.get())*num(risk.get())/100; out.config(text=f'Risk Amount: {amount:.2f}   |   Approx. Units: {amount/num(stop.get()):.4f}' if num(stop.get()) else f'Risk Amount: {amount:.2f}')
        self.button(box,'محاسبه',calc,True).pack(anchor='e',padx=12,pady=12)
    def _entry(self,p,label,default=''):
        f=tk.Frame(p,bg=self.panel); f.pack(fill='x',pady=5); tk.Label(f,text=label,bg=self.panel,fg=self.muted,width=18,anchor='e').pack(side='right'); e=tk.Entry(f,bg=self.panel2,fg=self.fg,insertbackground=self.fg,relief='flat',width=32); e.insert(0,default); e.pack(side='right',padx=8); return e
    def sessions(self):
        self.title('ساعت بازارها','بازه‌های رایج بازار')
        for n,a,b in [('Tokyo','00:00','09:00'),('London','08:00','17:00'),('New York','13:00','22:00')]: c=self.card(self.content); c.pack(fill='x',pady=6); tk.Label(c,text=f'{n}    {a} — {b}',bg=self.panel,fg=self.fg,font=('Segoe UI',14,'bold')).pack(anchor='e',padx=18,pady=14)
    def ff(self): self.title('Forex Factory','تقویم خبرها در مرورگر باز می‌شود'); self.button(self.content,'باز کردن Forex Factory',lambda:webbrowser.open('https://www.forexfactory.com/calendar/'),True).pack(anchor='e',pady=20)
    def reports(self):
        self.title('گزارش‌ها و خروجی','خروجی Journal'); box=self.card(self.content); box.pack(fill='x',pady=20); self.button(box,'CSV Crypto',lambda:self._report_csv('Crypto')).pack(side='left',padx=8,pady=18); self.button(box,'CSV Forex',lambda:self._report_csv('Forex')).pack(side='left',padx=8,pady=18); self.button(box,'گزارش TXT',self._report_txt,True).pack(side='left',padx=8,pady=18)
    def _report_csv(self,m):
        path=filedialog.asksaveasfilename(defaultextension='.csv',initialfile=f'{m}_Journal.csv',filetypes=[('CSV','*.csv')]);
        if not path:return
        with open(path,'w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction='ignore'); w.writeheader(); w.writerows(DB['journals'][m])
        messagebox.showinfo('گزارش','CSV ذخیره شد.')
    def _report_txt(self):
        path=filedialog.asksaveasfilename(defaultextension='.txt',initialfile='TraderPlanner_Report.txt',filetypes=[('Text','*.txt')]);
        if not path:return
        rows=DB['journals'][self.market]; rs=[num(x.get('Result (R)')) for x in rows]
        with open(path,'w',encoding='utf-8') as f:f.write(f'{APP} V{VERSION}\nMarket: {self.market}\nTrades: {len(rows)}\nNet R: {sum(rs):.2f}\n')
        messagebox.showinfo('گزارش','گزارش TXT ذخیره شد.')
    def settings(self):
        self.title('تنظیمات','اطلاعات کاربر'); box=self.card(self.content); box.pack(fill='x',pady=20); p=DB['profile']; name=self._entry(box,'نام',p.get('name','')); tz=self._entry(box,'Timezone',p.get('timezone','')); bal=self._entry(box,'Starting Balance',p.get('starting_balance',''))
        def save_settings(): p.update({'name':name.get().strip(),'timezone':tz.get().strip(),'starting_balance':bal.get().strip()}); save(); messagebox.showinfo('ذخیره شد','تنظیمات ذخیره شد.')
        self.button(box,'ذخیره تنظیمات',save_settings,True).pack(anchor='e',padx=12,pady=14)
if __name__=='__main__': App().mainloop()
