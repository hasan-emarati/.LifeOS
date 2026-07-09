"""Main Window v4"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QScrollArea,
    QStyle
)
from PyQt6.QtCore import Qt, QTimer, QPoint, QSize
from PyQt6.QtGui import QFont, QPainter, QColor, QIcon

from ui.theme import get_stylesheet, THEME, apply_theme
from ui.views.dashboard_view     import DashboardView
from ui.views.projects_view      import ProjectsView
from ui.views.tasks_view         import TasksView
from ui.views.gantt_view         import GanttView
from ui.views.goals_view         import GoalsView
from ui.views.habits_view        import HabitsView
from ui.views.skills_view        import SkillsView
from ui.views.notes_view         import NotesView
from ui.views.ideas_view         import IdeasView
from ui.views.daily_report_view  import DailyReportView
from ui.views.calendar_view      import CalendarView
from ui.views.analytics_view     import AnalyticsView
from ui.views.finance_view       import FinanceView
from ui.views.risks_view         import RisksView
from ui.views.time_tracking_view import TimeTrackingView
from ui.views.achievements_view  import AchievementsView
from ui.views.settings_view      import SettingsDialog
from ui.widgets.xp_widget        import XPWidget
from ui.widgets.alarm_popup      import AlarmPopup
from datetime import datetime, timedelta

NAV_ITEMS = [
    ("🏠", "داشبورد",       "dashboard"),
    ("📁", "پروژه‌ها",      "projects"),
    ("✅", "تسک‌ها",        "tasks"),
    ("📊", "گانت چارت",     "gantt"),
    ("🎯", "اهداف",         "goals"),
    ("🔥", "عادت‌ها",       "habits"),
    ("⚡", "مهارت‌ها",      "skills"),
    ("📝", "یادداشت‌ها",    "notes"),
    ("💡", "ایده‌ها",       "ideas"),
    ("📅", "تقویم",         "calendar"),
    ("📖", "گزارش روزانه",  "daily"),
    ("⏱️", "تایم ترکینگ",  "time"),
    ("⚠️", "مدیریت ریسک",  "risks"),
    ("💰", "مالی",          "finance"),
    ("📈", "آمار و تحلیل",  "analytics"),
    ("🏆", "دستاوردها",     "achievements"),
]


class SidebarButton(QPushButton):
    def __init__(self, icon: str, label: str, key: str, parent=None):
        super().__init__(parent)
        self.key = key
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(10)
        self.icon_label = QLabel(icon)
        self.icon_label.setFont(QFont("Segoe UI Emoji", 14))
        self.icon_label.setFixedWidth(22)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label = QLabel(label)
        self.text_label.setFont(QFont("Segoe UI Variable", 12))
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addStretch()
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_active(False)

    def set_active(self, active: bool):
        if active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {THEME['accent']}33,stop:1 transparent);
                    border:none;border-left:3px solid {THEME['accent']};border-radius:0;
                }}
            """)
            self.text_label.setStyleSheet(f"color:{THEME['accent_light']};font-weight:700;")
        else:
            self.setStyleSheet(f"""
                QPushButton {{background:transparent;border:none;border-left:3px solid transparent;border-radius:0;}}
                QPushButton:hover {{background:{THEME['bg_hover']};}}
            """)
            self.text_label.setStyleSheet(f"color:{THEME['text_secondary']};font-weight:400;")


