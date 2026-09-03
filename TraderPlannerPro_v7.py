# Trader Planner Pro V7 — verified daily planner + professional two-column journal
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, timedelta, datetime
from pathlib import Path
import json, csv, shutil, re, os, sys

APP = 'Trader Planner Pro'
VERSION = '7.0.1'
ROOT = Path.home() / 'TraderPlannerPro'
DATA = ROOT / 'data.json'
SCREENSHOTS = ROOT / 'Screenshots'

TASKS = [
    ('07:00','بیداری + آب + نور صبح','سلامت'),('07:15','صبحانه','غذا'),
    ('07:45','ورزش / پیاده‌روی صبح 30–45 دقیقه','ورزش'),('08:35','دوش + آماده‌سازی میز','روتین'),
    ('09:00','MARK UP — ساختار، روند، نقدینگی و نواحی','MARK UP'),('10:45','استراحت 15 دقیقه','استراحت'),
    ('11:00','MARK UP — سناریوی A/B و نقاط ابطال','MARK UP'),('12:30','ثبت سناریو + بررسی خبرها','تحلیل'),
    ('13:00','پایان MARK UP + بستن چارت','پایان'),('13:15','ناهار','غذا'),('14:00','استراحت / چرت کوتاه','ریکاوری'),
    ('14:30','مرور پلن + آماده‌سازی سشن','آماده‌سازی'),('15:30','TRADING — فقط ستاپ‌های مجاز','TRADING'),
    ('17:00','استراحت 10 دقیقه‌ای','کنترل'),('17:10','TRADING — ادامه سشن','TRADING'),('19:00','پایان قطعی ترید','پایان'),
    ('19:15','شام','غذا'),('19:45','ورزش / پیاده‌روی عصر 30 دقیقه','ورزش'),('20:30','تفریح بدون چارت','تفریح'),
    ('21:00','ژورنال + اسکرین‌شات + درس روز','ژورنال'),('21:40','مطالعه / بک‌تست سبک','یادگیری'),
    ('22:30','خاموشی صفحه‌نمایش','خواب'),('23:30','خواب','خواب')]
PLAN = ['بازارهای مجاز','تایم‌فریم‌های اصلی','ستاپ‌های مجاز','شرایط ورود','شرایط عدم ورود','حداکثر ریسک هر معامله (%)','حداکثر ضرر روزانه (%)','حداکثر معاملات روزانه','قانون خروج','قانون توقف بعد از باخت','قوانین روانشناسی','اهداف ماهانه']
CHECK = ['جهت و ساختار بازار مشخص است','ناحیه ورود معتبر و تازه است','ستاپ مطابق Trading Plan است','ریسک و حجم محاسبه شده','حد ضرر قبل از ورود مشخص است','R:R قابل قبول است','خبر مهم بررسی شده است','حالت روانی مناسب است','FOMO / Revenge ندارم','بعد از ورود قانون را تغییر نمی‌دهم']
FIELDS = ['Date','Symbol','Direction','Session','Timeframe','Entry','Stop Loss','Take Profit','Position Size','Risk %','Risk $','R:R','Setup','Market Structure','Liquidity','Entry Model','Emotion Before','Emotion During','Emotion After','Mistake','Result','Result (R)','P&L','Lesson','Notes','Screenshot']

C = {'bg':'#F6F3ED','panel':'#FFFFFF','soft':'#EEF6F5','text':'#203040','muted':'#70808A','accent':'#29B69B','line':'#D8E2E3','danger':'#C95757'}

def empty_db():
    today = date.today()
    tasks = {}
    for offset in range(-30, 180):
        day = (today + timedelta(days=offset)).isoformat()
        tasks[day] = [{'id': f'{day}-{i}', 'time': t, 'title': title, 'cat': cat, 'done': False} for i,(t,title,cat) in enumerate(TASKS)]
    return {'version': 7, 'market': 'Crypto', 'tasks': tasks, 'journals': {'Forex': [], 'Crypto': []},
            'plan': {x:'' for x in PLAN}, 'check': {x:False for x in CHECK},
            'profile': {'name':'','timezone':'','account_currency':'USD','starting_balance':''}}

