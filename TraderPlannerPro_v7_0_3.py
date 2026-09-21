from __future__ import annotations

import csv
import json
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import webbrowser
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from logo_3d import create_logo_image
from academy_content import SMART_MONEY_STRATEGIES, ICT_STRATEGIES, CANDLE_PLAYBOOK, GLOSSARY, ACADEMY_NOTE_FA, ACADEMY_NOTE_EN
from academy_visuals import render_visual, visual_key_for, source_for_visual, strategy_visual_key, pattern_visual_key, glossary_visual_key, bundled_asset_for_visual
from academy_diagrams import draw_setup, draw_candlestick
from glass_theme import apply_glass, set_widget_glass
from market_data import MarketDataService, cached_market_payload
from calendar_utils import display_date
from ai_assistant import AIOrchestrator
from news_data import fetch_market_news, COINDESK_HOME, COINDESK_RSS, CRYPTO_NEWS_HOME, FOREX_FACTORY
from google_oauth import google_status, login_google, logout_google, send_gmail, find_client_file
from statement_report import create_statement

APP = "Trader Planner Pro"
VERSION = "8.0.0"
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
THEMES = {
    "dark": {
        "bg":"#0A1018","panel":"#111A26","panel2":"#172230","soft":"#1D2B3A","text":"#EAF2F7","muted":"#90A3B3",
        "accent":"#27D3B0","gold":"#F2C46D","danger":"#FF6F7D","line":"#27384A","blue":"#63A7FF","shadow":"#050911",
        "panel3":"#0E1824","violet":"#9B8CFF","cyan":"#55D6FF"
    },
    "light": {
        "bg":"#F4F7FA","panel":"#FFFFFF","panel2":"#EEF3F7","soft":"#E4EBF1","text":"#17212B","muted":"#5F6F7C",
        "accent":"#0B9E83","gold":"#A96800","danger":"#C63A4D","line":"#CBD6DF","blue":"#2D74C8","shadow":"#C7D0D8",
        "panel3":"#F0F4F7","violet":"#6F56C8","cyan":"#087EA4"
    }
}

SKINS = {
    "glass": {
        "label_fa":"Acrylic Glass • شیشه‌ای واقعی", "label_en":"Acrylic Glass • Native",
        "dark":{"panel":"#101826","panel2":"#132033","soft":"#1A2A40","panel3":"#0A1320","line":"#294A62","accent":"#36E0C0","cyan":"#62DFFF","gold":"#F6D889","violet":"#A88EFF"},
        "light":{"panel":"#F7FBFD","panel2":"#EDF5F8","soft":"#E2EEF3","panel3":"#F0F7F9","line":"#C6D8E2","accent":"#0E987E","cyan":"#1683A3","gold":"#976600","violet":"#6E55C6"},
    },
    "obsidian": {
        "label_fa":"Obsidian • شیشه‌ای تیره", "label_en":"Obsidian • Dark Glass",
        "dark":{"panel":"#0F1520","panel2":"#151E2B","soft":"#1B2736","panel3":"#0B111A","line":"#26384A","accent":"#27D3B0","cyan":"#56E0FF","gold":"#FFD166","violet":"#9B8CFF"},
        "light":{"panel":"#FFFFFF","panel2":"#F3F7FA","soft":"#E9F0F4","panel3":"#EEF4F7","line":"#CED9E0","accent":"#0C9F85","cyan":"#087EA4","gold":"#9B6500","violet":"#6F56C8"},
    },
    "aurora": {
        "label_fa":"Aurora • نئونی", "label_en":"Aurora • Neon",
        "dark":{"panel":"#11142A","panel2":"#171B37","soft":"#20264A","panel3":"#0C1020","line":"#343A63","accent":"#65F2C6","cyan":"#67D8FF","gold":"#F6D77A","violet":"#B58CFF"},
        "light":{"panel":"#FFFFFF","panel2":"#F2F3FF","soft":"#E8EBFF","panel3":"#EFF1FF","line":"#C9D0ED","accent":"#147F6B","cyan":"#1877A6","gold":"#9B6500","violet":"#6E4BC4"},
    },
    "graphite": {
        "label_fa":"Graphite • مینیمال", "label_en":"Graphite • Minimal",
        "dark":{"panel":"#16181C","panel2":"#1D2026","soft":"#252A31","panel3":"#111317","line":"#373E48","accent":"#7DE2D1","cyan":"#7CC7FF","gold":"#EBCB8B","violet":"#B8A4FF"},
        "light":{"panel":"#FFFFFF","panel2":"#F5F6F7","soft":"#EAEDF0","panel3":"#F2F4F5","line":"#D2D7DC","accent":"#147D6B","cyan":"#246FA8","gold":"#946300","violet":"#6C55BC"},
    },
    "pearl": {
        "label_fa":"Pearl • روشن حرفه‌ای", "label_en":"Pearl • Light Pro",
        "dark":{"panel":"#10161D","panel2":"#172029","soft":"#202B36","panel3":"#0C1116","line":"#2F3D49","accent":"#8ED6FF","cyan":"#70D7FF","gold":"#F0C96A","violet":"#BBA3FF"},
        "light":{"panel":"#FFFFFF","panel2":"#F7FAFC","soft":"#EDF2F6","panel3":"#F2F7FA","line":"#D6E0E7","accent":"#176EA6","cyan":"#0B7FA7","gold":"#956500","violet":"#6D57BA"},
    },
    "midnight": {
        "label_fa":"Midnight • شیشه‌ای", "label_en":"Midnight • Glass",
        "dark":{"panel":"#0B1220","panel2":"#101B2E","soft":"#172642","panel3":"#08101B","line":"#253A58","accent":"#63F5D0","cyan":"#73C7FF","gold":"#F7D98B","violet":"#A990FF"},
        "light":{"panel":"#FFFFFF","panel2":"#F2F7FF","soft":"#E7EFF8","panel3":"#EEF5FC","line":"#CCD9EA","accent":"#16816C","cyan":"#2D79B9","gold":"#9A6800","violet":"#6E54C8"},
    },
    "ocean": {
        "label_fa":"Ocean • اقیانوسی", "label_en":"Ocean • Deep Blue",
        "dark":{"panel":"#0A1720","panel2":"#0F2431","soft":"#173344","panel3":"#071118","line":"#274858","accent":"#4DE4D5","cyan":"#59C8FF","gold":"#EFCF78","violet":"#9FA5FF"},
        "light":{"panel":"#FFFFFF","panel2":"#F1FBFC","soft":"#E3F3F5","panel3":"#EDF9FB","line":"#C9E0E4","accent":"#117E74","cyan":"#247FA7","gold":"#946500","violet":"#6B5BCC"},
    },
}

THEME_LABELS = {
    "fa": {"dark":"تیره","light":"روشن","auto":"خودکار","auto_start":"شروع حالت روشن","auto_end":"پایان حالت روشن"},
    "en": {"dark":"Dark","light":"Light","auto":"Automatic","auto_start":"Light mode start","auto_end":"Light mode end"},
}

INDICATOR_LABELS = {
    "fa": {"fear_greed":"ترس و طمع","btc_dom":"دامیننس بیت‌کوین","usdt_dom":"دامیننس تتر","vix":"VIX / نوسان","total_mcap":"ارزش کل بازار"},
    "en": {"fear_greed":"Fear & Greed","btc_dom":"BTC Dominance","usdt_dom":"USDT Dominance","vix":"VIX / Volatility","total_mcap":"Total Market Cap"},
}


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
        "education_note":"یادداشت آموزشی","calendar":"تقویم","ai":"🤖  AI Chat","news":"📰  اخبار بازار","calculators":"🧮  ماشین‌حساب‌ها","theme":"پوسته","theme_help":"پوسته را انتخاب کنید و برای حالت خودکار بازه زمانی تعیین کنید.","save_theme":"ذخیره پوسته","market_indicators":"شاخص‌های بازار","retry_market":"بروزرسانی بازار","market_source":"منبع بازار","offline":"آفلاین","market_error":"اتصال مستقیم به فید بازار برقرار نشد.","fear_greed":"ترس و طمع","btc_dom":"دامیننس بیت‌کوین","usdt_dom":"دامیننس تتر","vix":"VIX / نوسان","total_mcap":"ارزش کل بازار","crypto_calc":"ماشین‌حساب کریپتو","forex_calc":"ماشین‌حساب فارکس","risk_calc":"محاسبه ریسک","news_title":"مرکز اخبار بازار","news_sub":"اخبار کریپتو و تقویم اقتصادی فارکس در یک پنجره","open_forex_factory":"باز کردن Forex Factory داخل برنامه","open_coindesk":"باز کردن CoinDesk داخل برنامه","refresh_news":"بروزرسانی اخبار","ai_title":"دستیار هوشمند تریدر","ai_sub":"کمک در فرم‌ها، استراتژی، روانشناسی و نظم روزانه","ai_role":"نقش دستیار","ai_message":"پیام شما","ai_send":"ارسال","ai_status":"وضعیت دستیار","ai_local_note":"در صورت نصب Ollama، از مدل محلی نصب‌شده استفاده می‌شود؛ در غیر این صورت راهنمای داخلی فعال است.","ai_open_chat":"باز کردن چت هوش مصنوعی","ai_clear":"پاک کردن گفتگو","ai_close":"بستن","ai_welcome":"سلام. من دستیار Trader Planner Pro هستم. درباره فرم‌ها، استراتژی ثبت‌شده، روانشناسی و نظم معاملاتی سؤال بپرس.","reminders":"یادآورها","add_reminder":"＋ یادآور جدید","reminder_title":"عنوان یادآور","reminder_time":"ساعت","reminder_daily":"روزانه","reminder_enabled":"فعال","save_reminder":"ذخیره یادآور","delete_reminder":"حذف یادآور","calc":"محاسبه","balance":"موجودی حساب","risk_pct":"ریسک (%)","entry":"ورود","stop":"حد ضرر","target":"هدف","pip_size":"اندازه پیپ","pip_value":"ارزش هر پیپ برای ۱ لات","crypto_qty":"تعداد/حجم","notional":"ارزش معامله","risk_usd":"ریسک دلاری","stop_distance":"فاصله حد ضرر","rr":"R:R","lot_size":"لات","units":"واحد","invalid_input":"ورودی عددی را بررسی کنید","home_shortcut":"Home","date_info":"تاریخ","weekday":"روز","jalali":"شمسی","hijri":"قمری","quick_nav":"دسترسی سریع","crypto_mode":"کریپتو","forex_mode":"فارکس","academy_hub":"آکادمی","ai_chat":"گفت‌وگو با AI","nav_home":"خانه","source_chart":"نمودار منبع","setup_anatomy":"آناتومی ستاپ","family":"چارچوب","smc_family":"چارچوب SMC","ict_family":"مدل نام‌گذاری‌شده ICT","no_exact_image":"برای این اصطلاح تصویر اختصاصی منبع پیدا نشد؛ مرجع معتبر کنار آن نمایش داده می‌شود.","news_live":"اخبار زنده","news_fallback":"فید زنده در دسترس نیست؛ ترمینال منابع همچنان فعال است.","ai_quick_forms":"کمک برای پر کردن فرم","ai_quick_strategy":"توضیح این ستاپ","ai_quick_psychology":"بررسی روانشناسی","ai_quick_routine":"ساخت روتین","ai_placeholder":"سؤال خودت را از دستیار تریدر بپرس...","ai_page_note":"درباره ژورنال، چک‌لیست، پلن یا تعاریف آکادمی سؤال کن.","market_state_live":"فید زنده","market_state_cache":"نمایش آخرین Snapshot","market_state_offline":"آفلاین / بدون فید","market_switch":"تغییر بازار","skin_preview":"انتخاب پوسته","language_now":"زبان فعلی","choose_language":"انتخاب زبان","apply":"اعمال","market_tape":"نوار بازار","live":"زنده","cached":"کش","market_loading":"در حال دریافت داده بازار...","market_unavailable":"داده بازار در دسترس نیست","last_update":"آخرین بروزرسانی","home_shortcut":"برای برگشت به خانه کلید Home را بزنید","original_source":"تصویر اصلی منبع — بدون تغییر","open_source":"باز کردن منبع","session_strip":"سشن‌های جهانی","market_mode":"حالت بازار","live_feed":"فید زنده بازار","updated":"بروزرسانی","google_account":"حساب Google","google_login":"ورود با Google","google_logout":"خروج از Google","google_connected":"متصل به Google","google_credentials":"فایل OAuth Google","google_pick_credentials":"انتخاب فایل credentials.json","google_no_credentials":"برای Google Login یک OAuth Desktop Client از Google Cloud انتخاب کن.","email_statement":"ارسال Statement به Gmail","email_statement_subject":"Trading Statement","email_statement_ready":"Statement آماده شد و در حال ارسال است.","email_statement_sent":"Statement به Gmail ارسال شد.","email_statement_error":"ارسال Statement ناموفق بود.","ai_cloud":"OpenAI Cloud Agent","ai_cloud_key":"OpenAI API Key","ai_save_key":"ذخیره کلید AI","ai_clear_key":"پاک کردن کلید AI","ai_cloud_ready":"Cloud Agent فعال","ai_cloud_missing":"Cloud Agent نیازمند API Key است","ai_agent_product":"Product Strategist","ai_agent_academy":"Academy Tutor","ai_agent_roles":"Multi-Agent Roles","ai_provider":"AI Provider","agent_upgrade_ideas":"ایده‌های ارتقای محصول","ai_cloud_note":"مدل محلی رایگان با Ollama همیشه قابل استفاده است؛ OpenAI Cloud برای Agent قوی‌تر به API Key نیاز دارد."
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
        "education_note":"Training note","calendar":"Calendar","ai":"🤖  AI Chat","news":"📰  Market News","calculators":"🧮  Calculators","theme":"Theme","theme_help":"Choose a theme and set the light-mode interval for automatic mode.","save_theme":"Save Theme","market_indicators":"Market Indicators","retry_market":"Refresh Market","market_source":"Market Source","offline":"OFFLINE","market_error":"Direct market feed is unavailable.","fear_greed":"Fear & Greed","btc_dom":"BTC Dominance","usdt_dom":"USDT Dominance","vix":"VIX / Volatility","total_mcap":"Total Market Cap","crypto_calc":"Crypto Calculator","forex_calc":"Forex Calculator","risk_calc":"Risk Calculator","news_title":"Market News Center","news_sub":"Crypto news and the Forex economic calendar in one window","open_forex_factory":"Open Forex Factory in App","open_coindesk":"Open CoinDesk in App","refresh_news":"Refresh News","ai_title":"Trader AI Assistant","ai_sub":"Help with forms, strategies, psychology and daily discipline","ai_role":"Assistant Role","ai_message":"Your message","ai_send":"Send","ai_status":"Assistant Status","ai_local_note":"When Ollama is installed, the assistant uses an installed local model; otherwise built-in guidance stays available.","ai_open_chat":"Open AI Chat","ai_clear":"Clear Chat","ai_close":"Close","ai_welcome":"Hi. I am the Trader Planner Pro assistant. Ask about forms, documented strategies, psychology or your trading routine.","reminders":"Reminders","add_reminder":"＋ New Reminder","reminder_title":"Reminder Title","reminder_time":"Time","reminder_daily":"Daily","reminder_enabled":"Enabled","save_reminder":"Save Reminder","delete_reminder":"Delete Reminder","calc":"Calculate","balance":"Account Balance","risk_pct":"Risk (%)","entry":"Entry","stop":"Stop Loss","target":"Target","pip_size":"Pip Size","pip_value":"Pip Value per 1 Lot","crypto_qty":"Quantity / Size","notional":"Position Notional","risk_usd":"Risk $","stop_distance":"Stop Distance","rr":"R:R","lot_size":"Lot Size","units":"Units","invalid_input":"Check numeric inputs","home_shortcut":"Home","date_info":"Date","weekday":"Weekday","jalali":"Jalali","hijri":"Hijri","quick_nav":"Quick Nav","crypto_mode":"Crypto","forex_mode":"Forex","academy_hub":"Academy Hub","ai_chat":"Chat with AI","nav_home":"Home","source_chart":"Source chart","setup_anatomy":"Setup Anatomy","family":"Framework","smc_family":"SMC-style framework","ict_family":"ICT named model","no_exact_image":"No dedicated source image is mapped for this term; the source reference is shown instead.","news_live":"LIVE NEWS","news_fallback":"Live feed unavailable — source terminals remain available.","ai_quick_forms":"Help fill my form","ai_quick_strategy":"Explain this setup","ai_quick_psychology":"Psychology check","ai_quick_routine":"Build my routine","ai_placeholder":"Ask your trading assistant...","ai_page_note":"Ask about your journal, checklist, plan or Academy definitions.","market_state_live":"LIVE FEED","market_state_cache":"CACHED SNAPSHOT","market_state_offline":"OFFLINE / NO FEED","market_switch":"Switch market","skin_preview":"Choose a visual skin","language_now":"Current language","choose_language":"Choose language","apply":"Apply","market_tape":"MARKET TAPE","live":"LIVE","cached":"CACHED","market_loading":"Loading market data...","market_unavailable":"Market data unavailable","last_update":"Last update","home_shortcut":"Press Home anytime to return to Home","original_source":"Original source image — unmodified","open_source":"Open source page","session_strip":"GLOBAL SESSIONS","market_mode":"MARKET MODE","live_feed":"Live market feed","updated":"Updated","google_account":"Google Account","google_login":"Continue with Google","google_logout":"Sign out","google_connected":"Google connected","google_credentials":"Google OAuth credentials","google_pick_credentials":"Choose credentials.json","google_no_credentials":"Choose a Google Cloud OAuth Desktop client to enable Google Login.","email_statement":"Send Statement to Gmail","email_statement_subject":"Trading Statement","email_statement_ready":"Statement is ready and will be sent.","email_statement_sent":"Statement sent to Gmail.","email_statement_error":"Statement delivery failed.","ai_cloud":"OpenAI Cloud Agent","ai_cloud_key":"OpenAI API Key","ai_save_key":"Save AI Key","ai_clear_key":"Clear AI Key","ai_cloud_ready":"Cloud Agent ready","ai_cloud_missing":"Cloud Agent needs an API key","ai_agent_product":"Product Strategist","ai_agent_academy":"Academy Tutor","ai_agent_roles":"Multi-Agent Roles","ai_provider":"AI Provider","agent_upgrade_ideas":"Product upgrade ideas","ai_cloud_note":"Local Ollama remains available without cloud cost; the stronger OpenAI Cloud Agent requires an API key."
    }
}


