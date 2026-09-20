from __future__ import annotations

import csv
import json
import math
import os
import re
import shutil
import sys
import webbrowser
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from logo_3d import create_logo_image
from academy_content import SMART_MONEY_STRATEGIES, ICT_STRATEGIES, CANDLE_PLAYBOOK, GLOSSARY, ACADEMY_NOTE_FA, ACADEMY_NOTE_EN
from academy_visuals import render_visual, visual_key_for, source_for_visual

APP = "Trader Planner Pro"
VERSION = "7.3.0"
ROOT = Path.home() / "TraderPlannerPro"
DATA = ROOT / "data.json"
SCREENSHOTS = ROOT / "Screenshots"
REPORTS = ROOT / "TradingPlans"

PLAN_FIELDS = [
    "نام استراتژی", "نسخه استراتژی", "بازارهای مجاز", "تایم‌فریم‌های اصلی",
    "ستاپ‌های مجاز", "شرایط ورود", "شرایط عدم ورود", "حداکثر ریسک هر معامله (%)",
    "حداکثر ضرر روزانه (%)", "حداکثر معاملات روزانه", "قانون خروج",
    "قانون توقف بعد از باخت", "قوانین روانشناسی", "اهداف ماهانه",
]
LEGACY_PLAN_FIELDS = [
    "بازارهای مجاز", "تایم‌فریم‌های اصلی", "ستاپ‌های مجاز", "شرایط ورود",
    "شرایط عدم ورود", "حداکثر ریسک هر معامله (%)", "حداکثر ضرر روزانه (%)",
    "حداکثر معاملات روزانه", "قانون خروج", "قانون توقف بعد از باخت",
    "قوانین روانشناسی", "اهداف ماهانه",
]
DEFAULT_CHECKLIST = [
    ("جهت و ساختار بازار مشخص است", "Market Structure"),
    ("نقدینگی و ناحیه مهم مشخص است", "Liquidity"),
    ("ستاپ مطابق Trading Plan است", "Trading Plan"),
    ("تریگر ورود تایید شده است", "Entry Model"),
    ("ریسک و حجم محاسبه شده", "Risk"),
    ("حد ضرر قبل از ورود مشخص است", "Risk"),
    ("R:R قابل قبول است", "Risk"),
    ("خبر مهم بررسی شده است", "News"),
    ("حالت روانی مناسب است", "Psychology"),
    ("FOMO / Revenge ندارم", "Psychology"),
    ("بعد از ورود قانون را تغییر نمی‌دهم", "Discipline"),
]
FIELDS = [
    "Date","Symbol","Direction","Session","Timeframe","Entry","Stop Loss","Take Profit",
    "Position Size","Risk %","Risk $","R:R","Setup","Market Structure","Liquidity",
    "Entry Model","Emotion Before","Emotion During","Emotion After","Mistake",
    "Result","Result (R)","P&L","Lesson","Notes","Screenshot",
]

C = {
    "bg": "#0A1018", "panel": "#111A26", "panel2": "#172230", "soft": "#1D2B3A",
    "text": "#EAF2F7", "muted": "#90A3B3", "accent": "#27D3B0", "gold": "#F2C46D",
    "danger": "#FF6F7D", "line": "#27384A", "blue": "#63A7FF",
    "shadow": "#050911", "panel3": "#0E1824", "violet": "#9B8CFF", "cyan": "#55D6FF",
}

LANGUAGE_OPTIONS = [("fa", "فارسی"), ("en", "English")]

I18N = {
    "fa": {
        "home":"⌂  خانه","daily":"◫  برنامه روزانه","plan":"◈  Trading Plan","check":"✓  چک‌لیست",
        "journal":"▣  ژورنال","settings":"⚙  تنظیمات","new_profile":"＋ پروفایل جدید","edit_profile":"ویرایش پروفایل",
        "delete_profile":"حذف پروفایل","active_profile":"پروفایل فعال","initial_capital":"سرمایه اولیه",
        "dashboard":"داشبورد حرفه‌ای","dashboard_sub":"پروفایل، سرمایه، عملکرد ژورنال و وضعیت معاملاتی در یک نگاه",
        "trading_count":"تعداد معاملات","win_rate":"Win Rate","net_r":"Net R","initial_balance":"سرمایه اولیه",
        "performance":"نمودار عملکرد معاملات","distribution":"توزیع نتایج ژورنال","new_trade":"＋ ثبت معامله جدید",
        "daily_title":"برنامه روزانه","daily_sub":"قابل ویرایش، قابل تیک‌زدن و ذخیره روی همان مسیر داده قبلی",
        "prev_day":"روز قبل","next_day":"روز بعد","new_task":"＋ فعالیت جدید","edit":"ویرایش","delete":"حذف",
        "time":"زمان","activity":"فعالیت","category":"دسته","search":"جستجو:","export_csv":"خروجی CSV",
        "open_images":"باز کردن پوشه تصاویر","journal_empty":"ژورنال خالی","no_data":"هنوز داده‌ای برای نمودار نیست",
        "journal_profile":"پروفایل: {name} | ژورنال {market} مستقل از پروفایل‌های دیگر",
        "plan_title":"Trading Plan","plan_sub":"پلن را ویرایش کن، به‌عنوان نسخه مستقل ذخیره کن و خروجی A4 بگیر",
        "save_plan":"💾 ذخیره به‌عنوان Trading Plan","export_a4":"🖼 خروجی A4","saved_versions":"نسخه‌های ذخیره‌شده",
        "current_version":"عنوان نسخه فعلی:","check_title":"Checklist",
        "check_sub":"موارد را سریع ببین، تیک بزن، ویرایش کن و با دکمه‌های هر ردیف جابه‌جا کن",
        "add_condition":"＋ افزودن شرط","from_plan":"ساخت از Trading Plan","completed":"تکمیل شده",
        "required":"اجباری","source":"منبع","move_up":"↑","move_down":"↓","remove":"×","edit_row":"ویرایش",
        "settings_title":"تنظیمات","settings_sub":"زبان، پروفایل فعال و مسیر ذخیره‌سازی برنامه",
        "language":"زبان برنامه","language_help":"زبان رابط کاربری را انتخاب کن. تغییر زبان بلافاصله اعمال می‌شود.",
        "language_saved":"زبان تغییر کرد","language_saved_msg":"زبان برنامه روی {language} تنظیم شد.",
        "profile":"پروفایل","market":"بازار","data_path":"مسیر داده","reports_path":"مسیر خروجی A4",
        "manage_profiles":"مدیریت پروفایل‌ها","yes":"بله","no":"خیر","manual":"دستی","trading_plan":"Trading Plan",
        "strategy":"استراتژی","no_checklist":"چک‌لیست خالی است","save":"ذخیره","cancel":"انصراف",
        "delete_item":"حذف","generate":"تولید از Trading Plan","items":"مورد",
        "check_progress":"{done} از {total} مورد تکمیل شده","check_item":"شرط",
        "session_clocks":"ساعت سشن‌ها","local_time":"زمان محلی","session_hours":"ساعت سشن","open":"باز","closed":"بسته",
        "required_item":"این شرط اجباری است","condition_title":"عنوان شرط","condition_category":"دسته",
        "condition_source":"منبع","general":"عمومی","select_condition":"ابتدا یک شرط را انتخاب کن",
        "empty_plan":"ابتدا حداقل چند بخش از Trading Plan را پر کن.",

        "academy":"◉  آموزش","academy_title":"مرکز آموزش","academy_sub":"اسمارت مانی، ICT، کندل‌شناسی و لغتنامه جستجوپذیر",
        "smc":"Smart Money","ict":"ICT","candles":"Candlestick","glossary":"Glossary","search_term":"جستجوی اصطلاح...",
        "all_categories":"همه دسته‌ها","definition":"تعریف","usage":"کاربرد","steps":"مراحل","invalidation":"ابطال",
        "education_note":"یادداشت آموزشی","language_now":"زبان فعلی","choose_language":"انتخاب زبان","apply":"اعمال",
    },
    "en": {
        "home":"⌂  Home","daily":"◫  Daily Planner","plan":"◈  Trading Plan","check":"✓  Checklist",
        "journal":"▣  Journal","settings":"⚙  Settings","new_profile":"＋ New Profile","edit_profile":"Edit Profile",
        "delete_profile":"Delete Profile","active_profile":"Active Profile","initial_capital":"Initial Capital",
        "dashboard":"Professional Dashboard","dashboard_sub":"Profile, capital, journal performance and trading status at a glance",
        "trading_count":"Trades","win_rate":"Win Rate","net_r":"Net R","initial_balance":"Initial Capital",
        "performance":"Trade Performance","distribution":"Journal Results","new_trade":"＋ New Trade",
        "daily_title":"Daily Planner","daily_sub":"Editable, checkable and saved to the existing data path",
        "prev_day":"Previous Day","next_day":"Next Day","new_task":"＋ New Activity","edit":"Edit","delete":"Delete",
        "time":"Time","activity":"Activity","category":"Category","search":"Search:","export_csv":"Export CSV",
        "open_images":"Open Screenshots","journal_empty":"Empty Journal","no_data":"No data for this chart yet",
        "journal_profile":"Profile: {name} | Independent {market} journal",
        "plan_title":"Trading Plan","plan_sub":"Edit the plan, save named versions and export A4",
        "save_plan":"💾 Save as Trading Plan","export_a4":"🖼 Export A4","saved_versions":"Saved Versions",
        "current_version":"Current version title:","check_title":"Checklist",
        "check_sub":"Review items quickly, tick them, edit them, and reorder them with row controls",
        "add_condition":"＋ Add Condition","from_plan":"Build from Trading Plan","completed":"Completed",
        "required":"Required","source":"Source","move_up":"↑","move_down":"↓","remove":"×","edit_row":"Edit",
        "settings_title":"Settings","settings_sub":"Language, active profile and application storage paths",
        "language":"Application Language","language_help":"Choose the interface language. The change applies immediately.",
        "language_saved":"Language changed","language_saved_msg":"Application language set to {language}.",
        "profile":"Profile","market":"Market","data_path":"Data Path","reports_path":"A4 Output Path",
        "manage_profiles":"Manage Profiles","yes":"Yes","no":"No","manual":"Manual","trading_plan":"Trading Plan",
        "strategy":"Strategy","no_checklist":"Checklist is empty","save":"Save","cancel":"Cancel",
        "delete_item":"Delete","generate":"Build from Trading Plan","items":"items",
        "check_progress":"{done} of {total} items completed","check_item":"Condition",
        "session_clocks":"Trading Session Clocks","local_time":"Local Time","session_hours":"Session Hours","open":"OPEN","closed":"CLOSED",
        "required_item":"This condition is required","condition_title":"Condition Title","condition_category":"Category",
        "condition_source":"Source","general":"General","select_condition":"Select a condition first",
        "empty_plan":"Fill at least a few Trading Plan sections first.",
        "academy":"◉  Academy","academy_title":"Training Center","academy_sub":"Smart Money, ICT, candlestick reading and searchable glossary",
        "smc":"Smart Money","ict":"ICT","candles":"Candlestick","glossary":"Glossary","search_term":"Search a term...",
        "all_categories":"All Categories","definition":"Definition","usage":"Usage","steps":"Steps","invalidation":"Invalidation",
        "education_note":"Training note","language_now":"Current language","choose_language":"Choose language","apply":"Apply",
    }
}


