from __future__ import annotations

from datetime import date, datetime

try:
    import jdatetime
except Exception:
    jdatetime = None

try:
    from hijridate import Gregorian
except Exception:
    Gregorian = None

FA_WEEKDAYS = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
EN_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
FA_JALALI_MONTHS = [
    "فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور",
    "مهر","آبان","آذر","دی","بهمن","اسفند",
]


def calendar_snapshot(value: date | datetime | None = None):
    dt = value.date() if isinstance(value, datetime) else (value or date.today())
    weekday_fa = FA_WEEKDAYS[dt.weekday()]
    weekday_en = EN_WEEKDAYS[dt.weekday()]

    jalali_iso = ""
    jalali_fa = ""
    if jdatetime is not None:
        try:
            jd = jdatetime.date.fromgregorian(date=dt)
            jalali_iso = jd.strftime("%Y-%m-%d")
            jalali_fa = f"{jd.day} {FA_JALALI_MONTHS[jd.month-1]} {jd.year}"
        except Exception:
            pass

    hijri_iso = ""
    hijri_en = ""
    if Gregorian is not None:
        try:
            hd = Gregorian(dt.year, dt.month, dt.day).to_hijri()
            hijri_iso = hd.isoformat()
            hijri_en = hd.dmyformat()
        except Exception:
            pass

    return {
        "gregorian": dt.isoformat(),
        "weekday_fa": weekday_fa,
        "weekday_en": weekday_en,
        "jalali_iso": jalali_iso,
        "jalali_fa": jalali_fa,
        "hijri_iso": hijri_iso,
        "hijri_en": hijri_en,
    }


def display_date(value: date | datetime | None = None, language="fa"):
    s = calendar_snapshot(value)
    if language == "en":
        return (
            f"{s['weekday_en']} • {s['gregorian']}  |  "
            f"Jalali {s['jalali_iso'] or '—'}  |  Hijri {s['hijri_iso'] or '—'}"
        )
    return (
        f"{s['weekday_fa']} • {s['gregorian']}  |  "
        f"شمسی {s['jalali_fa'] or s['jalali_iso'] or '—'}  |  "
        f"قمری {s['hijri_iso'] or '—'}"
    )