SESSION_CLOCKS = [
    {"key":"sydney","fa":"سیدنی","en":"Sydney","tz":"Australia/Sydney","start":8,"end":17,"abbr":"SYD"},
    {"key":"tokyo","fa":"توکیو","en":"Tokyo","tz":"Asia/Tokyo","start":9,"end":18,"abbr":"TYO"},
    {"key":"london","fa":"لندن","en":"London","tz":"Europe/London","start":8,"end":17,"abbr":"LON"},
    {"key":"new_york","fa":"نیویورک","en":"New York","tz":"America/New_York","start":8,"end":17,"abbr":"NY"},
]

FA_TO_EN = {
    "خانه":"Home","برنامه روزانه":"Daily Planner","تنظیمات":"Settings","پروفایل جدید":"New Profile","ویرایش پروفایل":"Edit Profile",
    "حذف پروفایل":"Delete Profile","ذخیره":"Save","انصراف":"Cancel","ویرایش":"Edit","حذف":"Delete","بالا":"Up","پایین":"Down",
    "ذخیره پروفایل":"Save Profile","مدیریت پروفایل‌ها":"Manage Profiles","＋ افزودن شرط":"＋ Add Condition","ساخت از Trading Plan":"Build from Trading Plan",
    "نسخه‌های ذخیره‌شده":"Saved Versions","خروجی A4":"Export A4","ذخیره به‌عنوان Trading Plan":"Save as Trading Plan",
    "انتخاب تصویر":"Choose Image","باز کردن پوشه":"Open Folder","ذخیره معامله":"Save Trade","ثبت معامله":"Add Trade","＋ ثبت معامله":"＋ Add Trade",
    "خروجی CSV":"Export CSV","باز کردن پوشه تصاویر":"Open Screenshots","پایان MARK UP":"End MARK UP",
    "روز قبل":"Previous Day","روز بعد":"Next Day","＋ فعالیت جدید":"＋ New Activity","عنوان":"Title","دسته":"Category",
    "فعالیت":"Activity","زمان":"Time","پروفایل":"Profile","بازار":"Market","سرمایه اولیه":"Initial Capital",
    "عنوان شرط":"Condition Title","منبع":"Source","اجباری":"Required","بله":"Yes","خیر":"No","دستی":"Manual",
    "ژورنال":"Journal","چک‌لیست":"Checklist","آموزش":"Academy","سشن":"Session","جهت":"Direction","نتیجه":"Result","برد":"Win","باخت":"Loss","خنثی":"Flat",
    "تعداد معاملات":"Trades","نمودار عملکرد معاملات":"Trade Performance","توزیع نتایج ژورنال":"Journal Results","پروفایل فعال":"Active Profile","پروفایل ژورنال":"Journal Profile",
    "نام پروفایل":"Profile Name","بازار پیش‌فرض":"Default Market","ارز سرمایه":"Account Currency","حداقل یک پروفایل باید باقی بماند.":"At least one profile must remain.",
    "لغو":"Cancel","شرط":"Condition","عمومی":"General","فعالیت جدید":"New Activity","ویرایش فعالیت":"Edit Activity","ورودی ناقص":"Incomplete Input",
    "عنوان فعالیت را وارد کن":"Enter an activity title","انتخاب فعالیت":"Select Activity","ابتدا یک فعالیت را انتخاب کن":"Select an activity first","حذف فعالیت":"Delete Activity",
    "حذف معامله":"Delete Trade","ابتدا یک معامله را انتخاب کن":"Select a trade first","انتخاب اسکرین‌شات":"Choose Screenshot",
    "ژورنال خالی":"Empty Journal","معامله‌ای برای خروجی وجود ندارد":"No trades to export","ذخیره CSV":"Save CSV","انجام شد":"Done","خروجی CSV ذخیره شد":"CSV export saved",
    "نسخه‌های Trading Plan":"Trading Plan Versions","تاریخ":"Date","باز کردن نسخه انتخاب‌شده":"Open Selected Version","ذخیره شد":"Saved","Export آماده شد":"Export Ready","فایل A4 ساخته شد":"A4 file created",
    "الگوهای کندلی":"Candlestick Patterns","مراحل":"Steps","ابطال":"Invalidation","تعریف":"Definition","کاربرد":"Usage","آخرین معاملات | R":"Recent Trades | R","هنوز داده‌ای برای نمودار نیست":"No chart data yet",
    "تکمیل شده":"Completed","این شرط اجباری است":"This condition is required","فروش":"Sell","خرید":"Buy","اطلاعات معامله":"Trade Information","قیمت و ریسک":"Price & Risk","تحلیل":"Analysis","روانشناسی":"Psychology","اسکرین‌شات":"Screenshot",
    "بسته":"CLOSED","باز":"OPEN","جستجو:":"Search:","ساعت سشن‌ها":"Trading Session Clocks","زمان محلی":"Local Time","ساعت سشن":"Session Hours",
    "نام استراتژی":"Strategy Name","نسخه استراتژی":"Strategy Version","بازارهای مجاز":"Allowed Markets","تایم‌فریم‌های اصلی":"Primary Timeframes","ستاپ‌های مجاز":"Allowed Setups","شرایط ورود":"Entry Conditions","شرایط عدم ورود":"No-Trade Conditions",
    "حداکثر ریسک هر معامله (%)":"Max Risk per Trade (%)","حداکثر ضرر روزانه (%)":"Max Daily Loss (%)","حداکثر معاملات روزانه":"Max Daily Trades","قانون خروج":"Exit Rule","قانون توقف بعد از باخت":"Stop-After-Loss Rule","قوانین روانشناسی":"Psychology Rules","اهداف ماهانه":"Monthly Goals",
    "انتخاب زبان":"Choose Language","زبان فعلی":"Current Language","زبان برنامه":"Application Language","زبان رابط کاربری را انتخاب کن. تغییر زبان بلافاصله اعمال می‌شود.":"Choose the interface language. The change applies immediately.",
    "زبان تغییر کرد":"Language Changed","مسیر داده":"Data Path","مسیر خروجی A4":"A4 Output Path","مدیریت پروفایل‌ها":"Manage Profiles",
    "پروفایل، سرمایه، عملکرد ژورنال و وضعیت معاملاتی در یک نگاه":"Profile, capital, journal performance and trading status at a glance",
    "قابل ویرایش، قابل تیک‌زدن و ذخیره روی همان مسیر داده قبلی":"Editable, checkable and saved to the existing data path","موارد را سریع ببین، تیک بزن، ویرایش کن و با دکمه‌های هر ردیف جابه‌جا کن":"Review items, tick them, edit them and reorder them",
    "جهت و ساختار بازار مشخص است":"Market direction and structure are clear","نقدینگی و ناحیه مهم مشخص است":"Liquidity and key zone are marked","ستاپ مطابق Trading Plan است":"Setup matches the Trading Plan","تریگر ورود تایید شده است":"Entry trigger is confirmed",
    "ریسک و حجم محاسبه شده":"Risk and position size are calculated","حد ضرر قبل از ورود مشخص است":"Stop loss is defined before entry","R:R قابل قبول است":"R:R is acceptable",
    "خبر مهم بررسی شده است":"Important news checked","حالت روانی مناسب است":"Psychology is appropriate","FOMO / Revenge ندارم":"No FOMO / Revenge","بعد از ورود قانون را تغییر نمی‌دهم":"Do not change the rules after entry",
    "بیداری + آب + نور صبح":"Wake + water + morning light","صبحانه":"Breakfast","ورزش / پیاده‌روی صبح 30–45 دقیقه":"Morning walk / exercise 30–45 min","دوش + آماده‌سازی میز":"Shower + desk setup",
    "MARK UP — ساختار، روند، نقدینگی و نواحی":"MARK UP — structure, trend, liquidity and zones","استراحت 15 دقیقه":"15 minute break","MARK UP — سناریوی A/B و نقاط ابطال":"MARK UP — A/B scenarios and invalidation",
    "ثبت سناریو + بررسی خبرها":"Log scenarios + check news","پایان MARK UP + بستن چارت":"End MARK UP + close charts","مرور پلن + آماده‌سازی سشن":"Review plan + session preparation",
    "TRADING — فقط ستاپ‌های مجاز":"TRADING — allowed setups only","TRADING — ادامه سشن":"TRADING — continue session","پایان قطعی ترید":"Hard stop trading","ژورنال + اسکرین‌شات + درس روز":"Journal + screenshot + lesson of the day",
    "مطالعه / بک‌تست سبک":"Study / light backtest","خاموشی صفحه‌نمایش":"Screen-off time","خواب":"Sleep","سلامت":"Health","غذا":"Food","ورزش":"Exercise","روتین":"Routine","استراحت":"Break","آماده‌سازی":"Preparation","تحلیل":"Analysis","پایان":"End","یادگیری":"Learning",
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
    return {"version": 800, "active_profile_id": p["id"], "profiles": [p], "tasks": tasks, "settings": {"language":"fa","theme":"dark","theme_auto_start":"08:00","theme_auto_end":"20:00","skin":"glass","ai_reminders":[]}}

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
    base["settings"].setdefault("theme", "dark")
    base["settings"].setdefault("theme_auto_start", "08:00")
    base["settings"].setdefault("theme_auto_end", "20:00")
    base["settings"].setdefault("skin", "glass")
    base["settings"].setdefault("ai_reminders", [])
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
        base["version"] = 800
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
    base["version"] = 750
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
        self.menu_hide_job = None
        self.session_clock_job = None
        self.session_clock_widgets = []
        self.theme_auto_job = None
        self.reminder_job = None
        self.market_timeout_job = None
        self.market_data_payload = cached_market_payload(self.market)
        self.ticker_offset = 0
        self.ticker_job = None
        self.ai = AIOrchestrator()
        self.ai_history = []
        self.news_items = []
        self.market_data = MarketDataService(self._market_data_callback, refresh_seconds=60)
        self.theme_mode = DB.get("settings", {}).get("theme", "dark")
        self.theme_auto_start = DB.get("settings", {}).get("theme_auto_start", "08:00")
        self.theme_auto_end = DB.get("settings", {}).get("theme_auto_end", "20:00")
        self.skin = DB.get("settings", {}).get("skin", "glass")
        if self.skin not in SKINS: self.skin = "glass"
        self.ai_chat_window = None
        self.ai_chat_text = None
        self.ai_chat_input = None
        self._nav_job = None
        self._nav_token = 0
        self.quickbar = None
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("Treeview", background=C["panel"], fieldbackground=C["panel"], foreground=C["text"],
                             rowheight=38, borderwidth=0, font=("Segoe UI", 10))
        self.style.map("Treeview", background=[("selected", C["soft"])], foreground=[("selected", C["text"])])
        self.style.configure("TCombobox", fieldbackground=C["soft"], background=C["soft"], foreground=C["text"])
        self._logo_photo = None
        self.apply_theme(initial=True)
        self.bind_all("<Home>", self._home_shortcut)
        self.bind_all("<Alt-Home>", lambda e: self._hard_home())
        self.bind_all("<Control-K>", lambda e: self.open_ai_chat())
        self.bind_all("<F2>", lambda e: self.open_ai_chat())
        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.bind_all("<Escape>", lambda e: self._escape_ui())
        self.bind("<Motion>", self._shell_motion, add="+")
        self.build_shell()
        self.apply_language()
        self.update_idletasks()
        apply_glass(self, dark=self._effective_theme()=="dark", style="acrylic")
        self.show("home")
        self.market_data.start(self.market)
        self.after(700, self.clock)
        self.after(7000, self._market_loading_timeout)
        self.check_reminders()

    def _home_shortcut(self, event=None):
        widget = getattr(event, "widget", None)
        if isinstance(widget, (tk.Entry, tk.Text, ttk.Entry, ttk.Combobox)):
            return None
        self._hard_home()
        return "break"

    def _hard_home(self):
        """Return to Home through the same guarded renderer used by every page."""
        try:
            self._cancel_menu_hide()
            self.menu_open = False
            try:
                self.menu.place_configure(x=-304)
            except Exception:
                pass
            for job_name in ("session_clock_job", "ticker_job", "market_timeout_job"):
                job = getattr(self, job_name, None)
                if job is not None:
                    try:
                        self.after_cancel(job)
                    except Exception:
                        pass
                    setattr(self, job_name, None)
            self.session_clock_widgets = []
            self.market = active_profile().get("market", "Crypto")
            self.market_data.set_market(self.market)
            self.cur = "home"
            self.show("home")
            self.after_idle(self.market_data.refresh_now)
            self.focus_force()
        except Exception as exc:
            self._show_page_error("home", exc)

    def go_home(self):
        """Single source of truth for every Home action."""
        return self._hard_home()

    def close_app(self):
        try:
            if self.market_data:
                self.market_data.stop()
        except Exception:
            pass
        for job_name in ("session_clock_job", "ticker_job", "menu_hide_job", "theme_auto_job", "reminder_job", "market_timeout_job"):
            job = getattr(self, job_name, None)
            if job:
                try: self.after_cancel(job)
                except Exception: pass
        self.destroy()

    def _parse_hhmm(self, value, fallback="08:00"):
        try:
            h, m = [int(x) for x in str(value).split(":", 1)]
            if 0 <= h <= 23 and 0 <= m <= 59:
                return h * 60 + m
        except Exception:
            pass
        h, m = [int(x) for x in fallback.split(":")]
        return h * 60 + m

    def _valid_hhmm(self, value):
        try:
            h, m = [int(x) for x in str(value).split(":", 1)]
            return 0 <= h <= 23 and 0 <= m <= 59 and len(str(value).split(":",1)) == 2
        except Exception:
            return False

    def _effective_theme(self):
        mode = self.theme_mode if self.theme_mode in ("dark", "light", "auto") else "dark"
        if mode != "auto":
            return mode
        now = datetime.now().hour * 60 + datetime.now().minute
        start = self._parse_hhmm(self.theme_auto_start, "08:00")
        end = self._parse_hhmm(self.theme_auto_end, "20:00")
        if start <= end:
            return "light" if start <= now < end else "dark"
        return "light" if now >= start or now < end else "dark"

    def apply_theme(self, initial=False):
        effective = self._effective_theme()
        skin = self.skin if self.skin in SKINS else "glass"
        palette = dict(THEMES[effective])
        palette.update(SKINS[skin][effective])
        C.update(palette)
        self.configure(bg=C["bg"])
        self.style.configure("Treeview", background=C["panel"], fieldbackground=C["panel"], foreground=C["text"],
                             rowheight=38, borderwidth=0, font=("Segoe UI", 10))
        self.style.map("Treeview", background=[("selected", C["soft"])], foreground=[("selected", C["text"])])
        self.style.configure("TCombobox", fieldbackground=C["soft"], background=C["soft"], foreground=C["text"])
        self._last_effective_theme = effective
        if not initial and hasattr(self, "content"):
            self.content.configure(bg=C["bg"])
            self._refresh_shell_theme()
        try:
            apply_glass(self, dark=effective=="dark", style="acrylic")
        except Exception:
            pass
        if self.theme_mode == "auto":
            if self.theme_auto_job:
                try: self.after_cancel(self.theme_auto_job)
                except Exception: pass
            self.theme_auto_job = self.after(60000, self._theme_watch)
        elif self.theme_auto_job:
            try: self.after_cancel(self.theme_auto_job)
            except Exception: pass
            self.theme_auto_job = None

    def _theme_watch(self):
        self.theme_auto_job = None
        if self.theme_mode != "auto":
            return
        effective = self._effective_theme()
        if effective != getattr(self, "_last_effective_theme", effective):
            self.apply_theme()
            self.show(self.cur)
        else:
            self.apply_theme()
        if self.theme_mode == "auto":
            self.theme_auto_job = self.after(60000, self._theme_watch)

    def _refresh_shell_theme(self):
        if not hasattr(self, "topbar"):
            return
        try:
            self.topbar.configure(bg=C["panel"], highlightbackground=C["line"])
            self.menu.configure(bg=C["panel"], highlightbackground=C["line"])
        except Exception:
            pass
        for widget in (self.topbar, self.content, self.menu, getattr(self, "brand_frame", None),
                       getattr(self, "status_bar", None), getattr(self, "menu_title", None)):
            if widget is None:
                continue
            try:
                widget.configure(bg=C["panel"] if widget is not self.content else C["bg"])
            except Exception:
                pass
        for widget in self.menu.winfo_children():
            try:
                widget.configure(bg=C["panel"], fg=C["text"] if widget is not self.menu_title else C["accent"])
            except Exception:
                pass
        try:
            self.menu_home_hint.configure(bg=C["panel3"], fg=C["muted"])
        except Exception:
            pass
        for key, button in getattr(self, "menu_buttons", {}).items():
            try:
                button.configure(bg=C["panel"], fg=C["text"], activebackground=C["soft"], activeforeground=C["accent"])
            except Exception:
                pass
        for widget_name in ("menu_button", "market_btn", "global_home_btn", "global_ai_btn"):
            widget = getattr(self, widget_name, None)
            if widget:
                try:
                    widget.configure(bg=C["panel2"] if widget_name == "menu_button" else C["soft"], fg=C["text"],
                                      activebackground=C["accent"] if widget_name in ("menu_button","global_home_btn","global_ai_btn") else C["gold"],
                                      activeforeground="#061019")
                except Exception:
                    pass
        for widget in (getattr(self, "brand_title", None), getattr(self, "brand_subtitle", None)):
            if widget:
                try:
                    widget.configure(bg=C["panel"], fg=C["text"] if widget is self.brand_title else C["accent"])
                except Exception:
                    pass
        if hasattr(self, "clock_label"):
            self.clock_label.configure(bg=C["panel3"], fg=C["cyan"])
        if hasattr(self, "date_label"):
            self.date_label.configure(bg=C["panel3"], fg=C["muted"])
        if hasattr(self, "quickbar"):
            self.quickbar.configure(bg=C["bg"], highlightbackground=C["line"])
        for button in getattr(self, "_quick_nav_buttons", {}).values():
            try:
                button.configure(bg=C["panel2"], fg=C["text"], activebackground=C["accent"], activeforeground="#061019")
            except Exception:
                pass

    def _market_loading_timeout(self):
        self.market_timeout_job = None
        if self.cur == "home" and self.market_data_payload.get("status") == "loading":
            # Never leave Home visually stuck in a spinner/loading state.
            cached = cached_market_payload(self.market)
            if cached.get("items"):
                cached["message"] = self.tr("market_state_cache")
                self.market_data_payload = cached
            else:
                self.market_data_payload = {
                    "market": self.market,
                    "updated_at": None,
                    "source": "unavailable",
                    "items": [],
                    "indicators": {},
                    "status": "unavailable",
                    "message": self.tr("market_error"),
                }
            self._apply_market_data(self.market_data_payload)
        if self.cur == "home":
            self.market_timeout_job = self.after(7000, self._market_loading_timeout)

    def check_reminders(self):
        self.reminder_job = None
        reminders = DB.get("settings", {}).get("ai_reminders", [])
        now = datetime.now()
        hhmm = now.strftime("%H:%M")
        changed = False
        for reminder in reminders:
            if not reminder.get("enabled", True):
                continue
            if reminder.get("time") != hhmm:
                continue
            if reminder.get("daily", True) and reminder.get("last_notified") == now.date().isoformat():
                continue
            reminder["last_notified"] = now.date().isoformat()
            changed = True
            title = reminder.get("title") or self.tr("reminders")
            messagebox.showinfo(title, f"{title}\\n{self.display_date_now()}", parent=self)
        if changed:
            save_db()
        self.reminder_job = self.after(30000, self.check_reminders)

    def display_date_now(self):
        try:
            return display_date(date.today(), self.language)
        except Exception:
            return datetime.now().strftime("%Y-%m-%d")
 
    def tr(self, key, **kwargs):
        table = I18N.get(self.language, I18N["fa"])
        text = table.get(key, key)
        return text.format(**kwargs) if kwargs else text

    def ui_text(self, text):
        value = str(text)
        if self.language != "en":
            return value
        for fa, en in sorted(FA_TO_EN.items(), key=lambda kv: len(kv[0]), reverse=True):
            if fa and fa in value:
                value = value.replace(fa, en)
        return value

    def translate_widget_tree(self, root=None):
        root = root or self.content
        for widget in root.winfo_children():
            try:
                if isinstance(widget, ttk.Notebook):
                    for tab_id in widget.tabs():
                        widget.tab(tab_id, text=self.ui_text(widget.tab(tab_id, "text")))
                elif isinstance(widget, ttk.Treeview):
                    for col in widget["columns"]:
                        widget.heading(col, text=self.ui_text(widget.heading(col, "text")))
                elif isinstance(widget, tk.Text):
                    if str(widget.cget("state")) == "disabled":
                        current = widget.get("1.0", "end-1c")
                        translated = self.ui_text(current)
                        if translated != current:
                            widget.configure(state="normal")
                            widget.delete("1.0", "end")
                            widget.insert("1.0", translated)
                            widget.configure(state="disabled")
                elif "text" in widget.keys():
                    current = widget.cget("text")
                    translated = self.ui_text(current)
                    if translated != current:
                        widget.config(text=translated)
            except Exception:
                pass
            self.translate_widget_tree(widget)

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
        if hasattr(self, "global_home_btn"):
            self.global_home_btn.config(text=self.tr("nav_home"))
        if hasattr(self, "global_ai_btn"):
            self.global_ai_btn.config(text=self.tr("ai_chat"))
        if hasattr(self, "_quick_nav_buttons"):
            labels={
                "home":self.tr("nav_home"),
                "crypto":self.tr("crypto_mode"),
                "forex":self.tr("forex_mode"),
                "academy":self.tr("academy_hub"),
                "ai":self.tr("ai_chat"),
                "news":self.tr("news"),
                "calculators":self.tr("calculators"),
            }
            for key,label in labels.items():
                if key in self._quick_nav_buttons:
                    self._quick_nav_buttons[key].config(text=label)

    def set_language(self, code):
        if code not in dict(LANGUAGE_OPTIONS): return
        DB.setdefault("settings", {})["language"] = code
        self.language = code
        save_db()
        self.apply_language()
        self.show(self.cur)

    def build_shell(self):
        top = tk.Frame(self, bg=C["panel"], highlightbackground=C["line"], highlightthickness=1, bd=0)
        self.topbar = top
        top.pack(fill="x", padx=14, pady=(12, 7), ipady=5)
        try: set_widget_glass(top, 0.78)
        except Exception: pass
        self.menu_button = tk.Button(top, text="☰", command=self.toggle_menu, bg=C["panel2"], fg=C["text"],
                                     activebackground=C["accent"], activeforeground="#061019", relief="flat",
                                     font=("Segoe UI Symbol", 15, "bold"), width=3, cursor="hand2",
                                     highlightthickness=0)
        self.menu_button.pack(side="left", padx=8)
        try:
            logo_path = create_logo_image(Path(tempfile_path()), 300)
            from PIL import Image, ImageTk
            self._logo_photo = ImageTk.PhotoImage(Image.open(logo_path).convert("RGBA").resize((48,48)))
            tk.Label(top, image=self._logo_photo, bg=C["panel"]).pack(side="left", padx=(2,8))
        except Exception:
            pass
        brand = tk.Frame(top, bg=C["panel"]); self.brand_frame = brand; brand.pack(side="left", padx=2)
        self.brand_title = tk.Label(brand, text=APP, bg=C["panel"], fg=C["text"],
                                    font=("Segoe UI", 15, "bold")); self.brand_title.pack(anchor="w")
        self.brand_subtitle = tk.Label(brand, text="PRO TRADING WORKSPACE • MARKET DESK",
                                       bg=C["panel"], fg=C["accent"], font=("Segoe UI", 7, "bold"))
        self.brand_subtitle.pack(anchor="w")
        status = tk.Frame(top, bg=C["panel"]); self.status_bar = status; status.pack(side="right", padx=7)
        self.date_label = tk.Label(status, bg=C["panel3"], fg=C["muted"], font=("Segoe UI", 8, "bold"),
                                   padx=10, pady=6, anchor="center")
        self.date_label.pack(side="left", padx=3)
        self.clock_label = tk.Label(status, bg=C["panel3"], fg=C["cyan"], font=("Consolas", 9, "bold"),
                                     padx=10, pady=6); self.clock_label.pack(side="left", padx=3)
        self.profile_combo = ttk.Combobox(status, state="readonly", width=18, justify="right")
        self.profile_combo.bind("<<ComboboxSelected>>", self.on_profile_change)
        self.profile_combo.pack(side="left", padx=5)
        self.market_btn = tk.Button(status, text=self.market, command=self.change_market, bg=C["soft"], fg=C["text"],
                                    activebackground=C["gold"], relief="flat", highlightthickness=0,
                                    font=("Segoe UI", 9, "bold"), padx=12, pady=6, cursor="hand2")
        self.market_btn.pack(side="left", padx=4)
        self.global_home_btn = tk.Button(
            status, text=self.tr("nav_home"), command=self._hard_home,
            bg=C["accent"], fg="#061019", activebackground=C["gold"], activeforeground="#061019",
            relief="flat", highlightthickness=0, font=("Segoe UI",9,"bold"), padx=12, pady=6, cursor="hand2"
        )
        self.global_home_btn.pack(side="left", padx=4)
        self.global_ai_btn = tk.Button(
            status, text=self.tr("ai_chat"), command=lambda: self.go("ai"),
            bg=C["panel2"], fg=C["text"], activebackground=C["accent"], activeforeground="#061019",
            relief="flat", highlightthickness=0, font=("Segoe UI",9,"bold"), padx=10, pady=6, cursor="hand2"
        )
        self.global_ai_btn.pack(side="left", padx=4)
        self.refresh_profile_selector()

        self.quickbar = tk.Frame(self, bg=C["bg"], highlightbackground=C["line"], highlightthickness=1)
        self.quickbar.pack(fill="x", padx=14, pady=(0,7), ipady=4)
        try: set_widget_glass(self.quickbar, 0.74)
        except Exception: pass
        self._quick_nav_buttons = {}
        nav_specs = [
            ("home", self.tr("nav_home"), self._hard_home),
            ("crypto", self.tr("crypto_mode"), lambda: self.set_market_mode("Crypto")),
            ("forex", self.tr("forex_mode"), lambda: self.set_market_mode("Forex")),
            ("academy", self.tr("academy_hub"), lambda: self.go("academy")),
            ("ai", self.tr("ai_chat"), lambda: self.go("ai")),
            ("news", self.tr("news"), lambda: self.go("news")),
            ("calculators", self.tr("calculators"), lambda: self.go("calculators")),
        ]
        for key, label, cmd in nav_specs:
            b = tk.Button(self.quickbar, text=label, command=cmd, bg=C["panel2"], fg=C["text"],
                          activebackground=C["accent"], activeforeground="#061019", relief="flat",
                          font=("Segoe UI", 9, "bold"), padx=13, pady=7, cursor="hand2")
            b.pack(side="left", padx=3)
            self._quick_nav_buttons[key] = b

        self.content = tk.Frame(self, bg=C["bg"])
        self.content.pack(fill="both", expand=True, padx=14)

        self.menu = tk.Frame(self, bg=C["panel"], width=292, highlightbackground=C["line"], highlightthickness=1, bd=0)
        self.menu.place(x=-304, y=8, relheight=1)
        self.menu_title = tk.Label(self.menu, text="TRADER PLANNER PRO", bg=C["panel"], fg=C["accent"],
                                   font=("Segoe UI", 15, "bold"))
        self.menu_title.pack(anchor="w", padx=18, pady=(20,6))
        tk.Label(self.menu, text="FAST NAVIGATION • AUTO HIDE", bg=C["panel"], fg=C["muted"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=20, pady=(0,14))
        self.menu_buttons = {}
        for key in ("home","daily","plan","check","journal","academy","ai","news","calculators","settings"):
            cmd = lambda k=key: self.go(k)
            b = tk.Button(self.menu, text=self.tr(key), command=cmd, anchor="w",
                          bg=C["panel"], fg=C["text"], activebackground=C["soft"], activeforeground=C["accent"],
                          relief="flat", highlightthickness=0, font=("Segoe UI", 10, "bold"),
                          padx=18, pady=11, cursor="hand2")
            b.pack(fill="x", padx=7, pady=2); self.menu_buttons[key] = b
        self.menu_home_hint = tk.Label(self.menu, text=self.tr("home_shortcut"), bg=C["panel3"], fg=C["muted"],
                                       font=("Segoe UI", 8), wraplength=240, justify="left")
        self.menu_home_hint.pack(fill="x", padx=14, pady=(18,14), ipady=8)

    def _shell_motion(self, event):
        if self.menu_open:
            x, y = event.x_root, event.y_root
            mx, my = self.menu.winfo_rootx(), self.menu.winfo_rooty()
            inside = mx <= x <= mx + self.menu.winfo_width() + 12 and my <= y <= my + self.menu.winfo_height()
            if inside:
                self._cancel_menu_hide()
            else:
                self._schedule_menu_hide(900)

    def _escape_ui(self):
        if self.menu_open:
            self.toggle_menu()
        else:
            self.show("home")

    def _cancel_menu_hide(self):
        if self.menu_hide_job:
            try: self.after_cancel(self.menu_hide_job)
            except Exception: pass
            self.menu_hide_job = None

    def _schedule_menu_hide(self, delay=1200):
        self._cancel_menu_hide()
        if self.menu_open:
            self.menu_hide_job = self.after(delay, self._hide_menu)

    def _hide_menu(self):
        self.menu_hide_job = None
        if self.menu_open:
            self.menu.place_configure(x=-304)
            self.menu_open = False

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
        self.market_data.set_market(self.market)
        save_db(); self.show(self.cur)

    def toggle_menu(self):
        if self.menu_open:
            self._cancel_menu_hide()
            self.menu.place_configure(x=-304)
            self.menu_open = False
        else:
            self.menu.place_configure(x=8)
            self.menu_open = True
            self._schedule_menu_hide(1800)

    def go(self, key):
        self._cancel_menu_hide()
        if self.menu_open:
            self.menu.place_configure(x=-304)
            self.menu_open = False
        self.show(key)

    def show(self, key):
        allowed={"home","daily","plan","check","journal","academy","ai","news","calculators","settings"}
        if key not in allowed:
            key="home"
        self._cancel_menu_hide()
        self.cur = key
        self._nav_token += 1
        token = self._nav_token
        if self._nav_job is not None:
            try: self.after_cancel(self._nav_job)
            except Exception: pass
            self._nav_job = None
        self._render_page(key, token)
        return "break"

    def _render_page(self, key, token):
        self._nav_job = None
        if token != self._nav_token or not self.winfo_exists():
            return
        for job_name in ("session_clock_job","ticker_job"):
            job=getattr(self, job_name, None)
            if job is not None:
                try: self.after_cancel(job)
                except Exception: pass
                setattr(self, job_name, None)
        self.session_clock_widgets=[]
        for widget in self.content.winfo_children():
            try: widget.destroy()
            except Exception: pass
        try:
            getattr(self,key)()
            self.translate_widget_tree(self.content)
            self.content.update_idletasks()
        except Exception as exc:
            self._show_page_error(key,exc)

    def _show_page_error(self,key,exc):
        try:
            ROOT.mkdir(parents=True,exist_ok=True)
            with (ROOT/"ui_errors.log").open("a",encoding="utf-8") as log:
                log.write(f"{datetime.now().isoformat(timespec='seconds')} | page={key} | {type(exc).__name__}: {exc}\n")
        except Exception:
            pass
        for widget in self.content.winfo_children():
            try: widget.destroy()
            except Exception: pass
        box=self.card(self.content); box.pack(fill="both",expand=True,padx=30,pady=30)
        tk.Label(box,text="Trader Planner Pro",bg=C["panel"],fg=C["accent"],font=("Segoe UI",22,"bold")).pack(pady=(60,10))
        tk.Label(box,text=f"{key.upper()} • SAFE RECOVERY",bg=C["panel"],fg=C["gold"],font=("Consolas",11,"bold")).pack(pady=4)
        tk.Label(box,text="The page hit a UI error and was recovered safely.",bg=C["panel"],fg=C["text"],font=("Segoe UI",12)).pack(pady=8)
        tk.Label(box,text=str(exc),bg=C["soft"],fg=C["danger"],font=("Consolas",9),wraplength=1050,justify="center").pack(fill="x",padx=30,pady=20,ipady=12)
        self.btn(box,self.tr("home"),self.go_home,True).pack(pady=10)

    def _rounded_rect(self,canvas,x1,y1,x2,y2,radius=12,fill="",outline="",width=1):
        r=max(1,int(radius))
        canvas.create_arc(x1,y1,x1+2*r,y1+2*r,start=90,extent=90,fill=fill,outline=outline,width=width)
        canvas.create_arc(x2-2*r,y1,x2,y1+2*r,start=0,extent=90,fill=fill,outline=outline,width=width)
        canvas.create_arc(x1,y2-2*r,x1+2*r,y2,start=180,extent=90,fill=fill,outline=outline,width=width)
        canvas.create_arc(x2-2*r,y2-2*r,x2,y2,start=270,extent=90,fill=fill,outline=outline,width=width)
        canvas.create_rectangle(x1+r,y1,x2-r,y2,fill=fill,outline="")
        canvas.create_rectangle(x1,y1+r,x2,y2-r,fill=fill,outline="")
        if outline:
            canvas.create_line(x1+r,y1,x2-r,y1,fill=outline,width=width)
            canvas.create_line(x1+r,y2,x2-r,y2,fill=outline,width=width)
            canvas.create_line(x1,y1+r,x1,y2-r,fill=outline,width=width)
            canvas.create_line(x2,y1+r,x2,y2-r,fill=outline,width=width)

    def clock(self):
        now = datetime.now()
        self.clock_label.config(text=now.strftime("%H:%M:%S"))
        try:
            self.date_label.config(text=display_date(now, self.language).replace(" | ", "\n"))
        except Exception:
            self.date_label.config(text=now.strftime("%Y-%m-%d"))
        if self.theme_mode == "auto" and self._effective_theme() != getattr(self, "_last_effective_theme", self._effective_theme()):
            self.apply_theme()
            self.show(self.cur)
        self.after(1000, self.clock)

    def heading(self, title, sub=""):
        title = self.ui_text(title); sub = self.ui_text(sub)
        band = tk.Frame(self.content, bg=C["bg"]); band.pack(fill="x", pady=(7,4))
        accent = tk.Frame(band, bg=C["accent"], width=4, height=44); accent.pack(side="right", padx=(9,0), pady=2)
        texts = tk.Frame(band, bg=C["bg"]); texts.pack(side="right", fill="x", expand=True)
        tk.Label(texts, text=title, bg=C["bg"], fg=C["text"], font=("Segoe UI", 20, "bold")).pack(anchor="e")
        if sub:
            tk.Label(texts, text=sub, bg=C["bg"], fg=C["muted"], font=("Segoe UI", 9)).pack(anchor="e", pady=(2,0))
        left_tools = tk.Frame(band, bg=C["bg"]); left_tools.pack(side="left", padx=2)
        home_btn = tk.Button(left_tools, text=self.tr("home"), command=self.go_home,
                             bg=C["panel2"], fg=C["text"], activebackground=C["accent"], activeforeground="#061019",
                             relief="flat", font=("Segoe UI", 8, "bold"), padx=10, pady=6, cursor="hand2")
        home_btn.pack(side="left", padx=(0,5))
        if self.cur != "home":
            ai_btn = tk.Button(left_tools, text=self.tr("ai"), command=self.open_ai_chat,
                               bg=C["panel2"], fg=C["text"], activebackground=C["accent"], activeforeground="#061019",
                               relief="flat", font=("Segoe UI", 8, "bold"), padx=10, pady=6, cursor="hand2")
            ai_btn.pack(side="left", padx=(0,5))
        tk.Label(left_tools, text="HOME", bg=C["panel3"], fg=C["muted"],
                 font=("Consolas", 7, "bold"), padx=6, pady=5).pack(side="left")

    def card(self, parent, padx=1):
        frame=tk.Frame(parent,bg=C["panel"],highlightbackground=C["line"],highlightthickness=padx,bd=0,relief="flat")
        try:
            set_widget_glass(frame, 0.86)
        except Exception:
            pass
        return frame

    def btn(self, parent, text, cmd, primary=False, **kw):
        base=C["accent"] if primary else C["soft"]
        button=tk.Button(parent,text=self.ui_text(text),command=cmd,bg=base,fg="#061019" if primary else C["text"],
                         activebackground=C["gold"],relief="flat",highlightthickness=1,highlightbackground=C["line"],
                         borderwidth=0,font=("Segoe UI",10,"bold"),padx=13,pady=9,cursor="hand2",**kw)
        button.bind("<Enter>",lambda e:button.configure(bg=C["gold"] if not primary else C["cyan"]))
        button.bind("<Leave>",lambda e:button.configure(bg=base))
        try:
            set_widget_glass(button, 0.94)
        except Exception:
            pass
        return button

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
        dlg=tk.Toplevel(self); dlg.title(self.ui_text("پروفایل ژورنال")); dlg.geometry("520x360"); dlg.configure(bg=C["bg"]); dlg.transient(self); dlg.grab_set()
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
            save_db(); dlg.destroy(); self.market=active_profile()["market"]; self.market_btn.config(text=self.market); self.market_data.set_market(self.market); self.refresh_profile_selector(); self.show(self.cur)
        self.btn(dlg,"ذخیره پروفایل",submit,True).grid(row=5,column=0,padx=16,pady=16,sticky="e")
        self.btn(dlg,"انصراف",dlg.destroy).grid(row=5,column=1,padx=16,pady=16,sticky="w")
        self.translate_widget_tree(dlg)

    def delete_profile(self):
        if len(DB["profiles"]) <= 1:
            return messagebox.showinfo(self.ui_text("پروفایل"),self.ui_text("حداقل یک پروفایل باید باقی بماند."),parent=self)
        p=active_profile()
        if messagebox.askyesno(self.ui_text("حذف پروفایل"),self.ui_text(f"پروفایل «{p['name']}» و ژورنال آن حذف شود؟"),parent=self):
            DB["profiles"]=[x for x in DB["profiles"] if x["id"]!=p["id"]]
            DB["active_profile_id"]=DB["profiles"][0]["id"]; save_db()
            self.market=active_profile()["market"]; self.refresh_profile_selector(); self.show("home")

    def set_market_mode(self, market):
        market = "Forex" if str(market) == "Forex" else "Crypto"
        p = active_profile()
        p["market"] = market
        p["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self.market = market
        try:
            self.market_btn.config(text=market)
        except Exception:
            pass
        self.market_data.set_market(market)
        save_db()
        # Defer the rebuild one event-loop turn so the button callback never
        # destroys its own widget hierarchy while Tk is dispatching the click.
        self.after_idle(self._hard_home)

    def change_market(self):
        current = active_profile().get("market", "Crypto")
        self.set_market_mode("Forex" if current == "Crypto" else "Crypto")

    def home(self):
        p = active_profile()
        self.market = p.get("market", "Crypto")
        self.heading(self.tr("dashboard"), self.tr("dashboard_sub"))

        ticker_header = tk.Frame(self.content, bg=C["panel2"], highlightbackground=C["line"], highlightthickness=1)
        ticker_header.pack(fill="x", pady=(2,4))
        left = tk.Frame(ticker_header, bg=C["panel2"]); left.pack(side="left", padx=10, pady=7)
        tk.Label(left, text=self.tr("market_tape"), bg=C["panel2"], fg=C["gold"], font=("Segoe UI", 10, "bold")).pack(side="left")
        self.market_status_label = tk.Label(left, text="", bg=C["panel2"], fg=C["muted"], font=("Segoe UI", 8, "bold"))
        self.market_status_label.pack(side="left", padx=10)
        right = tk.Frame(ticker_header, bg=C["panel2"]); right.pack(side="right", padx=10)
        self.market_update_label = tk.Label(right, text="", bg=C["panel2"], fg=C["muted"], font=("Segoe UI", 8))
        self.market_update_label.pack(side="left", padx=8)
        self.btn(right, self.tr("retry_market"), self.refresh_market_data).pack(side="right", padx=3)

        self.ticker_canvas = tk.Canvas(self.content, height=76, bg=C["bg"], highlightthickness=0)
        self.ticker_canvas.pack(fill="x", pady=(0,6))
        self.render_market_ticker(self.market_data_payload)
        self.ticker_offset = 0
        self.ticker_job = self.after(45, self._animate_ticker)

        indicator_head = tk.Frame(self.content, bg=C["bg"]); indicator_head.pack(fill="x", pady=(1,2))
        tk.Label(indicator_head, text=self.tr("market_indicators"), bg=C["bg"], fg=C["text"], font=("Segoe UI", 11, "bold")).pack(side="right")
        tk.Label(indicator_head, text=f"{self.market} • {self.market_data_payload.get('source','—')}", bg=C["bg"], fg=C["muted"], font=("Segoe UI", 8)).pack(side="left")
        self.indicator_row = tk.Frame(self.content, bg=C["bg"]); self.indicator_row.pack(fill="x", pady=(0,7))
        self.render_market_indicators(self.market_data_payload)
        self.market_data.set_market(self.market)
        self.market_data.refresh_now()

        session_wrap = tk.Frame(self.content, bg=C["bg"]); session_wrap.pack(fill="x", pady=(1,7))
        session_head = tk.Frame(session_wrap, bg=C["bg"]); session_head.pack(fill="x")
        tk.Label(session_head, text=self.tr("session_strip"), bg=C["bg"], fg=C["text"], font=("Segoe UI", 11, "bold")).pack(side="right")
        tk.Label(session_head, text="SYD • TYO • LON • NY", bg=C["bg"], fg=C["muted"], font=("Consolas", 8, "bold")).pack(side="left")
        clocks = tk.Frame(session_wrap, bg=C["bg"]); clocks.pack(fill="x", pady=(4,0))
        for col, session in enumerate(SESSION_CLOCKS):
            clocks.columnconfigure(col, weight=1)
            card = self.card(clocks); card.grid(row=0, column=col, sticky="nsew", padx=4)
            self.draw_session_clock(card, session)
        self.update_session_clocks()

        stats = tk.Frame(self.content, bg=C["bg"]); stats.pack(fill="x", pady=5)
        cards = [
            ("◉", self.tr("trading_count"), len(p["journals"][self.market]), C["cyan"]),
            ("↗", self.tr("win_rate"), f"{self.win_rate(p['journals'][self.market]):.1f}%", C["accent"]),
            ("R", self.tr("net_r"), f"{sum(result_num(x) for x in p['journals'][self.market]):.2f} R", C["gold"]),
            ("$", self.tr("initial_balance"), f"{p['initial_balance']:,.2f} {p['currency']}", C["violet"]),
        ]
        for icon, title, value, accent_color in cards:
            box = self.card(stats); box.pack(side="left", fill="both", expand=True, padx=4)
            tk.Label(box, text=icon, bg=C["panel"], fg=accent_color, font=("Segoe UI Symbol", 15, "bold")).pack(anchor="w", padx=13, pady=(8,1))
            tk.Label(box, text=title, bg=C["panel"], fg=C["muted"], font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=13)
            tk.Label(box, text=value, bg=C["panel"], fg=C["text"], font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=13, pady=(0,8))

        lower = tk.Frame(self.content, bg=C["bg"]); lower.pack(fill="both", expand=True, pady=4)
        left = self.card(lower); left.pack(side="left", fill="both", expand=True, padx=(0,4))
        right = self.card(lower); right.pack(side="left", fill="both", expand=True, padx=(4,0))
        tk.Label(left, text=self.tr("performance"), bg=C["panel"], fg=C["text"], font=("Segoe UI", 11, "bold")).pack(anchor="e", padx=14, pady=8)
        self.draw_bar_chart(left, p["journals"][self.market])
        tk.Label(right, text=self.tr("distribution"), bg=C["panel"], fg=C["text"], font=("Segoe UI", 11, "bold")).pack(anchor="e", padx=14, pady=8)
        self.draw_pie_chart(right, p["journals"][self.market])

        actions = tk.Frame(self.content, bg=C["bg"]); actions.pack(fill="x", pady=(4,8))
        self.btn(actions, self.tr("new_trade"), self.add_trade, True).pack(side="right")
        self.btn(actions, self.tr("crypto_calc"), lambda:self.open_calculator("Crypto")).pack(side="left", padx=3)
        self.btn(actions, self.tr("forex_calc"), lambda:self.open_calculator("Forex")).pack(side="left", padx=3)
        self.btn(actions, self.tr("ai"), lambda:self.show("ai")).pack(side="left", padx=3)
        self.btn(actions, self.tr("news"), lambda:self.show("news")).pack(side="left", padx=3)
        self.btn(actions, self.tr("email_statement"), self.email_statement).pack(side="left", padx=3)

    def refresh_market_data(self):
        self.market_data_payload["status"] = "loading"
        self.market_data_payload["message"] = self.tr("market_loading")
        if hasattr(self, "market_status_label"):
            self.market_status_label.config(text=self.tr("market_loading"), fg=C["gold"])
        if hasattr(self, "ticker_canvas"):
            self.render_market_ticker(self.market_data_payload)
        self.market_data.set_market(self.market)
        self.market_data.refresh_now()

    def render_market_indicators(self, payload=None):
        if not hasattr(self, "indicator_row"):
            return
        payload = payload or self.market_data_payload
        for w in self.indicator_row.winfo_children():
            w.destroy()
        ind = payload.get("indicators") or {}
        fg = ind.get("fear_greed") or {}
        cards = [
            ("fear_greed", fg.get("value"), fg.get("label") or "—", "gauge"),
            ("btc_dom", ind.get("btc_dominance"), "%", "donut"),
            ("usdt_dom", ind.get("usdt_dominance"), "%", "donut"),
            ("vix", (ind.get("vix") or {}).get("value"), "", "bar"),
            ("total_mcap", ind.get("total_market_cap"), "", "value"),
        ]
        for key, value, suffix, kind in cards:
            card = self.card(self.indicator_row); card.pack(side="left", fill="both", expand=True, padx=3)
            title = INDICATOR_LABELS.get(self.language, INDICATOR_LABELS["en"]).get(key, key)
            tk.Label(card, text=title, bg=C["panel"], fg=C["muted"], font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=10, pady=(7,1))
            canvas = tk.Canvas(card, width=108, height=58, bg=C["panel"], highlightthickness=0)
            canvas.pack(side="left", padx=(6,2), pady=(2,5))
            text_box = tk.Frame(card, bg=C["panel"]); text_box.pack(side="left", fill="both", expand=True, padx=(0,7))
            main_value = "—"
            if value is not None:
                if key == "fear_greed": main_value = f"{int(value)}"
                elif key in ("btc_dom","usdt_dom","vix"): main_value = f"{value:.2f}{suffix}"
                else: main_value = ("USD " + f"{value/1_000_000_000:,.1f}B") if value >= 1e9 else ("USD " + f"{value:,.0f}")
            tk.Label(text_box, text=main_value, bg=C["panel"], fg=C["text"], font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(8,0))
            if key == "fear_greed":
                tk.Label(text_box, text=str(suffix), bg=C["panel"], fg=C["accent"], font=("Segoe UI", 8, "bold"), wraplength=90).pack(anchor="w")
            elif key in ("btc_dom","usdt_dom"):
                tk.Label(text_box, text="Market Share", bg=C["panel"], fg=C["muted"], font=("Segoe UI", 7)).pack(anchor="w")
            elif key == "vix":
                change = (ind.get("vix") or {}).get("change")
                tk.Label(text_box, text=("—" if change is None else f"{change:+.2f}%"), bg=C["panel"], fg=C["accent"] if (change or 0) <= 0 else C["danger"], font=("Consolas", 8, "bold")).pack(anchor="w")
            else:
                tk.Label(text_box, text="Global crypto market", bg=C["panel"], fg=C["muted"], font=("Segoe UI", 7)).pack(anchor="w")
            self._draw_indicator_shape(canvas, kind, value)

    def _draw_indicator_shape(self, canvas, kind, value):
        canvas.delete("all")
        if value is None:
            canvas.create_text(54,30,text="—",fill=C["muted"],font=("Segoe UI",16,"bold")); return
        if kind == "gauge":
            canvas.create_arc(8,8,100,100,start=180,extent=180,style="arc",outline=C["danger"],width=7)
            canvas.create_arc(8,8,100,100,start=252,extent=108,style="arc",outline=C["accent"],width=7)
            v=max(0,min(100,float(value))); angle=math.radians(180+(v*180/100))
            canvas.create_line(54,54,54+34*math.cos(angle),54+34*math.sin(angle),fill=C["text"],width=3)
            canvas.create_oval(50,50,58,58,fill=C["accent"],outline="")
        elif kind == "donut":
            pct=max(0,min(100,float(value)))
            canvas.create_arc(8,8,100,100,start=90,extent=-360,style="arc",outline=C["line"],width=10)
            canvas.create_arc(8,8,100,100,start=90,extent=-3.6*pct,style="arc",outline=C["accent"],width=10)
            canvas.create_text(54,54,text=f"{pct:.1f}",fill=C["text"],font=("Segoe UI",10,"bold"))
        elif kind == "bar":
            v=max(0,min(50,float(value)))
            canvas.create_rectangle(8,24,100,38,fill=C["soft"],outline="")
            canvas.create_rectangle(8,24,8+92*(v/50),38,fill=C["gold"],outline="")
            canvas.create_text(54,48,text="0 — 50",fill=C["muted"],font=("Consolas",7))
        else:
            canvas.create_line(8,42,100,42,fill=C["line"],width=1)
            pts=[(8,38),(24,32),(40,36),(56,23),(72,28),(88,18),(100,22)]
            canvas.create_line(pts,fill=C["accent"],width=2,smooth=True)
            canvas.create_text(8,10,text="LIVE",anchor="w",fill=C["muted"],font=("Consolas",7,"bold"))

    def render_market_ticker(self, payload=None):
        payload = payload or self.market_data_payload
        if not hasattr(self, "ticker_canvas") or not self.ticker_canvas.winfo_exists():
            return
        c = self.ticker_canvas
        c.delete("all")
        items = list(payload.get("items") or [])
        if not items:
            state = payload.get("status", "unavailable")
            if state == "loading":
                msg = payload.get("message") or self.tr("market_loading")
                fill = C["gold"]
            else:
                msg = payload.get("message") or self.tr("market_unavailable")
                fill = C["muted"]
            c.create_text(20, 38, text=msg, anchor="w", fill=fill, font=("Segoe UI", 10, "bold"))
        else:
            width = max(self.ticker_canvas.winfo_width(), 820)
            card_w = 170 if self.market == "Crypto" else 156
            gap = 8
            step = card_w + gap
            offset = self.ticker_offset % max(step * len(items), 1)
            x = 6 - offset
            for item in items * 3:
                price = item.get("price")
                if price is None:
                    x += step
                    continue
                tag = str(item.get("symbol", "")).upper()
                change = item.get("change")
                if price >= 1000: ptxt = f"{price:,.0f}"
                elif price >= 1: ptxt = f"{price:,.2f}"
                else: ptxt = f"{price:,.5f}"
                ctxt = "—" if change is None else f"{change:+.2f}%"
                accent = C["accent"] if (change or 0) >= 0 else C["danger"]
                self._rounded_rect(c, x, 7, x+card_w, 69, radius=14, fill=C["panel"], outline=C["line"], width=1)
                c.create_oval((x+10, 19, x+17, 26), fill=accent, outline="")
                c.create_text(x+24, 23, text=tag, anchor="w", fill=C["muted"], font=("Segoe UI", 8, "bold"))
                c.create_text(x+12, 47, text=ptxt, anchor="w", fill=C["text"], font=("Consolas", 12, "bold"))
                c.create_text(x+card_w-12, 47, text=ctxt, anchor="e", fill=accent, font=("Consolas", 9, "bold"))
                x += step
        state = payload.get("status", "unavailable")
        if hasattr(self, "market_status_label"):
            if state == "live":
                status_text = f"{self.tr('live')} • {payload.get('source','')}"
                status_fg = C["accent"]
            elif state == "cache":
                status_text = f"{self.tr('cached')} • {payload.get('source','')}"
                status_fg = C["gold"]
            elif state == "loading":
                status_text = self.tr("market_loading")
                status_fg = C["gold"]
            else:
                status_text = self.tr("market_unavailable")
                status_fg = C["danger"]
            self.market_status_label.config(text=status_text, fg=status_fg)
            if payload.get("message"):
                self.market_status_label.config(text=f"{status_text}  |  {payload.get('message')}")
        if hasattr(self, "market_update_label"):
            stamp = payload.get("updated_at") or ""
            self.market_update_label.config(text=f"{self.tr('last_update')}: {stamp.replace('T',' ')}")

    def _animate_ticker(self):
        if self.cur != "home":
            self.ticker_job = None
            return
        self.ticker_offset += 1
        self.render_market_ticker(self.market_data_payload)
        self.ticker_job = self.after(45, self._animate_ticker)

    def _market_data_callback(self, payload):
        self.market_data_payload = payload
        try:
            self.after(0, lambda p=payload: self._apply_market_data(p))
        except Exception:
            pass

    def _apply_market_data(self, payload):
        self.market_data_payload = payload
        if self.cur == "home":
            self.ticker_offset = 0
            self.render_market_ticker(payload)
            self.render_market_indicators(payload)

    def draw_session_clock(self, parent, session):
        holder = tk.Frame(parent, bg=C["panel"]); holder.pack(fill="x", padx=8, pady=4)
        canvas = tk.Canvas(holder, width=68, height=68, bg=C["panel"], highlightthickness=0)
        canvas.pack(side="left", padx=(3,8), pady=3)
        info = tk.Frame(holder, bg=C["panel"]); info.pack(side="left", fill="x", expand=True, pady=5)
        title = tk.Label(info, text=session["fa"] if self.language == "fa" else session["en"], bg=C["panel"],
                         fg=C["gold"], font=("Segoe UI", 9, "bold"))
        title.pack(anchor="w")
        status = tk.Label(info, text="", bg=C["panel"], fg=C["muted"], font=("Segoe UI", 8, "bold"))
        status.pack(anchor="w", pady=(2,0))
        hours = tk.Label(info, text="", bg=C["panel"], fg=C["muted"], font=("Consolas", 7))
        hours.pack(anchor="w")
        self.session_clock_widgets.append((canvas, status, hours, session))

    def update_session_clocks(self):
        if self.cur != "home":
            return
        for canvas, status, hours, session in list(self.session_clock_widgets):
            try:
                now = datetime.now(ZoneInfo(session["tz"]))
                w = h = 68
                cx = cy = 34
                r = 27
                canvas.delete("all")
                canvas.create_oval(2,2,66,66,fill=C["shadow"],outline=C["line"])
                canvas.create_oval(6,6,62,62,fill=C["panel3"],outline=C["soft"])
                local_minutes = now.hour*60 + now.minute
                start = session["start"]*60; end = session["end"]*60
                progress = max(0.0, min(1.0, (local_minutes-start)/max(1,end-start))) if start <= local_minutes < end else 0.0
                canvas.create_arc(5,5,63,63,start=90,extent=-360*progress,style="arc",
                                 outline=C["accent"] if progress else C["soft"], width=3)
                for n in (0,15,30,45):
                    ang = math.radians(n*6-90)
                    canvas.create_line(cx+math.cos(ang)*22, cy+math.sin(ang)*22,
                                       cx+math.cos(ang)*25, cy+math.sin(ang)*25, fill=C["muted"], width=1)
                hour = (now.hour % 12) + now.minute/60.0
                minute = now.minute + now.second/60.0
                for value,turns,length,width,color in ((hour,12,14,3,C["text"]),(minute,60,20,2,C["gold"])):
                    ang = math.radians(value*(360/turns)-90)
                    canvas.create_line(cx,cy,cx+math.cos(ang)*length,cy+math.sin(ang)*length,fill=color,width=width)
                canvas.create_oval(30,30,38,38,fill=C["accent"],outline=C["panel3"],width=1)
                is_open = start <= local_minutes < end
                status.config(text=f"{self.tr('open') if is_open else self.tr('closed')}  •  {now.strftime('%H:%M')}",
                              fg=C["accent"] if is_open else C["muted"])
                hours.config(text=f"{session['start']:02d}:00–{session['end']:02d}:00  {now.tzname() or ''}")
            except Exception:
                continue
        if self.cur == "home":
            self.session_clock_job = self.after(1000, self.update_session_clocks)

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
        tk.Label(nav,text=display_date(date.fromisoformat(self.day), self.language),bg=C["bg"],fg=C["text"],font=("Segoe UI",11,"bold")).pack(side="left",padx=15)
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
        dlg=tk.Toplevel(self); dlg.title(self.ui_text("ویرایش فعالیت" if item else "فعالیت جدید")); dlg.geometry("560x320"); dlg.configure(bg=C["bg"]); dlg.transient(self); dlg.grab_set()
        vals={k:tk.StringVar(value=(item or {}).get(k,"")) for k in ("time","title","cat")}
        for i,(label,key) in enumerate([("زمان","time"),("عنوان","title"),("دسته","cat")]):
            tk.Label(dlg,text=label,bg=C["bg"],fg=C["muted"]).grid(row=i,column=1,padx=14,pady=12,sticky="e")
            tk.Entry(dlg,textvariable=vals[key],bg=C["soft"],fg=C["text"],relief="flat",justify="right").grid(row=i,column=0,padx=14,pady=12,sticky="ew")
        dlg.columnconfigure(0,weight=1)
        def submit():
            if not vals["title"].get().strip(): return messagebox.showwarning(self.ui_text("ورودی ناقص"),self.ui_text("عنوان فعالیت را وارد کن"),parent=dlg)
            if item: item.update({k:v.get().strip() for k,v in vals.items()})
            else: DB["tasks"].setdefault(self.day,[]).append({"id":str(uuid4()),"time":vals["time"].get().strip(),"title":vals["title"].get().strip(),"cat":vals["cat"].get().strip(),"done":False})
            save_db(); dlg.destroy(); self.show("daily")
        self.btn(dlg,"ذخیره",submit,True).grid(row=4,column=0,padx=14,pady=16,sticky="e")
        self.btn(dlg,"انصراف",dlg.destroy).grid(row=4,column=1,padx=14,pady=16)

    def add_task(self): self.task_dialog()
    def edit_task(self):
        sel=self.task_tree.selection()
        if not sel:return messagebox.showinfo(self.ui_text("انتخاب فعالیت"),self.ui_text("ابتدا یک فعالیت را انتخاب کن"))
        self.task_dialog(DB["tasks"][self.day][int(sel[0])])
    def delete_task(self):
        sel=self.task_tree.selection()
        if not sel:return messagebox.showinfo(self.ui_text("انتخاب فعالیت"),self.ui_text("ابتدا یک فعالیت را انتخاب کن"))
        idx=int(sel[0]); item=DB["tasks"][self.day][idx]
        if messagebox.askyesno(self.ui_text("حذف فعالیت"),self.ui_text(f"«{item.get('title','')}» حذف شود؟"),parent=self):
            DB["tasks"][self.day].pop(idx); save_db(); self.show("daily")

    def journal(self):
        p=active_profile(); self.market=p["market"]; rows=p["journals"][self.market]
        self.heading(f"Journal — {self.market}",f"پروفایل: {p['name']} | {display_date(date.today(), self.language)}")
        bar=tk.Frame(self.content,bg=C["bg"]); bar.pack(fill="x",pady=3)
        self.btn(bar,"＋ ثبت معامله",self.add_trade,True).pack(side="left",padx=3)
        self.btn(bar,"ویرایش",self.edit_trade).pack(side="left",padx=3); self.btn(bar,"حذف",self.delete_trade).pack(side="left",padx=3)
        self.btn(bar,"خروجی CSV",self.export_journal).pack(side="left",padx=3)
        self.btn(bar,self.tr("email_statement"),self.email_statement,True).pack(side="left",padx=3)
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
        if not sel:return messagebox.showinfo(self.ui_text("انتخاب معامله"),self.ui_text("ابتدا یک معامله را انتخاب کن"))
        self.trade_dialog(active_profile()["journals"][self.market][int(sel[0])],int(sel[0]))
    def delete_trade(self):
        sel=self.jtree.selection()
        if not sel:return messagebox.showinfo(self.ui_text("انتخاب معامله"),self.ui_text("ابتدا یک معامله را انتخاب کن"))
        idx=int(sel[0]); row=active_profile()["journals"][self.market][idx]
        if messagebox.askyesno(self.ui_text("حذف معامله"),self.ui_text(f"معامله {row.get('Symbol','')} حذف شود؟"),parent=self):
            active_profile()["journals"][self.market].pop(idx); save_db(); self.show("journal")
    def add_trade(self): self.trade_dialog()

    def trade_dialog(self,row=None,index=None):
        dlg=tk.Toplevel(self); dlg.title(self.ui_text(("ویرایش" if row else "ثبت")+f" معامله — {self.market}")); dlg.geometry("1180x800"); dlg.minsize(1020,700); dlg.configure(bg=C["bg"]); dlg.transient(self); dlg.grab_set()
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
            src=filedialog.askopenfilename(title=self.ui_text("انتخاب اسکرین‌شات"),filetypes=[("Images","*.png *.jpg *.jpeg *.webp *.bmp"),("All","*.*")],parent=dlg)
            if src: vals["Screenshot"].set(src)
        self.btn(controls,"انتخاب تصویر",browse).pack(side="left")
        self.btn(controls,"باز کردن پوشه",lambda:self.open_path(screenshot_folder({"Date":vals["Date"].get(),"Symbol":vals["Symbol"].get()}))).pack(side="left",padx=6)
        footer=tk.Frame(dlg,bg=C["bg"]); footer.pack(fill="x",padx=24,pady=8)
        def submit():
            data={k:v.get().strip() for k,v in vals.items()}
            if not data.get("Symbol"): return messagebox.showwarning(self.ui_text("ورودی ناقص"),"Enter Symbol.",parent=dlg)
            src=data.get("Screenshot","")
            if src and Path(src).is_file(): data["Screenshot"]=attach_screenshot(data,src,market=self.market)
            elif row is not None: data["Screenshot"]=row.get("Screenshot","")
            upsert_trade(active_profile(),self.market,data,index); save_db(); dlg.destroy(); self.show("journal")
        self.btn(footer,"ذخیره معامله",submit,True).pack(side="right",padx=5); self.btn(footer,"انصراف",dlg.destroy).pack(side="right",padx=5)
        self.translate_widget_tree(dlg)

    def export_journal(self):
        rows=active_profile()["journals"][self.market]
        if not rows:return messagebox.showinfo(self.ui_text("ژورنال خالی"),self.ui_text("معامله‌ای برای خروجی وجود ندارد"),parent=self)
        target=filedialog.asksaveasfilename(title=self.ui_text("ذخیره CSV"),defaultextension=".csv",initialfile=f"{self.market}_Journal_{date.today().isoformat()}.csv",filetypes=[("CSV","*.csv")])
        if not target:return
        with open(target,"w",newline="",encoding="utf-8-sig") as h:
            writer=csv.DictWriter(h,fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)
        messagebox.showinfo(self.ui_text("انجام شد"),self.ui_text("خروجی CSV ذخیره شد"),parent=self)

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
        messagebox.showinfo(self.ui_text("ذخیره شد"),self.ui_text(f"نسخه «{title}» ذخیره شد."),parent=self); self.show("plan")

    def plan_history(self):
        p=active_profile(); dlg=tk.Toplevel(self); dlg.title(self.ui_text("نسخه‌های Trading Plan")); dlg.geometry("680x500"); dlg.configure(bg=C["bg"]); dlg.transient(self); dlg.grab_set()
        tree=ttk.Treeview(dlg,columns=("title","date"),show="headings"); tree.heading("title",text="عنوان"); tree.heading("date",text="تاریخ"); tree.column("title",width=400); tree.pack(fill="both",expand=True,padx=15,pady=15)
        for i,item in enumerate(p["plans"]): tree.insert("", "end",iid=str(i),values=(item.get("title",""),item.get("created_at","")))
        def load():
            sel=tree.selection()
            if not sel:return
            item=p["plans"][int(sel[0])]; p["plan_draft"]=dict(item.get("fields",{})); p["active_plan_id"]=item["id"]; save_db(); dlg.destroy(); self.show("plan")
        self.btn(dlg,"باز کردن نسخه انتخاب‌شده",load,True).pack(side="right",padx=15,pady=10)
        self.translate_widget_tree(dlg)

    def export_current_plan(self):
        p=active_profile(); title=self.current_plan_title(); path=export_plan_a4(p,title,p["plan_draft"])
        messagebox.showinfo(self.ui_text("Export آماده شد"),self.ui_text(f"فایل A4 ساخته شد:\n{path}"),parent=self)

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
            return messagebox.showinfo(self.ui_text(self.tr("check_title")),self.ui_text(self.tr("empty_plan")),parent=self)
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
                return messagebox.showwarning(self.ui_text(self.tr("check_item")),self.ui_text(self.tr("condition_title")),parent=dlg)
            data={"id":(item or {}).get("id",str(uuid4())),"title":title,
                  "category":vals["category"].get().strip() or self.tr("general"),
                  "source":vals["source"].get().strip() or self.tr("manual"),
                  "required":req.get(),"done":bool((item or {}).get("done",False))}
            if item is None: active_profile()["checklist"].append(data)
            else: active_profile()["checklist"][index]=data
            save_db(); dlg.destroy(); self.render_checklist()
        self.btn(footer,self.tr("cancel"),dlg.destroy).pack(side="right",padx=4)
        self.btn(footer,self.tr("save"),submit,True).pack(side="right",padx=4)
        self.translate_widget_tree(dlg)

    def open_ai_chat(self):
        if self.ai_chat_window is not None:
            try:
                if self.ai_chat_window.winfo_exists():
                    self.ai_chat_window.deiconify()
                    self.ai_chat_window.lift()
                    self.ai_chat_window.focus_force()
                    return
            except Exception:
                pass

        dlg=tk.Toplevel(self)
        self.ai_chat_window=dlg
        dlg.title("Trader Planner Pro • AI Chat")
        dlg.geometry("820x700")
        dlg.minsize(680,560)
        dlg.configure(bg=C["bg"])
        dlg.transient(self)
        dlg.update_idletasks()
        apply_glass(dlg, dark=self._effective_theme()=="dark", style="acrylic")

        header=tk.Frame(dlg,bg=C["panel"],highlightbackground=C["line"],highlightthickness=1)
        header.pack(fill="x",padx=12,pady=12)
        tk.Label(header,text=self.tr("ai_title"),bg=C["panel"],fg=C["text"],font=("Segoe UI",17,"bold")).pack(side="right",padx=14,pady=12)
        status=self.ai.status()
        status_text=("CLOUD AGENT • READY" if status.get("cloud") else ("LOCAL • READY" if status.get("ollama") else "BUILT-IN • READY"))
        tk.Label(header,text=status_text,bg=C["panel3"],fg=C["accent"],font=("Consolas",9,"bold"),padx=10,pady=6).pack(side="left",padx=10)

        toolbar=tk.Frame(dlg,bg=C["bg"]); toolbar.pack(fill="x",padx=12)
        role_var=tk.StringVar(value="orchestrator")
        role_labels={"orchestrator":"Trader Planner Master Agent","form":"Form Coach","strategy":"Strategy Coach","psychology":"Psychology Coach","planner":"Routine & Reminder Coach","academy":"Academy Tutor","product":"Product Strategist"}
        ttk.Combobox(toolbar,textvariable=role_var,state="readonly",values=list(role_labels.values()),
                     width=25,justify="right").pack(side="right",padx=4)
        self.btn(toolbar,"AI Web",lambda:self.open_webview("https://chatgpt.com/","Trader Planner Pro • AI Web")).pack(side="left",padx=4)
        self.btn(toolbar,self.tr("ai_clear"),lambda:self._clear_ai_chat(),).pack(side="left",padx=4)

        card=self.card(dlg); card.pack(fill="both",expand=True,padx=12,pady=8)
        chat=tk.Text(card,bg=C["soft"],fg=C["text"],insertbackground=C["text"],wrap="word",relief="flat",
                     font=("Segoe UI",11),padx=14,pady=12)
        chat.pack(fill="both",expand=True,padx=6,pady=6)
        self.ai_chat_text=chat
        chat.insert("1.0",self.tr("ai_welcome")+"\n\n")
        chat.configure(state="disabled")

        bottom=tk.Frame(dlg,bg=C["bg"]); bottom.pack(fill="x",padx=12,pady=(0,12))
        prompt=tk.Entry(bottom,bg=C["soft"],fg=C["text"],insertbackground=C["text"],relief="flat",
                        font=("Segoe UI",11),justify="right")
        prompt.pack(side="right",fill="x",expand=True,padx=5,ipady=10)
        self.ai_chat_input=prompt

        def send(_=None):
            msg=prompt.get().strip()
            if not msg: return
            prompt.delete(0,"end")
            role=next((k for k,v in role_labels.items() if v==role_var.get()),"form")
            context=self._ai_context()
            self._append_ai("You",msg)
            self._append_ai("Assistant","…")
            self.ai.respond(role,msg,context,lambda answer:self.after(0,lambda:self._replace_ai_waiting(answer)))

        send_btn=self.btn(bottom,self.tr("ai_send"),send,True); send_btn.pack(side="left",padx=5)
        self.btn(bottom,self.tr("ai_close"),dlg.destroy).pack(side="left",padx=5)
        prompt.bind("<Return>",send)

        def on_close():
            self.ai_chat_window=None
            self.ai_chat_text=None
            self.ai_chat_input=None
            dlg.destroy()
        dlg.protocol("WM_DELETE_WINDOW",on_close)

    def _ai_context(self):
        p=active_profile()
        recent=p.get("journals",{}).get(self.market,[])
        checklist=p.get("checklist",[])
        return (
            f"Current page: {self.cur}\n"
            f"Market: {self.market}\n"
            f"Profile: {p.get('name','')}\n"
            f"Trading plan: {json.dumps(p.get('plan_draft',{}),ensure_ascii=False)}\n"
            f"Recent trades: {json.dumps(recent[-5:],ensure_ascii=False)}\n"
            f"Checklist completed: {sum(1 for x in checklist if x.get('done'))}/{len(checklist)}\n"
            f"Market payload: {json.dumps(self.market_data_payload,ensure_ascii=False)}"
        )

    def _append_ai(self,speaker,text):
        if not self.ai_chat_text: return
        try:
            self.ai_chat_text.configure(state="normal")
            self.ai_chat_text.insert("end",f"{speaker}: {text}\n\n")
            self.ai_chat_text.configure(state="disabled")
            self.ai_chat_text.see("end")
        except Exception:
            pass

    def _replace_ai_waiting(self,answer):
        if not self.ai_chat_text: return
        try:
            self.ai_chat_text.configure(state="normal")
            current=self.ai_chat_text.get("1.0","end-1c")
            pos=current.rfind("Assistant: …")
            if pos>=0:
                self.ai_chat_text.delete(f"1.0+{pos}c",f"1.0+{pos+13}c")
                self.ai_chat_text.insert(f"1.0+{pos}c",f"Assistant: {answer}")
            else:
                self.ai_chat_text.insert("end",f"Assistant: {answer}\n")
            self.ai_chat_text.configure(state="disabled")
            self.ai_chat_text.see("end")
        except Exception:
            self._append_ai("Assistant",str(answer))

    def _clear_ai_chat(self):
        if self.ai_chat_text:
            try:
                self.ai_chat_text.configure(state="normal")
                self.ai_chat_text.delete("1.0","end")
                self.ai_chat_text.insert("1.0",self.tr("ai_welcome")+"\n\n")
                self.ai_chat_text.configure(state="disabled")
            except Exception:
                pass

    def _save_ai_key(self, api_key):
        try:
            from ai_assistant import save_openai_key
            save_openai_key(api_key)
            messagebox.showinfo(self.tr("ai_cloud"), self.tr("ai_cloud_ready"), parent=self)
            self.show("settings")
        except Exception as exc:
            messagebox.showerror(self.tr("ai_cloud"), str(exc), parent=self)

    def _clear_ai_key(self):
        try:
            from ai_assistant import clear_openai_key
            clear_openai_key()
            messagebox.showinfo(self.tr("ai_cloud"), self.tr("ai_cloud_missing"), parent=self)
            self.show("settings")
        except Exception as exc:
            messagebox.showerror(self.tr("ai_cloud"), str(exc), parent=self)

    def _open_product_agent_from_settings(self):
        self.show("ai")
        self.after(120, lambda: self.open_ai_chat())

    def _pick_google_credentials(self, status_label=None):
        path = filedialog.askopenfilename(
            parent=self,
            title=self.tr("google_pick_credentials"),
            filetypes=[("JSON files","*.json"),("All files","*.*")]
        )
        if not path:
            return
        DB.setdefault("settings", {})["google_credentials_path"] = path
        save_db()
        self._google_login_ui(status_label)

    def _google_login_ui(self, status_label=None):
        custom = DB.get("settings", {}).get("google_credentials_path", "")
        try:
            state = login_google(custom or None)
            text = f"{self.tr('google_connected')}: {state.get('email','')}"
            if status_label is not None and status_label.winfo_exists():
                status_label.config(text=text, fg=C["accent"])
            else:
                messagebox.showinfo(self.tr("google_account"), text, parent=self)
        except FileNotFoundError:
            self._pick_google_credentials(status_label)
        except Exception as exc:
            messagebox.showerror(self.tr("google_account"), str(exc), parent=self)

    def _google_logout_ui(self, status_label=None):
        try:
            logout_google()
            if status_label is not None and status_label.winfo_exists():
                status_label.config(text=self.tr("google_credentials"), fg=C["muted"])
            else:
                messagebox.showinfo(self.tr("google_account"), self.tr("google_logout"), parent=self)
        except Exception as exc:
            messagebox.showerror(self.tr("google_account"), str(exc), parent=self)

    def email_statement(self):
        rows = active_profile().get("journals", {}).get(self.market, [])
        state = google_status()
        if not state.get("connected"):
            if not messagebox.askyesno(
                self.tr("google_account"),
                self.tr("google_login") + "?",
                parent=self,
            ):
                return
            self._google_login_ui()
            state = google_status()
            if not state.get("connected"):
                return
        self._set_busy_cursor(True)
        profile_name = active_profile().get("name", "")
        def worker():
            try:
                out = create_statement(rows, self.market, profile_name, REPORTS)
                subject = f"{self.tr('email_statement_subject')} • {self.market} • {datetime.now().strftime('%Y-%m-%d')}"
                body = (
                    f"Trader Planner Pro\n\n"
                    f"Profile: {profile_name}\n"
                    f"Market: {self.market}\n"
                    f"Trades: {out['stats']['trades']}\n"
                    f"Win Rate: {out['stats']['win_rate']:.1f}%\n"
                    f"Net R: {out['stats']['net_r']:.2f}\n"
                    f"Average R: {out['stats']['avg_r']:.2f}\n"
                )
                send_gmail(state.get("email") or "", subject, body, [out["pdf"], out["png"]])
                self.after(0, lambda: (
                    self._set_busy_cursor(False),
                    messagebox.showinfo(self.tr("google_account"), self.tr("email_statement_sent"), parent=self)
                ))
            except Exception as exc:
                self.after(0, lambda: (
                    self._set_busy_cursor(False),
                    messagebox.showerror(self.tr("google_account"), f"{self.tr('email_statement_error')}\n{exc}", parent=self)
                ))
        threading.Thread(target=worker, name="TraderPlannerStatement", daemon=True).start()

    def _set_busy_cursor(self, busy):
        try:
            self.configure(cursor="watch" if busy else "")
            self.update_idletasks()
        except Exception:
            pass

    def open_webview(self, url, title="Trader Planner Pro"):
        try:
            if getattr(sys, "frozen", False):
                cmd = [sys.executable, "--webview", url, title]
            else:
                launcher = Path(__file__).with_name("launcher.py")
                cmd = [sys.executable, str(launcher), "--webview", url, title]
            creationflags = 0x08000000 if sys.platform.startswith("win") else 0
            subprocess.Popen(cmd, creationflags=creationflags)
        except Exception:
            webbrowser.open(url)

    def settings(self):
        p=active_profile()
        self.heading(self.tr("settings_title"), self.tr("settings_sub"))

        lang_box=self.card(self.content); lang_box.pack(fill="x",pady=8)
        tk.Label(lang_box,text=self.tr("choose_language"),bg=C["panel"],fg=C["text"],font=("Segoe UI",13,"bold")).pack(anchor="e",padx=18,pady=(16,5))
        tk.Label(lang_box,text=self.tr("language_help"),bg=C["panel"],fg=C["muted"],font=("Segoe UI",9)).pack(anchor="e",padx=18,pady=(0,12))
        row=tk.Frame(lang_box,bg=C["panel"]); row.pack(fill="x",padx=18,pady=(0,15))
        fa_btn=tk.Button(row,text="فارسی",command=lambda:self.set_language("fa"),bg=C["accent"] if self.language=="fa" else C["soft"],
                         fg="#061019" if self.language=="fa" else C["text"],relief="flat",font=("Segoe UI",10,"bold"),padx=24,pady=10)
        en_btn=tk.Button(row,text="English",command=lambda:self.set_language("en"),bg=C["accent"] if self.language=="en" else C["soft"],
                         fg="#061019" if self.language=="en" else C["text"],relief="flat",font=("Segoe UI",10,"bold"),padx=24,pady=10)
        fa_btn.pack(side="right",padx=5); en_btn.pack(side="right",padx=5)
        tk.Label(row,text=f"{self.tr('language_now')}: {'فارسی' if self.language=='fa' else 'English'}",
                 bg=C["panel"],fg=C["gold"],font=("Segoe UI",9,"bold")).pack(side="left",padx=8)

        skin_box=self.card(self.content); skin_box.pack(fill="x",pady=8)
        tk.Label(skin_box,text=self.tr("skin"),bg=C["panel"],fg=C["text"],font=("Segoe UI",13,"bold")).pack(anchor="e",padx=18,pady=(14,4))
        tk.Label(skin_box,text=self.tr("skin_help"),bg=C["panel"],fg=C["muted"],font=("Segoe UI",9)).pack(anchor="e",padx=18,pady=(0,12))
        skin_labels={}
        for k,v in SKINS.items():
            skin_labels[v.get(self.language=="fa" and "label_fa" or "label_en",k)]=k
        skin_var=tk.StringVar(value=SKINS[self.skin]["label_fa" if self.language=="fa" else "label_en"])
        skin_combo=ttk.Combobox(skin_box,textvariable=skin_var,state="readonly",values=list(skin_labels.keys()),width=30,justify="center")
        skin_combo.pack(anchor="e",padx=18,pady=(0,14))
        self.btn(skin_box,self.tr("save_theme"),lambda:self._save_skin_and_theme(skin_labels,skin_var),True).pack(anchor="e",padx=18,pady=(0,14))

        theme_box=self.card(self.content); theme_box.pack(fill="x",pady=8)
        tk.Label(theme_box,text=self.tr("theme"),bg=C["panel"],fg=C["text"],font=("Segoe UI",13,"bold")).pack(anchor="e",padx=18,pady=(14,4))
        tk.Label(theme_box,text=self.tr("theme_help"),bg=C["panel"],fg=C["muted"],font=("Segoe UI",9)).pack(anchor="e",padx=18,pady=(0,12))
        theme_row=tk.Frame(theme_box,bg=C["panel"]); theme_row.pack(fill="x",padx=18,pady=(0,15))
        labels=THEME_LABELS.get(self.language,THEME_LABELS["en"])
        theme_labels=THEME_LABELS.get(self.language,THEME_LABELS["en"])
        theme_display={theme_labels["dark"]:"dark",theme_labels["light"]:"light",theme_labels["auto"]:"auto"}
        theme_var=tk.StringVar(value=theme_labels.get(self.theme_mode,theme_labels["dark"]))
        theme_combo=ttk.Combobox(theme_row,textvariable=theme_var,state="readonly",
                                 values=list(theme_display.keys()),width=18,justify="center")
        theme_combo.pack(side="right",padx=6)
        tk.Label(theme_row,text=self.ui_text("Dark / Light / Automatic"),bg=C["panel"],fg=C["muted"],font=("Segoe UI",9)).pack(side="right",padx=8)

        times=tk.Frame(theme_box,bg=C["panel"]); times.pack(fill="x",padx=18,pady=(0,14))
        start_var=tk.StringVar(value=self.theme_auto_start); end_var=tk.StringVar(value=self.theme_auto_end)
        tk.Label(times,text=labels["auto_start"],bg=C["panel"],fg=C["muted"],font=("Segoe UI",9)).pack(side="right",padx=5)
        tk.Entry(times,textvariable=start_var,width=8,justify="center",bg=C["soft"],fg=C["text"],relief="flat").pack(side="right",padx=5)
        tk.Label(times,text=labels["auto_end"],bg=C["panel"],fg=C["muted"],font=("Segoe UI",9)).pack(side="right",padx=10)
        tk.Entry(times,textvariable=end_var,width=8,justify="center",bg=C["soft"],fg=C["text"],relief="flat").pack(side="right",padx=5)
        def save_theme():
            mode=theme_display.get(theme_var.get(),"dark")
            start=start_var.get().strip() or "08:00"; end=end_var.get().strip() or "20:00"
            if not self._valid_hhmm(start): start="08:00"
            if not self._valid_hhmm(end): end="20:00"
            DB.setdefault("settings",{}).update({"theme":mode,"theme_auto_start":start,"theme_auto_end":end})
            self.theme_mode=mode; self.theme_auto_start=start; self.theme_auto_end=end
            save_db(); self.apply_theme(); self.show(self.cur)
        self.btn(theme_box,self.tr("save_theme"),save_theme,True).pack(anchor="e",padx=18,pady=(0,14))

        # AI provider card
        ai_box=self.card(self.content); ai_box.pack(fill="x",pady=8)
        tk.Label(ai_box,text=self.tr("ai_agent_roles"),bg=C["panel"],fg=C["text"],font=("Segoe UI",13,"bold")).pack(anchor="e",padx=18,pady=(14,4))
        tk.Label(ai_box,text=self.tr("ai_cloud_note"),bg=C["panel"],fg=C["muted"],font=("Segoe UI",9),wraplength=1080,justify="right").pack(anchor="e",padx=18,pady=(0,10))
        ai_status=self.ai.status()
        status_text=self.tr("ai_cloud_ready") if ai_status.get("cloud") else self.tr("ai_cloud_missing")
        tk.Label(ai_box,text=status_text,bg=C["panel3"],fg=C["accent"] if ai_status.get("cloud") else C["gold"],font=("Consolas",9,"bold"),padx=10,pady=6).pack(anchor="e",padx=18,pady=4)
        ai_row=tk.Frame(ai_box,bg=C["panel"]); ai_row.pack(fill="x",padx=18,pady=8)
        ai_key=tk.StringVar()
        ai_entry=tk.Entry(ai_row,textvariable=ai_key,show="•",bg=C["soft"],fg=C["text"],insertbackground=C["text"],relief="flat",width=52,justify="left")
        ai_entry.pack(side="right",padx=5,ipady=8)
        self.btn(ai_row,self.tr("ai_save_key"),lambda:self._save_ai_key(ai_key.get()),True).pack(side="right",padx=4)
        self.btn(ai_row,self.tr("ai_clear_key"),self._clear_ai_key).pack(side="right",padx=4)
        self.btn(ai_box,self.tr("agent_upgrade_ideas"),lambda:self._open_product_agent_from_settings()).pack(anchor="e",padx=18,pady=(0,12))

        # Google / Gmail card
        google_box=self.card(self.content); google_box.pack(fill="x",pady=8)
        tk.Label(google_box,text=self.tr("google_account"),bg=C["panel"],fg=C["text"],font=("Segoe UI",13,"bold")).pack(anchor="e",padx=18,pady=(14,4))
        tk.Label(google_box,text=self.tr("google_no_credentials"),bg=C["panel"],fg=C["muted"],font=("Segoe UI",9),wraplength=1080,justify="right").pack(anchor="e",padx=18,pady=(0,10))
        google_state=google_status()
        google_text=(f"{self.tr('google_connected')}: {google_state.get('email','')}" if google_state.get("connected") else self.tr("google_credentials"))
        google_label=tk.Label(google_box,text=google_text,bg=C["panel3"],fg=C["accent"] if google_state.get("connected") else C["muted"],font=("Segoe UI",9,"bold"),anchor="e")
        google_label.pack(fill="x",padx=18,pady=5)
        g_row=tk.Frame(google_box,bg=C["panel"]); g_row.pack(fill="x",padx=18,pady=(2,14))
        self.btn(g_row,self.tr("google_login"),lambda:self._google_login_ui(google_label),True).pack(side="right",padx=4)
        self.btn(g_row,self.tr("google_logout"),lambda:self._google_logout_ui(google_label)).pack(side="right",padx=4)
        self.btn(g_row,self.tr("google_pick_credentials"),lambda:self._pick_google_credentials(google_label)).pack(side="right",padx=4)
        self.btn(g_row,"Google OAuth Guide",lambda:self.open_webview("https://developers.google.com/workspace/gmail/api/quickstart/python","Google Gmail API — OAuth Setup")).pack(side="right",padx=4)

        profile_box=self.card(self.content); profile_box.pack(fill="x",pady=8)
        info=(f"{self.tr('profile')}: {p['name']}\n"
              f"{self.tr('market')}: {p['market']}\n"
              f"{self.tr('initial_balance')}: {p['initial_balance']:,.2f} {p['currency']}\n"
              f"{self.tr('data_path')}: {DATA}\n{self.tr('reports_path')}: {REPORTS}")
        tk.Label(profile_box,text=info,bg=C["panel"],fg=C["muted"],justify="right",font=("Segoe UI",9)).pack(anchor="e",padx=18,pady=14)
        self.btn(profile_box,self.tr("manage_profiles"),self.edit_profile,True).pack(anchor="e",padx=18,pady=8)

    def open_calculator(self, market):
        self._calculator_market = "Forex" if market == "Forex" else "Crypto"
        self.show("calculators")

    def _save_skin_and_theme(self,skin_labels,skin_var):
        self.skin=skin_labels.get(skin_var.get(),"glass")
        DB.setdefault("settings",{})["skin"]=self.skin
        save_db()
        self.apply_theme()
        self.show(self.cur)

    def calculators(self):
        self.heading(self.tr("calculators"), self.tr("dashboard_sub"))
        nb=ttk.Notebook(self.content); nb.pack(fill="both",expand=True,pady=8)
        crypto_tab=tk.Frame(nb,bg=C["bg"]); forex_tab=tk.Frame(nb,bg=C["bg"])
        nb.add(crypto_tab,text=self.tr("crypto_calc")); nb.add(forex_tab,text=self.tr("forex_calc"))
        default_market = getattr(self, "_calculator_market", self.market)
        nb.select(forex_tab if default_market == "Forex" else crypto_tab)
        self._calculator_market = default_market

        def field(parent,label,default,row):
            tk.Label(parent,text=label,bg=C["panel"],fg=C["muted"],font=("Segoe UI",9,"bold")).grid(row=row,column=1,padx=8,pady=7,sticky="e")
            var=tk.StringVar(value=str(default))
            ent=tk.Entry(parent,textvariable=var,bg=C["soft"],fg=C["text"],insertbackground=C["text"],relief="flat",justify="center")
            ent.grid(row=row,column=0,padx=8,pady=7,sticky="ew")
            return var

        def build_crypto(parent):
            box=self.card(parent); box.pack(fill="x",padx=18,pady=18)
            box.columnconfigure(0,weight=1)
            balance=field(box,self.tr("balance"),1000,0); risk=field(box,self.tr("risk_pct"),1,1)
            entry=field(box,self.tr("entry"),100,2); stop=field(box,self.tr("stop"),95,3); target=field(box,self.tr("target"),110,4)
            out=tk.Label(parent,text="",bg=C["panel2"],fg=C["text"],justify="right",font=("Consolas",11),padx=14,pady=14)
            out.pack(fill="x",padx=18,pady=8)
            def calc():
                try:
                    bal=numeric(balance.get()); rp=numeric(risk.get())/100; en=numeric(entry.get()); sl=numeric(stop.get()); tp=numeric(target.get())
                    risk_usd=bal*rp; dist=abs(en-sl); qty=risk_usd/dist if dist>0 else 0; notional=qty*en; rr=abs(tp-en)/dist if dist>0 else 0
                    out.config(text=f"{self.tr('risk_usd')}: {risk_usd:,.2f}\n{self.tr('stop_distance')}: {dist:,.6f}\n{self.tr('crypto_qty')}: {qty:,.6f}\n{self.tr('notional')}: {notional:,.2f}\n{self.tr('rr')}: {rr:.2f}")
                except Exception: out.config(text=self.tr("invalid_input"))
            self.btn(parent,self.tr("calc"),calc,True).pack(anchor="e",padx=18,pady=8)
        build_crypto(crypto_tab)

        def build_forex(parent):
            box=self.card(parent); box.pack(fill="x",padx=18,pady=18); box.columnconfigure(0,weight=1)
            balance=field(box,self.tr("balance"),1000,0); risk=field(box,self.tr("risk_pct"),1,1)
            entry=field(box,self.tr("entry"),1.1000,2); stop=field(box,self.tr("stop"),1.0950,3); target=field(box,self.tr("target"),1.1100,4)
            pip_size=field(box,self.tr("pip_size"),0.0001,5); pip_value=field(box,self.tr("pip_value"),10,6)
            out=tk.Label(parent,text="",bg=C["panel2"],fg=C["text"],justify="right",font=("Consolas",11),padx=14,pady=14); out.pack(fill="x",padx=18,pady=8)
            def calc():
                try:
                    bal=numeric(balance.get()); rp=numeric(risk.get())/100; en=numeric(entry.get()); sl=numeric(stop.get()); tp=numeric(target.get())
                    ps=max(numeric(pip_size.get()),1e-12); pv=max(numeric(pip_value.get()),1e-12)
                    risk_usd=bal*rp; pips=abs(en-sl)/ps; lots=risk_usd/(pips*pv) if pips>0 else 0; units=lots*100000; rr=abs(tp-en)/abs(en-sl) if abs(en-sl)>0 else 0
                    out.config(text=f"{self.tr('risk_usd')}: {risk_usd:,.2f}\n{self.tr('stop_distance')}: {pips:.1f} pips\n{self.tr('lot_size')}: {lots:.3f}\n{self.tr('units')}: {units:,.0f}\n{self.tr('rr')}: {rr:.2f}")
                except Exception: out.config(text=self.tr("invalid_input"))
            self.btn(parent,self.tr("calc"),calc,True).pack(anchor="e",padx=18,pady=8)
        build_forex(forex_tab)

        shortcuts=tk.Frame(self.content,bg=C["bg"]); shortcuts.pack(fill="x",pady=(4,8))
        self.btn(shortcuts,self.tr("home_shortcut"),self.go_home).pack(side="left")

    def news(self):
        self.heading(self.tr("news_title"), self.tr("news_sub"))
        toolbar=tk.Frame(self.content,bg=C["bg"]); toolbar.pack(fill="x",pady=(2,6))
        self.btn(toolbar,self.tr("open_forex_factory"),lambda:self.open_webview(FOREX_FACTORY,"Forex Factory — Economic Calendar"),True).pack(side="right",padx=3)
        self.btn(toolbar,self.tr("open_coindesk"),lambda:self.open_webview(COINDESK_HOME,"CoinDesk — News Terminal")).pack(side="right",padx=3)
        self.btn(toolbar,"Cointelegraph",lambda:self.open_webview("https://cointelegraph.com/","Cointelegraph")).pack(side="right",padx=3)
        self.btn(toolbar,self.tr("refresh_news"),self.refresh_news).pack(side="left",padx=3)
        self.news_status=tk.Label(toolbar,text="● "+self.tr("market_loading"),bg=C["bg"],fg=C["gold"],font=("Consolas",8,"bold"))
        self.news_status.pack(side="left",padx=10)

        shell=self.card(self.content); shell.pack(fill="both",expand=True,pady=4)
        self.news_tree=ttk.Treeview(shell,columns=("source","time","title"),show="headings",selectmode="browse")
        self.news_tree.heading("source",text=self.ui_text("Source"))
        self.news_tree.heading("time",text=self.ui_text("Date"))
        self.news_tree.heading("title",text=self.ui_text("Headline"))
        self.news_tree.column("source",width=145,anchor="center",stretch=False)
        self.news_tree.column("time",width=170,anchor="center",stretch=False)
        self.news_tree.column("title",anchor="w")
        self.news_tree.pack(fill="both",expand=True,padx=8,pady=8)
        self.news_tree.bind("<Double-1>",self.open_selected_news)
        self.refresh_news()

    def refresh_news(self):
        if not hasattr(self,"news_tree"): return
        for item in self.news_tree.get_children(): self.news_tree.delete(item)
        self.news_status.config(text="● "+self.tr("market_loading"),fg=C["gold"])
        self.news_tree.insert("","end",iid="loading",values=("…","…",self.tr("market_loading")))
        def done(rows):
            try: self.after(0,lambda:self._apply_news(rows))
            except Exception: pass
        fetch_market_news(done, include_forex=True)

    def _apply_news(self,rows):
        self.news_items=rows or []
        if not hasattr(self,"news_tree"): return
        for item in self.news_tree.get_children(): self.news_tree.delete(item)
        if self.news_items:
            self.news_status.config(text=f"● {len(self.news_items)} headlines",fg=C["accent"])
            for i,row in enumerate(self.news_items):
                self.news_tree.insert("","end",iid=str(i),values=(row.get("source","News"),row.get("published",""),row.get("title","")))
        else:
            self.news_status.config(text="● "+self.tr("market_unavailable"),fg=C["danger"])
            fallback=[
                ("CoinDesk","Open CoinDesk crypto terminal",COINDESK_HOME),
                ("Cointelegraph","Open Cointelegraph crypto terminal","https://cointelegraph.com/"),
                ("Decrypt","Open Decrypt crypto terminal","https://decrypt.co/"),
                ("CryptoSlate","Open CryptoSlate news terminal","https://cryptoslate.com/news-terminal/"),
                ("Forex Factory","Open Forex Factory economic calendar",FOREX_FACTORY),
            ]
            for i,(source,title,url) in enumerate(fallback):
                self.news_tree.insert("","end",iid=f"fallback-{i}",values=(source,"LIVE",title))
            self.news_items=[{"source":s,"published":"LIVE","title":t,"link":u} for s,t,u in fallback]

    def open_selected_news(self,_=None):
        if not hasattr(self,"news_tree"): return
        sel=self.news_tree.selection()
        if not sel: return
        key=sel[0]
        try:
            row=self.news_items[int(key)] if key.isdigit() else next(r for r in self.news_items if r.get("source")==self.news_tree.item(key,"values")[0] and r.get("title")==self.news_tree.item(key,"values")[2])
            self.open_webview(row["link"],f"Trader Planner Pro • {row.get('source','News')}")
        except Exception:
            pass

    def ai(self):
        self.heading(self.tr("ai_title"), self.tr("ai_sub"))

        hero=self.card(self.content)
        hero.pack(fill="x",pady=(4,8))
        left=tk.Frame(hero,bg=C["panel"]); left.pack(side="right",fill="both",expand=True,padx=14,pady=12)
        tk.Label(left,text=self.tr("ai_page_note"),bg=C["panel"],fg=C["muted"],
                 font=("Segoe UI",10,"bold"),justify="right",anchor="e",
                 wraplength=850).pack(fill="x",anchor="e")

        role_var=tk.StringVar(value="orchestrator")
        role_labels={"orchestrator":"Trader Planner Master Agent","form":"Form Coach","strategy":"Strategy Coach","psychology":"Psychology Coach","planner":"Routine & Reminder Coach","academy":"Academy Tutor","product":"Product Strategist"}
        row=tk.Frame(hero,bg=C["panel"]); row.pack(fill="x",padx=14,pady=(0,12))
        tk.Label(row,text=self.tr("ai_role"),bg=C["panel"],fg=C["muted"],
                 font=("Segoe UI",9,"bold")).pack(side="right",padx=6)
        role_combo=ttk.Combobox(
            row,textvariable=role_var,state="readonly",
            values=list(role_labels.values()),justify="right",width=25
        )
        role_combo.pack(side="right",padx=6)
        status=self.ai.status()
        if status.get("cloud"):
            status_text="CLOUD MASTER AGENT • GPT-5.6-LUNA • HIGH REASONING"
            status_fg=C["accent"]
        elif status.get("ollama"):
            status_text="LOCAL OLLAMA • READY"
            status_fg=C["cyan"]
        else:
            status_text="BUILT-IN FALLBACK • CONNECT AI IN SETTINGS"
            status_fg=C["gold"]
        tk.Label(row,text=status_text,bg=C["panel3"],fg=status_fg,
                 font=("Consolas",8,"bold"),padx=10,pady=5).pack(side="left")
        if not status.get("cloud") and not status.get("ollama"):
            self.btn(row,"⚡ "+self.tr("ai_cloud"),lambda:self.show("settings")).pack(side="left",padx=6)
        self.btn(row,"AI Web",lambda:self.open_webview("https://chatgpt.com/","Trader Planner Pro • AI Web")).pack(side="left",padx=6)

        quick=tk.Frame(self.content,bg=C["bg"])
        quick.pack(fill="x",pady=(0,7))
        quick_prompts=[
            ("ai_quick_forms","Form coach: help me fill today's trading plan and checklist."),
            ("ai_quick_strategy","Explain the current setup step-by-step and tell me what condition is still missing."),
            ("ai_quick_psychology","Run a short psychology check before I take a trade."),
            ("ai_quick_routine","Build a disciplined trading routine for today's sessions."),
        ]

        shell=self.card(self.content)
        shell.pack(fill="both",expand=True,pady=4)
        chat=tk.Text(
            shell,bg=C["soft"],fg=C["text"],insertbackground=C["text"],
            wrap="word",relief="flat",font=("Segoe UI",12),padx=16,pady=14
        )
        chat.pack(fill="both",expand=True,padx=7,pady=7)
        chat.insert("1.0",self.tr("ai_page_note")+"\n\n")
        chat.configure(state="disabled")

        input_row=tk.Frame(self.content,bg=C["bg"])
        input_row.pack(fill="x",pady=8)
        prompt=tk.Entry(
            input_row,bg=C["soft"],fg=C["text"],insertbackground=C["text"],
            relief="flat",font=("Segoe UI",12),justify="right"
        )
        prompt.pack(side="right",fill="x",expand=True,padx=5,ipady=10)
        send_btn=self.btn(input_row,self.tr("ai_send"),None,True)
        send_btn.pack(side="left",padx=5)

        def append_chat(speaker,text_value):
            chat.configure(state="normal")
            chat.insert("end",f"{speaker}: {text_value}\n\n")
            chat.configure(state="disabled")
            chat.see("end")

        def send_message(message=None):
            msg=(message if message is not None else prompt.get()).strip()
            if not msg: return
            prompt.delete(0,"end")
            append_chat("You",msg)
            append_chat("Assistant","…")
            role=next((k for k,v in role_labels.items() if v==role_var.get()),"form")
            context=self._ai_context()
            self.ai.respond(
                role,msg,context,
                lambda answer:self.after(
                    0,lambda:self._replace_page_ai_waiting(chat,answer)
                )
            )

        send_btn.configure(command=send_message)
        prompt.bind("<Return>",lambda e:send_message())
        for key, prompt_text in quick_prompts:
            self.btn(
                quick,self.tr(key),lambda p=prompt_text:send_message(p)
            ).pack(side="left",padx=3)

        self.btn(
            quick,self.tr("ai_clear"),lambda:self._clear_page_ai(chat)
        ).pack(side="left",padx=3)

        reminders=self.card(self.content)
        reminders.pack(fill="x",pady=(7,4))
        tk.Label(
            reminders,text=self.tr("reminders"),bg=C["panel"],fg=C["gold"],
            font=("Segoe UI",10,"bold")
        ).pack(anchor="e",padx=12,pady=7)
        rem_tree=ttk.Treeview(
            reminders,columns=("time","title","enabled"),show="headings",height=4
        )
        rem_tree.heading("time",text=self.tr("reminder_time"))
        rem_tree.heading("title",text=self.tr("reminder_title"))
        rem_tree.heading("enabled",text=self.tr("reminder_enabled"))
        rem_tree.column("time",width=90)
        rem_tree.column("title",width=500)
        rem_tree.column("enabled",width=90)
        rem_tree.pack(fill="x",padx=10,pady=5)
        for idx,r in enumerate(DB.get("settings",{}).get("ai_reminders",[])):
            rem_tree.insert(
                "","end",iid=str(idx),
                values=(r.get("time",""),r.get("title",""),
                        "✓" if r.get("enabled",True) else "")
            )
        controls=tk.Frame(reminders,bg=C["panel"]); controls.pack(fill="x",padx=10,pady=5)
        self.btn(controls,self.tr("add_reminder"),self.add_reminder,True).pack(side="right",padx=3)
        self.btn(controls,self.tr("delete_reminder"),lambda:self.delete_reminder(rem_tree)).pack(side="right",padx=3)

    def _replace_page_ai_waiting(self,chat,answer):
        try:
            chat.configure(state="normal")
            current=chat.get("1.0","end-1c")
            pos=current.rfind("Assistant: …")
            if pos>=0:
                chat.delete(f"1.0+{pos}c",f"1.0+{pos+13}c")
                chat.insert(f"1.0+{pos}c",f"Assistant: {answer}")
            else:
                chat.insert("end",f"Assistant: {answer}\n")
            chat.configure(state="disabled")
            chat.see("end")
        except Exception:
            pass

    def _clear_page_ai(self,chat):
        try:
            chat.configure(state="normal")
            chat.delete("1.0","end")
            chat.insert("1.0",self.tr("ai_page_note")+"\n\n")
            chat.configure(state="disabled")
        except Exception:
            pass

    def _ai_finish(self,chat,answer):
        try:
            lines=chat.get("1.0","end-1c").splitlines()
            if lines and lines[-1].strip()=="Assistant: ...":
                chat.delete(f"{len(lines)}.0", "end")
            chat.insert("end",str(answer)+"\n")
            chat.see("end")
        except Exception: pass

    def add_reminder(self):
        dlg=tk.Toplevel(self); dlg.title(self.tr("add_reminder")); dlg.geometry("520x300"); dlg.configure(bg=C["bg"]); dlg.transient(self); dlg.grab_set()
        title=tk.StringVar(); tm=tk.StringVar(value="09:00"); enabled=tk.BooleanVar(value=True)
        tk.Label(dlg,text=self.tr("reminder_title"),bg=C["bg"],fg=C["muted"]).pack(anchor="e",padx=16,pady=(16,5))
        tk.Entry(dlg,textvariable=title,bg=C["soft"],fg=C["text"],relief="flat",justify="right").pack(fill="x",padx=16)
        row=tk.Frame(dlg,bg=C["bg"]); row.pack(fill="x",padx=16,pady=12)
        tk.Label(row,text=self.tr("reminder_time"),bg=C["bg"],fg=C["muted"]).pack(side="right",padx=5)
        tk.Entry(row,textvariable=tm,width=8,bg=C["soft"],fg=C["text"],relief="flat",justify="center").pack(side="right",padx=5)
        tk.Checkbutton(dlg,text=self.tr("reminder_enabled"),variable=enabled,bg=C["bg"],fg=C["text"],selectcolor=C["soft"],activebackground=C["bg"],activeforeground=C["text"]).pack(anchor="e",padx=16)
        def save():
            value=tm.get().strip()
            if not self._valid_hhmm(value):
                return messagebox.showwarning(self.tr("reminders"),self.tr("reminder_time"),parent=dlg)
            DB.setdefault("settings",{}).setdefault("ai_reminders",[]).append({"id":str(uuid4()),"title":title.get().strip() or self.tr("reminders"),"time":value,"daily":True,"enabled":enabled.get(),"last_notified":""})
            save_db(); dlg.destroy(); self.show("ai")
        self.btn(dlg,self.tr("save_reminder"),save,True).pack(anchor="e",padx=16,pady=14)

    def delete_reminder(self,tree):
        sel=tree.selection()
        if not sel: return
        idx=int(sel[0]); reminders=DB.get("settings",{}).get("ai_reminders",[])
        if 0<=idx<len(reminders):
            reminders.pop(idx); save_db(); self.show("ai")

    def _academy_visual(self, parent, key, title, subtitle, visual_kind=None, family=""):\n        """Render source-correct Academy visuals: exact source image + semantic setup anatomy."""\n        box = tk.Frame(parent, bg=C["panel3"], highlightbackground=C["line"], highlightthickness=1)\n        box.pack(fill="x", padx=10, pady=(4, 8))\n        kind = visual_kind or key\n        source_title, source_url = source_for_visual(kind)\n        family_key = "ict" if family == "ict" else ("smc" if family == "smc" else "candles")\n        family_text = {"smc": self.tr("smc_family"), "ict": self.tr("ict_family"), "candles": self.tr("candles")}[family_key]\n        family_fg = {"smc": C["accent"], "ict": C["violet"], "candles": C["gold"]}[family_key]\n\n        header = tk.Frame(box, bg=C["panel3"]); header.pack(fill="x", padx=12, pady=(10, 5))\n        tk.Label(header, text=family_text, bg=C["soft"], fg=family_fg, font=("Segoe UI", 8, "bold"), padx=9, pady=4).pack(side="right")\n        tk.Label(header, text=self.ui_text(title), bg=C["panel3"], fg=C["text"], font=("Segoe UI", 12, "bold")).pack(side="right", padx=8)\n\n        source_card = tk.Frame(box, bg=C["panel"]); source_card.pack(fill="x", padx=10, pady=(0, 6))\n        source_head = tk.Frame(source_card, bg=C["panel"]); source_head.pack(fill="x", padx=12, pady=(9, 5))\n        tk.Label(source_head, text="SOURCE VISUAL", bg=C["panel"], fg=C["cyan"], font=("Consolas", 9, "bold")).pack(side="left")\n        tk.Label(source_head, text=self.tr("original_source"), bg=C["panel"], fg=C["muted"], font=("Segoe UI", 9, "bold")).pack(side="right")\n\n        image_holder = tk.Frame(source_card, bg="#080D14"); image_holder.pack(fill="x", padx=10, pady=(0, 10))\n        image_label = tk.Label(image_holder, bg="#080D14", text=self.tr("market_loading"), fg=C["muted"], font=("Segoe UI", 9, "bold"))\n        image_label.pack(fill="x", ipady=35)\n        self._academy_image_refs = getattr(self, "_academy_image_refs", {})\n        image_ref_key = f"{id(image_label)}:{kind}"\n\n        def load_source_image():
            try:
                from PIL import Image
                path = bundled_asset_for_visual(kind)
                if path is None:
                    cache_path = ROOT / "cache" / "academy_visuals" / kind
                    path = render_visual(cache_path, kind, title=self.ui_text(title), subtitle=subtitle)
                image = Image.open(path).convert("RGB")
                max_w, max_h = 1120, 430
                ratio = min(max_w / max(image.width, 1), max_h / max(image.height, 1), 1.0)
                size = (max(1, int(image.width * ratio)), max(1, int(image.height * ratio)))
                image = image.resize(size, Image.LANCZOS)

                def apply_image():
                    try:
                        from PIL import ImageTk
                        if not image_label.winfo_exists():
                            return
                        photo = ImageTk.PhotoImage(image)
                        self._academy_image_refs[image_ref_key] = photo
                        image_label.configure(image=photo, text="")
                    except Exception as exc:
                        if image_label.winfo_exists():
                            image_label.configure(image="", text=self.tr("no_exact_image") + f"\n{exc}", wraplength=980, justify="center")

                self.after(0, apply_image)
            except Exception as exc:
                def show_error():
                    if image_label.winfo_exists():
                        image_label.configure(image="", text=self.tr("no_exact_image") + f"\n{exc}", wraplength=980, justify="center")
                self.after(0, show_error)
        threading.Thread(target=load_source_image, name="AcademyVisual", daemon=True).start()\n\n        source_meta = tk.Frame(source_card, bg=C["panel"]); source_meta.pack(fill="x", padx=12, pady=(0, 10))\n        tk.Label(source_meta, text=f"{self.tr('source_chart')} • {source_title}", bg=C["panel"], fg=C["muted"], font=("Segoe UI", 8, "bold"), wraplength=900, justify="right").pack(side="right", fill="x", expand=True)\n        self.btn(source_meta, self.tr("open_source"), lambda u=source_url: self.open_webview(u, source_title)).pack(side="left", padx=(8, 0))\n\n        semantic_card = tk.Frame(box, bg=C["panel3"]); semantic_card.pack(fill="x", padx=10, pady=(0, 8))\n        tk.Label(semantic_card, text="SETUP ANATOMY", bg=C["panel3"], fg=family_fg, font=("Consolas", 9, "bold")).pack(anchor="w", padx=12, pady=(6, 3))\n        tk.Label(semantic_card, text=self.ui_text(subtitle), bg=C["panel3"], fg=C["muted"], font=("Segoe UI", 9), wraplength=1050, justify="right").pack(fill="x", padx=12, pady=(0, 4))\n        diagram_holder = tk.Frame(semantic_card, bg=C["panel3"]); diagram_holder.pack(fill="x", padx=4, pady=(0, 6))\n        try:\n            if family_key in ("smc", "ict"): draw_setup(diagram_holder, family_key, self.ui_text(title), C)\n            else: draw_candlestick(diagram_holder, self.ui_text(title), C)\n        except Exception as exc:\n            tk.Label(diagram_holder, text=f"{self.tr('no_exact_image')}\n{exc}", bg=C["panel3"], fg=C["muted"], font=("Segoe UI", 9, "bold"), padx=20, pady=25, justify="center", wraplength=900).pack(fill="x")\n        return box\n\n    def academy(self):
        self.heading(self.tr("academy_title"), self.tr("academy_sub"))
        note=tk.Label(
            self.content,
            text=ACADEMY_NOTE_FA if self.language=="fa" else ACADEMY_NOTE_EN,
            bg=C["panel2"], fg=C["muted"], wraplength=1180, justify="right",
            padx=14, pady=10
        )
        note.pack(fill="x",pady=(0,7))

        family_map=self.card(self.content)
        family_map.pack(fill="x",pady=(0,7))
        tk.Label(family_map,text="SMC ≠ ICT",bg=C["panel"],fg=C["gold"],
                 font=("Segoe UI",12,"bold")).pack(anchor="e",padx=14,pady=(10,3))
        tk.Label(
            family_map,
            text=self.ui_text("SMC: ساختار بازار، نقدینگی، BOS/CHoCH، Order Block، FVG و ناحیه‌ها  •  ICT: مدل‌ها و اصطلاحات نام‌گذاری‌شده مانند 2022 Model، Silver Bullet، Judas Swing، AMD، OTE و Unicorn"),
            bg=C["panel"],fg=C["text"],font=("Segoe UI",10,"bold"),
            wraplength=1180,justify="right"
        ).pack(fill="x",padx=14,pady=(0,10))

        legend=tk.Frame(self.content,bg=C["bg"])
        legend.pack(fill="x",pady=(0,7))
        smc_badge=tk.Label(legend,text=self.tr("smc_family"),bg=C["soft"],fg=C["accent"],
                           font=("Segoe UI",9,"bold"),padx=10,pady=5)
        smc_badge.pack(side="right",padx=3)
        ict_badge=tk.Label(legend,text=self.tr("ict_family"),bg=C["soft"],fg=C["violet"],
                           font=("Segoe UI",9,"bold"),padx=10,pady=5)
        ict_badge.pack(side="right",padx=3)
        tk.Label(legend,text=self.tr("family"),bg=C["bg"],fg=C["muted"],
                 font=("Segoe UI",9,"bold"),padx=8).pack(side="right")

        nb=ttk.Notebook(self.content)
        nb.pack(fill="both",expand=True)
        tab_smc=tk.Frame(nb,bg=C["bg"])
        tab_ict=tk.Frame(nb,bg=C["bg"])
        tab_candle=tk.Frame(nb,bg=C["bg"])
        tab_gloss=tk.Frame(nb,bg=C["bg"])
        nb.add(tab_smc,text=self.tr("smc"))
        nb.add(tab_ict,text=self.tr("ict"))
        nb.add(tab_candle,text=self.tr("candles"))
        nb.add(tab_gloss,text=self.tr("glossary"))
        self._academy_notebook=nb

        self._build_strategy_tab(tab_smc, SMART_MONEY_STRATEGIES, "smc")
        self._build_strategy_tab(tab_ict, ICT_STRATEGIES, "ict")
        self._build_candle_tab(tab_candle)
        self._build_glossary_tab(tab_gloss)

    def _build_strategy_tab(self,parent,items,family):
        outer=tk.PanedWindow(parent,orient="horizontal",bg=C["bg"],sashwidth=8,showhandle=False)
        outer.pack(fill="both",expand=True,padx=8,pady=8)

        left=tk.Frame(outer,bg=C["panel"])
        right=tk.Frame(outer,bg=C["panel"])
        outer.add(left,minsize=330)
        outer.add(right,minsize=820)

        lb=tk.Listbox(
            left,bg=C["panel2"],fg=C["text"],selectbackground=C["accent"],
            selectforeground="#061019",font=("Segoe UI",10,"bold"),
            activestyle="none",borderwidth=0,highlightthickness=0
        )
        lb.pack(fill="both",expand=True,padx=8,pady=8)

        for item in items:
            lb.insert("end", item["name_fa"] if self.language=="fa" else item["name_en"])

        title=tk.Label(
            right,text="",bg=C["panel"],fg=C["gold"],font=("Segoe UI",17,"bold"),
            anchor="e",justify="right"
        )
        title.pack(fill="x",padx=18,pady=(14,5))

        badge_row=tk.Frame(right,bg=C["panel"])
        badge_row.pack(fill="x",padx=18,pady=(0,5))

        family_text=self.tr("smc_family") if family=="smc" else self.tr("ict_family")
        family_badge=tk.Label(
            badge_row,text=family_text,bg=C["soft"],fg=C["accent"],
            font=("Segoe UI",9,"bold"),padx=10,pady=5
        )
        family_badge.pack(side="right")

        visual_name=tk.Label(
            badge_row,text="",bg=C["panel"],fg=C["muted"],
            font=("Consolas",8,"bold")
        )
        visual_name.pack(side="left",padx=8)

        summary=tk.Label(
            right,text="",bg=C["panel"],fg=C["text"],font=("Segoe UI",12),
            anchor="e",justify="right",wraplength=940
        )
        summary.pack(fill="x",padx=18,pady=5)

        visual_holder=tk.Frame(right,bg=C["panel"])
        visual_holder.pack(fill="x",padx=8,pady=3)

        anatomy_title=tk.Label(
            right,text=self.tr("setup_anatomy"),bg=C["panel"],fg=C["gold"],
            font=("Segoe UI",11,"bold")
        )
        anatomy_title.pack(anchor="e",padx=18,pady=(6,3))

        anatomy=tk.Frame(right,bg=C["panel"])
        anatomy.pack(fill="x",padx=18,pady=(0,8))

        steps_frame=tk.Frame(right,bg=C["panel"])
        steps_frame.pack(fill="both",expand=True,padx=18,pady=8)

        text=tk.Text(
            steps_frame,bg=C["soft"],fg=C["text"],insertbackground=C["text"],
            relief="flat",wrap="word",font=("Segoe UI",12),height=11
        )
        text.pack(side="left",fill="both",expand=True)
        scr=ttk.Scrollbar(steps_frame,orient="vertical",command=text.yview)
        scr.pack(side="right",fill="y")
        text.configure(yscrollcommand=scr.set)

        def render(_=None):
            sel=lb.curselection()
            if not sel: return
            item=items[sel[0]]
            name_en=item["name_en"]
            title.config(text=item["name_fa"] if self.language=="fa" else name_en)
            summary.config(
                text=item["summary_fa"] if self.language=="fa" else item["summary_en"]
            )
            kind=strategy_visual_key(name_en)
            visual_name.config(text=kind.upper())

            for w in visual_holder.winfo_children():
                w.destroy()
            self._academy_visual(
                visual_holder,"strategy",name_en,
                item["summary_en"],visual_kind=kind,family=family
            )

            for w in anatomy.winfo_children():
                w.destroy()
            lines=item["steps_fa"] if self.language=="fa" else item["steps_en"]
            inv=item["risk_fa"] if self.language=="fa" else item["risk_en"]

            for idx,line in enumerate(lines,1):
                chip=tk.Frame(
                    anatomy,bg=C["soft"],highlightbackground=C["line"],
                    highlightthickness=1
                )
                chip.pack(side="left",fill="both",expand=True,padx=3)
                tk.Label(
                    chip,text=f"{idx:02d}",bg=C["accent"],fg="#061019",
                    font=("Segoe UI",9,"bold"),padx=7,pady=4
                ).pack(anchor="w")
                tk.Label(
                    chip,text=line,bg=C["soft"],fg=C["text"],
                    font=("Segoe UI",9,"bold"),wraplength=180,justify="right",
                    padx=8,pady=8
                ).pack(fill="both",expand=True)

            text.configure(state="normal")
            text.delete("1.0","end")
            text.insert("end",self.tr("steps")+"\n\n")
            for i,line in enumerate(lines,1):
                text.insert("end",f"{i}. {line}\n")
            text.insert("end","\n"+self.tr("invalidation")+"\n\n"+inv)
            text.configure(state="disabled")

        lb.bind("<<ListboxSelect>>",render)
        if items:
            lb.selection_set(0)
            lb.event_generate("<<ListboxSelect>>")

    def _build_candle_tab(self,parent):
        wrap=tk.Frame(parent,bg=C["panel"]); wrap.pack(fill="both",expand=True,padx=8,pady=8)
        left=tk.Frame(wrap,bg=C["panel"]); left.pack(side="left",fill="both",expand=True,padx=8,pady=8)
        right=tk.Frame(wrap,bg=C["panel"]); right.pack(side="left",fill="both",expand=True,padx=8,pady=8)
        lb=tk.Listbox(left,bg=C["panel2"],fg=C["text"],selectbackground=C["accent"],selectforeground="#061019",font=("Segoe UI",10,"bold"),activestyle="none",borderwidth=0,highlightthickness=0); lb.pack(fill="both",expand=True)
        for name,en,fa in CANDLE_PLAYBOOK: lb.insert("end",fa if self.language=="fa" else name)
        tk.Label(right,text=self.ui_text("الگوهای کندلی"),bg=C["panel"],fg=C["gold"],font=("Segoe UI",15,"bold")).pack(anchor="e",padx=12,pady=10)
        visual_holder=tk.Frame(right,bg=C["panel"]); visual_holder.pack(fill="x",padx=8,pady=4)
        desc=tk.Label(right,text="",bg=C["soft"],fg=C["text"],font=("Segoe UI",12),wraplength=860,justify="right",anchor="e"); desc.pack(fill="both",expand=True,padx=16,pady=10)
        en_desc={
            "Pin Bar / Rejection Candle":"A one-candle rejection pattern with a small body and a pronounced wick. TradingView's candlestick guidance stresses that the pattern must be read with trend, level and confirmation rather than in isolation.",
            "Bullish Engulfing":"After selling pressure, the second candle's real body fully overtakes the prior bearish real body. This is a candlestick pattern; it is not an ICT setup by itself.",
            "Bearish Engulfing":"After buying pressure, the second candle's real body fully overtakes the prior bullish real body. This is a candlestick pattern; it is not an ICT setup by itself.",
            "Inside Bar":"A two-candle containment pattern: the second candle's high and low remain inside the previous candle's range. It signals compression; direction needs context and confirmation.",
            "Morning Star":"A three-candle bullish reversal pattern usually studied after a decline: a strong bearish candle, a small-bodied middle candle, then a strong bullish candle that closes well into the first candle's body.",
            "Evening Star":"A three-candle bearish reversal pattern usually studied after a rise: a strong bullish candle, a small-bodied middle candle, then a strong bearish candle that closes well into the first candle's body.",
            "Hammer":"A bullish-leaning single-candle pattern with a small body and a long lower shadow. It is most meaningful after a decline or at a defined support area, with confirmation.",
            "Shooting Star":"A bearish-leaning single-candle pattern with a small body and a long upper shadow. It is most meaningful after an advance or near resistance, with confirmation.",
            "Doji":"A candle whose open and close are very close, showing temporary balance or indecision. Context determines whether it matters.",
            "Tweezer Top":"A bearish reversal pattern in which two nearby candles form matching or nearly matching highs near resistance; confirmation is still required.",
            "Tweezer Bottom":"A bullish reversal pattern in which two nearby candles form matching or nearly matching lows near support; confirmation is still required.",
            "Three White Soldiers":"Three consecutive strong bullish candles with progressively higher closes. It can describe sustained buying pressure after a decline, but context remains essential.",
            "Three Black Crows":"Three consecutive strong bearish candles with progressively lower closes. It can describe sustained selling pressure after an advance, but context remains essential.",
            "Marubozu":"A candle with little or no visible shadow and a large body, emphasizing directional movement from open toward close.",
            "Spinning Top":"A small real body with visible upper and lower shadows, showing a period of balance or indecision within a wider range.",
            "Long-Legged Doji":"A dramatic doji with long shadows showing a wide intraday battle between buyers and sellers. TradingView notes that a close below the candle midpoint can signal weakness in the example it discusses."
        }
        def render(_=None):
            if not lb.curselection(): return
            name,en,fa=CANDLE_PLAYBOOK[lb.curselection()[0]]
            for w in visual_holder.winfo_children(): w.destroy()
            self._academy_visual(
                visual_holder,"candlestick",name,
                en_desc.get(name,"Candlestick pattern reference."),
                visual_kind=pattern_visual_key(name),family="candles"
            )
            desc.config(text=f"{name}\n\n{fa if self.language=='fa' else en_desc.get(name,'Candlestick pattern reference.')}")
        lb.bind("<<ListboxSelect>>",render)
        if CANDLE_PLAYBOOK: lb.selection_set(0); lb.event_generate("<<ListboxSelect>>")
    def _build_glossary_tab(self,parent):
        bar=tk.Frame(parent,bg=C["panel"]); bar.pack(fill="x",padx=8,pady=8)
        q=tk.StringVar(); entry=tk.Entry(bar,textvariable=q,bg=C["soft"],fg=C["text"],insertbackground=C["text"],relief="flat",justify="right",font=("Segoe UI",10)); entry.pack(side="right",fill="x",expand=True,padx=8,pady=10)
        tk.Label(bar,text=self.tr("search_term"),bg=C["panel"],fg=C["muted"]).pack(side="right")
        cat=tk.StringVar(value="ALL"); cats=["ALL"]+sorted({x["category"] for x in GLOSSARY}); combo=ttk.Combobox(bar,textvariable=cat,values=cats,state="readonly",width=24,justify="right"); combo.pack(side="left",padx=8,pady=8)
        family_var=tk.StringVar(value="ALL")
        family_combo=ttk.Combobox(bar,textvariable=family_var,values=["ALL","SMC","ICT","CANDLE"],state="readonly",width=14,justify="center")
        family_combo.pack(side="left",padx=8,pady=8)
        body=tk.PanedWindow(parent,orient="horizontal",bg=C["bg"],sashwidth=8); body.pack(fill="both",expand=True,padx=8,pady=(0,8))
        left=tk.Frame(body,bg=C["panel"]); right=tk.Frame(body,bg=C["panel"]); body.add(left,minsize=380); body.add(right,minsize=760)
        tree=ttk.Treeview(left,columns=("term","category"),show="headings",selectmode="browse"); tree.heading("term",text="Term"); tree.heading("category",text="Category"); tree.column("term",width=260); tree.column("category",width=120); tree.pack(fill="both",expand=True,padx=8,pady=8)
        visual_holder=tk.Frame(right,bg=C["panel"]); visual_holder.pack(fill="x",padx=8,pady=(8,4))
        title=tk.Label(right,text="",bg=C["panel"],fg=C["gold"],font=("Segoe UI",15,"bold"),justify="right",anchor="e"); title.pack(fill="x",padx=18,pady=(8,5))
        meaning=tk.Label(right,text="",bg=C["soft"],fg=C["text"],font=("Segoe UI",12),wraplength=860,justify="right",anchor="e"); meaning.pack(fill="x",padx=18,pady=7)
        usage=tk.Label(right,text="",bg=C["panel"],fg=C["muted"],font=("Segoe UI",11),wraplength=860,justify="right",anchor="e"); usage.pack(fill="both",expand=True,padx=18,pady=7)
        def refresh(*_):
            term=q.get().strip().lower(); selected_cat=cat.get(); selected_family=family_var.get()
            for x in tree.get_children(): tree.delete(x)
            matched=[]
            for i,item in enumerate(GLOSSARY):
                blob=" ".join([item["term"],item["fa"],item["en"],item["category"],item["meaning_fa"],item["meaning_en"],item["usage_fa"],item["usage_en"]]).lower()
                if term and term not in blob: continue
                if selected_cat!="ALL" and item["category"]!=selected_cat: continue
                kind=glossary_visual_key(item["term"], item["category"], item["meaning_en"])
                family = "ICT" if kind.startswith("ict_") or kind in {"unicorn","breaker","smt"} else ("CANDLE" if kind in {"candlestick","bullish_engulfing","bearish_engulfing","doji","hammer","shooting_star","morning_star","evening_star","tweezer_top","tweezer_bottom","three_white_soldiers","three_black_crows","marubozu","spinning_top","long_legged_doji"} else "SMC")
                if selected_family!="ALL" and family!=selected_family: continue
                matched.append(i); tree.insert("", "end",iid=str(i),values=(item["term"],item["category"]))
            if matched: tree.selection_set(str(matched[0])); render()
        def render(_=None):
            sel=tree.selection()
            if not sel: return
            item=GLOSSARY[int(sel[0])]
            kind=glossary_visual_key(item["term"], item["category"], item["meaning_en"])
            for w in visual_holder.winfo_children(): w.destroy()
            family = "ict" if kind.startswith("ict_") or kind in {"unicorn","breaker","smt"} else ("candles" if kind in {"candlestick","bullish_engulfing","bearish_engulfing","doji","hammer","shooting_star","morning_star","evening_star","tweezer_top","tweezer_bottom","three_white_soldiers","three_black_crows","marubozu","spinning_top","long_legged_doji"} else "smc")
            self._academy_visual(visual_holder,kind,item["en"],item["meaning_en"],family=family)
            title.config(text=item["term"]+"  |  "+(item["fa"] if self.language=="fa" else item["en"]))
            meaning.config(text=self.tr("definition")+"\n"+(item["meaning_fa"] if self.language=="fa" else item["meaning_en"]))
            usage.config(text=self.tr("usage")+"\n"+(item["usage_fa"] if self.language=="fa" else item["usage_en"]))
        tree.bind("<<TreeviewSelect>>",render); entry.bind("<KeyRelease>",refresh); combo.bind("<<ComboboxSelected>>",refresh); family_combo.bind("<<ComboboxSelected>>",refresh); refresh()
        tk.Label(parent,text=f"{len(GLOSSARY)} terms",bg=C["bg"],fg=C["muted"],font=("Segoe UI",8)).pack(anchor="e",padx=10,pady=(0,6))
    def open_path(self,path):
        path=Path(path); path.mkdir(parents=True,exist_ok=True)
        try:
            if sys.platform.startswith("win"): os.startfile(str(path))
            elif sys.platform=="darwin": os.system(f'open "{path}"')
            else: os.system(f'xdg-open "{path}"')
        except OSError as exc:
            messagebox.showerror(self.ui_text("خطا"),str(exc),parent=self)

def tempfile_path():
    path = ROOT / "cache"
    path.mkdir(parents=True, exist_ok=True)
    return path / "trader_planner_pro_3d_logo.png"

if __name__ == "__main__":
    save_db()
    App().mainloop()
