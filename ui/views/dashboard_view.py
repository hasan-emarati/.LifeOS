"""
Dashboard View v2 — داشبورد اصلی با انگیزه‌بخشی روان‌شناختی
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QProgressBar, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime, date, timedelta
import random
from ui.theme import THEME
from core.jalali import today_jalali, format_jalali, JALALI_MONTHS

MOTIVATIONAL_QUOTES = [
    "💪 «هر تسکی که امروز انجام می‌دهی، سنگ‌بنای فردای بهتر توست.»",
    "🚀 «موفقیت نتیجه عادت‌های روزانه است، نه تحولات یک‌شبه.»",
    "⚡ «یک قدم کوچک امروز، یک جهش بزرگ در آینده.»",
    "🎯 «تمرکز روی پیشرفت، نه کمال.»",
    "🔥 «هر روزی که کار می‌کنی، از دیروزت بهتر می‌شوی.»",
    "🏆 «قهرمانان هم روزهایی دارند که دلشان نمی‌خواهد؛ اما می‌روند.»",
    "💡 «ایده‌ها ارزان‌اند؛ اجرا گران است.»",
    "📚 «هر ساعت مطالعه، سرمایه‌گذاری در خودت است.»",
    "🌟 «بهترین زمان برای شروع، همین الان است.»",
    "⏰ «وقت مثل پول است — صرفه‌جویی کن، سرمایه‌گذاری کن.»",
]

WEEKDAY_FA = ['دوشنبه','سه‌شنبه','چهارشنبه','پنج‌شنبه','جمعه','شنبه','یک‌شنبه']


class StatCard(QFrame):
    def __init__(self, icon, title, value, color, subtitle="", clickable=False):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background:{THEME['bg_secondary']};
                border:1px solid {THEME['border_subtle']};
                border-radius:14px;
            }}
            QFrame:hover {{
                border-color:{color}66;
                background:{THEME['bg_tertiary']};
            }}
        """)
        if clickable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(8)

        top = QHBoxLayout()
        ic = QLabel(icon)
        ic.setFont(QFont("Segoe UI Emoji", 20))
        ic.setStyleSheet(
            f"background:{color}22;border-radius:10px;padding:8px;"
            f"border:1px solid {color}44;"
        )
        ic.setFixedSize(50, 50)
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top.addWidget(ic)
        top.addStretch()
        lay.addLayout(top)

        val_lbl = QLabel(str(value))
        val_lbl.setFont(QFont("Segoe UI Variable", 28, QFont.Weight.Bold))
        val_lbl.setStyleSheet(
            f"color:{THEME['text_primary']};background:transparent;border:none;"
        )
        lay.addWidget(val_lbl)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI Variable", 12))
        title_lbl.setStyleSheet(
            f"color:{THEME['text_secondary']};background:transparent;border:none;"
        )
        lay.addWidget(title_lbl)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setFont(QFont("Segoe UI Variable", 10))
            sub_lbl.setStyleSheet(
                f"color:{color};background:transparent;border:none;"
            )
            lay.addWidget(sub_lbl)


