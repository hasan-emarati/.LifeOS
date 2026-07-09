# 🧠 LifeOS v2 — سیستم عامل زندگی

## ساختار فایل‌ها — دقیقاً این مسیرها را رعایت کنید

```
LifeOS\                          ← پوشه اصلی (مثلاً C:\LifeOS)
│
├── main.py
├── requirements.txt
├── run.bat                      ← دابل‌کلیک برای اجرا
├── README.md
│
├── core\
│   ├── __init__.py
│   ├── database.py              ← دیتابیس SQLite
│   └── jalali.py               ← تقویم شمسی
│
└── ui\
    ├── __init__.py
    ├── main_window.py           ← پنجره اصلی
    ├── theme.py                 ← تم‌ها و رنگ‌ها
    │
    ├── views\
    │   ├── __init__.py
    │   ├── dashboard_view.py
    │   ├── projects_view.py
    │   ├── tasks_view.py
    │   ├── gantt_view.py
    │   ├── goals_view.py
    │   ├── habits_view.py
    │   ├── skills_view.py
    │   ├── notes_view.py
    │   ├── ideas_view.py
    │   ├── calendar_view.py
    │   ├── daily_report_view.py
    │   ├── time_tracking_view.py
    │   ├── risks_view.py
    │   ├── finance_view.py
    │   ├── analytics_view.py
    │   ├── achievements_view.py
    │   └── settings_view.py
    │
    └── widgets\
        ├── __init__.py
        ├── xp_widget.py
        └── title_bar.py
```

## نصب و اجرا

### روش آسان (ویندوز)
1. Python 3.11+ را از python.org نصب کنید
2. موقع نصب تیک "Add Python to PATH" را بزنید
3. روی `run.bat` دابل‌کلیک کنید

### روش دستی
```
pip install PyQt6 matplotlib numpy
python main.py
```

## دیتابیس
در `C:\Users\<نام>\\.lifeOS\lifeOS.db` ذخیره می‌شود
