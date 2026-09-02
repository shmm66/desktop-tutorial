# Trader Planner Pro - Windows 11 desktop app
# Built with Python/Tkinter. Offline-first; user-editable trading plan/checklists/journals.
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date, timedelta, datetime
import json, os, math

APP_DIR=os.path.join(os.path.expanduser('~'),'TraderPlannerPro')
os.makedirs(APP_DIR,exist_ok=True)
DB=os.path.join(APP_DIR,'data.json')
START=date(2026,9,3)
DAYS=[START+timedelta(days=i) for i in range(30)]
FA_DAYS=['دوشنبه','سه‌شنبه','چهارشنبه','پنجشنبه','جمعه','شنبه','یکشنبه']

DEFAULT_TASKS=[
('07:00','بیداری + آب + نور صبح','سلامت'),('07:15','صبحانه','غذا'),('07:45','ورزش 30–45 دقیقه','ورزش'),
('08:35','دوش + آماده‌سازی میز','准备'),('09:00','MARK UP — ساختار، روند، نقدینگی و نواحی مهم','MARK UP'),
('11:00','استراحت 15 دقیقه','استراحت'),('11:15','MARK UP — سناریوی A/B و نقاط ابطال','MARK UP'),('13:00','پایان مارک‌آپ + بستن چارت','پایان'),
('13:15','ناهار','غذا'),('14:00','استراحت / چرت کوتاه','ریکاوری'),('14:30','مرور پلن + آماده‌سازی سشن','آماده‌سازی'),
('15:30','TRADING — فقط ستاپ‌های مجاز','TRADING'),('17:15','استراحت 10 دقیقه‌ای','کنترل'),('17:25','TRADING — ادامه سشن','TRADING'),
('19:00','پایان قطعی ترید + خروج از پلتفرم','پایان'),('19:15','شام','غذا'),('20:00','تفریح بدون چارت','تفریح'),
('21:15','ژورنال: اسکرین‌شات، R، اشتباهات و درس‌ها','ژورنال'),('21:45','مطالعه / بک‌تست سبک','یادگیری'),('22:30','خاموشی صفحه‌نمایش + آماده خواب','خواب'),('23:00','خواب','خواب')]

PLAN_FIELDS=['بازارهای مجاز','تایم‌فریم‌ها','ستاپ‌های مجاز','شرایط ورود','شرایط عدم ورود','حداکثر ریسک هر معامله (%)','حداکثر ضرر روزانه (%)','حداکثر معاملات روزانه','قانون خروج','قانون توقف بعد از باخت','قوانین روانشناسی','اهداف ماهانه']
CHECKLIST=['جهت/ساختار بازار مشخص است','ناحیه ورود معتبر است','ستاپ مطابق Trading Plan است','ریسک معامله محاسبه شده','حد ضرر قبل از ورود مشخص است','نسبت R:R قابل قبول است','خبر مهم نزدیک نیست / اثر آن بررسی شده','حالت روانی مناسب است','ورود از روی FOMO یا Revenge نیست','بعد از ورود حد ضرر دستکاری نمی‌شود']


def default_db():
    return {'theme':'dark','tasks':{d.isoformat():[{'time':t,'title':x,'cat':c,'done':False} for t,x,c in DEFAULT_TASKS] for d in DAYS},
            'plan':{f:'' for f in PLAN_FIELDS},'checklist':{x:False for x in CHECKLIST},'journals':{'Forex':[],'Crypto':[]},'alarms':{},'selected_market':'Forex'}

def load():
    if os.path.exists(DB):
        try:
            with open(DB,'r',encoding='utf-8') as f: db=json.load(f)
            base=default_db(); base.update(db); base['tasks'].update(db.get('tasks',{})); base['plan'].update(db.get('plan',{})); base['checklist'].update(db.get('checklist',{})); base['journals'].update(db.get('journals',{})); return base
        except Exception: pass
    return default_db()