def load_db(path=DATA):
    db = empty_db()
    try:
        old = json.loads(Path(path).read_text(encoding='utf-8'))
        if isinstance(old, dict):
            for key, value in old.items():
                if isinstance(value, dict) and isinstance(db.get(key), dict): db[key].update(value)
                else: db[key] = value
    except (OSError, ValueError, TypeError):
        pass
    db.setdefault('journals', {'Forex': [], 'Crypto': []})
    db['journals'].setdefault('Forex', []); db['journals'].setdefault('Crypto', [])
    db.setdefault('tasks', {}); db.setdefault('plan', {}); db.setdefault('check', {}); db.setdefault('profile', {})
    db['version'] = 7
    return db

DB = load_db()

def save_db(path=DATA):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(DB, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, path)

def safe(value):
    return re.sub(r'[^A-Za-z0-9._-]+', '_', str(value)).strip('_') or 'Unknown'

def screenshot_folder(row, root=SCREENSHOTS, market=None):
    row = row or {}
    day = safe(row.get('Date') or date.today().isoformat())
    market = safe(market or DB.get('market', 'Crypto'))
    symbol = safe(row.get('Symbol') or 'Unknown')
    folder = Path(root) / day / market / symbol
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def attach_screenshot(row, source, root=SCREENSHOTS, market=None):
    source = Path(source)
    if not source.is_file(): return ''
    folder = screenshot_folder(row, root, market)
    stamp = datetime.now().strftime('%H%M%S')
    ext = source.suffix.lower() or '.png'
    target = folder / f"{safe(row.get('Date'))}_{safe(row.get('Symbol'))}_{safe(row.get('Direction',''))}_{stamp}{ext}"
    shutil.copy2(source, target)
    return str(target)

def toggle_task(db, day, index):
    items = db.setdefault('tasks', {}).setdefault(day, [])
    if not 0 <= index < len(items): raise IndexError(index)
    items[index]['done'] = not bool(items[index].get('done'))
    return items[index]['done']

def upsert_trade(db, market, row, index=None):
    row = {key: str(row.get(key, '')) for key in FIELDS}
    row['Date'] = row['Date'] or date.today().isoformat()
    if not row['Symbol'].strip(): raise ValueError('Symbol is required')
    db.setdefault('journals', {}).setdefault(market, [])
    if index is None: db['journals'][market].append(row); return len(db['journals'][market]) - 1
    if not 0 <= index < len(db['journals'][market]): raise IndexError(index)
    db['journals'][market][index] = row
    return index