SESSION_CLOCKS = [
    {"key":"sydney","fa":"سیدنی","en":"Sydney","tz":"Australia/Sydney","start":8,"end":17,"abbr":"SYD"},
    {"key":"tokyo","fa":"توکیو","en":"Tokyo","tz":"Asia/Tokyo","start":9,"end":18,"abbr":"TYO"},
    {"key":"london","fa":"لندن","en":"London","tz":"Europe/London","start":8,"end":17,"abbr":"LON"},
    {"key":"new_york","fa":"نیویورک","en":"New York","tz":"America/New_York","start":8,"end":17,"abbr":"NY"},
]

FA_TO_EN = {
    "خانه":"Home","برنامه روزانه":"Daily Planner","تنظیمات":"Settings","پروفایل جدید":"New Profile",
    "ویرایش پروفایل":"Edit Profile","حذف پروفایل":"Delete Profile","ذخیره":"Save","انصراف":"Cancel",
    "ویرایش":"Edit","حذف":"Delete","بالا":"Up","پایین":"Down","ذخیره پروفایل":"Save Profile",
    "مدیریت پروفایل‌ها":"Manage Profiles","＋ افزودن شرط":"＋ Add Condition","ساخت از Trading Plan":"Build from Trading Plan",
    "نسخه‌های ذخیره‌شده":"Saved Versions","خروجی A4":"Export A4","ذخیره به‌عنوان Trading Plan":"Save as Trading Plan",
    "انتخاب تصویر":"Choose Image","باز کردن پوشه":"Open Folder","ذخیره معامله":"Save Trade","ثبت معامله":"Add Trade",
    "خروجی CSV":"Export CSV","باز کردن پوشه تصاویر":"Open Screenshots","پایان MARK UP":"End MARK UP",
    "روز قبل":"Previous Day","روز بعد":"Next Day","＋ فعالیت جدید":"＋ New Activity","عنوان":"Title","دسته":"Category",
    "فعالیت":"Activity","زمان":"Time","پروفایل":"Profile","بازار":"Market","سرمایه اولیه":"Initial Capital",
    "عنوان شرط":"Condition Title","منبع":"Source","اجباری":"Required","بله":"Yes","خیر":"No","دستی":"Manual"
}


TASKS = [
    ("07:00","بیداری + آب + نور صبح","سلامت"),("07:15","صبحانه","غذا"),
    ("07:45","ورزش / پیاده‌روی صبح 30–45 دقیقه","ورزش"),("08:35","دوش + آماده‌سازی میز","روتین"),
    ("09:00","MARK UP — ساختار، روند، نقدینگی و نواحی","MARK UP"),
    ("10:45","استراحت 15 دقیقه","استراحت"),("11:00","MARK UP — سناریوی A/B و نقاط ابطال","MARK UP"),
    ("12:30","ثبت سناریو + بررسی خبرها","تحلیل"),("13:00","پایان MARK UP + بستن چارت","پایان"),
    ("14:30","مرور پلن + آماده‌سازی سشن","آماده‌سازی"),("15:30","TRADING — فقط ستاپ‌های مجاز","TRADING"),
    ("17:10","TRADING — ادامه سشن","TRADING"),("19:00","پایان قطعی ترید","پایان"),
    ("21:00","ژورنال + اسکرین‌شات + درس روز","ژورنال"),("21:40","مطالعه / بک‌تست سبک","یادگیری"),
    ("22:30","خاموشی صفحه‌نمایش","خواب"),("23:30","خواب","خواب"),
]

def default_checklist():
    return [
        {"id": str(uuid4()), "title": title, "category": category, "required": True, "done": False, "source": "default"}
        for title, category in DEFAULT_CHECKLIST
    ]

def empty_profile(name="Main Profile", market="Crypto", currency="USD", initial_balance=0.0):
    return {
        "id": str(uuid4()), "name": name, "market": market, "currency": currency,
        "initial_balance": float(initial_balance or 0), "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "journals": {"Forex": [], "Crypto": []},
        "plans": [], "active_plan_id": None, "plan_draft": {k: "" for k in PLAN_FIELDS},
        "checklist": default_checklist(),
    }

def empty_db():
    today = date.today()
    tasks = {}
    for offset in range(-30, 180):
        day = (today + timedelta(days=offset)).isoformat()
        tasks[day] = [
            {"id": f"{day}-{i}", "time": t, "title": title, "cat": cat, "done": False}
            for i, (t, title, cat) in enumerate(TASKS)
        ]
    p = empty_profile()
    return {"version": 710, "active_profile_id": p["id"], "profiles": [p], "tasks": tasks, "settings": {"language": "fa"}}

def numeric(value):
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0

def migrate_payload(old):
    base = empty_db()
    if not isinstance(old, dict):
        return base
    # Preserve legacy daily planner.
    if isinstance(old.get("tasks"), dict):
        base["tasks"] = old["tasks"]
    if isinstance(old.get("settings"), dict):
        base["settings"].update(old["settings"])
    base["settings"].setdefault("language", "fa")
    if isinstance(old.get("profiles"), list) and old["profiles"]:
        base["profiles"] = old["profiles"]
        active = old.get("active_profile_id") or base["profiles"][0].get("id")
        base["active_profile_id"] = active
        for p in base["profiles"]:
            p.setdefault("id", str(uuid4()))
            p.setdefault("name", "Profile")
            p.setdefault("market", "Crypto")
            p.setdefault("currency", "USD")
            p.setdefault("initial_balance", 0.0)
            p.setdefault("journals", {"Forex": [], "Crypto": []})
            p["journals"].setdefault("Forex", []); p["journals"].setdefault("Crypto", [])
            p.setdefault("plans", [])
            p.setdefault("active_plan_id", None)
            p.setdefault("plan_draft", {k: "" for k in PLAN_FIELDS})
            p.setdefault("checklist", default_checklist())
            for item in p["checklist"]:
                item.setdefault("id", str(uuid4())); item.setdefault("done", False)
        base["version"] = 710
        return base
    # V7.0.2 -> profile migration without data loss.
    legacy_profile = old.get("profile") if isinstance(old.get("profile"), dict) else {}
    p = empty_profile(
        legacy_profile.get("name") or "Main Profile",
        old.get("market") if old.get("market") in ("Forex", "Crypto") else "Crypto",
        legacy_profile.get("account_currency") or "USD",
        numeric(legacy_profile.get("starting_balance")),
    )
    journals = old.get("journals") if isinstance(old.get("journals"), dict) else {}
    p["journals"]["Forex"] = list(journals.get("Forex") or [])
    p["journals"]["Crypto"] = list(journals.get("Crypto") or [])
    legacy_plan = old.get("plan") if isinstance(old.get("plan"), dict) else {}
    for k in LEGACY_PLAN_FIELDS:
        p["plan_draft"][k] = str(legacy_plan.get(k, ""))
    p["plan_draft"]["نام استراتژی"] = "Migrated Trading Plan"
    if any(v.strip() for v in p["plan_draft"].values()):
        p["plans"].append({
            "id": str(uuid4()), "title": "Migrated Trading Plan",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "fields": dict(p["plan_draft"]),
        })
        p["active_plan_id"] = p["plans"][-1]["id"]
    legacy_check = old.get("check") if isinstance(old.get("check"), dict) else {}
    if legacy_check:
        p["checklist"] = [
            {"id": str(uuid4()), "title": str(k), "category": "Migrated",
             "required": True, "done": bool(v), "source": "v7.0.2"}
            for k, v in legacy_check.items()
        ]
    base["profiles"] = [p]
    base["active_profile_id"] = p["id"]
    base["version"] = 710
    return base

def load_db(path=DATA):
    try:
        old = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        old = None
    return migrate_payload(old)

DB = load_db()

def save_db(path=DATA):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(DB, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)

def active_profile():
    pid = DB.get("active_profile_id")
    for p in DB["profiles"]:
        if p.get("id") == pid:
            return p
    DB["active_profile_id"] = DB["profiles"][0]["id"]
    return DB["profiles"][0]

def safe(value):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("_") or "Unknown"

def screenshot_folder(row, root=SCREENSHOTS, market=None):
    day = safe((row or {}).get("Date") or date.today().isoformat())
    market = safe(market or active_profile().get("market", "Crypto"))
    symbol = safe((row or {}).get("Symbol") or "Unknown")
    folder = Path(root) / safe(active_profile().get("id")) / day / market / symbol
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def attach_screenshot(row, source, root=SCREENSHOTS, market=None):
    source = Path(source)
    if not source.is_file():
        return ""
    folder = screenshot_folder(row, root, market)
    stamp = datetime.now().strftime("%H%M%S")
    ext = source.suffix.lower() or ".png"
    target = folder / f"{safe(row.get('Date'))}_{safe(row.get('Symbol'))}_{safe(row.get('Direction',''))}_{stamp}{ext}"
    shutil.copy2(source, target)
    return str(target)

def upsert_trade(profile, market, row, index=None):
    row = {key: str(row.get(key, "")) for key in FIELDS}
    row["Date"] = row["Date"] or date.today().isoformat()
    if not row["Symbol"].strip():
        raise ValueError("Symbol is required")
    rows = profile["journals"].setdefault(market, [])
    if index is None:
        rows.append(row)
    else:
        if not 0 <= index < len(rows):
            raise IndexError(index)
        rows[index] = row
    profile["updated_at"] = datetime.now().isoformat(timespec="seconds")

def result_num(row):
    return numeric(row.get("Result (R)", 0))