class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos = QPoint()
        self.setFixedHeight(42)
        self._build()

    def _build(self):
        self.setStyleSheet(f"""
            QWidget {{background:{THEME['titlebar_bg']};border-bottom:1px solid {THEME['border_subtle']};}}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 8, 0)
        lay.setSpacing(8)
        icon = QLabel("🧠"); icon.setFont(QFont("Segoe UI Emoji",14)); icon.setStyleSheet("background:transparent;border:none;")
        title = QLabel("LifeOS"); title.setFont(QFont("Segoe UI Variable",12,QFont.Weight.Bold))
        title.setStyleSheet(f"color:{THEME['titlebar_text']};background:transparent;border:none;")
        lay.addWidget(icon); lay.addWidget(title); lay.addStretch()

        buttons = [
            (QStyle.StandardPixmap.SP_TitleBarMinButton,  "کوچک کردن", "#f59e0b", self._minimize),
            (QStyle.StandardPixmap.SP_TitleBarMaxButton,  "بزرگ/کوچک", "#10b981", self._maximize),
            (QStyle.StandardPixmap.SP_TitleBarCloseButton,"بستن",       "#ef4444", self._close),
        ]
        for icon_type, tip, hover_color, fn in buttons:
            btn = QPushButton()
            std_icon = self.style().standardIcon(icon_type)
            px = std_icon.pixmap(18, 18)
            painter = QPainter(px)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(px.rect(), QColor("white"))
            painter.end()
            btn.setIcon(QIcon(px)); btn.setIconSize(QSize(18,18))
            btn.setFixedSize(32,32); btn.setToolTip(tip)
            btn.setStyleSheet(f"""
                QPushButton{{background:transparent;border:none;border-radius:6px;}}
                QPushButton:hover{{background:{hover_color};}}
            """)
            btn.clicked.connect(fn); lay.addWidget(btn)

    def _minimize(self): self.window().showMinimized()
    def _maximize(self):
        w = self.window()
        w.showNormal() if w.isMaximized() else w.showMaximized()
    def _close(self): self.window().close()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.window().move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseDoubleClickEvent(self, e): self._maximize()


class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        saved_theme = db.get_setting("theme", "dark")
        apply_theme(saved_theme)
        self.setWindowTitle("LifeOS")
        self.setMinimumSize(1100, 700)
        self.resize(1440, 900)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(get_stylesheet())
        self._build_ui()
        self._nav_to("dashboard")
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._auto_refresh)
        self._refresh_timer.start(60_000)

        # ── چک‌کردن آلارم رویدادهای تقویم هر ۲۰ ثانیه ──
        self._alarm_popups = []  # جلوگیری از garbage-collect شدن پاپ‌آپ‌های باز
        self._alarm_timer = QTimer(self)
        self._alarm_timer.timeout.connect(self._check_alarms)
        self._alarm_timer.start(20_000)
        QTimer.singleShot(3_000, self._check_alarms)  # یک چک اولیه کوتاه بعد از باز شدن

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        self.title_bar = CustomTitleBar(self)
        root.addWidget(self.title_bar)

        main_area = QWidget()
        main_row = QHBoxLayout(main_area)
        main_row.setContentsMargins(0,0,0,0); main_row.setSpacing(0)

        self.sidebar = self._build_sidebar()
        main_row.addWidget(self.sidebar)

        sep = QFrame(); sep.setFixedWidth(1)
        sep.setStyleSheet(f"background:{THEME['border_subtle']};")
        main_row.addWidget(sep)

        right = QWidget()
        rl = QVBoxLayout(right); rl.setContentsMargins(0,0,0,0); rl.setSpacing(0)
        self.topbar = self._build_topbar()
        rl.addWidget(self.topbar)
        self.stack = QStackedWidget()
        rl.addWidget(self.stack)
        main_row.addWidget(right)
        root.addWidget(main_area)

        view_map = {
            "dashboard":    DashboardView,
            "projects":     ProjectsView,
            "tasks":        TasksView,
            "gantt":        GanttView,
            "goals":        GoalsView,
            "habits":       HabitsView,
            "skills":       SkillsView,
            "notes":        NotesView,
            "ideas":        IdeasView,
            "calendar":     CalendarView,
            "daily":        DailyReportView,
            "time":         TimeTrackingView,
            "risks":        RisksView,
            "finance":      FinanceView,
            "analytics":    AnalyticsView,
            "achievements": AchievementsView,
        }
        self._views = {}
        for key, cls in view_map.items():
            view = cls(self.db)
            self._views[key] = view
            self.stack.addWidget(view)

    def _build_sidebar(self):
        sidebar = QWidget(); sidebar.setFixedWidth(224)
        sidebar.setStyleSheet(f"background:{THEME['bg_secondary']};")
        layout = QVBoxLayout(sidebar); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)

        logo = QWidget(); logo.setFixedHeight(64)
        ll = QHBoxLayout(logo); ll.setContentsMargins(16,0,16,0); ll.setSpacing(10)
        brain = QLabel("🧠"); brain.setFont(QFont("Segoe UI Emoji",20)); brain.setStyleSheet("background:transparent;border:none;")
        text_col = QVBoxLayout(); text_col.setSpacing(0)
        t1 = QLabel("LifeOS"); t1.setFont(QFont("Segoe UI Variable",15,QFont.Weight.Bold))
        t1.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;")
        t2 = QLabel("سیستم عامل زندگی"); t2.setFont(QFont("Segoe UI Variable",8))
        t2.setStyleSheet(f"color:{THEME['text_tertiary']};background:transparent;border:none;")
        text_col.addWidget(t1); text_col.addWidget(t2)
        ll.addWidget(brain); ll.addLayout(text_col); ll.addStretch()
        layout.addWidget(logo)

        sep = QFrame(); sep.setFixedHeight(1); sep.setStyleSheet(f"background:{THEME['border_subtle']};"); layout.addWidget(sep)
        self.xp_widget = XPWidget(self.db); layout.addWidget(self.xp_widget)
        sep2 = QFrame(); sep2.setFixedHeight(1); sep2.setStyleSheet(f"background:{THEME['border_subtle']};"); layout.addWidget(sep2)
        layout.addSpacing(4)

        nav_scroll = QScrollArea(); nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.Shape.NoFrame)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav_scroll.setStyleSheet("background:transparent;border:none;")
        nav_widget = QWidget(); nav_widget.setStyleSheet("background:transparent;")
        nav_layout = QVBoxLayout(nav_widget); nav_layout.setContentsMargins(0,0,0,0); nav_layout.setSpacing(1)
        self._nav_buttons: dict = {}
        for icon, label, key in NAV_ITEMS:
            btn = SidebarButton(icon, label, key)
            btn.clicked.connect(lambda _, k=key: self._nav_to(k))
            self._nav_buttons[key] = btn; nav_layout.addWidget(btn)
        nav_layout.addStretch(); nav_scroll.setWidget(nav_widget); layout.addWidget(nav_scroll)

        sep3 = QFrame(); sep3.setFixedHeight(1); sep3.setStyleSheet(f"background:{THEME['border_subtle']};"); layout.addWidget(sep3)
        ver = QLabel("LifeOS v2.0"); ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:10px;padding:10px;"); layout.addWidget(ver)
        return sidebar

    def _build_topbar(self):
        bar = QWidget(); bar.setFixedHeight(54)
        bar.setStyleSheet(f"background:{THEME['bg_secondary']};border-bottom:1px solid {THEME['border_subtle']};")
        bl = QHBoxLayout(bar); bl.setContentsMargins(22,0,22,0); bl.setSpacing(12)
        self.page_title = QLabel("داشبورد")
        self.page_title.setFont(QFont("Segoe UI Variable",15,QFont.Weight.Bold))
        self.page_title.setStyleSheet(f"color:{THEME['text_primary']};")
        bl.addWidget(self.page_title); bl.addStretch()

        from core.jalali import today_jalali, JALALI_MONTHS
        jy,jm,jd = today_jalali()
        date_lbl = QLabel(f"📅  {jd} {JALALI_MONTHS[jm-1]} {jy}")
        date_lbl.setStyleSheet(f"color:{THEME['text_secondary']};font-size:12px;"); bl.addWidget(date_lbl)

        settings_btn = QPushButton()
        std_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        px = std_icon.pixmap(20, 20)
        painter = QPainter(px)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(px.rect(), QColor(THEME['text_secondary']))
        painter.end()
        settings_btn.setIcon(QIcon(px)); settings_btn.setIconSize(QSize(20,20))
        settings_btn.setFixedSize(40,40)
        settings_btn.setToolTip("تنظیمات")
        settings_btn.setStyleSheet(f"""
            QPushButton{{
                background:{THEME['bg_tertiary']};
                border:1px solid {THEME['border_default']};
                border-radius:10px;
            }}
            QPushButton:hover{{
                background:{THEME['accent']};
                border-color:{THEME['accent']};
            }}
        """)
        settings_btn.clicked.connect(self._open_settings)
        bl.addWidget(settings_btn)
        return bar

    def _nav_to(self, key: str):
        for k, btn in self._nav_buttons.items():
            btn.set_active(k == key)
        for icon, label, k in NAV_ITEMS:
            if k == key:
                self.page_title.setText(f"{icon}  {label}")
                break
        if key in self._views:
            self.stack.setCurrentWidget(self._views[key])
            view = self._views[key]
            if hasattr(view, 'refresh'):
                view.refresh()

    def _open_settings(self):
        dlg = SettingsDialog(self.db, parent=self)
        dlg.exec()
        self.setStyleSheet(get_stylesheet())
        self._refresh_sidebar_styles()

    def _refresh_sidebar_styles(self):
        self.sidebar.setStyleSheet(f"background:{THEME['bg_secondary']};")
        active_key = None
        for key, view in self._views.items():
            if self.stack.currentWidget() == view:
                active_key = key; break
        for key, btn in self._nav_buttons.items():
            btn.set_active(key == active_key)

    def _auto_refresh(self):
        current = self.stack.currentWidget()
        if current and hasattr(current, 'refresh'):
            current.refresh()
        if hasattr(self, 'xp_widget'):
            self.xp_widget.refresh()

    # ── آلارم صوتی تقویم ──────────────────────────────
    def _check_alarms(self):
        """رویدادها و تسک‌های دارای آلارم که زمانشان رسیده و هنوز اعلان نشده‌اند را پیدا و آلارم می‌کند."""
        now = datetime.now()
        self._check_event_alarms(now)
        self._check_task_alarms(now)

    def _check_event_alarms(self, now):
        try:
            events = self.db.fetchall(
                "SELECT * FROM events WHERE (notified IS NULL OR notified=0) "
                "AND (alarm_enabled IS NULL OR alarm_enabled=1) "
                "AND start_datetime IS NOT NULL AND start_datetime!=''"
            )
        except Exception:
            return
        for ev in events:
            raw = (ev.get('start_datetime') or '')[:19]
            try:
                start = datetime.fromisoformat(raw)
            except Exception:
                continue
            remind_minutes = ev.get('reminder_minutes', 15) or 0
            remind_at = start - timedelta(minutes=remind_minutes)
            if now >= remind_at:
                self.db.execute("UPDATE events SET notified=1 WHERE id=?", (ev['id'],))
                # اگر رویداد خیلی قدیمی است (مثلاً برنامه بسته بوده) بی‌سروصدا رد شو
                if now <= start + timedelta(hours=2):
                    self._fire_alarm(ev)

    def _check_task_alarms(self, now):
        try:
            tasks = self.db.fetchall(
                "SELECT * FROM tasks WHERE alarm_enabled=1 AND (alarm_notified IS NULL OR alarm_notified=0) "
                "AND due_date IS NOT NULL AND due_date!='' AND status!='done'"
            )
        except Exception:
            return
        for t in tasks:
            due_time = t.get('due_time') or '09:00'
            try:
                due_dt = datetime.fromisoformat(f"{t['due_date']}T{due_time}:00")
            except Exception:
                continue
            if now >= due_dt:
                self.db.execute("UPDATE tasks SET alarm_notified=1 WHERE id=?", (t['id'],))
                if now <= due_dt + timedelta(hours=2):
                    self._fire_alarm({
                        'title': t.get('title', ''),
                        'description': t.get('description') or '',
                        'start_datetime': due_dt.strftime('%Y-%m-%dT%H:%M'),
                        'event_type': 'task',
                    })

    def _fire_alarm(self, event: dict):
        popup = AlarmPopup(event, parent=self)
        popup.snoozed.connect(self._snooze_event)
        popup.destroyed.connect(lambda: self._alarm_popups.remove(popup) if popup in self._alarm_popups else None)
        self._alarm_popups.append(popup)

    def _snooze_event(self, event: dict):
        QTimer.singleShot(5 * 60_000, lambda: self._fire_alarm(event))