def delete_trade(db, market, index):
    rows = db.setdefault('journals', {}).setdefault(market, [])
    if not 0 <= index < len(rows): raise IndexError(index)
    return rows.pop(index)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f'{APP} V7'); self.geometry('1500x930'); self.minsize(1120,720); self.configure(bg=C['bg'])
        self.market = DB.get('market','Crypto'); self.day = date.today().isoformat(); self.cur = 'home'; self.menu_open = False
        self.style = ttk.Style(self); self.style.theme_use('clam')
        self.style.configure('Treeview', background=C['panel'], fieldbackground=C['panel'], foreground=C['text'], rowheight=38, borderwidth=0)
        self.style.map('Treeview', background=[('selected',C['soft'])], foreground=[('selected',C['text'])])
        self.style.configure('TCombobox', fieldbackground=C['soft'], background=C['soft'])
        self.build_shell(); self.show('home'); self.after(500, self.clock)

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
    def go(self,key):
        if self.menu_open: self.toggle_menu()
        self.show(key)
    def show(self,key):
        self.cur=key
        for widget in self.content.winfo_children(): widget.destroy()
        getattr(self,key)()
    def clock(self): self.clock_label.config(text=datetime.now().strftime('%Y-%m-%d  |  %H:%M:%S')); self.after(500,self.clock)
    def heading(self,title,sub=''):
        tk.Label(self.content,text=title,bg=C['bg'],fg=C['text'],font=('Segoe UI',22,'bold')).pack(anchor='e',pady=(8,2))
        if sub: tk.Label(self.content,text=sub,bg=C['bg'],fg=C['muted'],font=('Segoe UI',10)).pack(anchor='e',pady=(0,10))
    def card(self,parent): return tk.Frame(parent,bg=C['panel'],highlightbackground=C['line'],highlightthickness=1)
    def btn(self,parent,text,cmd,primary=False): return tk.Button(parent,text=text,command=cmd,bg=C['accent'] if primary else C['soft'],fg=C['text'],relief='flat',font=('Segoe UI',10,'bold'),padx=13,pady=8)
    def change_market(self):
        self.market='Forex' if self.market=='Crypto' else 'Crypto'; DB['market']=self.market; save_db(); self.market_btn.config(text=self.market); self.show(self.cur)

    def home(self):
        self.heading('داشبورد','نمای سریع عملکرد، نظم روزانه و معاملات اخیر')
        rows=DB['journals'][self.market]; results=[]
        for row in rows:
            try: results.append(float(str(row.get('Result (R)','0')).replace(',','')))
            except ValueError: pass
        tasks=DB['tasks'].setdefault(self.day,[]); done=sum(bool(x.get('done')) for x in tasks)
        cards=[('معاملات',len(rows)),('Win Rate',f'{sum(x>0 for x in results)/len(results)*100:.1f}%' if results else '0%'),('Net R',f'{sum(results):.2f} R'),('پیشرفت امروز',f'{done/len(tasks)*100:.0f}%' if tasks else '0%'),('بازار فعال',self.market)]
        row=tk.Frame(self.content,bg=C['bg']); row.pack(fill='x',pady=8)
        for title,value in cards:
            box=self.card(row); box.pack(side='left',fill='both',expand=True,padx=4); tk.Label(box,text=title,bg=C['panel'],fg=C['muted']).pack(anchor='w',padx=15,pady=(11,2)); tk.Label(box,text=value,bg=C['panel'],fg=C['text'],font=('Segoe UI',17,'bold')).pack(anchor='w',padx=15,pady=(0,11))
        lower=tk.Frame(self.content,bg=C['bg']); lower.pack(fill='both',expand=True,pady=14)
        left=self.card(lower); left.pack(side='left',fill='both',expand=True,padx=4); right=self.card(lower); right.pack(side='left',fill='both',expand=True,padx=4)
        tk.Label(left,text='آخرین معاملات',bg=C['panel'],fg=C['text'],font=('Segoe UI',13,'bold')).pack(anchor='e',padx=16,pady=12)
        for row_data in rows[-6:][::-1]:
            line=tk.Frame(left,bg=C['panel']); line.pack(fill='x',padx=12,pady=4); tk.Label(line,text=f"{row_data.get('Symbol','—')}  {row_data.get('Direction','')}",bg=C['panel'],fg=C['text'],font=('Segoe UI',10,'bold')).pack(side='left'); tk.Label(line,text=f"{row_data.get('Result (R)','0')}R   {row_data.get('P&L','0')}",bg=C['panel'],fg=C['accent'] if self.result_num(row_data)>0 else C['danger']).pack(side='right')
        tk.Label(right,text='کنترل امروز',bg=C['panel'],fg=C['text'],font=('Segoe UI',13,'bold')).pack(anchor='e',padx=16,pady=12)
        self.btn(right,'باز کردن برنامه روزانه',lambda:self.show('daily'),True).pack(anchor='e',padx=16,pady=8)
        self.btn(right,'＋ ثبت معامله جدید',self.add_trade,True).pack(anchor='e',padx=16,pady=8)
        self.btn(right,'مشاهده ژورنال',lambda:self.show('journal')).pack(anchor='e',padx=16,pady=8)
    def result_num(self,row):
        try:return float(str(row.get('Result (R)','0')).replace(',',''))
        except ValueError:return 0.0

    def daily(self):
        self.heading('برنامه روزانه','تیک، ویرایش، حذف و افزودن فعالیت؛ هر تغییر فوراً ذخیره می‌شود')
        nav=tk.Frame(self.content,bg=C['bg']); nav.pack(fill='x',pady=4)
        self.btn(nav,'روز قبل',lambda:self.shift_day(-1)).pack(side='left'); tk.Label(nav,text=self.day,bg=C['bg'],fg=C['text'],font=('Segoe UI',12,'bold')).pack(side='left',padx=16); self.btn(nav,'روز بعد',lambda:self.shift_day(1)).pack(side='left')
        self.btn(nav,'＋ فعالیت جدید',self.add_task,True).pack(side='right',padx=4); self.btn(nav,'ویرایش انتخاب‌شده',self.edit_task).pack(side='right',padx=4); self.btn(nav,'حذف انتخاب‌شده',self.delete_task).pack(side='right',padx=4)
        tasks=DB['tasks'].setdefault(self.day,[]); done=sum(bool(x.get('done')) for x in tasks)
        tk.Label(nav,text=f'{done}/{len(tasks)} انجام شد  |  {done/len(tasks)*100:.0f}%',bg=C['bg'],fg=C['accent'],font=('Segoe UI',11,'bold')).pack(side='right',padx=15)
        wrap=tk.Frame(self.content,bg=C['bg']); wrap.pack(fill='both',expand=True,pady=10)
        cols=('done','time','title','cat'); tree=ttk.Treeview(wrap,columns=cols,show='headings',selectmode='browse'); self.task_tree=tree
        for col,text in [('done','✓'),('time','زمان'),('title','فعالیت'),('cat','دسته')]: tree.heading(col,text=text)
        tree.column('done',width=55,anchor='center'); tree.column('time',width=100,anchor='center'); tree.column('cat',width=150,anchor='e'); tree.column('title',anchor='e')
        for i,item in enumerate(tasks): tree.insert('', 'end', iid=str(i), values=('☑' if item.get('done') else '☐',item.get('time',''),item.get('title',''),item.get('cat','')))
        tree.pack(side='left',fill='both',expand=True); sb=ttk.Scrollbar(wrap,orient='vertical',command=tree.yview); sb.pack(side='right',fill='y'); tree.configure(yscrollcommand=sb.set)
        tree.bind('<Double-1>',lambda e:self.toggle_selected_task())
        tk.Label(self.content,text='برای تیک‌زدن دوبار کلیک کن؛ برای ویرایش یا حذف، ردیف را انتخاب کن.',bg=C['bg'],fg=C['muted']).pack(anchor='e')
    def toggle_selected_task(self):
        sel=self.task_tree.selection()
        if not sel:return
        toggle_task(DB,self.day,int(sel[0])); save_db(); self.show('daily')
    def shift_day(self,delta):
        self.day=(date.fromisoformat(self.day)+timedelta(days=delta)).isoformat(); DB['tasks'].setdefault(self.day,[])
        if not DB['tasks'][self.day]: DB['tasks'][self.day]=[{'id':f'{self.day}-{i}','time':t,'title':title,'cat':cat,'done':False} for i,(t,title,cat) in enumerate(TASKS)]
        save_db(); self.show('daily')
    def task_dialog(self,item=None):
        dlg=tk.Toplevel(self); dlg.title('ویرایش فعالیت' if item else 'فعالیت جدید'); dlg.geometry('540x320'); dlg.configure(bg=C['bg']); dlg.transient(self); dlg.grab_set()
        vars={}; fields=[('زمان','time'),('عنوان','title'),('دسته','cat')]
        for row,(label,key) in enumerate(fields):
            tk.Label(dlg,text=label,bg=C['bg'],fg=C['text']).grid(row=row,column=1,padx=12,pady=10,sticky='e'); value=tk.StringVar(value=(item or {}).get(key,'')); vars[key]=value; tk.Entry(dlg,textvariable=value,justify='right',font=('Segoe UI',11),bg=C['panel'],relief='flat').grid(row=row,column=0,padx=12,pady=10,sticky='ew')
        dlg.columnconfigure(0,weight=1)
        def submit():
            if not vars['title'].get().strip(): messagebox.showwarning('ورودی ناقص','عنوان فعالیت را وارد کن',parent=dlg); return
            if item is not None: item.update({key:value.get().strip() for key,value in vars.items()})
            else: DB['tasks'].setdefault(self.day,[]).append({'id':f'{self.day}-{datetime.now().timestamp()}','time':vars['time'].get().strip(),'title':vars['title'].get().strip(),'cat':vars['cat'].get().strip(),'done':False})
            save_db(); dlg.destroy(); self.show('daily')
        self.btn(dlg,'ذخیره',submit,True).grid(row=4,column=0,padx=12,pady=15,sticky='e'); self.btn(dlg,'انصراف',dlg.destroy).grid(row=4,column=1,padx=12,pady=15)
    def add_task(self): self.task_dialog()
    def edit_task(self):
        sel=self.task_tree.selection()
        if not sel:return messagebox.showinfo('انتخاب فعالیت','ابتدا یک فعالیت را انتخاب کن')
        self.task_dialog(DB['tasks'][self.day][int(sel[0])])
    def delete_task(self):
        sel=self.task_tree.selection()
        if not sel:return messagebox.showinfo('انتخاب فعالیت','ابتدا یک فعالیت را انتخاب کن')
        index=int(sel[0]); item=DB['tasks'][self.day][index]
        if messagebox.askyesno('حذف فعالیت',f"«{item.get('title','')}» حذف شود؟",parent=self): DB['tasks'][self.day].pop(index); save_db(); self.show('daily')

    def journal(self):
        self.heading(f'Journal — {self.market}','ثبت سریع + ویرایش کامل + حذف + جستجو + مدیریت Screenshot')
        bar=tk.Frame(self.content,bg=C['bg']); bar.pack(fill='x',pady=3)
        for text,cmd,primary in [('＋ ثبت معامله',self.add_trade,True),('ویرایش',self.edit_trade,False),('حذف',self.delete_trade,False),('باز کردن پوشه تصاویر',self.open_screenshot_root,False),('خروجی CSV',self.export_journal,False)]: self.btn(bar,text,cmd,primary).pack(side='left',padx=3)
        filter_var=tk.StringVar(); tk.Label(bar,text='جستجو:',bg=C['bg'],fg=C['muted']).pack(side='right'); entry=tk.Entry(bar,textvariable=filter_var,width=30,justify='right',relief='flat'); entry.pack(side='right',padx=6); entry.bind('<KeyRelease>',lambda e:self.fill_journal_tree(filter_var.get()))
        cols=('date','symbol','direction','session','tf','entry','sl','tp','r','pnl','setup','result'); self.jtree=ttk.Treeview(self.content,columns=cols,show='headings',selectmode='browse')
        heads={'date':'تاریخ','symbol':'نماد','direction':'جهت','session':'سشن','tf':'TF','entry':'Entry','sl':'SL','tp':'TP','r':'R','pnl':'P&L','setup':'Setup','result':'نتیجه'}
        for col in cols:self.jtree.heading(col,text=heads[col]); self.jtree.column(col,width=95,anchor='center')
        self.jtree.column('symbol',width=115); self.jtree.column('setup',width=150); self.jtree.pack(fill='both',expand=True,pady=10); self.jtree.bind('<Double-1>',lambda e:self.edit_trade()); self.fill_journal_tree()
    def fill_journal_tree(self,query=''):
        for item in self.jtree.get_children(): self.jtree.delete(item)
        q=query.strip().lower(); rows=DB['journals'][self.market]
        for index,row in enumerate(rows):
            if q and q not in ' '.join(str(row.get(k,'')) for k in FIELDS).lower(): continue
            self.jtree.insert('', 'end', iid=str(index), values=(row.get('Date',''),row.get('Symbol',''),row.get('Direction',''),row.get('Session',''),row.get('Timeframe',''),row.get('Entry',''),row.get('Stop Loss',''),row.get('Take Profit',''),row.get('Result (R)',''),row.get('P&L',''),row.get('Setup',''),row.get('Result','')))
    def edit_trade(self):
        sel=self.jtree.selection()
        if not sel:return messagebox.showinfo('انتخاب معامله','ابتدا یک معامله را انتخاب کن')
        self.trade_dialog(DB['journals'][self.market][int(sel[0])],int(sel[0]))
    def delete_trade(self):
        sel=self.jtree.selection()
        if not sel:return messagebox.showinfo('انتخاب معامله','ابتدا یک معامله را انتخاب کن')
        index=int(sel[0]); row=DB['journals'][self.market][index]
        if messagebox.askyesno('حذف معامله',f"معامله {row.get('Symbol','')} در تاریخ {row.get('Date','')} حذف شود؟",parent=self): delete_trade(DB,self.market,index); save_db(); self.show('journal')
    def add_trade(self): self.trade_dialog()

    def trade_dialog(self,row=None,index=None):
        dlg=tk.Toplevel(self); dlg.title(('ویرایش' if row else 'ثبت')+f' معامله — {self.market}'); dlg.geometry('1160x780'); dlg.minsize(1000,700); dlg.configure(bg=C['bg']); dlg.transient(self); dlg.grab_set()
        outer=tk.Frame(dlg,bg=C['bg']); outer.pack(fill='both',expand=True,padx=18,pady=16)
        left=self.card(outer); right=self.card(outer); left.pack(side='left',fill='both',expand=True,padx=6); right.pack(side='left',fill='both',expand=True,padx=6)
        vars={}; widgets={}
        groups_left=[('اطلاعات معامله',['Date','Symbol','Direction','Session','Timeframe']),('قیمت و ریسک',['Entry','Stop Loss','Take Profit','Position Size','Risk %','Risk $','R:R']),('تحلیل',['Setup','Market Structure','Liquidity','Entry Model'])]
        groups_right=[('روانشناسی',['Emotion Before','Emotion During','Emotion After','Mistake']),('نتیجه',['Result','Result (R)','P&L','Lesson','Notes']),('اسکرین‌شات',['Screenshot'])]
        def section(parent,title,fields):
            box=tk.Frame(parent,bg=C['panel']); box.pack(fill='x',padx=14,pady=8); tk.Label(box,text=title,bg=C['panel'],fg=C['accent'],font=('Segoe UI',12,'bold')).grid(row=0,column=0,columnspan=2,sticky='e',pady=(10,6),padx=8)
            for r,key in enumerate(fields,1):
                tk.Label(box,text=key,bg=C['panel'],fg=C['muted'],font=('Segoe UI',9)).grid(row=r,column=1,padx=7,pady=5,sticky='e')
                value=tk.StringVar(value=str((row or {}).get(key,''))); vars[key]=value
                if key in ('Direction','Result','Session','Timeframe','Emotion Before','Emotion During','Emotion After'):
                    options={'Direction':['LONG','SHORT'],'Result':['WIN','LOSS','BE'],'Session':['Asia','London','New York','Overlap','Other'],'Timeframe':['1m','3m','5m','15m','30m','1H','4H','D','W'],'Emotion Before':['Calm','Focused','FOMO','Fear','Greedy','Neutral'],'Emotion During':['Calm','Focused','FOMO','Fear','Greedy','Neutral'],'Emotion After':['Satisfied','Neutral','Frustrated','Angry','Confident']}[key]
                    widget=ttk.Combobox(box,textvariable=value,values=options,state='readonly',justify='right')
                else: widget=tk.Entry(box,textvariable=value,justify='right',bg=C['soft'],relief='flat',font=('Segoe UI',9))
                widgets[key]=widget; widget.grid(row=r,column=0,padx=7,pady=5,sticky='ew'); box.columnconfigure(0,weight=1)
            return box
        for title,fields in groups_left: section(left,title,fields)
        for title,fields in groups_right: section(right,title,fields)
        if not row:
            vars['Date'].set(date.today().isoformat()); vars['Direction'].set('LONG'); vars['Result'].set('BE')
        shot=widgets['Screenshot']
        def browse():
            source=filedialog.askopenfilename(title='انتخاب اسکرین‌شات',filetypes=[('Images','*.png *.jpg *.jpeg *.webp *.bmp'),('All files','*.*')],parent=dlg)
            if source: vars['Screenshot'].set(source)
        controls=tk.Frame(shot.master,bg=C['panel']); controls.grid(row=2,column=0,columnspan=2,sticky='ew',padx=7,pady=(0,8)); self.btn(controls,'انتخاب تصویر',browse).pack(side='left'); self.btn(controls,'باز کردن پوشه معامله',lambda:self.open_path(screenshot_folder({'Date':vars['Date'].get(),'Symbol':vars['Symbol'].get()}))).pack(side='left',padx=6)
        footer=tk.Frame(dlg,bg=C['bg']); footer.pack(fill='x',padx=24,pady=8)
        def submit():
            data={key:value.get().strip() for key,value in vars.items()}
            data['Date']=data.get('Date') or date.today().isoformat()
            if not data.get('Symbol'): return messagebox.showwarning('ورودی ناقص','Symbol را وارد کن',parent=dlg)
            source=data.get('Screenshot','')
            if source and Path(source).is_file(): data['Screenshot']=attach_screenshot(data,source,market=self.market)
            elif row is not None: data['Screenshot']=row.get('Screenshot','')
            for key in FIELDS: data.setdefault(key,'')
            upsert_trade(DB,self.market,data,index); save_db(); dlg.destroy(); self.show('journal')
        self.btn(footer,'ذخیره معامله',submit,True).pack(side='right',padx=5); self.btn(footer,'انصراف',dlg.destroy).pack(side='right',padx=5)
    def open_screenshot_root(self): self.open_path(SCREENSHOTS)
    def open_path(self,path):
        path=Path(path); path.mkdir(parents=True,exist_ok=True)
        try:
            if sys.platform.startswith('win'): os.startfile(str(path))
            elif sys.platform=='darwin': os.system(f'open "{path}"')
            else: os.system(f'xdg-open "{path}"')
        except OSError as exc: messagebox.showerror('خطا',str(exc),parent=self)
    def export_journal(self):
        rows=DB['journals'][self.market]
        if not rows:return messagebox.showinfo('ژورنال خالی','معامله‌ای برای خروجی وجود ندارد',parent=self)
        target=filedialog.asksaveasfilename(title='ذخیره CSV',defaultextension='.csv',initialfile=f'{self.market}_Journal_{date.today().isoformat()}.csv',filetypes=[('CSV','*.csv')])
        if not target:return
        with open(target,'w',newline='',encoding='utf-8-sig') as handle: csv.DictWriter(handle,fieldnames=FIELDS).writerows(rows)
        messagebox.showinfo('انجام شد','خروجی CSV ذخیره شد',parent=self)

    def plan(self):
        self.heading('Trading Plan','قوانین خودت را بنویس؛ هر تغییر در لحظه ذخیره می‌شود')
        wrap=tk.Frame(self.content,bg=C['bg']); wrap.pack(fill='both',expand=True); left=self.card(wrap); right=self.card(wrap); left.pack(side='left',fill='both',expand=True,padx=6); right.pack(side='left',fill='both',expand=True,padx=6)
        for i,key in enumerate(PLAN):
            parent=left if i < len(PLAN)//2 else right; tk.Label(parent,text=key,bg=C['panel'],fg=C['muted']).pack(anchor='e',padx=14,pady=(9,2)); value=tk.StringVar(value=DB['plan'].get(key,'')); entry=tk.Entry(parent,textvariable=value,justify='right',bg=C['soft'],relief='flat'); entry.pack(fill='x',padx=14,pady=(0,8)); entry.bind('<FocusOut>',lambda event,k=key,v=value:self.plan_save(k,v))
    def plan_save(self,key,value): DB['plan'][key]=value.get(); save_db()
    def check(self):
        self.heading('Checklist','قبل از ورود، ده شرط اصلی را کنترل کن')
        box=self.card(self.content); box.pack(fill='x',pady=12)
        for key in CHECK:
            value=tk.BooleanVar(value=bool(DB['check'].get(key))); tk.Checkbutton(box,text=key,variable=value,command=lambda k=key,v=value:self.check_save(k,v),bg=C['panel'],fg=C['text'],selectcolor=C['soft'],anchor='e',font=('Segoe UI',10)).pack(fill='x',padx=20,pady=7)
    def check_save(self,key,value): DB['check'][key]=bool(value.get()); save_db()
    def settings(self):
        self.heading('تنظیمات','اطلاعات پایه و محل ذخیره داده‌ها')
        box=self.card(self.content); box.pack(fill='x',pady=15); profile=DB['profile']
        for i,key in enumerate(['name','timezone','account_currency','starting_balance']):
            tk.Label(box,text=key,bg=C['panel'],fg=C['muted']).grid(row=i,column=1,padx=12,pady=10,sticky='e'); value=tk.StringVar(value=profile.get(key,'')); tk.Entry(box,textvariable=value,justify='right',bg=C['soft'],relief='flat').grid(row=i,column=0,padx=12,pady=10,sticky='ew'); value.trace_add('write',lambda *_args,k=key,v=value:self.profile_save(k,v))
        box.columnconfigure(0,weight=1); tk.Label(box,text=f'Data: {DATA}\nScreenshots: {SCREENSHOTS}',bg=C['panel'],fg=C['muted'],justify='left').grid(row=5,column=0,columnspan=2,padx=12,pady=20,sticky='w')
    def profile_save(self,key,value): DB['profile'][key]=value.get(); save_db()

if __name__=='__main__': App().mainloop()
