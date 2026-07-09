"""
core/alarm.py — پخش صدای آلارم برای یادآورهای تقویم
روی ویندوز از winsound (داخلی پایتون، بدون نیاز به نصب چیزی) استفاده می‌کند.
روی سایر سیستم‌عامل‌ها از بیپ سیستمی Qt استفاده می‌کند.
"""
import sys
import threading


def play_alarm_sound(repeats: int = 3):
    """صدای آلارم را پخش می‌کند.
    روی ویندوز winsound.Beep (بلاک‌کننده‌ی OS، نه Qt) در یک ترد جدا اجرا می‌شود.
    روی سایر سیستم‌عامل‌ها از QApplication.beep در ترد اصلی (Qt-safe) استفاده می‌شود.
    """
    if sys.platform.startswith("win"):
        def _run():
            try:
                import winsound
                for i in range(repeats):
                    # دو تن متفاوت شبیه آلارم
                    winsound.Beep(880, 220)
                    winsound.Beep(660, 220)
            except Exception:
                _qt_beep(repeats)
        try:
            t = threading.Thread(target=_run, daemon=True)
            t.start()
        except Exception:
            _qt_beep(repeats)
    else:
        _qt_beep(repeats)


def _qt_beep(repeats: int = 3):
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        app = QApplication.instance()
        if not app:
            return
        for i in range(repeats):
            QTimer.singleShot(i * 300, QApplication.beep)
    except Exception:
        pass
