# Trader Planner Pro V7 — deep daily planner + professional two-column journal
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, timedelta, datetime
from pathlib import Path
import json, csv, shutil, re, os, sys

APP = 'Trader Planner Pro'
VERSION = '7.0.0'
ROOT = Path.home() / 'TraderPlannerPro'
DATA = ROOT / 'data.json'
SCREENSHOTS = ROOT / 'Screenshots'
ROOT.mkdir(parents=True, exist_ok=True)
SCREENSHOTS.mkdir(parents=True, exist_ok=True)

TASKS = [
('07:00','بیداری + آب + نور صبح','سلامت'),('07:15','صبحانه','غذا'),('07:45','ورزش / پیاده‌روی صبح 30–45 دقیقه','ورزش'),
('08:35','دوش + آماده‌سازی میز','روتین'),('09:00','MARK UP — ساختار، روند، نقدینگی و نواحی','MARK UP'),
('10:45','استراحت 15 دقیقه','استراحت'),('11:00','MARK UP — سناریوی A/B و نقاط ابطال','MARK UP'),
('12:30','ثبت سناریو + بررسی خبرها','تحلیل'),('13:00','پایان MARK UP + بستن چارت','پایان'),('13:15','ناهار','غذا'),
('14:00','استراحت / چرت کوتاه','ریکاوری'),('14:30','مرور پلن + آماده‌سازی سشن','آماده‌سازی'),
('15:30','TRADING — فقط ستاپ‌های مجاز','TRADING'),('17:00','استراحت 10 دقیقه‌ای','کنترل'),('17:10','TRADING — ادامه سشن','TRADING'),
('19:00','پایان قطعی ترید','پایان'),('19:15','شام','غذا'),('19:45','ورزش / پیاده‌روی عصر 30 دقیقه','ورزش'),
('20:30','تفریح بدون چارت','تفریح'),('21:00','ژورنال + اسکرین‌شات + درس روز','ژورنال'),('21:40','مطالعه / بک‌تست سبک','یادگیری'),
('22:30','خاموشی صفحه‌نمایش','خواب'),('23:30','خواب','خواب')]

PLAN = ['بازارهای مجاز','تایم‌فریم‌های اصلی','ستاپ‌های مجاز','شرایط ورود','شرایط عدم ورود','حداکثر ریسک هر معامله (%)','حداکثر ضرر روزانه (%)','حداکثر معاملات روزانه','قانون خروج','قانون توقف بعد از باخت','قوانین روانشناسی','اهداف ماهانه']
CHECK = ['جهت و ساختار بازار مشخص است','ناحیه ورود معتبر و تازه است','ستاپ مطابق Trading Plan است','ریسک و حجم محاسبه شده','حد ضرر قبل از ورود مشخص است','R:R قابل قبول است','خبر مهم بررسی شده است','حالت روانی مناسب است','FOMO / Revenge ندارم','بعد از ورود قانون را تغییر نمی‌دهم']
FIELDS = ['Date','Symbol','Direction','Session','Timeframe','Entry','Stop Loss','Take Profit','Position Size','Risk %','Risk $','R:R','Setup','Market Structure','Liquidity','Entry Model','Emotion Before','Emotion During','Emotion After','Mistake','Result','Result (R)','P&L','Lesson','Notes','Screenshot']

C = {'bg':'#F6F3ED','panel':'#FFFFFF','soft':'#EEF6F5','text':'#203040','muted':'#70808A','accent':'#29B69B','line':'#D8E2E3','danger':'#C95757','gold':'#D19A32'}

def fresh():
    d = date.today()
    tasks = {}
    for i in range(120):
        tasks[(d + timedelta(i)).isoformat()] = [{'id': f'{(d+timedelta(i)).isoformat()}-{j}', 'time':t, 'title':x, 'cat':c, 'done':False} for j,(t,x,c) in enumerate(TASKS)]
    return {'version':7,'market':'Crypto','tasks':tasks,'journals':{'Forex':[],'Crypto':[]},'plan':{x:'' for x in PLAN},'check':{x:False for x in CHECK},'profile':{'name':'','timezone':'','account_currency':'USD','starting_balance':''}}

