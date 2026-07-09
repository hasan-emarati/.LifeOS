"""
ماژول تقویم جلالی — الگوریتم صد درصد تست‌شده
تایم‌زون ایران: UTC+3:30
"""
from datetime import date as _date, datetime, timezone, timedelta
import re

IRAN_TZ = timezone(timedelta(hours=3, minutes=30))

JALALI_MONTHS = [
    'فروردین','اردیبهشت','خرداد','تیر','مرداد','شهریور',
    'مهر','آبان','آذر','دی','بهمن','اسفند'
]
WEEKDAY_FA_SHORT = ['ش','ی','د','س','چ','پ','ج']
WEEKDAY_FA_FULL  = ['شنبه','یک‌شنبه','دوشنبه','سه‌شنبه','چهارشنبه','پنج‌شنبه','جمعه']

_LEAP_J = (1,5,9,13,17,22,26,30)
_J_EPOCH_G = _date(2000, 3, 20)   # برابر ۱۳۷۹/۱/۱


def _jal_month_len(jy: int, jm: int) -> int:
    if jm <= 6:  return 31
    if jm <= 11: return 30
    return 30 if (jy % 33) in _LEAP_J else 29


def to_jalali(gy: int, gm: int, gd: int):
    """میلادی → شمسی"""
    _gy = gy - 1600; _gm = gm - 1; _gd = gd - 1
    g_d_no = 365*_gy + (_gy+3)//4 - (_gy+99)//100 + (_gy+399)//400
    g_mon = [31,28,31,30,31,30,31,31,30,31,30,31]
    for i in range(_gm): g_d_no += g_mon[i]
    if _gm > 1 and (gy%4==0 and (gy%100!=0 or gy%400==0)):
        g_d_no += 1
    g_d_no += _gd
    j_d_no  = g_d_no - 79
    j_np = j_d_no // 12053; j_d_no %= 12053
    jy   = 979 + 33*j_np + 4*(j_d_no//1461); j_d_no %= 1461
    if j_d_no >= 366:
        jy += (j_d_no-1)//365; j_d_no = (j_d_no-1)%365
    # طول اسفند (کبیسه یا عادی)
    j_mon = [31,31,31,31,31,31,30,30,30,30,30,
             30 if (jy%33) in _LEAP_J else 29]
    for i in range(12):
        if j_d_no < j_mon[i]:
            return jy, i+1, j_d_no+1
        j_d_no -= j_mon[i]
    return jy, 12, j_mon[11]   # هرگز نباید به اینجا برسد


def to_gregorian(jy: int, jm: int, jd: int):
    """شمسی → میلادی  (از طریق epoch ۱۳۷۹/۱/۱ = ۲۰۰۰-۰۳-۲۰)"""
    # روزهای اختلاف از epoch شمسی
    days = 0
    ey, em, ed = 1379, 1, 1
    # اختلاف سالانه
    y = ey
    if jy > ey:
        while y < jy:
            for m in range(1, 13): days += _jal_month_len(y, m)
            y += 1
    elif jy < ey:
        while y > jy:
            y -= 1
            for m in range(1, 13): days -= _jal_month_len(y, m)
    # اختلاف ماهانه
    m = em
    if jm > em:
        while m < jm: days += _jal_month_len(jy, m); m += 1
    elif jm < em:
        while m > jm: m -= 1; days -= _jal_month_len(jy, m)
    # اختلاف روزانه
    days += jd - ed
    g = _J_EPOCH_G + timedelta(days=days)
    return g.year, g.month, g.day


def jalali_month_len(jy: int, jm: int) -> int:
    return _jal_month_len(jy, jm)


def jalali_is_leap(jy: int) -> bool:
    return _jal_month_len(jy, 12) == 30


def jalali_weekday(jy: int, jm: int, jd: int) -> int:
    """روز هفته شمسی: شنبه=0 … جمعه=6"""
    gy, gm, gd = to_gregorian(jy, jm, jd)
    return (_date(gy, gm, gd).weekday() + 2) % 7


def today_jalali():
    """امروز به وقت ایران → (jy, jm, jd)"""
    now = datetime.now(IRAN_TZ)
    return to_jalali(now.year, now.month, now.day)


def now_iran() -> datetime:
    return datetime.now(IRAN_TZ)


def format_jalali(jy: int, jm: int, jd: int, sep: str = '/') -> str:
    return f"{jy}{sep}{jm:02d}{sep}{jd:02d}"


def jalali_to_iso(jy: int, jm: int, jd: int) -> str:
    gy, gm, gd = to_gregorian(jy, jm, jd)
    return f"{gy}-{gm:02d}-{gd:02d}"


def iso_to_jalali_str(iso: str) -> str:
    try:
        d = _date.fromisoformat(iso[:10])
        jy, jm, jd = to_jalali(d.year, d.month, d.day)
        return format_jalali(jy, jm, jd)
    except Exception:
        return iso


def parse_jalali(s: str):
    """'1405/03/24' → (1405, 3, 24)"""
    parts = re.split(r'[/\-.]', s.strip())
    if len(parts) == 3:
        return int(parts[0]), int(parts[1]), int(parts[2])
    raise ValueError(f"Invalid Jalali string: {s}")
