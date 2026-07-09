"""
ui/widgets/alarm_popup.py — پاپ‌آپ شناور آلارم برای رویدادهای تقویم
هنگام رسیدن به زمان یادآور یک رویداد، این ویجت گوشه‌ی پنجره ظاهر می‌شود
و همزمان صدای آلارم پخش می‌شود.
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from ui.theme import THEME
from core.alarm import play_alarm_sound

EVENT_ICONS = {
    'meeting': '🤝', 'deadline': '⏰', 'exam': '📝',
    'holiday': '🎉', 'reminder': '🔔', 'personal': '👤',
    'task': '✅',
}


class AlarmPopup(QFrame):
    """پاپ‌آپ فریم‌لس شناور روی پنجره‌ی اصلی — غیرمودال، رابط کاربری را قفل نمی‌کند."""
    snoozed = pyqtSignal(dict)

    def __init__(self, event: dict, parent=None):
        super().__init__(parent, Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint |
                          Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.event_data = event
        self.setFixedWidth(340)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self._build()
        self._position()
        play_alarm_sound()

    def _build(self):
        icon = EVENT_ICONS.get(self.event_data.get('event_type', 'reminder'), '🔔')
        self.setStyleSheet(f"""
            QFrame#card {{
                background:{THEME['bg_secondary']};
                border:1px solid {THEME['accent']};
                border-radius:14px;
            }}
        """)
        self.setObjectName("card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame(); card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(18, 16, 18, 16)
        cl.setSpacing(8)

        top = QHBoxLayout()
        ic = QLabel(icon); ic.setFont(QFont("Segoe UI Emoji", 20))
        ic.setStyleSheet(f"background:{THEME['accent']}22;border-radius:10px;padding:6px;border:1px solid {THEME['accent']}44;")
        ic.setFixedSize(42, 42); ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("🔔 یادآور تسک" if self.event_data.get('event_type') == 'task' else "🔔 یادآور رویداد")
        title.setFont(QFont("Segoe UI Variable", 12, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{THEME['accent_light']};background:transparent;border:none;")
        top.addWidget(ic); top.addWidget(title); top.addStretch()
        cl.addLayout(top)

        name = QLabel(self.event_data.get('title', ''))
        name.setFont(QFont("Segoe UI Variable", 14, QFont.Weight.Bold))
        name.setWordWrap(True)
        name.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;")
        cl.addWidget(name)

        dt = (self.event_data.get('start_datetime') or '')[:16].replace('T', '  ')
        when = QLabel(f"🕐 {dt}")
        when.setStyleSheet(f"color:{THEME['text_secondary']};font-size:11px;background:transparent;border:none;")
        cl.addWidget(when)

        desc = self.event_data.get('description') or ''
        if desc:
            dl = QLabel(desc[:120])
            dl.setWordWrap(True)
            dl.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:11px;background:transparent;border:none;")
            cl.addWidget(dl)

        btn_row = QHBoxLayout()
        snooze = QPushButton("⏰ ۵ دقیقه دیگه")
        snooze.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_primary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:6px 12px;font-size:11px;")
        snooze.clicked.connect(self._snooze)
        close_btn = QPushButton("✓ متوجه شدم")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(snooze); btn_row.addStretch(); btn_row.addWidget(close_btn)
        cl.addLayout(btn_row)

        outer.addWidget(card)

        # بستن خودکار بعد از ۳۰ ثانیه اگر کاربر کاری نکرد
        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self.close)
        self._auto_timer.start(30_000)

    def _snooze(self):
        self.snoozed.emit(self.event_data)
        self.close()

    def _position(self):
        try:
            parent = self.parent()
            if parent:
                geo = parent.geometry()
                x = geo.x() + geo.width() - self.width() - 24
                y = geo.y() + 60
            else:
                x, y = 100, 100
            self.move(x, y)
        except Exception:
            pass
        self.show()