def load_db():
    db=fresh()
    try:
        old=json.loads(DATA.read_text(encoding='utf-8'))
        if isinstance(old,dict):
            for k,v in old.items():
                if isinstance(v,dict) and isinstance(db.get(k),dict): db[k].update(v)
                else: db[k]=v
    except Exception: pass
    db.setdefault('journals',{'Forex':[],'Crypto':[]})
    db['journals'].setdefault('Forex',[]); db['journals'].setdefault('Crypto',[])
    db.setdefault('tasks',{}); db.setdefault('plan',{}); db.setdefault('check',{}); db.setdefault('profile',{})
    for day,items in list(db['tasks'].items()):
        if isinstance(items,list):
            for j,item in enumerate(items):
                item.setdefault('id',f'{day}-{j}'); item.setdefault('done',False); item.setdefault('cat','')
    db['version']=7
    return db

DB=load_db()

def save():
    tmp=DATA.with_suffix('.tmp')
    tmp.write_text(json.dumps(DB,ensure_ascii=False,indent=2),encoding='utf-8')
    os.replace(tmp,DATA)

def num(v):
    try:return float(str(v).replace(',','').strip())
    except:return 0.0

def safe(s): return re.sub(r'[^A-Za-z0-9._-]+','_',str(s)).strip('_') or 'Unknown'

def screenshot_folder(row):
    d=row.get('Date') or date.today().isoformat(); market=DB.get('market','Crypto'); symbol=safe(row.get('Symbol','Unknown'))
    folder=SCREENSHOTS/safe(d)/safe(market)/symbol
    folder.mkdir(parents=True,exist_ok=True); return folder

