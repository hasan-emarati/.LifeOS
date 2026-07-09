"""
Calendar View v2 — تقویم کامل شمسی با الگوریتم صحیح
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QLineEdit, QTextEdit,
    QComboBox, QDateTimeEdit, QSpinBox, QGridLayout, QMessageBox,
    QCheckBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QDateTime, QDate
from PyQt6.QtGui import QFont, QColor
from datetime import date, timedelta
from ui.theme import THEME
from core.jalali import (
    to_jalali, to_gregorian, jalali_month_len, jalali_weekday,
    today_jalali, format_jalali, jalali_to_iso, JALALI_MONTHS,
    WEEKDAY_FA_FULL, WEEKDAY_FA_SHORT
)

EVENT_TYPES = [
    ('meeting',  '🤝 جلسه',   THEME['info']),
    ('deadline', '⏰ مهلت',   THEME['danger']),
    ('exam',     '📝 امتحان', THEME['warning']),
    ('holiday',  '🎉 تعطیل', THEME['success']),
    ('reminder', '🔔 یادآور', THEME['accent']),
    ('personal', '👤 شخصی',  THEME['xp_platinum']),
    ('task',     '✅ تسک',    THEME['xp_gold']),
]
ET_MAP = {k: (l, c) for k, l, c in EVENT_TYPES}


class DayCell(QFrame):
    def __init__(self, greg_d, jal_t, events, is_today,
                 is_current_month, is_friday, on_click):
        super().__init__()
        self.greg_d = greg_d
        self.jal_t = jal_t
        self._build(events, is_today, is_current_month, is_friday, on_click)

    def _build(self, events, is_today, is_current_month, is_friday, on_click):
        jy, jm, jd = self.jal_t

        if is_today:
            bg, border = THEME['accent'] + '33', THEME['accent']
        elif is_friday and is_current_month:
            bg, border = THEME['danger'] + '0d', THEME['danger'] + '44'
        elif not is_current_month:
            bg, border = THEME['bg_primary'], THEME['border_subtle'] + '44'
        else:
            bg, border = THEME['bg_secondary'], THEME['border_subtle']

        self.setStyleSheet(f"""
            QFrame {{
                background:{bg};border:1px solid {border};
                border-radius:7px;
            }}
            QFrame:hover {{
                background:{THEME['bg_hover']};
                border-color:{THEME['accent']}88;
            }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # اندازه‌ی ثابت برای همه‌ی سلول‌ها — اضافه‌شدن رویداد/تسک دیگر باعث تغییر
        # اندازه‌ی ستون یا ردیف نمی‌شود
        self.setFixedHeight(96)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(5, 4, 5, 4)
        lay.setSpacing(2)

        # شمسی (بزرگ) + میلادی (کوچک)
        top = QHBoxLayout()
        j_color = (THEME['accent_light'] if is_today
                   else THEME['danger'] if (is_friday and is_current_month)
                   else THEME['text_primary'] if is_current_month
                   else THEME['text_tertiary'])

        jd_lbl = QLabel(str(jd))
        jd_lbl.setFont(QFont("Segoe UI Variable", 13,
                              QFont.Weight.Bold if is_today else QFont.Weight.Normal))
        jd_lbl.setStyleSheet(
            f"color:{j_color};background:transparent;border:none;"
        )

        gd_lbl = QLabel(str(self.greg_d.day))
        gd_lbl.setFont(QFont("Segoe UI Variable", 8))
        gd_lbl.setStyleSheet(
            f"color:{THEME['text_tertiary'] if is_current_month else THEME['border_default']};"
            f"background:transparent;border:none;"
        )

        top.addWidget(jd_lbl)
        top.addStretch()
        top.addWidget(gd_lbl)
        lay.addLayout(top)

        for ev in events[:2]:
            _, ev_color = ET_MAP.get(ev.get('event_type', 'reminder'),
                                      ('🔔', THEME['accent']))
            full_title = ev.get('title', '')
            short_title = full_title if len(full_title) <= 12 else full_title[:11] + '…'
            ev_lbl = QLabel(short_title)
            ev_lbl.setFont(QFont("Segoe UI Variable", 8))
            ev_lbl.setToolTip(full_title)
            ev_lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            ev_lbl.setFixedHeight(15)
            ev_lbl.setStyleSheet(
                f"color:white;background:{ev_color};"
                f"border-radius:3px;padding:1px 4px;border:none;"
            )
            lay.addWidget(ev_lbl)

        if len(events) > 2:
            more = QLabel(f"+{len(events)-2}")
            more.setFont(QFont("Segoe UI Variable", 8))
            more.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            more.setStyleSheet(
                f"color:{THEME['text_tertiary']};background:transparent;border:none;"
            )
            lay.addWidget(more)

        lay.addStretch()
        self.mousePressEvent = lambda e: on_click(self.greg_d, self.jal_t)


class EventDialog(QDialog):
    def __init__(self, db, greg_d=None, jal_t=None, event=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("رویداد جدید" if not event else "ویرایش رویداد")
        self.setMinimumWidth(480)
        self.setStyleSheet(
            f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};"
        )
        self._build(greg_d, jal_t)
        if event:
            self._fill(event)

    def _build(self, greg_d, jal_t):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)

        def lbl(t):
            l = QLabel(t)
            l.setFont(QFont("Segoe UI Variable", 11, QFont.Weight.Bold))
            l.setStyleSheet(f"color:{THEME['text_secondary']};")
            return l

        if jal_t:
            jy, jm, jd = jal_t
            date_info = QLabel(
                f"📅  {format_jalali(jy,jm,jd)}  —  {JALALI_MONTHS[jm-1]} {jy}"
            )
            date_info.setStyleSheet(
                f"color:{THEME['accent_light']};font-size:13px;font-weight:700;"
                f"background:{THEME['accent']}15;border:1px solid {THEME['accent']}33;"
                f"border-radius:8px;padding:8px 14px;"
            )
            lay.addWidget(date_info)

        lay.addWidget(lbl("عنوان رویداد *"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("عنوان رویداد...")
        lay.addWidget(self.title_edit)

        lay.addWidget(lbl("توضیحات"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(70)
        lay.addWidget(self.desc_edit)

        row = QHBoxLayout()
        tc = QVBoxLayout()
        tc.addWidget(lbl("نوع رویداد"))
        self.type_combo = QComboBox()
        for v, l, _ in EVENT_TYPES:
            self.type_combo.addItem(l, v)
        tc.addWidget(self.type_combo)

        pc = QVBoxLayout()
        pc.addWidget(lbl("پروژه"))
        self.proj_combo = QComboBox()
        self.proj_combo.addItem("بدون پروژه", None)
        for p in self.db.fetchall("SELECT id,name FROM projects WHERE archived=0"):
            self.proj_combo.addItem(p['name'], p['id'])
        pc.addWidget(self.proj_combo)

        row.addLayout(tc)
        row.addLayout(pc)
        lay.addLayout(row)

        lay.addWidget(lbl("تاریخ و ساعت"))
        default_dt = (
            QDateTime(
                QDate(greg_d.year, greg_d.month, greg_d.day),
                QDateTime.currentDateTime().time()
            ) if greg_d else QDateTime.currentDateTime()
        )
        self.start_dt = QDateTimeEdit(default_dt)
        self.start_dt.setCalendarPopup(True)
        self.start_dt.setDisplayFormat("yyyy-MM-dd  HH:mm")
        lay.addWidget(self.start_dt)

        lay.addWidget(lbl("یادآور (دقیقه قبل)"))
        self.reminder_spin = QSpinBox()
        self.reminder_spin.setRange(0, 10080)
        self.reminder_spin.setValue(15)
        self.reminder_spin.setSuffix(" دقیقه")
        lay.addWidget(self.reminder_spin)

        self.alarm_check = QCheckBox("🔔 سر ساعت یادآور، آلارم و نوتیفیکیشن نشون بده")
        self.alarm_check.setChecked(True)
        self.alarm_check.setStyleSheet(f"color:{THEME['text_primary']};font-size:12px;")
        lay.addWidget(self.alarm_check)

        btn_row = QHBoxLayout()
        cancel = QPushButton("انصراف")
        cancel.setStyleSheet(
            f"background:{THEME['bg_tertiary']};color:{THEME['text_primary']};"
            f"border:1px solid {THEME['border_default']};border-radius:8px;padding:8px 20px;"
        )
        cancel.clicked.connect(self.reject)
        save = QPushButton("📅 ذخیره رویداد")
        save.clicked.connect(self._save)
        btn_row.addStretch()
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _fill(self, e):
        self.title_edit.setText(e.get('title', ''))
        self.desc_edit.setPlainText(e.get('description', '') or '')
        idx = self.type_combo.findData(e.get('event_type', 'reminder'))
        if idx >= 0: self.type_combo.setCurrentIndex(idx)
        if e.get('start_datetime'):
            self.start_dt.setDateTime(
                QDateTime.fromString(e['start_datetime'][:16], "yyyy-MM-dd HH:mm")
            )
        self.reminder_spin.setValue(e.get('reminder_minutes', 15))
        self.alarm_check.setChecked(bool(e.get('alarm_enabled', 1)))

    def _save(self):
        title = self.title_edit.text().strip()
        if not title:
            return
        self.result_data = {
            'title':            title,
            'description':      self.desc_edit.toPlainText(),
            'event_type':       self.type_combo.currentData(),
            'project_id':       self.proj_combo.currentData(),
            'start_datetime':   self.start_dt.dateTime().toString("yyyy-MM-dd HH:mm"),
            'reminder_minutes': self.reminder_spin.value(),
            'alarm_enabled':    1 if self.alarm_check.isChecked() else 0,
        }
        self.accept()


class CalendarView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        jy, jm, jd = today_jalali()
        self._jy = jy
        self._jm = jm
        self._sel_greg = date.today()
        self._sel_jal  = (jy, jm, jd)
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Nav bar
        nav = QWidget()
        nav.setFixedHeight(64)
        nav.setStyleSheet(
            f"background:{THEME['bg_primary']};"
            f"border-bottom:1px solid {THEME['border_subtle']};"
        )
        nl = QHBoxLayout(nav)
        nl.setContentsMargins(20, 0, 20, 0)
        nl.setSpacing(10)

        prev_btn = QPushButton("◀  ماه قبل")
        prev_btn.setStyleSheet(self._nav_style())
        prev_btn.clicked.connect(self._prev_month)

        self.month_lbl = QLabel()
        self.month_lbl.setFont(QFont("Segoe UI Variable", 16, QFont.Weight.Bold))
        self.month_lbl.setStyleSheet(f"color:{THEME['text_primary']};")
        self.month_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        next_btn = QPushButton("ماه بعد  ▶")
        next_btn.setStyleSheet(self._nav_style())
        next_btn.clicked.connect(self._next_month)

        today_btn = QPushButton("📅 امروز")
        today_btn.clicked.connect(self._go_today)

        add_btn = QPushButton("+ رویداد جدید")
        add_btn.clicked.connect(
            lambda: self._add_event(self._sel_greg, self._sel_jal)
        )

        nl.addWidget(prev_btn)
        nl.addWidget(self.month_lbl, 1)
        nl.addWidget(next_btn)
        nl.addStretch()
        nl.addWidget(today_btn)
        nl.addWidget(add_btn)
        lay.addWidget(nav)

        # Content scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        self.cl = QVBoxLayout(container)
        self.cl.setContentsMargins(20, 14, 20, 20)
        self.cl.setSpacing(10)

        # Week header (شنبه → جمعه)
        hdr = QHBoxLayout()
        hdr.setSpacing(4)
        for i, day_name in enumerate(WEEKDAY_FA_FULL):
            lbl = QLabel(day_name)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFont(QFont("Segoe UI Variable", 10, QFont.Weight.Bold))
            color = THEME['danger'] if day_name == 'جمعه' else THEME['text_secondary']
            lbl.setStyleSheet(
                f"color:{color};background:transparent;"
            )
            hdr.addWidget(lbl, 1)
        self.cl.addLayout(hdr)

        # Calendar grid
        self.grid = QGridLayout()
        self.grid.setSpacing(4)
        for c in range(7):
            self.grid.setColumnStretch(c, 1)
        self.cl.addLayout(self.grid)

        # Upcoming events
        self.upcoming_title = QLabel("🔔  رویدادهای آینده")
        self.upcoming_title.setFont(QFont("Segoe UI Variable", 13, QFont.Weight.Bold))
        self.upcoming_title.setStyleSheet(f"color:{THEME['text_primary']};margin-top:6px;")
        self.cl.addWidget(self.upcoming_title)

        self.upcoming_lay = QVBoxLayout()
        self.upcoming_lay.setSpacing(5)
        self.cl.addLayout(self.upcoming_lay)
        self.cl.addStretch()

        scroll.setWidget(container)
        lay.addWidget(scroll)

    def _nav_style(self):
        return (
            f"background:{THEME['bg_tertiary']};color:{THEME['text_secondary']};"
            f"border:1px solid {THEME['border_default']};border-radius:8px;"
            f"padding:6px 16px;"
        )

    def refresh(self):
        jy, jm = self._jy, self._jm
        # month label: شمسی + میلادی
        gy_approx, gm_approx, _ = to_gregorian(jy, jm, 1)
        greg_months = ['ژانویه','فوریه','مارس','آوریل','مه','ژوئن',
                       'ژوئیه','اوت','سپتامبر','اکتبر','نوامبر','دسامبر']
        self.month_lbl.setText(
            f"{JALALI_MONTHS[jm-1]}  {jy}   —   {greg_months[gm_approx-1]}"
        )
        self._draw_grid()
        self._draw_upcoming()

    def _events_for_month(self):
        jy, jm = self._jy, self._jm
        gy1, gm1, gd1 = to_gregorian(jy, jm, 1)
        last_day = jalali_month_len(jy, jm)
        gy2, gm2, gd2 = to_gregorian(jy, jm, last_day)
        try:
            start = date(gy1, gm1, gd1).isoformat()
            end   = date(gy2, gm2, gd2).isoformat()
        except Exception:
            return {}

        events = self.db.fetchall(
            "SELECT * FROM events "
            "WHERE date(start_datetime)>=? AND date(start_datetime)<=?",
            (start, end)
        )
        by_date = {}
        for ev in events:
            k = ev.get('start_datetime', '')[:10]
            by_date.setdefault(k, []).append(ev)

        # تسک‌های دارای آلارم هم به‌صورت نشان روی تقویم نمایش داده می‌شوند
        tasks = self.db.fetchall(
            "SELECT id,title,due_date,due_time,status FROM tasks "
            "WHERE alarm_enabled=1 AND due_date>=? AND due_date<=? AND status!='done'",
            (start, end)
        )
        for t in tasks:
            k = t['due_date'][:10]
            by_date.setdefault(k, []).append({
                'id': f"task-{t['id']}",
                'title': t.get('title', ''),
                'event_type': 'task',
                'start_datetime': f"{t['due_date']}T{t.get('due_time') or '09:00'}",
                'is_task': True,
                'task_id': t['id'],
            })
        return by_date

    def _draw_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        jy, jm = self._jy, self._jm
        today_jal = today_jalali()
        today_greg = date.today()
        month_len = jalali_month_len(jy, jm)
        first_wd  = jalali_weekday(jy, jm, 1)   # شنبه=0

        events_by_date = self._events_for_month()

        # ماه قبل
        if jm == 1:
            prev_jy, prev_jm = jy - 1, 12
        else:
            prev_jy, prev_jm = jy, jm - 1
        prev_len = jalali_month_len(prev_jy, prev_jm)

        # ماه بعد
        if jm == 12:
            next_jy, next_jm = jy + 1, 1
        else:
            next_jy, next_jm = jy, jm + 1

        row, col = 0, 0

        # سلول‌های ماه قبل
        for i in range(first_wd):
            jd_prev = prev_len - first_wd + i + 1
            gy, gm, gd = to_gregorian(prev_jy, prev_jm, jd_prev)
            try:
                g = date(gy, gm, gd)
            except Exception:
                g = today_greg
            ev = events_by_date.get(g.isoformat(), [])
            is_fri = (col == 6)
            cell = DayCell(g, (prev_jy, prev_jm, jd_prev),
                           ev, g == today_greg, False, is_fri,
                           self._day_clicked)
            self.grid.addWidget(cell, row, col)
            col += 1
            if col == 7:
                col = 0; row += 1

        # روزهای این ماه
        for jd in range(1, month_len + 1):
            gy, gm, gd = to_gregorian(jy, jm, jd)
            try:
                g = date(gy, gm, gd)
            except Exception:
                g = today_greg
            ev = events_by_date.get(g.isoformat(), [])
            is_today = (jy, jm, jd) == today_jal
            is_fri = (col == 6)
            cell = DayCell(g, (jy, jm, jd),
                           ev, is_today, True, is_fri,
                           self._day_clicked)
            self.grid.addWidget(cell, row, col)
            col += 1
            if col == 7:
                col = 0; row += 1

        # سلول‌های ماه بعد
        nd = 1
        while col > 0 and col < 7:
            gy, gm, gd = to_gregorian(next_jy, next_jm, nd)
            try:
                g = date(gy, gm, gd)
            except Exception:
                g = today_greg
            ev = events_by_date.get(g.isoformat(), [])
            is_fri = (col == 6)
            cell = DayCell(g, (next_jy, next_jm, nd),
                           ev, g == today_greg, False, is_fri,
                           self._day_clicked)
            self.grid.addWidget(cell, row, col)
            col += 1; nd += 1

    def _draw_upcoming(self):
        while self.upcoming_lay.count():
            item = self.upcoming_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        events = self.db.fetchall(
            "SELECT * FROM events WHERE date(start_datetime)>=date('now') "
            "ORDER BY start_datetime LIMIT 10"
        )

        if not events:
            lbl = QLabel("رویداد آینده‌ای ثبت نشده است.")
            lbl.setStyleSheet(
                f"color:{THEME['text_tertiary']};font-size:12px;padding:6px 0;"
            )
            self.upcoming_lay.addWidget(lbl)
            return

        for ev in events:
            _, ev_color = ET_MAP.get(ev.get('event_type', 'reminder'),
                                      ('🔔', THEME['accent']))
            dt_str = ev.get('start_datetime', '')[:10]
            try:
                g  = date.fromisoformat(dt_str)
                jy2, jm2, jd2 = to_jalali(g.year, g.month, g.day)
                jal_str = format_jalali(jy2, jm2, jd2)
                time_str = ev.get('start_datetime', '')[11:16]
            except Exception:
                jal_str = dt_str
                time_str = ''

            row = QFrame()
            row.setStyleSheet(f"""
                QFrame{{
                    background:{THEME['bg_secondary']};
                    border-left:3px solid {ev_color};
                    border-radius:8px;margin-bottom:3px;
                }}
            """)
            rl = QHBoxLayout(row)
            rl.setContentsMargins(14, 8, 14, 8)

            title_lbl = QLabel(ev.get('title', ''))
            title_lbl.setFont(QFont("Segoe UI Variable", 12, QFont.Weight.Bold))
            title_lbl.setStyleSheet(
                f"color:{THEME['text_primary']};background:transparent;border:none;"
            )

            date_lbl = QLabel(f"📅 {jal_str}  {time_str}")
            date_lbl.setStyleSheet(
                f"color:{THEME['text_tertiary']};font-size:10px;"
                f"background:transparent;border:none;"
            )

            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(26, 26)
            edit_btn.setStyleSheet(
                f"QPushButton{{background:transparent;border:none;font-size:11px;}}"
                f"QPushButton:hover{{background:{THEME['bg_hover']};border-radius:5px;}}"
            )
            edit_btn.clicked.connect(lambda _, e=ev: self._edit_event(e))

            del_btn = QPushButton("🗑️")
            del_btn.setFixedSize(26, 26)
            del_btn.setStyleSheet(
                f"QPushButton{{background:transparent;border:none;font-size:11px;}}"
                f"QPushButton:hover{{background:{THEME['danger']}33;border-radius:5px;}}"
            )
            del_btn.clicked.connect(lambda _, eid=ev['id']: self._delete_event(eid))

            rl.addWidget(title_lbl)
            rl.addStretch()
            rl.addWidget(date_lbl)
            rl.addSpacing(8)
            rl.addWidget(edit_btn)
            rl.addWidget(del_btn)
            self.upcoming_lay.addWidget(row)

    def _day_clicked(self, greg_d, jal_t):
        self._sel_greg = greg_d
        self._sel_jal  = jal_t
        self._add_event(greg_d, jal_t)

    def _add_event(self, greg_d, jal_t):
        dlg = EventDialog(self.db, greg_d=greg_d, jal_t=jal_t, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.result_data
            self.db.execute(
                "INSERT INTO events (title,description,event_type,project_id,"
                "start_datetime,reminder_minutes,alarm_enabled,notified) VALUES (?,?,?,?,?,?,?,0)",
                (d['title'], d['description'], d['event_type'], d['project_id'],
                 d['start_datetime'], d['reminder_minutes'], d['alarm_enabled'])
            )
            self.refresh()

    def _edit_event(self, event):
        dlg = EventDialog(self.db, event=event, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.result_data
            notified = event.get('notified', 0) or 0
            if (event.get('start_datetime') != d['start_datetime'] or
                    (event.get('alarm_enabled') or 0) != d['alarm_enabled']):
                notified = 0
            self.db.execute(
                "UPDATE events SET title=?,description=?,event_type=?,project_id=?,"
                "start_datetime=?,reminder_minutes=?,alarm_enabled=?,notified=? WHERE id=?",
                (d['title'], d['description'], d['event_type'], d['project_id'],
                 d['start_datetime'], d['reminder_minutes'], d['alarm_enabled'], notified, event['id'])
            )
            self.refresh()

    def _delete_event(self, event_id):
        msg = QMessageBox(self)
        msg.setWindowTitle("حذف رویداد")
        msg.setText("آیا مطمئنید؟")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg.setStyleSheet(
            f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};"
        )
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM events WHERE id=?", (event_id,))
            self.refresh()

    def _prev_month(self):
        if self._jm == 1:
            self._jy -= 1; self._jm = 12
        else:
            self._jm -= 1
        self.refresh()

    def _next_month(self):
        if self._jm == 12:
            self._jy += 1; self._jm = 1
        else:
            self._jm += 1
        self.refresh()

    def _go_today(self):
        jy, jm, jd = today_jalali()
        self._jy, self._jm = jy, jm
        self._sel_jal = (jy, jm, jd)
        self._sel_greg = date.today()
        self.refresh()