class TaskRow(QFrame):
    def __init__(self, task, projects):
        super().__init__()
        pc = {
            'critical': THEME['priority_critical'],
            'high':     THEME['priority_high'],
            'medium':   THEME['priority_medium'],
            'low':      THEME['priority_low'],
        }.get(task.get('priority', 'medium'), THEME['priority_medium'])

        self.setStyleSheet(f"""
            QFrame {{
                background:{THEME['bg_tertiary']};
                border-left:3px solid {pc};
                border-radius:8px;margin-bottom:4px;
            }}
            QFrame:hover {{ background:{THEME['bg_hover']}; }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(10)

        title = QLabel(task.get('title', '')[:45])
        title.setFont(QFont("Segoe UI Variable", 12))
        title.setStyleSheet(
            f"color:{THEME['text_primary']};background:transparent;border:none;"
        )

        proj_id = task.get('project_id')
        proj_name = projects.get(proj_id, '') if proj_id else ''
        if proj_name:
            proj_lbl = QLabel(f"📁 {proj_name[:18]}")
            proj_lbl.setStyleSheet(
                f"color:{THEME['accent_light']};font-size:10px;"
                f"background:transparent;border:none;"
            )
        due = task.get('due_date', '')
        if due:
            try:
                from datetime import date as _d
                d = _d.fromisoformat(due[:10])
                from core.jalali import to_jalali
                jy, jm, jd = to_jalali(d.year, d.month, d.day)
                due_str = format_jalali(jy, jm, jd)
                is_overdue = d < _d.today()
                due_color = THEME['danger'] if is_overdue else THEME['text_tertiary']
            except Exception:
                due_str = due[:10]
                due_color = THEME['text_tertiary']
        else:
            due_str = ''
            due_color = THEME['text_tertiary']

        due_lbl = QLabel(due_str)
        due_lbl.setFont(QFont("Segoe UI Variable", 10))
        due_lbl.setStyleSheet(
            f"color:{due_color};background:transparent;border:none;"
        )
        due_lbl.setFixedWidth(90)

        xp_lbl = QLabel(f"⭐{task.get('xp_reward',10)}")
        xp_lbl.setFont(QFont("Segoe UI Variable", 10, QFont.Weight.Bold))
        xp_lbl.setStyleSheet(
            f"color:{THEME['xp_gold']};background:transparent;border:none;"
        )
        xp_lbl.setFixedWidth(40)

        lay.addWidget(title)
        lay.addStretch()
        if proj_name:
            lay.addWidget(proj_lbl)
        lay.addWidget(due_lbl)
        lay.addWidget(xp_lbl)


class DashboardView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build()
        self.refresh()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        container = QWidget()
        self.main_lay = QVBoxLayout(container)
        self.main_lay.setContentsMargins(28, 22, 28, 22)
        self.main_lay.setSpacing(20)
        scroll.setWidget(container)

        # Greeting placeholder
        self.greeting_lbl = QLabel()
        self.greeting_lbl.setFont(QFont("Segoe UI Variable", 22, QFont.Weight.Bold))
        self.greeting_lbl.setStyleSheet(f"color:{THEME['text_primary']};")
        self.main_lay.addWidget(self.greeting_lbl)

        # Date + streak
        self.date_streak_row = QHBoxLayout()
        self.jalali_lbl = QLabel()
        self.jalali_lbl.setFont(QFont("Segoe UI Variable", 14))
        self.jalali_lbl.setStyleSheet(f"color:{THEME['text_secondary']};")
        self.streak_lbl = QLabel()
        self.streak_lbl.setFont(QFont("Segoe UI Variable", 13, QFont.Weight.Bold))
        self.streak_lbl.setStyleSheet(f"color:{THEME['streak_fire']};")
        self.date_streak_row.addWidget(self.jalali_lbl)
        self.date_streak_row.addStretch()
        self.date_streak_row.addWidget(self.streak_lbl)
        self.main_lay.addLayout(self.date_streak_row)

        # Motivational quote
        self.quote_lbl = QLabel()
        self.quote_lbl.setFont(QFont("Segoe UI Variable", 12))
        self.quote_lbl.setWordWrap(True)
        self.quote_lbl.setStyleSheet(f"""
            color:{THEME['text_secondary']};
            background:{THEME['accent']}15;
            border:1px solid {THEME['accent']}33;
            border-radius:10px;padding:12px 18px;
        """)
        self.main_lay.addWidget(self.quote_lbl)

        # KPI grid
        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(14)
        self.main_lay.addLayout(self.kpi_grid)

        # Daily progress bar
        daily_frame = QFrame()
        daily_frame.setStyleSheet(f"""
            QFrame{{
                background:{THEME['bg_secondary']};
                border:1px solid {THEME['border_subtle']};
                border-radius:12px;
            }}
        """)
        dfl = QVBoxLayout(daily_frame)
        dfl.setContentsMargins(20, 14, 20, 14)
        dfl.setSpacing(8)
        daily_hdr = QHBoxLayout()
        d_title = QLabel("📅 پیشرفت روز")
        d_title.setFont(QFont("Segoe UI Variable", 13, QFont.Weight.Bold))
        d_title.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;")
        self.daily_pct_lbl = QLabel("0%")
        self.daily_pct_lbl.setFont(QFont("Segoe UI Variable", 13, QFont.Weight.Bold))
        self.daily_pct_lbl.setStyleSheet(
            f"color:{THEME['success']};background:transparent;border:none;"
        )
        daily_hdr.addWidget(d_title)
        daily_hdr.addStretch()
        daily_hdr.addWidget(self.daily_pct_lbl)
        dfl.addLayout(daily_hdr)
        self.daily_bar = QProgressBar()
        self.daily_bar.setFixedHeight(10)
        self.daily_bar.setTextVisible(False)
        self.daily_bar.setStyleSheet(f"""
            QProgressBar{{background:{THEME['bg_primary']};border:none;border-radius:5px;}}
            QProgressBar::chunk{{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {THEME['success']}, stop:1 {THEME['accent']});
                border-radius:5px;
            }}
        """)
        dfl.addWidget(self.daily_bar)
        self.daily_sub_lbl = QLabel("")
        self.daily_sub_lbl.setStyleSheet(
            f"color:{THEME['text_tertiary']};font-size:11px;background:transparent;border:none;"
        )
        dfl.addWidget(self.daily_sub_lbl)
        self.main_lay.addWidget(daily_frame)

        # ── کارهای روزانه (محل نمایش جدا از تسک‌های عادی) ──
        daily_tasks_frame = QFrame()
        daily_tasks_frame.setStyleSheet(f"""
            QFrame{{
                background:{THEME['bg_secondary']};
                border:1px solid {THEME['accent']}55;
                border-radius:12px;
            }}
        """)
        dtl = QVBoxLayout(daily_tasks_frame)
        dtl.setContentsMargins(20, 14, 20, 14)
        dtl.setSpacing(8)
        dt_hdr = QHBoxLayout()
        dt_title = QLabel("📌 کارهای روزانه")
        dt_title.setFont(QFont("Segoe UI Variable", 13, QFont.Weight.Bold))
        dt_title.setStyleSheet(f"color:{THEME['accent_light']};background:transparent;border:none;")
        dt_hdr.addWidget(dt_title)
        dt_hdr.addStretch()
        self.daily_tasks_pct_lbl = QLabel("")
        self.daily_tasks_pct_lbl.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:11px;background:transparent;border:none;")
        dt_hdr.addWidget(self.daily_tasks_pct_lbl)
        dtl.addLayout(dt_hdr)
        self.daily_tasks_container = QVBoxLayout()
        self.daily_tasks_container.setSpacing(4)
        dtl.addLayout(self.daily_tasks_container)
        self.main_lay.addWidget(daily_tasks_frame)

        # Two-column: tasks + projects
        cols = QHBoxLayout()
        cols.setSpacing(18)

        # Left: tasks
        left_col = QVBoxLayout()
        left_col.setSpacing(8)
        left_title_row = QHBoxLayout()
        lt = QLabel("📋 تسک‌های اولویت‌دار")
        lt.setFont(QFont("Segoe UI Variable", 14, QFont.Weight.Bold))
        lt.setStyleSheet(f"color:{THEME['text_primary']};")
        left_title_row.addWidget(lt)
        left_title_row.addStretch()
        left_col.addLayout(left_title_row)
        self.tasks_container = QVBoxLayout()
        self.tasks_container.setSpacing(4)
        left_col.addLayout(self.tasks_container)
        left_col.addStretch()
        cols.addLayout(left_col, 3)

        # Right: active projects
        right_col = QVBoxLayout()
        right_col.setSpacing(8)
        rt = QLabel("🚀 پروژه‌های فعال")
        rt.setFont(QFont("Segoe UI Variable", 14, QFont.Weight.Bold))
        rt.setStyleSheet(f"color:{THEME['text_primary']};")
        right_col.addWidget(rt)
        self.projects_container = QVBoxLayout()
        self.projects_container.setSpacing(6)
        right_col.addLayout(self.projects_container)
        right_col.addStretch()
        cols.addLayout(right_col, 2)

        self.main_lay.addLayout(cols)

        # Habits today
        habits_frame = QFrame()
        habits_frame.setStyleSheet(f"""
            QFrame{{
                background:{THEME['bg_secondary']};
                border:1px solid {THEME['border_subtle']};
                border-radius:12px;
            }}
        """)
        hfl = QVBoxLayout(habits_frame)
        hfl.setContentsMargins(20, 14, 20, 14)
        hfl.setSpacing(8)
        ht = QLabel("🔥 عادت‌های امروز")
        ht.setFont(QFont("Segoe UI Variable", 13, QFont.Weight.Bold))
        ht.setStyleSheet(
            f"color:{THEME['text_primary']};background:transparent;border:none;"
        )
        hfl.addWidget(ht)
        self.habits_row = QHBoxLayout()
        self.habits_row.setSpacing(8)
        hfl.addLayout(self.habits_row)
        self.main_lay.addWidget(habits_frame)
        self.main_lay.addStretch()

    # ── Refresh ──────────────────────────────────────────────────────
    def refresh(self):
        self._update_header()
        self._update_kpi()
        self._update_daily_progress()
        self._update_daily_tasks()
        self._update_tasks()
        self._update_projects()
        self._update_habits()

    def _update_header(self):
        hour = datetime.now().hour
        if hour < 6:
            greeting, emoji = "شب بخیر", "🌙"
        elif hour < 12:
            greeting, emoji = "صبح بخیر", "☀️"
        elif hour < 17:
            greeting, emoji = "ظهر بخیر", "🌤️"
        elif hour < 21:
            greeting, emoji = "عصر بخیر", "🌅"
        else:
            greeting, emoji = "شب بخیر", "🌙"

        self.greeting_lbl.setText(f"{emoji} {greeting}! امروز هم یه روز عالیه.")
        self.quote_lbl.setText(random.choice(MOTIVATIONAL_QUOTES))

        # تاریخ شمسی
        jy, jm, jd = today_jalali()
        today_g = date.today()
        day_fa = WEEKDAY_FA[today_g.weekday()]
        self.jalali_lbl.setText(
            f"📅  {day_fa}  {jd} {JALALI_MONTHS[jm-1]} {jy}"
        )

        stats = self.db.fetchone("SELECT streak_days FROM user_stats LIMIT 1")
        streak = stats['streak_days'] if stats else 0
        if streak > 0:
            self.streak_lbl.setText(f"🔥 {streak} روز متوالی")
        else:
            self.streak_lbl.setText("")

    def _update_kpi(self):
        while self.kpi_grid.count():
            item = self.kpi_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        today_str = date.today().isoformat()
        open_tasks  = self.db.fetchone("SELECT COUNT(*) as c FROM tasks WHERE status!='done'")
        done_today  = self.db.fetchone("SELECT COUNT(*) as c FROM tasks WHERE status='done' AND date(completed_at)=?", (today_str,))
        active_proj = self.db.fetchone("SELECT COUNT(*) as c FROM projects WHERE status='active' AND archived=0")
        user_stats  = self.db.fetchone("SELECT * FROM user_stats LIMIT 1") or {}

        kpis = [
            ("✅", "تسک باز",        open_tasks['c'] if open_tasks else 0,  THEME['info'],         ""),
            ("🎉", "انجام‌شده امروز", done_today['c'] if done_today else 0, THEME['success'],      ""),
            ("📁", "پروژه فعال",     active_proj['c'] if active_proj else 0, THEME['accent'],       ""),
            ("⭐", "کل XP",          f"{user_stats.get('total_xp',0):,}",   THEME['xp_gold'],      f"سطح {user_stats.get('level',1)}"),
        ]

        for i, (icon, title, val, color, sub) in enumerate(kpis):
            card = StatCard(icon, title, val, color, sub)
            self.kpi_grid.addWidget(card, 0, i)

    def _update_daily_progress(self):
        today_str = date.today().isoformat()
        total = self.db.fetchone("SELECT COUNT(*) as c FROM tasks")
        done_today = self.db.fetchone(
            "SELECT COUNT(*) as c FROM tasks WHERE status='done' AND date(completed_at)=?",
            (today_str,)
        )
        total_open = self.db.fetchone("SELECT COUNT(*) as c FROM tasks WHERE status!='done'")

        # تسک‌های امروز برای انجام
        to_do_today = self.db.fetchone(
            "SELECT COUNT(*) as c FROM tasks WHERE status!='done' AND due_date<=?",
            (today_str,)
        )
        done_c = done_today['c'] if done_today else 0
        target = to_do_today['c'] if to_do_today else 0
        pct = int((done_c / max(target + done_c, 1)) * 100) if (target + done_c) > 0 else 0

        self.daily_bar.setValue(pct)
        self.daily_pct_lbl.setText(f"{pct}%")
        self.daily_sub_lbl.setText(
            f"امروز {done_c} تسک انجام دادی  •  {target} تسک باقی‌مانده"
        )

    def _update_daily_tasks(self):
        """تسک‌های روزانه در بخش جداگانه — چک‌لیستی که هر روز ریست می‌شود."""
        while self.daily_tasks_container.count():
            item = self.daily_tasks_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        today_str = date.today().isoformat()
        daily_tasks = self.db.fetchall(
            "SELECT * FROM tasks WHERE is_daily=1 ORDER BY title"
        )

        if not daily_tasks:
            empty = QLabel("هنوز تسک روزانه‌ای تعریف نکردی. از صفحه‌ی «تسک‌ها» یکی بساز و گزینه‌ی «تسک روزانه» رو تیک بزن.")
            empty.setWordWrap(True)
            empty.setStyleSheet(
                f"color:{THEME['text_tertiary']};font-size:12px;background:transparent;border:none;"
            )
            self.daily_tasks_container.addWidget(empty)
            self.daily_tasks_pct_lbl.setText("")
            return

        done_count = 0
        for task in daily_tasks:
            log = self.db.fetchone(
                "SELECT completed FROM daily_task_logs WHERE task_id=? AND date=?",
                (task['id'], today_str)
            )
            is_done = bool(log and log.get('completed'))
            if is_done:
                done_count += 1

            row = QFrame()
            row.setStyleSheet(f"""
                QFrame{{background:{THEME['bg_tertiary']};border-radius:8px;margin-bottom:2px;}}
                QFrame:hover{{background:{THEME['bg_hover']};}}
            """)
            rl = QHBoxLayout(row)
            rl.setContentsMargins(12, 6, 12, 6)

            cb = QCheckBox(task.get('title', ''))
            cb.setChecked(is_done)
            cb.setStyleSheet(
                f"color:{THEME['text_tertiary'] if is_done else THEME['text_primary']};"
                f"font-size:12px;background:transparent;border:none;"
                + ("text-decoration:line-through;" if is_done else "")
            )
            cb.stateChanged.connect(lambda state, tid=task['id']: self._toggle_daily_task(tid, state))
            rl.addWidget(cb)
            rl.addStretch()

            xp_lbl = QLabel(f"⭐{task.get('xp_reward',10)}")
            xp_lbl.setFont(QFont("Segoe UI Variable", 10, QFont.Weight.Bold))
            xp_lbl.setStyleSheet(f"color:{THEME['xp_gold']};background:transparent;border:none;")
            rl.addWidget(xp_lbl)

            self.daily_tasks_container.addWidget(row)

        self.daily_tasks_pct_lbl.setText(f"{done_count}/{len(daily_tasks)} انجام شد امروز")

    def _toggle_daily_task(self, task_id, state):
        today_str = date.today().isoformat()
        completed = 1 if state == Qt.CheckState.Checked.value or state == 2 else 0
        existing = self.db.fetchone(
            "SELECT id FROM daily_task_logs WHERE task_id=? AND date=?", (task_id, today_str)
        )
        if existing:
            self.db.execute(
                "UPDATE daily_task_logs SET completed=? WHERE id=?", (completed, existing['id'])
            )
        else:
            self.db.execute(
                "INSERT INTO daily_task_logs(task_id,date,completed) VALUES(?,?,?)",
                (task_id, today_str, completed)
            )
        # فقط یک بار در روز XP بده (وقتی برای اولین بار تیک می‌خوره)
        if completed and not existing:
            task = self.db.fetchone("SELECT xp_reward FROM tasks WHERE id=?", (task_id,))
            xp = (task.get('xp_reward', 5) if task else 5) or 5
            self.db.execute("UPDATE user_stats SET total_xp=total_xp+?", (xp,))
            self.db.execute(
                "INSERT INTO xp_log(amount,reason) VALUES(?,?)",
                (xp, "تسک روزانه انجام شد")
            )
        self._update_daily_tasks()
        self._update_kpi()

    def _update_tasks(self):
        while self.tasks_container.count():
            item = self.tasks_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        projects = {
            p['id']: p['name']
            for p in self.db.fetchall("SELECT id,name FROM projects")
        }
        tasks = self.db.fetchall(
            "SELECT * FROM tasks WHERE status!='done' AND (is_daily IS NULL OR is_daily=0) "
            "ORDER BY CASE priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 "
            "WHEN 'medium' THEN 2 ELSE 3 END, due_date ASC LIMIT 8"
        )

        if not tasks:
            empty = QLabel("✨ همه تسک‌ها انجام شده! عالیه!")
            empty.setStyleSheet(f"""
                color:{THEME['success']};background:{THEME['success']}15;
                border-radius:8px;padding:14px;font-size:13px;
                border:1px solid {THEME['success']}33;
            """)
            self.tasks_container.addWidget(empty)
        else:
            for task in tasks:
                row = TaskRow(task, projects)
                self.tasks_container.addWidget(row)

    def _update_projects(self):
        while self.projects_container.count():
            item = self.projects_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        projects = self.db.fetchall(
            "SELECT * FROM projects WHERE status='active' AND archived=0 "
            "ORDER BY priority DESC LIMIT 5"
        )

        for proj in projects:
            # محاسبه پیشرفت از تسک‌ها
            tasks = self.db.fetchall(
                "SELECT status,weight FROM tasks WHERE project_id=?", (proj['id'],)
            )
            if tasks:
                total_w = sum(t.get('weight', 1) or 1 for t in tasks)
                done_w  = sum(t.get('weight', 1) or 1 for t in tasks if t.get('status') == 'done')
                progress = int((done_w / total_w) * 100) if total_w else 0
            else:
                progress = proj.get('progress', 0) or 0

            color = proj.get('color', THEME['accent'])

            card = QFrame()
            card.setStyleSheet(f"""
                QFrame{{
                    background:{THEME['bg_tertiary']};
                    border-radius:10px;
                    border:1px solid {THEME['border_subtle']};
                    border-left:3px solid {color};
                }}
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(14, 10, 14, 10)
            cl.setSpacing(6)

            name_lbl = QLabel(f"{proj.get('icon','📁')}  {proj['name']}")
            name_lbl.setFont(QFont("Segoe UI Variable", 12, QFont.Weight.Bold))
            name_lbl.setStyleSheet(
                f"color:{THEME['text_primary']};background:transparent;border:none;"
            )
            cl.addWidget(name_lbl)

            bar = QProgressBar()
            bar.setValue(progress)
            bar.setFixedHeight(6)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar{{background:{THEME['bg_primary']};border:none;border-radius:3px;}}
                QProgressBar::chunk{{background:{color};border-radius:3px;}}
            """)
            cl.addWidget(bar)

            pct_lbl = QLabel(f"{progress}% پیشرفت")
            pct_lbl.setFont(QFont("Segoe UI Variable", 10))
            pct_lbl.setStyleSheet(
                f"color:{color};background:transparent;border:none;"
            )
            cl.addWidget(pct_lbl)
            self.projects_container.addWidget(card)

    def _update_habits(self):
        while self.habits_row.count():
            item = self.habits_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        habits = self.db.fetchall("SELECT * FROM habits WHERE active=1 LIMIT 8")
        today_str = date.today().isoformat()

        if not habits:
            no_lbl = QLabel("هنوز عادتی تعریف نشده.")
            no_lbl.setStyleSheet(
                f"color:{THEME['text_tertiary']};font-size:12px;"
                f"background:transparent;border:none;"
            )
            self.habits_row.addWidget(no_lbl)
        else:
            for h in habits:
                log = self.db.fetchone(
                    "SELECT completed FROM habit_logs WHERE habit_id=? AND date=? AND completed=1",
                    (h['id'], today_str)
                )
                done = log is not None
                color = h.get('color', THEME['success'])

                btn = QFrame()
                btn.setFixedSize(68, 68)
                btn.setStyleSheet(f"""
                    QFrame{{
                        background:{color if done else THEME['bg_tertiary']};
                        border:2px solid {color};
                        border-radius:12px;
                    }}
                """)
                bl = QVBoxLayout(btn)
                bl.setContentsMargins(0, 0, 0, 0)
                bl.setSpacing(2)

                ic = QLabel(h.get('icon', '⭐'))
                ic.setFont(QFont("Segoe UI Emoji", 18))
                ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
                ic.setStyleSheet("background:transparent;border:none;")

                nm = QLabel(h.get('name', '')[:6])
                nm.setFont(QFont("Segoe UI Variable", 8))
                nm.setAlignment(Qt.AlignmentFlag.AlignCenter)
                nm.setStyleSheet(
                    f"color:{'white' if done else THEME['text_secondary']};"
                    f"background:transparent;border:none;"
                )

                bl.addWidget(ic)
                bl.addWidget(nm)
                self.habits_row.addWidget(btn)

        self.habits_row.addStretch()