def attach_screenshot(row, source):
    if not source or not Path(source).exists(): return ''
    folder=screenshot_folder(row)
    stamp=datetime.now().strftime('%H%M%S')
    ext=Path(source).suffix.lower() or '.png'
    target=folder/f"{safe(row.get('Date'))}_{safe(row.get('Symbol'))}_{safe(row.get('Direction',''))}_{stamp}{ext}"
    shutil.copy2(source,target); return str(target)

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title(f'{APP} V7'); self.geometry('1500x930'); self.minsize(1120,720); self.configure(bg=C['bg'])
        self.market=DB.get('market','Crypto'); self.day=date.today().isoformat(); self.cur='home'; self.menu_open=False
        self.style=ttk.Style(self); self.style.theme_use('clam'); self.style.configure('Treeview',background=C['panel'],fieldbackground=C['panel'],foreground=C['text'],rowheight=36,borderwidth=0); self.style.map('Treeview',background=[('selected',C['soft'])],foreground=[('selected',C['text'])]); self.style.configure('TCombobox',fieldbackground=C['soft'],background=C['soft']); self.style.configure('TNotebook',background=C['bg'],borderwidth=0)
        self.build_shell(); self.show('home'); self.after(400,self.clock)
    def build_shell(self):
        top=tk.Frame(self,bg=C['bg']); top.pack(fill='x',padx=18,pady=12)
        tk.Button(top,text='☰',command=self.toggle_menu,bg=C['panel'],fg=C['text'],relief='flat',font=('Segoe UI',18,'bold'),width=3).pack(side='left')
        tk.Label(top,text=APP,bg=C['bg'],fg=C['accent'],font=('Segoe UI',23,'bold')).pack(side='left',padx=14)
        self.clock_label=tk.Label(top,bg=C['bg'],fg=C['text'],font=('Segoe UI',10,'bold')); self.clock_label.pack(side='right')
        self.market_btn=tk.Button(top,text=self.market,command=self.change_market,bg=C['soft'],fg=C['text'],relief='flat',font=('Segoe UI',10,'bold'),padx=16,pady=8); self.market_btn.pack(side='right',padx=14)
        self.content=tk.Frame(self,bg=C['bg']); self.content.pack(fill='both',expand=True,padx=16)
        self.menu=tk.Frame(self,bg=C['panel'],width=300); self.menu.place(x=-310,y=0,relheight=1)
        tk.Label(self.menu,text='TRADER PLANNER PRO',bg=C['panel'],fg=C['accent'],font=('Segoe UI',17,'bold')).pack(anchor='w',padx=22,pady=24)
        for text,key in [('⌂  Home','home'),('◫  برنامه روزانه','daily'),('◈  Trading Plan','plan'),('✓  Checklist','check'),('▣  Journal','journal'),('⚙  تنظیمات','settings')]:
            tk.Button(self.menu,text=text,command=lambda k=key:self.go(k),anchor='w',bg=C['panel'],fg=C['text'],activebackground=C['soft'],relief='flat',font=('Segoe UI',11),padx=22,pady=11).pack(fill='x')
    def toggle_menu(self): self.menu.place_configure(x=0 if not self.menu_open else -310); self.menu_open=not self.menu_open
    def go(self,k):
        if self.menu_open:self.toggle_menu()
        self.show(k)
    def show(self,k):
        self.cur=k
        for w in self.content.winfo_children(): w.destroy()
        getattr(self,k)()
    def clock(self): self.clock_label.config(text=datetime.now().strftime('%Y-%m-%d  |  %H:%M:%S')); self.after(500,self.clock)
    def heading(self,title,sub=''):
        tk.Label(self.content,text=title,bg=C['bg'],fg=C['text'],font=('Segoe UI',22,'bold')).pack(anchor='e',pady=(8,2))
        if sub: tk.Label(self.content,text=sub,bg=C['bg'],fg=C['muted'],font=('Segoe UI',10)).pack(anchor='e',pady=(0,10))
    def card(self,p): return tk.Frame(p,bg=C['panel'],highlightbackground=C['line'],highlightthickness=1)
    def btn(self,p,text,cmd,primary=False): return tk.Button(p,text=text,command=cmd,bg=C['accent'] if primary else C['soft'],fg=C['text'],relief='flat',font=('Segoe UI',10,'bold'),padx=13,pady=8)
    def change_market(self): self.market='Forex' if self.market=='Crypto' else 'Crypto'; DB['market']=self.market; save(); self.market_btn.config(text=self.market); self.show(self.cur)
    def home(self):
        self.heading('داشبورد','نمای سریع عملکرد، نظم روزانه و معاملات اخیر')
        rows=DB['journals'][self.market]; rs=[num(r.get('Result (R)')) for r in rows]; tasks=DB['tasks'].setdefault(self.day,[]); done=sum(bool(x.get('done')) for x in tasks)
        cards=[('معاملات',len(rows)),('Win Rate',f'{sum(r>0 for r in rs)/len(rs)*100:.1f}%' if rs else '0%'),('Net R',f'{sum(rs):.2f} R'),('پیشرفت امروز',f'{done/len(tasks)*100:.0f}%' if tasks else '0%'),('بازار فعال',self.market)]
        row=tk.Frame(self.content,bg=C['bg']); row.pack(fill='x',pady=8)
        for a,b in cards:
            c=self.card(row); c.pack(side='left',fill='both',expand=True,padx=4); tk.Label(c,text=a,bg=C['panel'],fg=C['muted']).pack(anchor='w',padx=15,pady=(11,2)); tk.Label(c,text=b,bg=C['panel'],fg=C['text'],font=('Segoe UI',17,'bold')).pack(anchor='w',padx=15,pady=(0,11))
        lower=tk.Frame(self.content,bg=C['bg']); lower.pack(fill='both',expand=True,pady=14)
        left=self.card(lower); left.pack(side='left',fill='both',expand=True,padx=4); right=self.card(lower); right.pack(side='left',fill='both',expand=True,padx=4)
        tk.Label(left,text='آخرین معاملات',bg=C['panel'],fg=C['text'],font=('Segoe UI',13,'bold')).pack(anchor='e',padx=16,pady=12)
        for r in rows[-6:][::-1]:
            line=tk.Frame(left,bg=C['panel']); line.pack(fill='x',padx=12,pady=4); tk.Label(line,text=f"{r.get('Symbol','—')}  {r.get('Direction','')}",bg=C['panel'],fg=C['text'],font=('Segoe UI',10,'bold')).pack(side='left'); tk.Label(line,text=f"{r.get('Result (R)','0')}R   {r.get('P&L','0')}",bg=C['panel'],fg=C['accent'] if num(r.get('Result (R'))) > 0 else C['danger']).pack(side='right')
        tk.Label(right,text='کنترل امروز',bg=C['panel'],fg=C['text'],font=('Segoe UI',13,'bold')).pack(anchor='e',padx=16,pady=12)
        self.btn(right,'باز کردن برنامه روزانه',lambda:self.show('daily'),True).pack(anchor='e',padx=16,pady=8)
        self.btn(right,'＋ ثبت معامله جدید',self.add_trade,True).pack(anchor='e',padx=16,pady=8)
        self.btn(right,'مشاهده ژورنال',lambda:self.show('journal')).pack(anchor='e',padx=16,pady=8)
    def daily(self):
        self.heading('برنامه روزانه','هر فعالیت قابل تیک، ویرایش، حذف و افزودن است؛ تغییرات فوراً ذخیره می‌شوند')
        nav=tk.Frame(self.content,bg=C['bg']); nav.pack(fill='x',pady=4)
        self.btn(nav,'روز قبل',lambda:self.shift_day(-1)).pack(side='left'); tk.Label(nav,text=self.day,bg=C['bg'],fg=C['text'],font=('Segoe UI',12,'bold')).pack(side='left',padx=16); self.btn(nav,'روز بعد',lambda:self.shift_day(1)).pack(side='left')
        self.btn(nav,'＋ فعالیت جدید',self.add_task,True).pack(side='right',padx=4); self.btn(nav,'ویرایش انتخاب‌شده',self.edit_task).pack(side='right',padx=4); self.btn(nav,'حذف انتخاب‌شده',self.delete_task).pack(side='right',padx=4)
        tasks=DB['tasks'].setdefault(self.day,[]); done=sum(bool(x.get('done')) for x in tasks)
        tk.Label(nav,text=f'{done}/{len(tasks)} انجام شد  |  {done/len(tasks)*100:.0f}%',bg=C['bg'],fg=C['accent'],font=('Segoe UI',11,'bold')).pack(side='right',padx=15)
        wrap=tk.Frame(self.content,bg=C['bg']); wrap.pack(fill='both',expand=True,pady=10); cols=('done','time','title','cat')
        tree=ttk.Treeview(wrap,columns=cols,show='headings',selectmode='browse'); self.task_tree=tree; tree.heading('done',text='✓'); tree.heading('time',text='زمان'); tree.heading('title',text='فعالیت'); tree.heading('cat',text='دسته'); tree.column('done',width=55,anchor='center'); tree.column('time',width=100,anchor='center'); tree.column('cat',width=150,anchor='e'); tree.column('title',anchor='e')
        for i,x in enumerate(tasks): tree.insert('', 'end', iid=str(i), values=('☑' if x.get('done') else '☐',x.get('time',''),x.get('title',''),x.get('cat','')))
        tree.pack(side='left',fill='both',expand=True); sb=ttk.Scrollbar(wrap,orient='vertical',command=tree.yview); sb.pack(side='right',fill='y'); tree.configure(yscrollcommand=sb.set); tree.bind('<Double-1>',lambda e:self.toggle_selected_task())
        tk.Label(self.content,text='نکته: برای تیک‌زدن روی ردیف دوبار کلیک کن؛ برای ویرایش یا حذف یک ردیف را انتخاب کن.',bg=C['bg'],fg=C['muted']).pack(anchor='e')
    def toggle_selected_task(self):
        sel=self.task_tree.selection()
        if not sel:return
        i=int(sel[0]); DB['tasks'][self.day][i]['done']=not bool(DB['tasks'][self.day][i].get('done')); save(); self.show('daily')
    def shift_day(self,n): self.day=(date.fromisoformat(self.day)+timedelta(days=n)).isoformat(); DB['tasks'].setdefault(self.day,[]); save(); self.show('daily')
    def task_dialog(self,item=None):
        dlg=tk.Toplevel(self); dlg.title('ویرایش فعالیت' if item else 'فعالیت جدید'); dlg.geometry('520x310'); dlg.configure(bg=C['bg']); dlg.transient(self); dlg.grab_set()
        fields=[('زمان','time'),('عنوان','title'),('دسته','cat')]; vars={}
        for r,(label,key) in enumerate(fields):
            tk.Label(dlg,text=label,bg=C['bg'],fg=C['text']).grid(row=r,column=1,padx=12,pady=10,sticky='e'); v=tk.StringVar(value=(item or {}).get(key,'')); vars[key]=v; tk.Entry(dlg,textvariable=v,justify='right',font=('Segoe UI',11),bg=C['panel'],relief='flat').grid(row=r,column=0,padx=12,pady=10,sticky='ew')
        dlg.columnconfigure(0,weight=1)
        def ok():
            if not vars['title'].get().strip(): messagebox.showwarning('ورودی ناقص','عنوان فعالیت را وارد کن',parent=dlg); return
            if item: item.update({k:v.get().strip() for k,v in vars.items()})
            else: DB['tasks'].setdefault(self.day,[]).append({'id':f'{self.day}-{datetime.now().timestamp()}','time':vars['time'].get().strip(),'title':vars['title'].get().strip(),'cat':vars['cat'].get().strip(),'done':False})
            save(); dlg.destroy(); self.show('daily')
        self.btn(dlg,'ذخیره',ok,True).grid(row=4,column=0,padx=12,pady=15,sticky='e'); self.btn(dlg,'انصراف',dlg.destroy).grid(row=4,column=1,padx=12,pady=15)
    def add_task(self): self.task_dialog()
    def edit_task(self):
        sel=self.task_tree.selection()
        if not sel:return messagebox.showinfo('انتخاب فعالیت','ابتدا یک فعالیت را انتخاب کن')
        self.task_dialog(DB['tasks'][self.day][int(sel[0])])
    def delete_task(self):
        sel=self.task_tree.selection()
        if not sel:return messagebox.showinfo('انتخاب فعالیت','ابتدا یک فعالیت را انتخاب کن')
        i=int(sel[0]); item=DB['tasks'][self.day][i]
        if messagebox.askyesno('حذف فعالیت',f"«{item.get('title','')}» حذف شود؟"):
            DB['tasks'][self.day].pop(i); save(); self.show('daily')
    def journal(self):
        self.heading(f'Journal — {self.market}','ثبت سریع، ویرایش کامل، حذف، فیلتر و مدیریت تصاویر معامله')
        bar=tk.Frame(self.content,bg=C['bg']); bar.pack(fill='x',pady=3); self.btn(bar,'＋ ثبت معامله',self.add_trade,True).pack(side='left',padx=3); self.btn(bar,'ویرایش',self.edit_trade).pack(side='left',padx=3); self.btn(bar,'حذف',self.delete_trade).pack(side='left',padx=3); self.btn(bar,'باز کردن پوشه تصاویر',self.open_screenshot_root).pack(side='left',padx=3); self.btn(bar,'خروجی CSV',self.export_journal).pack(side='left',padx=3)
        filterv=tk.StringVar(); tk.Label(bar,text='جستجو:',bg=C['bg'],fg=C['muted']).pack(side='right'); ent=tk.Entry(bar,textvariable=filterv,width=28,justify='right',relief='flat'); ent.pack(side='right',padx=6); ent.bind('<KeyRelease>',lambda e:self.fill_journal_tree(filterv.get()))
        cols=('date','symbol','direction','session','tf','entry','sl','tp','r','pnl','setup','result'); self.jtree=ttk.Treeview(self.content,columns=cols,show='headings',selectmode='browse')
        heads={'date':'تاریخ','symbol':'نماد','direction':'جهت','session':'سشن','tf':'TF','entry':'Entry','sl':'SL','tp':'TP','r':'R','pnl':'P&L','setup':'Setup','result':'نتیجه'}
        for c in cols:self.jtree.heading(c,text=heads[c]); self.jtree.column(c,width=95,anchor='center')
        self.jtree.column('symbol',width=115); self.jtree.column('setup',width=150); self.jtree.pack(fill='both',expand=True,pady=10); self.jtree.bind('<Double-1>',lambda e:self.edit_trade()); self.fill_journal_tree()
    def fill_journal_tree(self,query=''):
        for x in self.jtree.get_children():self.jtree.delete(x)
        q=query.strip().lower(); rows=DB['journals'][self.market]
        for i,r in enumerate(rows):
            hay=' '.join(str(r.get(k,'')) for k in FIELDS).lower()
            if q and q not in hay:continue
            self.jtree.insert('', 'end', iid=str(i), values=(r.get('Date',''),r.get('Symbol',''),r.get('Direction',''),r.get('Session',''),r.get('Timeframe',''),r.get('Entry',''),r.get('Stop Loss',''),r.get('Take Profit',''),r.get('Result (R)',''),r.get('P&L',''),r.get('Setup',''),r.get('Result','')))
    def edit_trade(self):
        sel=self.jtree.selection()
        if not sel:return messagebox.showinfo('انتخاب معامله','ابتدا یک معامله را انتخاب کن')
        self.trade_dialog(DB['journals'][self.market][int(sel[0])],int(sel[0]))
    def delete_trade(self):
        sel=self.jtree.selection()
        if not sel:return messagebox.showinfo('انتخاب معامله','ابتدا یک معامله را انتخاب کن')
        i=int(sel[0]); r=DB['journals'][self.market][i]
        if messagebox.askyesno('حذف معامله',f"معامله {r.get('Symbol','')} در تاریخ {r.get('Date','')} حذف شود؟"):
            DB['journals'][self.market].pop(i); save(); self.show('journal')
    def add_trade(self): self.trade_dialog()
    def trade_dialog(self,row=None,index=None):
        dlg=tk.Toplevel(self); dlg.title(('ویرایش' if row else 'ثبت')+f' معامله — {self.market}'); dlg.geometry('1120x760'); dlg.minsize(980,680); dlg.configure(bg=C['bg']); dlg.transient(self); dlg.grab_set()
        outer=tk.Frame(dlg,bg=C['bg']); outer.pack(fill='both',expand=True,padx=18,pady=16)
        left=self.card(outer); left.pack(side='left',fill='both',expand=True,padx=6); right=self.card(outer); right.pack(side='left',fill='both',expand=True,padx=6)
        vars={}; widgets={}
        sections=[('اطلاعات معامله',['Date','Symbol','Direction','Session','Timeframe']),('قیمت و ریسک',['Entry','Stop Loss','Take Profit','Position Size','Risk %','Risk $','R:R']),('تحلیل',['Setup','Market Structure','Liquidity','Entry Model'])]
        sections2=[('روانشناسی',['Emotion Before','Emotion During','Emotion After','Mistake']),('نتیجه',['Result','Result (R)','P&L','Lesson','Notes']),('اسکرین‌شات',['Screenshot'])]
        def section(parent,title,fields):
            box=tk.Frame(parent,bg=C['panel']); box.pack(fill='x',padx=14,pady=8); tk.Label(box,text=title,bg=C['panel'],fg=C['accent'],font=('Segoe UI',12,'bold')).grid(row=0,column=0,columnspan=2,sticky='e',pady=(10,6),padx=8)
            for rr,key in enumerate(fields,1):
                tk.Label(box,text=key,bg=C['panel'],fg=C['muted'],font=('Segoe UI',9)).grid(row=rr,column=1,padx=7,pady=5,sticky='e')
                v=tk.StringVar(value=str((row or {}).get(key,''))); vars[key]=v
                if key in ('Direction','Result','Session','Timeframe','Emotion Before','Emotion During','Emotion After'):
                    vals={'Direction':['LONG','SHORT'],'Result':['WIN','LOSS','BE'],'Session':['Asia','London','New York','Overlap','Other'],'Timeframe':['1m','3m','5m','15m','30m','1H','4H','D','W'],'Emotion Before':['Calm','Focused','FOMO','Fear','Greedy','Neutral'],'Emotion During':['Calm','Focused','FOMO','Fear','Greedy','Neutral'],'Emotion After':['Satisfied','Neutral','Frustrated','Angry','Confident']}[key]
                    w=ttk.Combobox(box,textvariable=v,values=vals,state='readonly',justify='right')
                elif key in ('Lesson','Notes','Market Structure','Liquidity','Entry Model','Setup','Mistake'):
                    w=tk.Entry(box,textvariable=v,justify='right',bg=C['soft'],relief='flat',font=('Segoe UI',9))
                else:w=tk.Entry(box,textvariable=v,justify='right',bg=C['soft'],relief='flat',font=('Segoe UI',9))
                widgets[key]=w; w.grid(row=rr,column=0,padx=7,pady=5,sticky='ew'); box.columnconfigure(0,weight=1)
            return box
        for t,f in sections:section(left,t,f)
        for t,f in sections2:section(right,t,f)
        shot=widgets['Screenshot'];
        def browse():
            src=filedialog.askopenfilename(title='انتخاب اسکرین‌شات',filetypes=[('Images','*.png *.jpg *.jpeg *.webp *.bmp'),('All files','*.*')],parent=dlg)
            if src: vars['Screenshot'].set(src)
        self.btn(right,'انتخاب فایل اسکرین‌شات',browse).pack_forget()
        # add screenshot controls under screenshot entry's parent
        p=shot.master; controls=tk.Frame(p,bg=C['panel']); controls.grid(row=2,column=0,columnspan=2,sticky='ew',padx=7,pady=(0,8)); self.btn(controls,'انتخاب تصویر',browse).pack(side='left'); self.btn(controls,'باز کردن پوشه',lambda:self.open_path(screenshot_folder({**(row or {}),'Date':vars.get('Date',tk.StringVar()).get(),'Symbol':vars.get('Symbol',tk.StringVar()).get()}))).pack(side='left',padx=6)
        if not row:
            vars['Date'].set(date.today().isoformat()); vars['Direction'].set('LONG'); vars['Result'].set('BE')
        foot=tk.Frame(dlg,bg=C['bg']); foot.pack(fill='x',padx=24,pady=8)
        def save_trade():
            data={k:v.get().strip() for k,v in vars.items()}
            if not data['Date']: data['Date']=date.today().isoformat()
            if not data['Symbol']: return messagebox.showwarning('ورودی ناقص','Symbol را وارد کن',parent=dlg)
            src=data.get('Screenshot','');
            if src and Path(src).exists(): data['Screenshot']=attach_screenshot(data,src)
            elif row: data['Screenshot']=row.get('Screenshot','')
            for k in FIELDS:data.setdefault(k,'')
            if row is not None: DB['journals'][self.market][index]=data
            else: DB['journals'][self.market].append(data)
            save(); dlg.destroy(); self.show('journal')
        self.btn(foot,'ذخیره معامله',save_trade,True).pack(side='right',padx=5); self.btn(foot,'انصراف',dlg.destroy).pack(side='right',padx=5)
    def open_screenshot_root(self): self.open_path(SCREENSHOTS)
    def open_path(self,p):
        p=Path(p); p.mkdir(parents=True,exist_ok=True)
        try:
            if sys.platform.startswith('win'): os.startfile(str(p))
            elif sys.platform=='darwin': os.system(f'open "{p}"')
            else: os.system(f'xdg-open "{p}"')
        except Exception as e: messagebox.showerror('خطا',str(e))
    def export_journal(self):
        rows=DB['journals'][self.market]
        if not rows:return messagebox.showinfo('ژورنال خالی','معامله‌ای برای خروجی وجود ندارد')
        target=filedialog.asksaveasfilename(title='ذخیره CSV',defaultextension='.csv',initialfile=f'{self.market}_Journal_{date.today().isoformat()}.csv',filetypes=[('CSV','*.csv')])
        if not target:return
        with open(target,'w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
        messagebox.showinfo('انجام شد','خروجی CSV ذخیره شد')
    def plan(self):
        self.heading('Trading Plan','قوانین خودت را بنویس؛ این اطلاعات در data.json ذخیره می‌شوند')
        wrap=tk.Frame(self.content,bg=C['bg']); wrap.pack(fill='both',expand=True)
        left=self.card(wrap); left.pack(side='left',fill='both',expand=True,padx=6); right=self.card(wrap); right.pack(side='left',fill='both',expand=True,padx=6)
        for i,k in enumerate(PLAN):
            p=left if i<len(PLAN)//2 else right; tk.Label(p,text=k,bg=C['panel'],fg=C['muted']).pack(anchor='e',padx=14,pady=(9,2)); v=tk.StringVar(value=DB['plan'].get(k,'')); e=tk.Entry(p,textvariable=v,justify='right',bg=C['soft'],relief='flat'); e.pack(fill='x',padx=14,pady=(0,8)); e.bind('<FocusOut>',lambda ev,key=k,var=v:self.plan_save(key,var))
    def plan_save(self,k,v): DB['plan'][k]=v.get(); save()
    def check(self):
        self.heading('Checklist','قبل از ورود، ده شرط اصلی را کنترل کن')
        box=self.card(self.content); box.pack(fill='x',pady=12)
        for k in CHECK:
            v=tk.BooleanVar(value=bool(DB['check'].get(k))); tk.Checkbutton(box,text=k,variable=v,command=lambda key=k,var=v:self.check_save(key,var),bg=C['panel'],fg=C['text'],selectcolor=C['soft'],anchor='e',font=('Segoe UI',10)).pack(fill='x',padx=20,pady=7)
    def check_save(self,k,v):DB['check'][k]=bool(v.get());save()
    def settings(self):
        self.heading('تنظیمات','اطلاعات پایه و محل ذخیره داده‌ها')
        box=self.card(self.content); box.pack(fill='x',pady=15)
        profile=DB['profile']
        for i,k in enumerate(['name','timezone','account_currency','starting_balance']):
            tk.Label(box,text=k,bg=C['panel'],fg=C['muted']).grid(row=i,column=1,padx=12,pady=10,sticky='e'); v=tk.StringVar(value=profile.get(k,'')); tk.Entry(box,textvariable=v,justify='right',bg=C['soft'],relief='flat').grid(row=i,column=0,padx=12,pady=10,sticky='ew'); v.trace_add('write',lambda *_args,key=k,var=v:self.profile_save(key,var))
        box.columnconfigure(0,weight=1); tk.Label(box,text=f'Data: {DATA}\nScreenshots: {SCREENSHOTS}',bg=C['panel'],fg=C['muted'],justify='left').grid(row=5,column=0,columnspan=2,padx=12,pady=20,sticky='w')
    def profile_save(self,k,v):DB['profile'][k]=v.get();save()

if __name__=='__main__':
    App().mainloop()
