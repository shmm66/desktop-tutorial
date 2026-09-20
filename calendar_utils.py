from __future__ import annotations
from datetime import date, datetime
import jdatetime
from hijridate import Gregorian

FA_WEEKDAYS = ["دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه","شنبه","یکشنبه"]
FA_JALALI_MONTHS = ["فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور","مهر","آبان","آذر","دی","بهمن","اسفند"]
FA_HIJRI_MONTHS = ["محرم","صفر","ربیع‌الاول","ربیع‌الثانی","جمادی‌الاول","جمادی‌الثانی","رجب","شعبان","رمضان","شوال","ذی‌القعده","ذی‌الحجه"]

def calendar_bundle(value=None):
    value = value or datetime.now()
    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time())
    g = value.date()
    jd = jdatetime.date.fromgregorian(date=g)
    hd = Gregorian(g.year, g.month, g.day).to_hijri()
    weekday = FA_WEEKDAYS[g.weekday()]
    return {
        "gregorian": g,
        "gregorian_text": f"{weekday} • {g.year:04d}/{g.month:02d}/{g.day:02d}",
        "jalali": jd,
        "jalali_text": f"{weekday} • {jd.year:04d}/{jd.month:02d}/{jd.day:02d}",
        "jalali_long": f"{weekday} {jd.day} {FA_JALALI_MONTHS[jd.month-1]} {jd.year}",
        "hijri": hd,
        "hijri_text": f"{weekday} • {hd.year:04d}/{hd.month:02d}/{hd.day:02d} هـ",
        "hijri_long": f"{weekday} {hd.day} {FA_HIJRI_MONTHS[hd.month-1]} {hd.year} هـ",
    }

def date_label(value=None, english=False):
    b = calendar_bundle(value)
    g = b["gregorian"]
    if english:
        return f"{g.strftime('%A')} • Gregorian {g:%Y-%m-%d} | Jalali {b['jalali'].year:04d}-{b['jalali'].month:02d}-{b['jalali'].day:02d} | Hijri {b['hijri'].year:04d}-{b['hijri'].month:02d}-{b['hijri'].day:02d}"
    return f"{b['jalali_long']}  |  {b['hijri_long']}  |  {b['gregorian_text']}"