db=load()
def save():
    with open(DB,'w',encoding='utf-8') as f: json.dump(db,f,ensure_ascii=False,indent=2)

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('TRADER PLANNER PRO'); self.geometry('1320x860'); self.minsize(1050,700)
        self.day=0; self.market=db.get('selected_market','Forex'); self.style(); self.build(); self.render(); self.after(1000,self.tick)
    def style(self):
        self.bg='#0b1020' if db.get('theme')=='dark' else '#eef2f7'; self.card='#121a2d' if db.get('theme')=='dark' else '#ffffff'; self.fg='#eef3ff' if db.get('theme')=='dark' else '#172033'; self.muted='#9aa8c7' if db.get('theme')=='dark' else '#637083'; self.input='#10192c' if db.get('theme')=='dark' else '#f5f7fa'; self.accent='#62d5b2'; self.configure(bg=self.bg)
        s=ttk.Style(self); s.theme_use('clam'); s.configure('TNotebook',background=self.bg,borderwidth=0); s.configure('TNotebook.Tab',background=self.card,foreground=self.fg,padding=(18,10)); s.map('TNotebook.Tab',background=[('selected','#1d3557')],foreground=[('selected','#ffffff')]); s.configure('Treeview',background=self.input,foreground=self.fg,fieldbackground=self.input,rowheight=40); s.map('Treeview',background=[('selected','#1d3557')]); s.configure('TCombobox',fieldbackground=self.input,background=self.input,foreground=self.fg)
    def header(self,parent):
        h=tk.Frame(parent,bg=self.bg); h.pack(fill='x'); tk.Label(h,text='TRADER PLANNER PRO',font=('Segoe UI',24,'bold'),fg=self.accent,bg=self.bg).pack(side='left',padx=25,pady=15); self.clock=tk.Label(h,fg=self.fg,bg=self.bg,font=('Segoe UI',11,'bold')); self.clock.pack(side='right',padx=25)
    def build(self):
        self.header(self); self.tabs=ttk.Notebook(self); self.tabs.pack(fill='both',expand=True,padx=14,pady=8)
        self.daily_tab=tk.Frame(self.tabs,bg=self.bg); self.plan_tab=tk.Frame(self.tabs,bg=self.bg); self.check_tab=tk.Frame(self.tabs,bg=self.bg); self.journal_tab=tk.Frame(self.tabs,bg=self.bg); self.risk_tab=tk.Frame(self.tabs,bg=self.bg); self.stats_tab=tk.Frame(self.tabs,bg=self.bg); self.settings_tab=tk.Frame(self.tabs,bg=self.bg)
        for f,n in [(self.daily_tab,'📅 برنامه روزانه'),(self.plan_tab,'📋 Trading Plan'),(self.check_tab,'✅ Checklist'),(self.journal_tab,'📓 Journal'),(self.risk_tab,'🧮 مدیریت ریسک'),(self.stats_tab,'📊 عملکرد ماهانه'),(self.settings_tab,'⚙ تنظیمات')]: self.tabs.add(f,text=n)
        self.build_daily(); self.build_plan(); self.build_check(); self.build_journal(); self.build_risk(); self.build_stats(); self.build_settings()
    def build_daily(self):
        left=tk.Frame(self.daily_tab,bg=self.card,width=260); left.pack(side='left',fill='y',padx=(0,12)); left.pack_propagate(False); tk.Label(left,text='تقویم ۳۰ روزه',bg=self.card,fg=self.fg,font=('Segoe UI',15,'bold')).pack(anchor='e',padx=16,pady=12)
        self.days=tk.Listbox(left,bg=self.input,fg=self.fg,selectbackground='#1d3557',borderwidth=0,highlightthickness=0,font=('Segoe UI',10)); self.days.pack(fill='both',expand=True,padx=12); self.days.bind('<<ListboxSelect>>',self.pick_day)
        for d in DAYS:self.days.insert('end',f'{d.isoformat()}  {FA_DAYS[d.weekday()]}')
        btn=tk.Frame(left,bg=self.card); btn.pack(fill='x',pady=10,padx=12); tk.Button(btn,text='+ افزودن',command=self.add_task,bg='#1b806a',fg='white',relief='flat').pack(fill='x',pady=3); tk.Button(btn,text='− حذف',command=self.del_task,bg='#57283a',fg='white',relief='flat').pack(fill='x',pady=3)
        main=tk.Frame(self.daily_tab,bg=self.card); main.pack(side='left',fill='both',expand=True); self.daytitle=tk.Label(main,bg=self.card,fg=self.fg,font=('Segoe UI',19,'bold')); self.daytitle.pack(anchor='e',padx=20,pady=(15,2)); self.daysub=tk.Label(main,bg=self.card,fg=self.muted); self.daysub.pack(anchor='e',padx=20,pady=(0,12))
        self.tree=ttk.Treeview(main,columns=('time','task','cat','done'),show='headings');
        for c,h,w in [('time','زمان',90),('task','فعالیت',600),('cat','دسته',120),('done','انجام',70)]:self.tree.heading(c,text=h);self.tree.column(c,width=w,anchor='e')
        self.tree.pack(fill='both',expand=True,padx=18); self.tree.bind('<Double-1>',self.toggle_task); self.tree.bind('<ButtonPress-1>',self.drag_start); self.tree.bind('<ButtonRelease-1>',self.drag_end); self.drag_i=None
        self.note=tk.Text(main,height=4,bg=self.input,fg=self.fg,insertbackground=self.fg,relief='flat'); self.note.pack(fill='x',padx=18,pady=12); self.note.bind('<KeyRelease>',lambda e:self.save_day_note())
    def build_plan(self):
        self.plan_vars={}; tk.Label(self.plan_tab,text='Trading Plan — فرم پیش‌فرض و قابل تکمیل توسط کاربر',bg=self.bg,fg=self.fg,font=('Segoe UI',18,'bold')).pack(anchor='e',padx=25,pady=18); grid=tk.Frame(self.plan_tab,bg=self.bg);grid.pack(fill='both',expand=True,padx=25)
        for i,f in enumerate(PLAN_FIELDS):
            tk.Label(grid,text=f,bg=self.bg,fg=self.fg,font=('Segoe UI',10,'bold')).grid(row=i,column=1,sticky='e',padx=10,pady=6); v=tk.Text(grid,height=2,bg=self.input,fg=self.fg,insertbackground=self.fg,relief='flat');v.grid(row=i,column=0,sticky='ew',padx=10,pady=4);v.insert('1.0',db['plan'].get(f,''));v.bind('<KeyRelease>',lambda e:self.save_plan());self.plan_vars[f]=v
        grid.columnconfigure(0,weight=1); tk.Button(self.plan_tab,text='💾 ذخیره Trading Plan',command=self.save_plan,bg='#1b806a',fg='white',relief='flat').pack(pady=12)
    def save_plan(self,e=None):
        for f,v in self.plan_vars.items():db['plan'][f]=v.get('1.0','end').strip()
        save()
    def build_check(self):
        tk.Label(self.check_tab,text='چک‌لیست ترید — قبل از هر ورود',bg=self.bg,fg=self.fg,font=('Segoe UI',18,'bold')).pack(anchor='e',padx=25,pady=18); self.check_vars=[]
        box=tk.Frame(self.check_tab,bg=self.card);box.pack(fill='x',padx=25,pady=10)
        for item in CHECKLIST:
            v=tk.BooleanVar(value=db['checklist'].get(item,False));self.check_vars.append((item,v));tk.Checkbutton(box,text=item,variable=v,command=self.save_check,bg=self.card,fg=self.fg,selectcolor=self.input,activebackground=self.card,activeforeground=self.fg,anchor='e').pack(fill='x',padx=20,pady=5)
        tk.Button(self.check_tab,text='ریست چک‌لیست',command=self.reset_check,bg='#57283a',fg='white',relief='flat').pack(pady=12)
    def save_check(self):
        db['checklist']={i:v.get() for i,v in self.check_vars};save()
    def reset_check(self):
        for _,v in self.check_vars:v.set(False)
        self.save_check()
    def build_journal(self):
        top=tk.Frame(self.journal_tab,bg=self.bg);top.pack(fill='x',padx=25,pady=16);tk.Label(top,text='Trading Journal',bg=self.bg,fg=self.fg,font=('Segoe UI',18,'bold')).pack(side='left');self.marketbox=ttk.Combobox(top,values=['Forex','Crypto'],state='readonly',width=12);self.marketbox.set(self.market);self.marketbox.pack(side='right');self.marketbox.bind('<<ComboboxSelected>>',lambda e:self.switch_market())
        form=tk.Frame(self.journal_tab,bg=self.card);form.pack(fill='x',padx=25,pady=5); self.jv={}
        fields=['Date','Symbol','Direction','Entry','Stop Loss','Take Profit','Risk %','R:R','Result (R)','P&L','Setup','Emotion','Mistake','Lesson','Screenshot/Chart link']
        for i,f in enumerate(fields):
            r=i//3;c=i%3;tk.Label(form,text=f,bg=self.card,fg=self.muted).grid(row=r*2,column=c,sticky='e',padx=10,pady=(8,0));e=tk.Entry(form,bg=self.input,fg=self.fg,insertbackground=self.fg,relief='flat');e.grid(row=r*2+1,column=c,sticky='ew',padx=10,pady=(2,8));self.jv[f]=e
        for c in range(3):form.columnconfigure(c,weight=1)
        tk.Button(self.journal_tab,text='+ ثبت معامله',command=self.add_trade,bg='#1b806a',fg='white',relief='flat').pack(pady=8);self.jtree=ttk.Treeview(self.journal_tab,columns=('date','symbol','dir','rr','r','pnl','setup'),show='headings')
        for c,h in zip(self.jtree['columns'],['Date','Symbol','Dir','R:R','R','P&L','Setup']):self.jtree.heading(c,text=h);self.jtree.column(c,width=110)
        self.jtree.pack(fill='both',expand=True,padx=25,pady=5)
    def switch_market(self):self.market=self.marketbox.get();db['selected_market']=self.market;save();self.render_journal();self.render_stats()
    def add_trade(self):
        t={k:v.get().strip() for k,v in self.jv.items()}; t['Date']=t['Date'] or date.today().isoformat(); db['journals'][self.market].append(t);save();self.render_journal();self.render_stats()
    def render_journal(self):
        if not hasattr(self,'jtree'):return
        self.jtree.delete(*self.jtree.get_children())
        for t in db['journals'].get(self.market,[]):self.jtree.insert('','end',values=(t.get('Date',''),t.get('Symbol',''),t.get('Direction',''),t.get('R:R',''),t.get('Result (R)',''),t.get('P&L',''),t.get('Setup','')))
    def build_risk(self):
        tk.Label(self.risk_tab,text='مدیریت ریسک و محاسبه حجم',bg=self.bg,fg=self.fg,font=('Segoe UI',18,'bold')).pack(anchor='e',padx=25,pady=18); box=tk.Frame(self.risk_tab,bg=self.card);box.pack(fill='x',padx=25,pady=10)
        self.rv={}; fields=['Account Balance','Risk %','Entry Price','Stop Loss Price','Pip/Point Value'];
        for i,f in enumerate(fields):tk.Label(box,text=f,bg=self.card,fg=self.fg).grid(row=i,column=1,padx=15,pady=10,sticky='e');e=tk.Entry(box,bg=self.input,fg=self.fg,relief='flat');e.grid(row=i,column=0,padx=15,pady=10,sticky='ew');self.rv[f]=e
        box.columnconfigure(0,weight=1);tk.Button(box,text='محاسبه',command=self.calc_risk,bg='#1b806a',fg='white',relief='flat').grid(row=5,column=0,pady=12);self.rout=tk.Label(box,text='—',bg=self.card,fg=self.accent,font=('Segoe UI',15,'bold'));self.rout.grid(row=5,column=1,padx=20)
    def calc_risk(self):
        try:
            bal=float(self.rv['Account Balance'].get());rp=float(self.rv['Risk %'].get());entry=float(self.rv['Entry Price'].get());sl=float(self.rv['Stop Loss Price'].get());pv=float(self.rv['Pip/Point Value'].get());risk=bal*rp/100;dist=abs(entry-sl);units=risk/(dist*pv) if dist*pv else 0;self.rout.config(text=f'حداکثر ضرر: {risk:.2f}\nفاصله SL: {dist:.6g}\nحجم تقریبی: {units:.4g}')
        except:messagebox.showerror('خطا','اعداد را صحیح وارد کنید.')
    def build_stats(self):
        tk.Label(self.stats_tab,text='داشبورد عملکرد ماهانه',bg=self.bg,fg=self.fg,font=('Segoe UI',18,'bold')).pack(anchor='e',padx=25,pady=18);self.statlab=tk.Label(self.stats_tab,bg=self.card,fg=self.fg,font=('Segoe UI',13),justify='right');self.statlab.pack(fill='x',padx=25,pady=10);self.canvas=tk.Canvas(self.stats_tab,bg=self.input,highlightthickness=0,height=360);self.canvas.pack(fill='both',expand=True,padx=25,pady=10)
    def render_stats(self):
        trades=db['journals'].get(self.market,[]);rs=[];wins=0
        for t in trades:
            try:r=float(t.get('Result (R)',''));rs.append(r);wins+=r>0
            except:pass
        total=sum(rs);wr=(wins/len(rs)*100) if rs else 0;self.statlab.config(text=f'بازار: {self.market}    |    معاملات: {len(rs)}    |    Win Rate: {wr:.1f}%    |    مجموع R: {total:.2f}    |    میانگین R: {(total/len(rs) if rs else 0):.2f}')
        self.canvas.delete('all');w=max(self.canvas.winfo_width(),700);h=330;self.canvas.create_line(45,h-45,w-25,h-45,fill=self.muted);self.canvas.create_line(45,20,45,h-45,fill=self.muted)
        if not rs:return
        cum=0;pts=[];mx=max(1,max(abs(sum(rs[:i+1])) for i in range(len(rs))));
        for i,r in enumerate(rs):cum+=r;x=55+(w-90)*(i/max(1,len(rs)-1));y=(h/2)-(cum/mx)*(h/2-45);pts.append((x,y))
        for a,b in zip(pts,pts[1:]):self.canvas.create_line(*a,*b,fill=self.accent,width=3)
        for x,y in pts:self.canvas.create_oval(x-3,y-3,x+3,y+3,fill=self.accent,outline='')
    def build_settings(self):
        tk.Label(self.settings_tab,text='تنظیمات',bg=self.bg,fg=self.fg,font=('Segoe UI',18,'bold')).pack(anchor='e',padx=25,pady=18);tk.Button(self.settings_tab,text='🌓 تغییر Dark / Light',command=self.toggle_theme,bg='#17233b',fg='white',relief='flat').pack(anchor='e',padx=25,pady=8);tk.Label(self.settings_tab,text='آلارم‌ها در نسخه فعلی بر پایه زمان‌بندی سیستم آماده‌اند؛ برای صدای سفارشی می‌توان مسیر صدا را در کد تنظیم کرد.',bg=self.bg,fg=self.muted,wraplength=800,justify='right').pack(anchor='e',padx=25,pady=15)
    def toggle_theme(self):db['theme']='light' if db.get('theme')=='dark' else 'dark';save();messagebox.showinfo('Theme','برای اعمال کامل تم، برنامه را دوباره اجرا کنید.')
    def pick_day(self,e):
        s=self.days.curselection()
        if s:self.day=s[0];self.render()
    def render(self):
        d=DAYS[self.day];key=d.isoformat();self.daytitle.config(text=f'برنامه {d.isoformat()}');self.daysub.config(text=f'{FA_DAYS[d.weekday()]} | 09:00–13:00 MARK UP | 15:30–19:00 TRADING');self.tree.delete(*self.tree.get_children())
        for i,t in enumerate(db['tasks'][key]):self.tree.insert('','end',iid=str(i),values=(t['time'],t['title'],t['cat'],'✓' if t['done'] else '○'))
        self.days.selection_clear(0,'end');self.days.selection_set(self.day);self.days.see(self.day);self.note.delete('1.0','end');self.note.insert('1.0',db['tasks'][key][0].get('note','') if db['tasks'][key] else '')
        self.render_journal();self.render_stats()
    def save_day_note(self):
        key=DAYS[self.day].isoformat();
        if db['tasks'][key]:db['tasks'][key][0]['note']=self.note.get('1.0','end').strip();save()
    def toggle_task(self,e=None):
        s=self.tree.selection();
        if not s:return
        i=int(s[0]);db['tasks'][DAYS[self.day].isoformat()][i]['done']=not db['tasks'][DAYS[self.day].isoformat()][i]['done'];save();self.render()
    def add_task(self):
        title=simpledialog.askstring('فعالیت جدید','عنوان فعالیت:',parent=self)
        if title:
            tm=simpledialog.askstring('زمان','مثلاً 20:30',initialvalue='20:30',parent=self) or '20:30';cat=simpledialog.askstring('دسته','مثلاً تفریح/ورزش',initialvalue='شخصی',parent=self) or 'شخصی';db['tasks'][DAYS[self.day].isoformat()].append({'time':tm,'title':title,'cat':cat,'done':False});save();self.render()
    def del_task(self):
        s=self.tree.selection();
        if s and messagebox.askyesno('حذف','فعالیت حذف شود؟'):del db['tasks'][DAYS[self.day].isoformat()][int(s[0])];save();self.render()
    def drag_start(self,e):
        row=self.tree.identify_row(e.y);self.drag_i=int(row) if row else None
    def drag_end(self,e):
        if self.drag_i is None:return
        row=self.tree.identify_row(e.y);i=self.drag_i;self.drag_i=None
        if row is None:return
        j=int(row);tasks=db['tasks'][DAYS[self.day].isoformat()];tasks.insert(j,tasks.pop(i));save();self.render()
    def tick(self):self.clock.config(text=datetime.now().strftime('%Y-%m-%d  %H:%M:%S'));self.after(1000,self.tick)

if __name__=='__main__':App().mainloop()