def find_font():
    candidates = [
        r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\segoeuib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for item in candidates:
        if Path(item).exists():
            return item
    return None

def export_plan_a4(profile, title, fields):
    from PIL import Image, ImageDraw, ImageFont
    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / f"{safe(profile['name'])}_{safe(title)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    W, H = 2480, 3508
    img = Image.new("RGB", (W, H), "#0A1018")
    draw = ImageDraw.Draw(img)
    font_path = find_font()
    try:
        f_title = ImageFont.truetype(font_path, 68) if font_path else ImageFont.load_default()
        f_head = ImageFont.truetype(font_path, 34) if font_path else ImageFont.load_default()
        f_body = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
        f_small = ImageFont.truetype(font_path, 22) if font_path else ImageFont.load_default()
    except OSError:
        f_title = f_head = f_body = f_small = ImageFont.load_default()
    def rtl(text, xy, font, fill):
        try:
            draw.text(xy, text, font=font, fill=fill, anchor="ra", direction="rtl")
        except TypeError:
            draw.text(xy, text, font=font, fill=fill, anchor="ra")
    draw.rounded_rectangle((70, 70, W-70, H-70), radius=48, fill="#111A26", outline="#27D3B0", width=4)
    draw.rounded_rectangle((110, 110, W-110, 400), radius=38, fill="#172230")
    rtl("TRADER PLANNER PRO", (W-170, 185), f_title, "#27D3B0")
    rtl(title, (W-170, 275), f_head, "#F2C46D")
    rtl(f"پروفایل: {profile['name']}  |  بازار: {profile['market']}  |  سرمایه اولیه: {profile['initial_balance']:,.2f} {profile['currency']}",
        (W-170, 350), f_small, "#EAF2F7")
    y = 480
    for key in PLAN_FIELDS:
        value = str(fields.get(key, "")).strip() or "—"
        draw.rounded_rectangle((140, y, W-140, y+150), radius=24, fill="#172230", outline="#27384A", width=2)
        rtl(key, (W-190, y+38), f_head, "#27D3B0")
        text = value if len(value) <= 95 else value[:92] + "…"
        rtl(text, (W-190, y+105), f_body, "#EAF2F7")
        y += 175
        if y > H-250:
            break
    rtl(f"Exported {datetime.now().strftime('%Y-%m-%d %H:%M')}", (W-170, H-115), f_small, "#90A3B3")
    img.save(path, "PNG", optimize=True)
    return path

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP} V{VERSION}")
        self.geometry("1520x960"); self.minsize(1180, 760); self.configure(bg=C["bg"])
        self.cur = "home"; self.day = date.today().isoformat(); self.market = active_profile().get("market", "Crypto")
        self.language = DB.get("settings", {}).get("language", "fa")
        if self.language not in dict(LANGUAGE_OPTIONS): self.language = "fa"
        self.menu_open = False
        self.session_clock_job = None
        self.session_clock_widgets = []
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("Treeview", background=C["panel"], fieldbackground=C["panel"], foreground=C["text"],
                             rowheight=38, borderwidth=0, font=("Segoe UI", 10))
        self.style.map("Treeview", background=[("selected", C["soft"])], foreground=[("selected", C["text"])])
        self.style.configure("TCombobox", fieldbackground=C["soft"], background=C["soft"], foreground=C["text"])
        self._logo_photo = None
        self.build_shell()
        self.apply_language()
        self.show("home")
        self.after(500, self.clock)

    def tr(self, key, **kwargs):
        table = I18N.get(self.language, I18N["fa"])
        text = table.get(key, key)
        return text.format(**kwargs) if kwargs else text

    def ui_text(self, text):
        if self.language != "en":
            return text
        return FA_TO_EN.get(str(text), str(text))

    def apply_language(self):
        self.title(f"{APP} V{VERSION}")
        if hasattr(self, "brand_title"): self.brand_title.config(text=APP)
        if hasattr(self, "brand_subtitle"): self.brand_subtitle.config(text="PRO TRADING WORKSPACE")
        if hasattr(self, "menu_title"): self.menu_title.config(text="TRADER PLANNER PRO")
        if hasattr(self, "menu_buttons"):
            for key, button in self.menu_buttons.items():
                button.config(text=self.tr(key))
        if hasattr(self, "market_btn"):
            self.market_btn.config(text=self.market)

    def set_language(self, code):
        if code not in dict(LANGUAGE_OPTIONS): return
        DB.setdefault("settings", {})["language"] = code
        self.language = code
        save_db()
        self.apply_language()
        self.show(self.cur)

    def build_shell(self):
        top = tk.Frame(self, bg=C["bg"]); top.pack(fill="x", padx=18, pady=14)
        tk.Button(top, text="☰", command=self.toggle_menu, bg=C["panel2"], fg=C["text"], relief="flat",
                  font=("Segoe UI", 18, "bold"), width=3).pack(side="left")
        try:
            logo_path = create_logo_image(Path(tempfile_path()), 260)
            from PIL import Image, ImageTk
            self._logo_photo = ImageTk.PhotoImage(Image.open(logo_path).convert("RGBA").resize((62,62)))
            tk.Label(top, image=self._logo_photo, bg=C["bg"]).pack(side="left", padx=(12,4))
        except Exception:
            pass
        brand = tk.Frame(top, bg=C["bg"]); brand.pack(side="left")
        self.brand_title = tk.Label(brand, text=APP, bg=C["bg"], fg=C["text"], font=("Segoe UI", 21, "bold")); self.brand_title.pack(anchor="w")
        self.brand_subtitle = tk.Label(brand, text="PRO TRADING WORKSPACE", bg=C["bg"], fg=C["accent"], font=("Segoe UI", 8, "bold")); self.brand_subtitle.pack(anchor="w")
        self.clock_label = tk.Label(top, bg=C["bg"], fg=C["muted"], font=("Segoe UI", 10, "bold")); self.clock_label.pack(side="right")
        self.profile_combo = ttk.Combobox(top, state="readonly", width=22, justify="right")
        self.profile_combo.bind("<<ComboboxSelected>>", self.on_profile_change)
        self.profile_combo.pack(side="right", padx=10)
        self.market_btn = tk.Button(top, text=self.market, command=self.change_market, bg=C["soft"], fg=C["text"],
                                    relief="flat", font=("Segoe UI", 10, "bold"), padx=14, pady=8)
        self.market_btn.pack(side="right", padx=6)
        self.refresh_profile_selector()
        self.content = tk.Frame(self, bg=C["bg"]); self.content.pack(fill="both", expand=True, padx=16)
        self.menu = tk.Frame(self, bg=C["panel"], width=300, highlightbackground=C["line"], highlightthickness=1)
        self.menu.place(x=-310, y=0, relheight=1)
        self.menu_title = tk.Label(self.menu, text="TRADER PLANNER PRO", bg=C["panel"], fg=C["accent"], font=("Segoe UI", 17, "bold")); self.menu_title.pack(anchor="w", padx=22, pady=24)
        self.menu_buttons = {}
        for key in ("home","daily","plan","check","journal","academy","settings"):
            b = tk.Button(self.menu, text=self.tr(key), command=lambda k=key:self.go(k), anchor="w",
                          bg=C["panel"], fg=C["text"], activebackground=C["soft"], relief="flat",
                          font=("Segoe UI",11), padx=22, pady=11)
            b.pack(fill="x"); self.menu_buttons[key] = b

    def refresh_profile_selector(self):
        names = [p.get("name", "Profile") for p in DB["profiles"]]
        self.profile_combo["values"] = names
        p = active_profile()
        try: self.profile_combo.current(names.index(p["name"]))
        except ValueError: self.profile_combo.current(0)

    def on_profile_change(self, _=None):
        idx = self.profile_combo.current()
        if idx < 0: return
        DB["active_profile_id"] = DB["profiles"][idx]["id"]
        self.market = active_profile().get("market", "Crypto")
        self.market_btn.config(text=self.market)
        save_db(); self.show(self.cur)

    def toggle_menu(self):
        self.menu.place_configure(x=0 if not self.menu_open else -310); self.menu_open = not self.menu_open

    def go(self, key):
        if self.menu_open: self.toggle_menu()
        self.show(key)

    def show(self, key):
        if self.session_clock_job is not None:
            try: self.after_cancel(self.session_clock_job)
            except Exception: pass
            self.session_clock_job = None
        self.session_clock_widgets = []
        self.cur = key
        for widget in self.content.winfo_children(): widget.destroy()
        getattr(self, key)()

    def clock(self):
        self.clock_label.config(text=datetime.now().strftime("%Y-%m-%d  |  %H:%M:%S"))
        self.after(500, self.clock)

    def heading(self, title, sub=""):
        title = self.ui_text(title); sub = self.ui_text(sub)
        tk.Label(self.content, text=title, bg=C["bg"], fg=C["text"], font=("Segoe UI",22,"bold")).pack(anchor="e", pady=(8,2))
        if sub: tk.Label(self.content, text=sub, bg=C["bg"], fg=C["muted"], font=("Segoe UI",10)).pack(anchor="e", pady=(0,10))

    def card(self, parent, padx=1):
        return tk.Frame(parent, bg=C["panel"], highlightbackground=C["line"], highlightthickness=padx)

    def btn(self, parent, text, cmd, primary=False, **kw):
        return tk.Button(parent, text=self.ui_text(text), command=cmd, bg=C["accent"] if primary else C["soft"],
                         fg="#061019" if primary else C["text"], activebackground=C["gold"], relief="flat",
                         font=("Segoe UI",10,"bold"), padx=13, pady=8, **kw)

    def profile_panel(self, parent):
        box = self.card(parent); box.pack(fill="x", pady=8)
        left = tk.Frame(box, bg=C["panel"]); left.pack(side="left", fill="x", expand=True, padx=14, pady=12)
        self.btn(left, "＋ پروفایل جدید", self.add_profile, True).pack(side="left", padx=3)
        self.btn(left, "ویرایش پروفایل", self.edit_profile).pack(side="left", padx=3)
        self.btn(left, "حذف پروفایل", self.delete_profile).pack(side="left", padx=3)
        p = active_profile()
        tk.Label(box, text=f"پروفایل فعال: {p['name']}   |   سرمایه اولیه: {p['initial_balance']:,.2f} {p['currency']}",
                 bg=C["panel"], fg=C["gold"], font=("Segoe UI",11,"bold")).pack(side="right", padx=14, pady=12)

    def add_profile(self):
        self.profile_dialog()

    def edit_profile(self):
        self.profile_dialog(active_profile())

    def profile_dialog(self, profile=None):
        dlg=tk.Toplevel(self); dlg.title("پروفایل ژورنال"); dlg.geometry("520x360"); dlg.configure(bg=C["bg"]); dlg.transient(self); dlg.grab_set()
        vals = {
            "name": tk.StringVar(value=(profile or {}).get("name","")),
            "market": tk.StringVar(value=(profile or {}).get("market","Crypto")),
            "currency": tk.StringVar(value=(profile or {}).get("currency","USD")),
            "initial": tk.StringVar(value=str((profile or {}).get("initial_balance",0))),
        }
        labels=[("نام پروفایل","name"),("بازار پیش‌فرض","market"),("ارز سرمایه","currency"),("سرمایه اولیه","initial")]
        for i,(label,key) in enumerate(labels):
            tk.Label(dlg,text=label,bg=C["bg"],fg=C["muted"]).grid(row=i,column=1,padx=16,pady=12,sticky="e")
            if key=="market":
                w=ttk.Combobox(dlg,textvariable=vals[key],values=["Crypto","Forex"],state="readonly",justify="right")
            else:
                w=tk.Entry(dlg,textvariable=vals[key],bg=C["soft"],fg=C["text"],relief="flat",justify="right")
            w.grid(row=i,column=0,padx=16,pady=12,sticky="ew")
        dlg.columnconfigure(0, weight=1)
        def submit():
            name=vals["name"].get().strip() or "Profile"
            initial=numeric(vals["initial"].get())
            if profile:
                profile.update(name=name,market=vals["market"].get(),currency=vals["currency"].get().strip() or "USD",initial_balance=initial)
            else:
                p=empty_profile(name,vals["market"].get(),vals["currency"].get().strip() or "USD",initial)
                DB["profiles"].append(p); DB["active_profile_id"]=p["id"]
            save_db(); dlg.destroy(); self.market=active_profile()["market"]; self.market_btn.config(text=self.market); self.refresh_profile_selector(); self.show(self.cur)
        self.btn(dlg,"ذخیره پروفایل",submit,True).grid(row=5,column=0,padx=16,pady=16,sticky="e")
        self.btn(dlg,"انصراف",dlg.destroy).grid(row=5,column=1,padx=16,pady=16,sticky="w")

    def delete_profile(self):
        if len(DB["profiles"]) <= 1:
            return messagebox.showinfo("پروفایل","حداقل یک پروفایل باید باقی بماند.",parent=self)
        p=active_profile()
        if messagebox.askyesno("حذف پروفایل",f"پروفایل «{p['name']}» و ژورنال آن حذف شود؟",parent=self):
            DB["profiles"]=[x for x in DB["profiles"] if x["id"]!=p["id"]]
            DB["active_profile_id"]=DB["profiles"][0]["id"]; save_db()
            self.market=active_profile()["market"]; self.refresh_profile_selector(); self.show("home")

    def change_market(self):
        p=active_profile(); p["market"]="Forex" if p.get("market")=="Crypto" else "Crypto"
        self.market=p["market"]; self.market_btn.config(text=self.market); p["updated_at"]=datetime.now().isoformat(timespec="seconds")
        save_db(); self.show(self.cur)

    def home(self):
        p=active_profile(); self.market=p.get("market","Crypto")
        self.heading("داشبورد حرفه‌ای", "پروفایل، سرمایه، عملکرد ژورنال و وضعیت معاملاتی در یک نگاه")
        self.profile_panel(self.content)
        hero=tk.Frame(self.content,bg=C["bg"]); hero.pack(fill="x", pady=6)
        for title,value,accent in [
            ("تعداد معاملات", len(p["journals"][self.market]), C["text"]),
            ("Win Rate", f"{self.win_rate(p['journals'][self.market]):.1f}%", C["accent"]),
            ("Net R", f"{sum(result_num(x) for x in p['journals'][self.market]):.2f} R", C["gold"]),
            ("سرمایه اولیه", f"{p['initial_balance']:,.2f} {p['currency']}", C["text"]),
        ]:
            box=self.card(hero); box.pack(side="left",fill="both",expand=True,padx=4)
            tk.Label(box,text=self.ui_text(title),bg=C["panel"],fg=C["muted"]).pack(anchor="w",padx=16,pady=(14,2))
            tk.Label(box,text=value,bg=C["panel"],fg=accent,font=("Segoe UI",18,"bold")).pack(anchor="w",padx=16,pady=(0,14))

        session_title=tk.Frame(self.content,bg=C["bg"]); session_title.pack(fill="x",pady=(8,2))
        tk.Label(session_title,text=self.tr("session_clocks"),bg=C["bg"],fg=C["text"],font=("Segoe UI",14,"bold")).pack(anchor="e")
        tk.Label(session_title,text=self.tr("local_time")+" • "+self.tr("session_hours"),bg=C["bg"],fg=C["muted"],font=("Segoe UI",9)).pack(anchor="e")

        clocks=tk.Frame(self.content,bg=C["bg"]); clocks.pack(fill="x",pady=(4,10))
        for col,session in enumerate(SESSION_CLOCKS):
            clocks.columnconfigure(col,weight=1)
            card=self.card(clocks); card.grid(row=0,column=col,sticky="nsew",padx=4)
            self.draw_session_clock(card,session)
        self.update_session_clocks()

        lower=tk.Frame(self.content,bg=C["bg"]); lower.pack(fill="both",expand=True,pady=4)
        left=self.card(lower); left.pack(side="left",fill="both",expand=True,padx=4)
        right=self.card(lower); right.pack(side="left",fill="both",expand=True,padx=4)
        tk.Label(left,text=self.ui_text("نمودار عملکرد معاملات"),bg=C["panel"],fg=C["text"],font=("Segoe UI",13,"bold")).pack(anchor="e",padx=15,pady=10)
        self.draw_bar_chart(left,p["journals"][self.market])
        tk.Label(right,text=self.ui_text("توزیع نتایج ژورنال"),bg=C["panel"],fg=C["text"],font=("Segoe UI",13,"bold")).pack(anchor="e",padx=15,pady=10)
        self.draw_pie_chart(right,p["journals"][self.market])
        self.btn(self.content,self.tr("new_trade"),self.add_trade,True).pack(anchor="e",padx=6,pady=8)

    def draw_session_clock(self,parent,session):
        title_color=C["gold"] if session["key"]=="london" else C["text"]
        tk.Label(parent,text=session["fa"] if self.language=="fa" else session["en"],
                 bg=C["panel"],fg=title_color,font=("Segoe UI",12,"bold")).pack(pady=(10,2))
        canvas=tk.Canvas(parent,width=190,height=190,bg=C["panel"],highlightthickness=0)
        canvas.pack(pady=2)
        status=tk.Label(parent,text="",bg=C["panel"],fg=C["muted"],font=("Segoe UI",9,"bold"))
        status.pack(pady=(2,0))
        hours=tk.Label(parent,text="",bg=C["panel"],fg=C["muted"],font=("Segoe UI",8))
        hours.pack(pady=(0,10))
        self.session_clock_widgets.append((canvas,status,hours,session))

    def update_session_clocks(self):
        if self.cur!="home": return
        for canvas,status,hours,session in list(self.session_clock_widgets):
            try:
                now=datetime.now(ZoneInfo(session["tz"]))
                w,h=190,190; cx,cy=95,88; r=72
                canvas.delete("all")
                canvas.create_oval(cx-r,cy-r,cx+r,cy+r,fill=C["panel2"],outline=C["line"],width=3)
                canvas.create_oval(cx-r+7,cy-r+7,cx+r-7,cy+r-7,fill=C["panel"],outline=C["soft"],width=2)
                for n in range(60):
                    ang=math.radians(n*6-90)
                    outer=r-11; inner=r-18 if n%5 else r-25
                    width=1 if n%5 else 2
                    canvas.create_line(cx+math.cos(ang)*inner,cy+math.sin(ang)*inner,
                                       cx+math.cos(ang)*outer,cy+math.sin(ang)*outer,
                                       fill=C["muted"],width=width)
                for num in (12,3,6,9):
                    ang=math.radians(num*30-90)
                    tx=cx+math.cos(ang)*(r-33); ty=cy+math.sin(ang)*(r-33)
                    canvas.create_text(tx,ty,text=str(num),fill=C["text"],font=("Segoe UI",9,"bold"))
                hour12=(now.hour%12)+now.minute/60.0
                minute=now.minute+now.second/60.0
                second=now.second+now.microsecond/1_000_000
                for value,turns,length,width,color in [
                    (hour12,12,38,5,C["text"]),
                    (minute,60,55,3,C["gold"]),
                    (second,60,62,1,C["accent"]),
                ]:
                    ang=math.radians(value*(360/turns)-90)
                    canvas.create_line(cx,cy,cx+math.cos(ang)*length,cy+math.sin(ang)*length,fill=color,width=width)
                canvas.create_oval(cx-5,cy-5,cx+5,cy+5,fill=C["accent"],outline="")
                local_minutes=now.hour*60+now.minute
                start=session["start"]*60; end=session["end"]*60
                is_open=start <= local_minutes < end
                status_text=(self.tr("open") if is_open else self.tr("closed"))
                status_color=C["accent"] if is_open else C["muted"]
                status.config(text=f"{status_text}  •  {now.strftime('%H:%M:%S')}",fg=status_color)
                hours.config(text=f"{session['start']:02d}:00 – {session['end']:02d}:00  {now.tzname() or ''}".strip())
            except Exception:
                continue
        if self.cur=="home":
            self.session_clock_job=self.after(1000,self.update_session_clocks)

    def win_rate(self, rows):
        if not rows: return 0.0
        wins=sum(1 for r in rows if result_num(r)>0)
        return wins/len(rows)*100.0

    def draw_bar_chart(self, parent, rows):
        c=tk.Canvas(parent,bg=C["panel"],highlightthickness=0,height=270); c.pack(fill="x",padx=10,pady=6)
        vals=[result_num(r) for r in rows[-12:]] or [0]; lo=min(vals); hi=max(max(vals),1); span=max(hi-lo,1)
        w=max(480,parent.winfo_width() or 700); h=240; pad=35; bw=max(18,(w-2*pad)/max(len(vals),1)-12)
        c.create_line(pad,h//2,w-pad,h//2,fill=C["line"])
        for i,v in enumerate(vals):
            x1=pad+i*(bw+12); x2=x1+bw; y0=h//2; y1=y0-(v/span)*(h*.34)
            color=C["accent"] if v>=0 else C["danger"]
            c.create_rectangle(x1,min(y0,y1),x2,max(y0,y1),fill=color,outline="")
            c.create_text((x1+x2)/2,h-15,text=str(len(rows)-len(vals)+i+1),fill=C["muted"],font=("Segoe UI",8))
        c.create_text(w-8,12,text="آخرین معاملات | R",anchor="ne",fill=C["muted"],font=("Segoe UI",8))

    def draw_pie_chart(self,parent,rows):
        c=tk.Canvas(parent,bg=C["panel"],highlightthickness=0,height=270); c.pack(fill="x",padx=10,pady=6)
        wins=sum(1 for r in rows if result_num(r)>0); losses=sum(1 for r in rows if result_num(r)<0); be=max(len(rows)-wins-losses,0)
        counts=[wins,losses,be]; total=sum(counts)
        if total==0:
            c.create_text(340,120,text="هنوز داده‌ای برای نمودار نیست",fill=C["muted"],font=("Segoe UI",11)); return
        colors=[C["accent"],C["danger"],C["gold"]]; labels=["برد","باخت","خنثی"]
        start=0
        box=(120,30,340,250)
        for count,color,label in zip(counts,colors,labels):
            extent=360*count/total
            if count: c.create_arc(*box,start=start,extent=extent,fill=color,outline=C["panel"])
            start += extent
        y=60
        for count,color,label in zip(counts,colors,labels):
            c.create_rectangle(390,y,408,y+18,fill=color,outline=""); c.create_text(420,y+9,text=f"{label}: {count}",anchor="w",fill=C["text"],font=("Segoe UI",10))
            y+=34

    def daily(self):
        self.heading("برنامه روزانه","قابل ویرایش، قابل تیک‌زدن و ذخیره روی همان مسیر داده قبلی")
        nav=tk.Frame(self.content,bg=C["bg"]); nav.pack(fill="x",pady=4)
        self.btn(nav,"روز قبل",lambda:self.shift_day(-1)).pack(side="left")
        tk.Label(nav,text=self.day,bg=C["bg"],fg=C["text"],font=("Segoe UI",12,"bold")).pack(side="left",padx=15)
        self.btn(nav,"روز بعد",lambda:self.shift_day(1)).pack(side="left")
        self.btn(nav,"＋ فعالیت جدید",self.add_task,True).pack(side="right",padx=3)
        self.btn(nav,"ویرایش",self.edit_task).pack(side="right",padx=3); self.btn(nav,"حذف",self.delete_task).pack(side="right",padx=3)
        tasks=DB["tasks"].setdefault(self.day,[])
        wrap=tk.Frame(self.content,bg=C["bg"]); wrap.pack(fill="both",expand=True,pady=10)
        self.task_tree=ttk.Treeview(wrap,columns=("done","time","title","cat"),show="headings",selectmode="browse")
        for col,txt in [("done","✓"),("time","زمان"),("title","فعالیت"),("cat","دسته")]: self.task_tree.heading(col,text=txt)
        self.task_tree.column("done",width=55,anchor="center"); self.task_tree.column("time",width=100,anchor="center")
        self.task_tree.column("cat",width=160,anchor="e"); self.task_tree.column("title",anchor="e")
        for i,item in enumerate(tasks):
            self.task_tree.insert("", "end", iid=str(i), values=("☑" if item.get("done") else "☐",item.get("time",""),item.get("title",""),item.get("cat","")))
        self.task_tree.pack(side="left",fill="both",expand=True)
        ttk.Scrollbar(wrap,orient="vertical",command=self.task_tree.yview).pack(side="right",fill="y")
        self.task_tree.bind("<Double-1>",lambda e:self.toggle_selected_task())

    def toggle_selected_task(self):
        sel=self.task_tree.selection()
        if not sel:return
        idx=int(sel[0]); DB["tasks"][self.day][idx]["done"]=not bool(DB["tasks"][self.day][idx].get("done")); save_db(); self.show("daily")

    def shift_day(self,delta):
        self.day=(date.fromisoformat(self.day)+timedelta(days=delta)).isoformat()
        if not DB["tasks"].get(self.day):
            DB["tasks"][self.day]=[
                {"id":f"{self.day}-{i}","time":t,"title":title,"cat":cat,"done":False}
                for i,(t,title,cat) in enumerate(TASKS)
            ]
        save_db(); self.show("daily")

    def task_dialog(self,item=None):
        dlg=tk.Toplevel(self); dlg.title("ویرایش فعالیت" if item else "فعالیت جدید"); dlg.geometry("560x320"); dlg.configure(bg=C["bg"]); dlg.transient(self); dlg.grab_set()
        vals={k:tk.StringVar(value=(item or {}).get(k,"")) for k in ("time","title","cat")}
        for i,(label,key) in enumerate([("زمان","time"),("عنوان","title"),("دسته","cat")]):
            tk.Label(dlg,text=label,bg=C["bg"],fg=C["muted"]).grid(row=i,column=1,padx=14,pady=12,sticky="e")
            tk.Entry(dlg,textvariable=vals[key],bg=C["soft"],fg=C["text"],relief="flat",justify="right").grid(row=i,column=0,padx=14,pady=12,sticky="ew")
        dlg.columnconfigure(0,weight=1)
        def submit():
            if not vals["title"].get().strip(): return messagebox.showwarning("ورودی ناقص","عنوان فعالیت را وارد کن",parent=dlg)
            if item: item.update({k:v.get().strip() for k,v in vals.items()})
            else: DB["tasks"].setdefault(self.day,[]).append({"id":str(uuid4()),"time":vals["time"].get().strip(),"title":vals["title"].get().strip(),"cat":vals["cat"].get().strip(),"done":False})
            save_db(); dlg.destroy(); self.show("daily")
        self.btn(dlg,"ذخیره",submit,True).grid(row=4,column=0,padx=14,pady=16,sticky="e")
        self.btn(dlg,"انصراف",dlg.destroy).grid(row=4,column=1,padx=14,pady=16)

    def add_task(self): self.task_dialog()
    def edit_task(self):
        sel=self.task_tree.selection()
        if not sel:return messagebox.showinfo("انتخاب فعالیت","ابتدا یک فعالیت را انتخاب کن")
        self.task_dialog(DB["tasks"][self.day][int(sel[0])])
    def delete_task(self):
        sel=self.task_tree.selection()
        if not sel:return messagebox.showinfo("انتخاب فعالیت","ابتدا یک فعالیت را انتخاب کن")
        idx=int(sel[0]); item=DB["tasks"][self.day][idx]
        if messagebox.askyesno("حذف فعالیت",f"«{item.get('title','')}» حذف شود؟",parent=self):
            DB["tasks"][self.day].pop(idx); save_db(); self.show("daily")

    def journal(self):
        p=active_profile(); self.market=p["market"]; rows=p["journals"][self.market]
        self.heading(f"Journal — {self.market}",f"پروفایل: {p['name']} | ژورنال {self.market} مستقل از پروفایل‌های دیگر")
        bar=tk.Frame(self.content,bg=C["bg"]); bar.pack(fill="x",pady=3)
        self.btn(bar,"＋ ثبت معامله",self.add_trade,True).pack(side="left",padx=3)
        self.btn(bar,"ویرایش",self.edit_trade).pack(side="left",padx=3); self.btn(bar,"حذف",self.delete_trade).pack(side="left",padx=3)
        self.btn(bar,"خروجی CSV",self.export_journal).pack(side="left",padx=3)
        self.btn(bar,"باز کردن پوشه تصاویر",lambda:self.open_path(SCREENSHOTS / safe(p["id"]))).pack(side="left",padx=3)
        qv=tk.StringVar(); tk.Label(bar,text="جستجو:",bg=C["bg"],fg=C["muted"]).pack(side="right")
        ent=tk.Entry(bar,textvariable=qv,width=30,justify="right",bg=C["soft"],fg=C["text"],relief="flat"); ent.pack(side="right",padx=6)
        ent.bind("<KeyRelease>",lambda e:self.fill_journal_tree(qv.get()))
        self.jtree=ttk.Treeview(self.content,columns=("date","symbol","direction","session","tf","entry","sl","tp","r","pnl","setup","result"),show="headings",selectmode="browse")
        heads={"date":"تاریخ","symbol":"نماد","direction":"جهت","session":"سشن","tf":"TF","entry":"Entry","sl":"SL","tp":"TP","r":"R","pnl":"P&L","setup":"Setup","result":"نتیجه"}
        for col in self.jtree["columns"]:
            self.jtree.heading(col,text=heads[col]); self.jtree.column(col,width=95,anchor="center")
        self.jtree.column("symbol",width=115); self.jtree.column("setup",width=150)
        self.jtree.pack(fill="both",expand=True,pady=10)
        self.jtree.bind("<Double-1>",lambda e:self.edit_trade()); self.fill_journal_tree()

    def fill_journal_tree(self,q=""):
        for item in self.jtree.get_children(): self.jtree.delete(item)
        rows=active_profile()["journals"][self.market]; query=q.strip().lower()
        for i,row in enumerate(rows):
            if query and query not in " ".join(str(row.get(k,"")) for k in FIELDS).lower(): continue
            self.jtree.insert("", "end", iid=str(i), values=(
                row.get("Date",""),row.get("Symbol",""),row.get("Direction",""),row.get("Session",""),
                row.get("Timeframe",""),row.get("Entry",""),row.get("Stop Loss",""),row.get("Take Profit",""),
                row.get("Result (R)",""),row.get("P&L",""),row.get("Setup",""),row.get("Result","")
            ))

    def edit_trade(self):
        sel=self.jtree.selection()
        if not sel:return messagebox.showinfo("انتخاب معامله","ابتدا یک معامله را انتخاب کن")
        self.trade_dialog(active_profile()["journals"][self.market][int(sel[0])],int(sel[0]))
    def delete_trade(self):
        sel=self.jtree.selection()
        if not sel:return messagebox.showinfo("انتخاب معامله","ابتدا یک معامله را انتخاب کن")
        idx=int(sel[0]); row=active_profile()["journals"][self.market][idx]
        if messagebox.askyesno("حذف معامله",f"معامله {row.get('Symbol','')} حذف شود؟",parent=self):
            active_profile()["journals"][self.market].pop(idx); save_db(); self.show("journal")
    def add_trade(self): self.trade_dialog()

    def trade_dialog(self,row=None,index=None):
        dlg=tk.Toplevel(self); dlg.title(("ویرایش" if row else "ثبت")+f" معامله — {self.market}"); dlg.geometry("1180x800"); dlg.minsize(1020,700); dlg.configure(bg=C["bg"]); dlg.transient(self); dlg.grab_set()
        outer=tk.Frame(dlg,bg=C["bg"]); outer.pack(fill="both",expand=True,padx=18,pady=14)
        left=self.card(outer); right=self.card(outer); left.pack(side="left",fill="both",expand=True,padx=6); right.pack(side="left",fill="both",expand=True,padx=6)
        vals={}; widgets={}
        groups_left=[("اطلاعات معامله",["Date","Symbol","Direction","Session","Timeframe"]),("قیمت و ریسک",["Entry","Stop Loss","Take Profit","Position Size","Risk %","Risk $","R:R"]),("تحلیل",["Setup","Market Structure","Liquidity","Entry Model"])]
        groups_right=[("روانشناسی",["Emotion Before","Emotion During","Emotion After","Mistake"]),("نتیجه",["Result","Result (R)","P&L","Lesson","Notes"]),("اسکرین‌شات",["Screenshot"])]
        options={
            "Direction":["LONG","SHORT"],"Result":["WIN","LOSS","BE"],
            "Session":["Asia","London","New York","Overlap","Other"],
            "Timeframe":["1m","3m","5m","15m","30m","1H","4H","D","W"],
            "Emotion Before":["Calm","Focused","FOMO","Fear","Greedy","Neutral"],
            "Emotion During":["Calm","Focused","FOMO","Fear","Greedy","Neutral"],
            "Emotion After":["Satisfied","Neutral","Frustrated","Angry","Confident"],
        }
        def section(parent,title,fields):
            box=tk.Frame(parent,bg=C["panel2"]); box.pack(fill="x",padx=12,pady=7)
            tk.Label(box,text=title,bg=C["panel2"],fg=C["accent"],font=("Segoe UI",12,"bold")).grid(row=0,column=0,columnspan=2,sticky="e",padx=8,pady=(9,5))
            for r,key in enumerate(fields,1):
                tk.Label(box,text=key,bg=C["panel2"],fg=C["muted"],font=("Segoe UI",9)).grid(row=r,column=1,padx=7,pady=5,sticky="e")
                v=tk.StringVar(value=str((row or {}).get(key,""))); vals[key]=v
                w=ttk.Combobox(box,textvariable=v,values=options[key],state="readonly",justify="right") if key in options else tk.Entry(box,textvariable=v,justify="right",bg=C["soft"],fg=C["text"],relief="flat")
                widgets[key]=w; w.grid(row=r,column=0,padx=7,pady=5,sticky="ew"); box.columnconfigure(0,weight=1)
        for t,f in groups_left: section(left,t,f)
        for t,f in groups_right: section(right,t,f)
        if not row:
            vals["Date"].set(date.today().isoformat()); vals["Direction"].set("LONG"); vals["Result"].set("BE")
        shot=widgets["Screenshot"]
        controls=tk.Frame(shot.master,bg=C["panel2"]); controls.grid(row=2,column=0,columnspan=2,sticky="ew",padx=7,pady=(0,8))
        def browse():
            src=filedialog.askopenfilename(title="انتخاب اسکرین‌شات",filetypes=[("Images","*.png *.jpg *.jpeg *.webp *.bmp"),("All","*.*")],parent=dlg)
            if src: vals["Screenshot"].set(src)
        self.btn(controls,"انتخاب تصویر",browse).pack(side="left")
        self.btn(controls,"باز کردن پوشه",lambda:self.open_path(screenshot_folder({"Date":vals["Date"].get(),"Symbol":vals["Symbol"].get()}))).pack(side="left",padx=6)
        footer=tk.Frame(dlg,bg=C["bg"]); footer.pack(fill="x",padx=24,pady=8)
        def submit():
            data={k:v.get().strip() for k,v in vals.items()}
            if not data.get("Symbol"): return messagebox.showwarning("ورودی ناقص","Symbol را وارد کن",parent=dlg)
            src=data.get("Screenshot","")
            if src and Path(src).is_file(): data["Screenshot"]=attach_screenshot(data,src,market=self.market)
            elif row is not None: data["Screenshot"]=row.get("Screenshot","")
            upsert_trade(active_profile(),self.market,data,index); save_db(); dlg.destroy(); self.show("journal")
        self.btn(footer,"ذخیره معامله",submit,True).pack(side="right",padx=5); self.btn(footer,"انصراف",dlg.destroy).pack(side="right",padx=5)

    def export_journal(self):
        rows=active_profile()["journals"][self.market]
        if not rows:return messagebox.showinfo("ژورنال خالی","معامله‌ای برای خروجی وجود ندارد",parent=self)
        target=filedialog.asksaveasfilename(title="ذخیره CSV",defaultextension=".csv",initialfile=f"{self.market}_Journal_{date.today().isoformat()}.csv",filetypes=[("CSV","*.csv")])
        if not target:return
        with open(target,"w",newline="",encoding="utf-8-sig") as h:
            writer=csv.DictWriter(h,fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)
        messagebox.showinfo("انجام شد","خروجی CSV ذخیره شد",parent=self)

    def plan(self):
        p=active_profile()
        self.heading("Trading Plan", self.tr("plan_sub"))
        toolbar=tk.Frame(self.content,bg=C["bg"]); toolbar.pack(fill="x",pady=4)
        self.btn(toolbar,self.tr("save_plan"),self.save_plan,True).pack(side="left",padx=3)
        self.btn(toolbar,self.tr("export_a4"),self.export_current_plan).pack(side="left",padx=3)
        self.btn(toolbar,self.tr("saved_versions"),self.plan_history).pack(side="left",padx=3)
        title_var=tk.StringVar(value=self.current_plan_title())
        tk.Label(toolbar,text=self.tr("current_version"),bg=C["bg"],fg=C["muted"]).pack(side="right",padx=5)
        tk.Entry(toolbar,textvariable=title_var,width=34,justify="right",bg=C["soft"],fg=C["text"],relief="flat").pack(side="right")
        wrap=tk.Frame(self.content,bg=C["bg"]); wrap.pack(fill="both",expand=True,pady=8)
        left=self.card(wrap); right=self.card(wrap)
        left.pack(side="left",fill="both",expand=True,padx=4); right.pack(side="left",fill="both",expand=True,padx=4)
        draft=p["plan_draft"]
        for i,key in enumerate(PLAN_FIELDS):
            parent=left if i < len(PLAN_FIELDS)//2+1 else right
            tk.Label(parent,text=key,bg=C["panel"],fg=C["muted"],font=("Segoe UI",9,"bold")).pack(anchor="e",padx=14,pady=(9,2))
            value=tk.StringVar(value=draft.get(key,""))
            ent=tk.Entry(parent,textvariable=value,justify="right",bg=C["soft"],fg=C["text"],relief="flat")
            ent.pack(fill="x",padx=14,pady=(0,8)); ent.bind("<FocusOut>",lambda e,k=key,v=value:self.plan_save(k,v))
        self._plan_title_var=title_var

    def current_plan_title(self):
        p=active_profile()
        for plan in p["plans"]:
            if plan.get("id")==p.get("active_plan_id"): return plan.get("title","Trading Plan")
        return "Trading Plan"

    def plan_save(self,key,value):
        active_profile()["plan_draft"][key]=value.get(); active_profile()["updated_at"]=datetime.now().isoformat(timespec="seconds"); save_db()

    def save_plan(self):
        p=active_profile(); title=(getattr(self,"_plan_title_var",None).get().strip() if getattr(self,"_plan_title_var",None) else "")
        title=title or "Trading Plan"
        item={"id":str(uuid4()),"title":title,"created_at":datetime.now().isoformat(timespec="seconds"),"fields":dict(p["plan_draft"])}
        p["plans"].append(item); p["active_plan_id"]=item["id"]; save_db()
        messagebox.showinfo("ذخیره شد",f"نسخه «{title}» ذخیره شد.",parent=self); self.show("plan")

    def plan_history(self):
        p=active_profile(); dlg=tk.Toplevel(self); dlg.title("نسخه‌های Trading Plan"); dlg.geometry("680x500"); dlg.configure(bg=C["bg"]); dlg.transient(self); dlg.grab_set()
        tree=ttk.Treeview(dlg,columns=("title","date"),show="headings"); tree.heading("title",text="عنوان"); tree.heading("date",text="تاریخ"); tree.column("title",width=400); tree.pack(fill="both",expand=True,padx=15,pady=15)
        for i,item in enumerate(p["plans"]): tree.insert("", "end",iid=str(i),values=(item.get("title",""),item.get("created_at","")))
        def load():
            sel=tree.selection()
            if not sel:return
            item=p["plans"][int(sel[0])]; p["plan_draft"]=dict(item.get("fields",{})); p["active_plan_id"]=item["id"]; save_db(); dlg.destroy(); self.show("plan")
        self.btn(dlg,"باز کردن نسخه انتخاب‌شده",load,True).pack(side="right",padx=15,pady=10)

    def export_current_plan(self):
        p=active_profile(); title=self.current_plan_title(); path=export_plan_a4(p,title,p["plan_draft"])
        messagebox.showinfo("Export آماده شد",f"فایل A4 ساخته شد:\n{path}",parent=self)

    def check(self):
        p=active_profile()
        self.heading(self.tr("check_title"), self.tr("check_sub"))
        top=self.card(self.content); top.pack(fill="x",pady=6)
        left=tk.Frame(top,bg=C["panel"]); left.pack(side="left",fill="x",expand=True,padx=12,pady=10)
        self.btn(left,self.tr("add_condition"),self.add_check_item,True).pack(side="left",padx=3)
        self.btn(left,self.tr("from_plan"),self.sync_check_from_plan).pack(side="left",padx=3)
        self.check_progress_label=tk.Label(top,text="",bg=C["panel"],fg=C["gold"],font=("Segoe UI",10,"bold"))
        self.check_progress_label.pack(side="right",padx=16)
        body=tk.Frame(self.content,bg=C["bg"]); body.pack(fill="both",expand=True,pady=6)
        self.check_canvas=tk.Canvas(body,bg=C["bg"],highlightthickness=0,borderwidth=0)
        scrollbar=ttk.Scrollbar(body,orient="vertical",command=self.check_canvas.yview)
        self.check_list_frame=tk.Frame(self.check_canvas,bg=C["bg"])
        self.check_window=self.check_canvas.create_window((0,0),window=self.check_list_frame,anchor="nw")
        self.check_canvas.configure(yscrollcommand=scrollbar.set)
        self.check_list_frame.bind("<Configure>",lambda e:self.check_canvas.configure(scrollregion=self.check_canvas.bbox("all")))
        self.check_canvas.bind("<Configure>",lambda e:self.check_canvas.itemconfigure(self.check_window,width=e.width))
        self.check_canvas.pack(side="left",fill="both",expand=True); scrollbar.pack(side="right",fill="y")
        self.check_canvas.bind_all("<MouseWheel>",self._check_mousewheel)
        self.render_checklist()

    def _check_mousewheel(self,event):
        try: self.check_canvas.yview_scroll(int(-1*(event.delta/120)),"units")
        except Exception: pass

    def render_checklist(self):
        p=active_profile(); items=p.get("checklist",[])
        for w in self.check_list_frame.winfo_children(): w.destroy()
        done=sum(1 for x in items if x.get("done"))
        self.check_progress_label.config(text=self.tr("check_progress",done=done,total=len(items)))
        if not items:
            box=self.card(self.check_list_frame); box.pack(fill="x",padx=4,pady=20)
            tk.Label(box,text=self.tr("no_checklist"),bg=C["panel"],fg=C["muted"],font=("Segoe UI",12)).pack(pady=35)
            return
        for idx,item in enumerate(items):
            self._check_row(idx,item)

    def _check_row(self,index,item):
        row=tk.Frame(self.check_list_frame,bg=C["panel"],highlightbackground=C["line"],highlightthickness=1)
        row.pack(fill="x",padx=4,pady=5)
        num=tk.Label(row,text=f"{index+1:02d}",bg=C["panel2"],fg=C["gold"],font=("Segoe UI",10,"bold"),width=4)
        num.pack(side="left",padx=(8,4),pady=8)
        toggle=tk.Button(row,text="☑" if item.get("done") else "☐",command=lambda i=index:self.toggle_check(i),
                         bg=C["accent"] if item.get("done") else C["soft"],fg="#061019" if item.get("done") else C["text"],
                         relief="flat",font=("Segoe UI",11,"bold"),width=3,pady=4)
        toggle.pack(side="left",padx=4,pady=8)
        info=tk.Frame(row,bg=C["panel"]); info.pack(side="left",fill="both",expand=True,padx=10,pady=8)
        title=item.get("title","")
        title_btn=tk.Button(info,text=title,command=lambda i=index:self.edit_check_index(i),anchor="e",justify="right",
                            wraplength=760,bg=C["panel"],fg=C["text"],activebackground=C["panel"],activeforeground=C["accent"],
                            relief="flat",font=("Segoe UI",11,"bold"),cursor="hand2")
        title_btn.pack(fill="x",anchor="e")
        meta=tk.Frame(info,bg=C["panel"]); meta.pack(fill="x",pady=(5,0))
        tk.Label(meta,text=f"{self.tr('condition_category') if self.language=='en' else 'دسته'}: {item.get('category') or self.tr('general')}",
                 bg=C["panel"],fg=C["muted"],font=("Segoe UI",9)).pack(side="left",padx=4)
        tk.Label(meta,text=f"{self.tr('condition_source') if self.language=='en' else 'منبع'}: {item.get('source') or self.tr('manual')}",
                 bg=C["panel"],fg=C["muted"],font=("Segoe UI",9)).pack(side="left",padx=12)
        required=tk.Label(meta,text=self.tr("required"),bg=C["soft"],fg=C["text"],font=("Segoe UI",8,"bold"),padx=7,pady=3)
        required.pack(side="right",padx=4)
        controls=tk.Frame(row,bg=C["panel"]); controls.pack(side="right",padx=8,pady=8)
        self.btn(controls,self.tr("edit_row"),lambda i=index:self.edit_check_index(i)).pack(fill="x",pady=2)
        self.btn(controls,self.tr("move_up"),lambda i=index:self.move_check_index(i,-1)).pack(fill="x",pady=2)
        self.btn(controls,self.tr("move_down"),lambda i=index:self.move_check_index(i,1)).pack(fill="x",pady=2)
        self.btn(controls,self.tr("remove"),lambda i=index:self.delete_check_index(i)).pack(fill="x",pady=2)

    def toggle_check(self,index):
        p=active_profile()
        if not 0 <= index < len(p["checklist"]): return
        p["checklist"][index]["done"]=not p["checklist"][index].get("done",False)
        save_db(); self.render_checklist()

    def add_check_item(self):
        self.check_item_dialog()

    def edit_check_item(self):
        return

    def delete_check_item(self):
        return

    def move_check(self,delta):
        return

    def edit_check_index(self,index):
        p=active_profile()
        if 0 <= index < len(p["checklist"]):
            self.check_item_dialog(p["checklist"][index],index)

    def delete_check_index(self,index):
        p=active_profile()
        if not 0 <= index < len(p["checklist"]): return
        item=p["checklist"][index]
        if messagebox.askyesno(self.tr("delete_item"),item.get("title",""),parent=self):
            p["checklist"].pop(index); save_db(); self.render_checklist()

    def move_check_index(self,index,delta):
        p=active_profile(); j=index+delta
        if not 0 <= index < len(p["checklist"]) or not 0 <= j < len(p["checklist"]): return
        p["checklist"][index],p["checklist"][j]=p["checklist"][j],p["checklist"][index]
        save_db(); self.render_checklist()

    def sync_check_from_plan(self):
        p=active_profile(); items=[]
        for key,value in p["plan_draft"].items():
            value=str(value).strip()
            if value:
                items.append({"id":str(uuid4()),"title":f"{key}: {value}","category":self.tr("trading_plan"),"required":True,"done":False,"source":"Trading Plan"})
        if not items:
            return messagebox.showinfo(self.tr("check_title"),self.tr("empty_plan"),parent=self)
        p["checklist"] = items + [x for x in p["checklist"] if x.get("source") not in ("Trading Plan","Strategy")]
        save_db(); self.render_checklist()

    def check_item_dialog(self,item=None,index=None):
        dlg=tk.Toplevel(self)
        dlg.title(self.tr("check_item"))
        dlg.geometry("700x470"); dlg.minsize(620,420); dlg.configure(bg=C["bg"]); dlg.transient(self); dlg.grab_set()
        outer=self.card(dlg); outer.pack(fill="both",expand=True,padx=18,pady=18)
        tk.Label(outer,text=self.tr("condition_title"),bg=C["panel"],fg=C["muted"],font=("Segoe UI",9,"bold")).pack(anchor="e",padx=18,pady=(16,4))
        title_box=tk.Text(outer,height=5,wrap="word",bg=C["soft"],fg=C["text"],insertbackground=C["text"],relief="flat",font=("Segoe UI",11))
        title_box.pack(fill="x",padx=18,pady=(0,12))
        title_box.insert("1.0",str((item or {}).get("title","")))
        form=tk.Frame(outer,bg=C["panel"]); form.pack(fill="x",padx=18)
        vals={k:tk.StringVar(value=str((item or {}).get(k,""))) for k in ("category","source")}
        for r,(label,key) in enumerate(((self.tr("condition_category"),"category"),(self.tr("condition_source"),"source"))):
            tk.Label(form,text=label,bg=C["panel"],fg=C["muted"],font=("Segoe UI",9,"bold")).grid(row=r,column=1,padx=8,pady=8,sticky="e")
            ent=tk.Entry(form,textvariable=vals[key],bg=C["soft"],fg=C["text"],relief="flat",justify="right")
            ent.grid(row=r,column=0,padx=8,pady=8,sticky="ew")
        form.columnconfigure(0,weight=1)
        req=tk.BooleanVar(value=bool((item or {}).get("required",True)))
        tk.Checkbutton(outer,text=self.tr("required_item"),variable=req,bg=C["panel"],fg=C["text"],selectcolor=C["soft"],
                       activebackground=C["panel"],activeforeground=C["text"],anchor="e").pack(fill="x",padx=18,pady=10)
        footer=tk.Frame(outer,bg=C["panel"]); footer.pack(fill="x",padx=18,pady=(8,16))
        def submit():
            title=title_box.get("1.0","end").strip()
            if not title:
                return messagebox.showwarning(self.tr("check_item"),self.tr("condition_title"),parent=dlg)
            data={"id":(item or {}).get("id",str(uuid4())),"title":title,
                  "category":vals["category"].get().strip() or self.tr("general"),
                  "source":vals["source"].get().strip() or self.tr("manual"),
                  "required":req.get(),"done":bool((item or {}).get("done",False))}
            if item is None: active_profile()["checklist"].append(data)
            else: active_profile()["checklist"][index]=data
            save_db(); dlg.destroy(); self.render_checklist()
        self.btn(footer,self.tr("cancel"),dlg.destroy).pack(side="right",padx=4)
        self.btn(footer,self.tr("save"),submit,True).pack(side="right",padx=4)

    def settings(self):
        p=active_profile()
        self.heading(self.tr("settings_title"), self.tr("settings_sub"))
        lang_box=self.card(self.content); lang_box.pack(fill="x",pady=10)
        tk.Label(lang_box,text=self.tr("choose_language"),bg=C["panel"],fg=C["text"],font=("Segoe UI",13,"bold")).pack(anchor="e",padx=18,pady=(18,6))
        tk.Label(lang_box,text=self.tr("language_help"),bg=C["panel"],fg=C["muted"],font=("Segoe UI",9)).pack(anchor="e",padx=18,pady=(0,14))
        current=tk.StringVar(value=self.language)
        row=tk.Frame(lang_box,bg=C["panel"]); row.pack(fill="x",padx=18,pady=(0,18))
        fa_btn=tk.Button(row,text="فارسی",command=lambda:self.set_language("fa"),bg=C["accent"] if self.language=="fa" else C["soft"],
                         fg="#061019" if self.language=="fa" else C["text"],relief="flat",font=("Segoe UI",11,"bold"),padx=30,pady=12)
        en_btn=tk.Button(row,text="English",command=lambda:self.set_language("en"),bg=C["accent"] if self.language=="en" else C["soft"],
                         fg="#061019" if self.language=="en" else C["text"],relief="flat",font=("Segoe UI",11,"bold"),padx=30,pady=12)
        fa_btn.pack(side="right",padx=6); en_btn.pack(side="right",padx=6)
        tk.Label(row,text=f"{self.tr('language_now')}: {'فارسی' if self.language=='fa' else 'English'}",
                 bg=C["panel"],fg=C["gold"],font=("Segoe UI",10,"bold")).pack(side="left",padx=10)
        profile_box=self.card(self.content); profile_box.pack(fill="x",pady=10)
        info=(f"{self.tr('profile')}: {p['name']}\n"
              f"{self.tr('market')}: {p['market']}\n"
              f"{self.tr('initial_balance')}: {p['initial_balance']:,.2f} {p['currency']}\n"
              f"{self.tr('data_path')}: {DATA}\n{self.tr('reports_path')}: {REPORTS}")
        tk.Label(profile_box,text=info,bg=C["panel"],fg=C["muted"],justify="right",font=("Segoe UI",10)).pack(anchor="e",padx=18,pady=18)
        self.btn(profile_box,self.tr("manage_profiles"),self.edit_profile,True).pack(anchor="e",padx=18,pady=10)

    def academy(self):
        self.heading(self.tr("academy_title"), self.tr("academy_sub"))
        note=tk.Label(self.content,text=ACADEMY_NOTE_FA if self.language=="fa" else ACADEMY_NOTE_EN,
                      bg=C["panel2"],fg=C["muted"],wraplength=1180,justify="right",padx=14,pady=10)
        note.pack(fill="x",pady=(0,10))
        nb=ttk.Notebook(self.content)
        nb.pack(fill="both",expand=True)
        tab_smc=tk.Frame(nb,bg=C["bg"]); tab_ict=tk.Frame(nb,bg=C["bg"]); tab_candle=tk.Frame(nb,bg=C["bg"]); tab_gloss=tk.Frame(nb,bg=C["bg"])
        nb.add(tab_smc,text=self.tr("smc")); nb.add(tab_ict,text=self.tr("ict")); nb.add(tab_candle,text=self.tr("candles")); nb.add(tab_gloss,text=self.tr("glossary"))
        self._academy_notebook=nb
        self._build_strategy_tab(tab_smc,SMART_MONEY_STRATEGIES)
        self._build_strategy_tab(tab_ict,ICT_STRATEGIES)
        self._build_candle_tab(tab_candle)
        self._build_glossary_tab(tab_gloss)

    def _build_strategy_tab(self,parent,items):
        outer=tk.PanedWindow(parent,orient="horizontal",bg=C["bg"],sashwidth=6,showhandle=False)
        outer.pack(fill="both",expand=True,padx=8,pady=8)
        left=tk.Frame(outer,bg=C["panel"]); right=tk.Frame(outer,bg=C["panel"])
        outer.add(left,minsize=330); outer.add(right,minsize=620)
        lb=tk.Listbox(left,bg=C["panel2"],fg=C["text"],selectbackground=C["accent"],selectforeground="#061019",
                      font=("Segoe UI",10,"bold"),activestyle="none",borderwidth=0,highlightthickness=0)
        lb.pack(fill="both",expand=True,padx=8,pady=8)
        for item in items: lb.insert("end",item["name_fa"] if self.language=="fa" else item["name_en"])
        title=tk.Label(right,text="",bg=C["panel"],fg=C["gold"],font=("Segoe UI",16,"bold"),anchor="e",justify="right")
        title.pack(fill="x",padx=18,pady=(16,8))
        summary=tk.Label(right,text="",bg=C["panel"],fg=C["text"],font=("Segoe UI",10),anchor="e",justify="right",wraplength=700)
        summary.pack(fill="x",padx=18,pady=6)
        steps_frame=tk.Frame(right,bg=C["panel"]); steps_frame.pack(fill="both",expand=True,padx=18,pady=8)
        text=tk.Text(steps_frame,bg=C["soft"],fg=C["text"],insertbackground=C["text"],relief="flat",wrap="word",font=("Segoe UI",10),height=18)
        text.pack(side="left",fill="both",expand=True)
        scr=ttk.Scrollbar(steps_frame,orient="vertical",command=text.yview); scr.pack(side="right",fill="y"); text.configure(yscrollcommand=scr.set)
        def render(_=None):
            sel=lb.curselection()
            if not sel: return
            item=items[sel[0]]
            title.config(text=item["name_fa"] if self.language=="fa" else item["name_en"])
            summary.config(text=item["summary_fa"] if self.language=="fa" else item["summary_en"])
            lines=(item["steps_fa"] if self.language=="fa" else item["steps_en"])
            inv=item["risk_fa"] if self.language=="fa" else item["risk_en"]
            text.configure(state="normal"); text.delete("1.0","end")
            text.insert("end",self.tr("steps")+"\n\n")
            for i,line in enumerate(lines,1): text.insert("end",f"{i}. {line}\n")
            text.insert("end","\n"+self.tr("invalidation")+"\n\n"+inv)
            text.configure(state="disabled")
        lb.bind("<<ListboxSelect>>",render)
        if items: lb.selection_set(0); lb.event_generate("<<ListboxSelect>>")

    def _build_candle_tab(self,parent):
        wrap=tk.Frame(parent,bg=C["panel"]); wrap.pack(fill="both",expand=True,padx=8,pady=8)
        left=tk.Frame(wrap,bg=C["panel"]); left.pack(side="left",fill="both",expand=True,padx=8,pady=8)
        right=tk.Frame(wrap,bg=C["panel"]); right.pack(side="left",fill="both",expand=True,padx=8,pady=8)
        lb=tk.Listbox(left,bg=C["panel2"],fg=C["text"],selectbackground=C["accent"],selectforeground="#061019",
                      font=("Segoe UI",10,"bold"),activestyle="none",borderwidth=0,highlightthickness=0)
        lb.pack(fill="both",expand=True)
        for name,en,fa in CANDLE_PLAYBOOK:
            lb.insert("end", fa if self.language=="fa" else name)
        tk.Label(right,text=("الگوهای کندلی" if self.language=="fa" else "Candlestick Patterns"),bg=C["panel"],fg=C["gold"],font=("Segoe UI",15,"bold")).pack(anchor="e",padx=12,pady=12)
        desc=tk.Label(right,text="",bg=C["panel"],fg=C["text"],font=("Segoe UI",10),wraplength=650,justify="right")
        desc.pack(fill="both",expand=True,padx=16,pady=16)
        def render(_=None):
            if not lb.curselection(): return
            name,en,fa=CANDLE_PLAYBOOK[lb.curselection()[0]]
            desc.config(text=(f"{name}\n\n{fa}" if self.language=="fa" else f"{name}\n\n{fa}"))
        lb.bind("<<ListboxSelect>>",render)
        if CANDLE_PLAYBOOK: lb.selection_set(0); lb.event_generate("<<ListboxSelect>>")

    def _build_glossary_tab(self,parent):
        bar=tk.Frame(parent,bg=C["panel"]); bar.pack(fill="x",padx=8,pady=8)
        q=tk.StringVar()
        entry=tk.Entry(bar,textvariable=q,bg=C["soft"],fg=C["text"],insertbackground=C["text"],relief="flat",justify="right",font=("Segoe UI",10))
        entry.pack(side="right",fill="x",expand=True,padx=8,pady=10)
        tk.Label(bar,text=self.tr("search_term"),bg=C["panel"],fg=C["muted"]).pack(side="right")
        cat=tk.StringVar(value="ALL")
        cats=["ALL"]+sorted({x["category"] for x in GLOSSARY})
        combo=ttk.Combobox(bar,textvariable=cat,values=cats,state="readonly",width=24,justify="right"); combo.pack(side="left",padx=8,pady=8)
        body=tk.PanedWindow(parent,orient="horizontal",bg=C["bg"],sashwidth=6); body.pack(fill="both",expand=True,padx=8,pady=(0,8))
        left=tk.Frame(body,bg=C["panel"]); right=tk.Frame(body,bg=C["panel"]); body.add(left,minsize=360); body.add(right,minsize=600)
        tree=ttk.Treeview(left,columns=("term","category"),show="headings",selectmode="browse")
        tree.heading("term",text="Term"); tree.heading("category",text="Category"); tree.column("term",width=260); tree.column("category",width=120)
        tree.pack(fill="both",expand=True,padx=8,pady=8)
        title=tk.Label(right,text="",bg=C["panel"],fg=C["gold"],font=("Segoe UI",15,"bold"),justify="right",anchor="e")
        title.pack(fill="x",padx=18,pady=(14,8))
        meaning=tk.Label(right,text="",bg=C["panel"],fg=C["text"],font=("Segoe UI",10),wraplength=720,justify="right",anchor="e")
        meaning.pack(fill="x",padx=18,pady=8)
        usage=tk.Label(right,text="",bg=C["panel"],fg=C["muted"],font=("Segoe UI",10),wraplength=720,justify="right",anchor="e")
        usage.pack(fill="x",padx=18,pady=8)
        def refresh(*_):
            term=q.get().strip().lower(); selected_cat=cat.get()
            for x in tree.get_children(): tree.delete(x)
            matched=[]
            for i,item in enumerate(GLOSSARY):
                text=" ".join([item["term"],item["fa"],item["en"],item["category"],item["meaning_fa"],item["meaning_en"],item["usage_fa"],item["usage_en"]]).lower()
                if term and term not in text: continue
                if selected_cat!="ALL" and item["category"]!=selected_cat: continue
                matched.append(i); tree.insert("", "end",iid=str(i),values=(item["term"],item["category"]))
            if matched:
                tree.selection_set(str(matched[0])); render()
        def render(_=None):
            sel=tree.selection()
            if not sel: return
            item=GLOSSARY[int(sel[0])]
            title.config(text=item["term"]+"  |  "+(item["fa"] if self.language=="fa" else item["en"]))
            meaning.config(text=(self.tr("definition")+"\n"+(item["meaning_fa"] if self.language=="fa" else item["meaning_en"])))
            usage.config(text=(self.tr("usage")+"\n"+(item["usage_fa"] if self.language=="fa" else item["usage_en"])))
        tree.bind("<<TreeviewSelect>>",render); entry.bind("<KeyRelease>",refresh); combo.bind("<<ComboboxSelected>>",refresh)
        refresh()
        tk.Label(parent,text=f"{len(GLOSSARY)} terms",bg=C["bg"],fg=C["muted"],font=("Segoe UI",8)).pack(anchor="e",padx=10,pady=(0,6))

    def open_path(self,path):
        path=Path(path); path.mkdir(parents=True,exist_ok=True)
        try:
            if sys.platform.startswith("win"): os.startfile(str(path))
            elif sys.platform=="darwin": os.system(f'open "{path}"')
            else: os.system(f'xdg-open "{path}"')
        except OSError as exc:
            messagebox.showerror("خطا",str(exc),parent=self)

def tempfile_path():
    path = ROOT / "cache"
    path.mkdir(parents=True, exist_ok=True)
    return path / "trader_planner_pro_3d_logo.png"

if __name__ == "__main__":
    save_db()
    App().mainloop()
