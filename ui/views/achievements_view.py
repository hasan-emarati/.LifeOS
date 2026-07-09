"""Achievements View v3 — با قابلیت تعریف دستاورد جدید"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QProgressBar, QLineEdit,
    QSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ui.theme import THEME
from ui.widgets.xp_widget import xp_for_level
from ui.widgets.themed_dialog import ThemedDialog


class AchievementDialog(ThemedDialog):
    """دیالوگ تعریف دستاورد جدید"""
    def __init__(self, db, achievement=None, parent=None):
        title = "✏️ ویرایش دستاورد" if achievement else "🏆 دستاورد جدید"
        super().__init__(title, parent)
        self.db = db
        self.achievement = achievement
        self.setMinimumWidth(440)
        self._build_form()
        if achievement:
            self._fill(achievement)

    def _build_form(self):
        lay = self.content_layout()

        def lbl(t):
            l = QLabel(t)
            l.setFont(QFont("Segoe UI Variable", 11, QFont.Weight.Bold))
            l.setStyleSheet(f"color:{THEME['text_secondary']};")
            return l

        lay.addWidget(lbl("عنوان دستاورد *"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("مثلاً: قهرمان مطالعه")
        lay.addWidget(self.title_edit)

        lay.addWidget(lbl("توضیحات"))
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("شرط رسیدن به این دستاورد...")
        lay.addWidget(self.desc_edit)

        row = QHBoxLayout()
        icon_col = QVBoxLayout()
        icon_col.addWidget(lbl("آیکون"))
        self.icon_edit = QLineEdit("🏆")
        self.icon_edit.setMaximumWidth(70)
        icon_col.addWidget(self.icon_edit)

        xp_col = QVBoxLayout()
        xp_col.addWidget(lbl("جایزه XP"))
        self.xp_spin = QSpinBox()
        self.xp_spin.setRange(10, 10000)
        self.xp_spin.setValue(100)
        self.xp_spin.setSingleStep(50)
        xp_col.addWidget(self.xp_spin)

        row.addLayout(icon_col)
        row.addLayout(xp_col)
        lay.addLayout(row)

        # کلید یکتا (key)
        lay.addWidget(lbl("کلید یکتا (برای سیستم داخلی)"))
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("مثلاً: my_custom_achievement_1")
        if not self.achievement:
            import time
            self.key_edit.setText(f"custom_{int(time.time())}")
        lay.addWidget(self.key_edit)

        hint = QLabel("💡 دستاوردهای دستی باید دستی هم باز شوند (از دکمه «باز کردن» در لیست دستاوردها).")
        hint.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:10px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        btn_row = QHBoxLayout()
        cancel = QPushButton("انصراف")
        cancel.setStyleSheet(
            f"background:{THEME['bg_tertiary']};color:{THEME['text_primary']};"
            f"border:1px solid {THEME['border_default']};border-radius:8px;padding:8px 20px;"
        )
        cancel.clicked.connect(self.reject)
        save = QPushButton("💾 ذخیره دستاورد")
        save.clicked.connect(self._save)
        btn_row.addStretch()
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _fill(self, a):
        self.title_edit.setText(a.get('title', ''))
        self.desc_edit.setText(a.get('description', '') or '')
        self.icon_edit.setText(a.get('icon', '🏆'))
        self.xp_spin.setValue(a.get('xp_reward', 100))
        self.key_edit.setText(a.get('key', ''))

    def _save(self):
        title = self.title_edit.text().strip()
        key   = self.key_edit.text().strip()
        if not title or not key:
            return
        self.result_data = {
            'title':       title,
            'description': self.desc_edit.text(),
            'icon':        self.icon_edit.text() or '🏆',
            'xp_reward':   self.xp_spin.value(),
            'key':         key,
        }
        self.accept()


class AchievementsView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Toolbar
        toolbar = QWidget()
        toolbar.setFixedHeight(64)
        toolbar.setStyleSheet(
            f"background:{THEME['bg_primary']};"
            f"border-bottom:1px solid {THEME['border_subtle']};"
        )
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(22, 0, 22, 0)
        tl.setSpacing(12)
        tl.addStretch()

        new_ach_btn = QPushButton("+ دستاورد جدید")
        new_ach_btn.clicked.connect(self._new_achievement)
        tl.addWidget(new_ach_btn)

        lay.addWidget(toolbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        self.cl = QVBoxLayout(container)
        self.cl.setContentsMargins(28, 22, 28, 22)
        self.cl.setSpacing(20)

        scroll.setWidget(container)
        lay.addWidget(scroll)

    def refresh(self):
        while self.cl.count():
            item = self.cl.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        stats = self.db.fetchone("SELECT * FROM user_stats LIMIT 1") or {}
        total_xp  = stats.get('total_xp', 0)
        level     = stats.get('level', 1)
        streak    = stats.get('streak_days', 0)
        tasks_c   = stats.get('tasks_completed', 0)
        habits_c  = stats.get('habits_completed', 0)

        xp_needed = xp_for_level(level)
        xp_prev   = xp_for_level(level - 1) if level > 1 else 0
        progress  = total_xp - xp_prev
        needed    = xp_needed - xp_prev
        pct       = int((progress / max(needed, 1)) * 100)

        # ── XP Banner ───────────────────────────────────
        banner = QFrame()
        banner.setStyleSheet(f"""
            QFrame {{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {THEME['accent']}33,stop:1 {THEME['bg_secondary']});
                border:1px solid {THEME['accent']}44;border-radius:16px;
            }}
        """)
        bl = QVBoxLayout(banner)
        bl.setContentsMargins(28, 20, 28, 20)
        bl.setSpacing(10)

        top_row = QHBoxLayout()
        lv = QLabel(f"⭐  سطح {level}")
        lv.setFont(QFont("Segoe UI Variable", 24, QFont.Weight.Bold))
        lv.setStyleSheet(f"color:{THEME['xp_gold']};background:transparent;border:none;")
        xpl = QLabel(f"{total_xp:,} XP")
        xpl.setFont(QFont("Segoe UI Variable", 16, QFont.Weight.Bold))
        xpl.setStyleSheet(f"color:{THEME['text_secondary']};background:transparent;border:none;")
        top_row.addWidget(lv); top_row.addStretch(); top_row.addWidget(xpl)
        bl.addLayout(top_row)

        bar = QProgressBar()
        bar.setValue(pct); bar.setFixedHeight(10); bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar{{background:{THEME['bg_primary']};border:none;border-radius:5px;}}
            QProgressBar::chunk{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {THEME['xp_gold']},stop:1 {THEME['accent_light']});border-radius:5px;}}
        """)
        bl.addWidget(bar)

        sub = QLabel(f"تا سطح {level+1}:  {xp_needed-total_xp:,} XP مانده")
        sub.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:11px;background:transparent;border:none;")
        bl.addWidget(sub)

        mini = QHBoxLayout()
        for icon, val, lbl_text in [
            ("🔥", streak,   "روز متوالی"),
            ("✅", tasks_c,  "تسک تکمیل"),
            ("💪", habits_c, "عادت انجام"),
        ]:
            mc = QVBoxLayout()
            v = QLabel(str(val))
            v.setFont(QFont("Segoe UI Variable", 18, QFont.Weight.Bold))
            v.setStyleSheet(f"color:{THEME['accent_light']};background:transparent;border:none;")
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l = QLabel(f"{icon} {lbl_text}")
            l.setFont(QFont("Segoe UI Variable", 10))
            l.setStyleSheet(f"color:{THEME['text_secondary']};background:transparent;border:none;")
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            mc.addWidget(v); mc.addWidget(l)
            mini.addLayout(mc)
        bl.addLayout(mini)
        self.cl.addWidget(banner)

        # ── XP Log ───────────────────────────────────────
        xp_title = QLabel("⚡ آخرین XP کسب‌شده")
        xp_title.setFont(QFont("Segoe UI Variable", 13, QFont.Weight.Bold))
        xp_title.setStyleSheet(f"color:{THEME['text_primary']};")
        self.cl.addWidget(xp_title)

        for log in self.db.fetchall("SELECT * FROM xp_log ORDER BY earned_at DESC LIMIT 8"):
            row = QFrame()
            row.setStyleSheet(
                f"QFrame{{background:{THEME['bg_secondary']};border-left:3px solid {THEME['xp_gold']};border-radius:8px;margin-bottom:3px;}}"
            )
            rl = QHBoxLayout(row); rl.setContentsMargins(14, 8, 14, 8)
            reason = QLabel(log.get('reason', ''))
            reason.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;font-size:12px;")
            amount = QLabel(f"+{log.get('amount', 0)} XP")
            amount.setFont(QFont("Segoe UI Variable", 12, QFont.Weight.Bold))
            amount.setStyleSheet(f"color:{THEME['xp_gold']};background:transparent;border:none;")
            date_lbl = QLabel(str(log.get('earned_at', ''))[:16])
            date_lbl.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:10px;background:transparent;border:none;")
            rl.addWidget(reason); rl.addStretch(); rl.addWidget(date_lbl); rl.addSpacing(12); rl.addWidget(amount)
            self.cl.addWidget(row)

        # ── Achievements Grid ─────────────────────────────
        ach_hdr = QHBoxLayout()
        ach_title = QLabel("🏆 دستاوردها")
        ach_title.setFont(QFont("Segoe UI Variable", 13, QFont.Weight.Bold))
        ach_title.setStyleSheet(f"color:{THEME['text_primary']};margin-top:8px;")
        ach_hdr.addWidget(ach_title)
        ach_hdr.addStretch()
        self.cl.addLayout(ach_hdr)

        achievements = self.db.fetchall(
            "SELECT * FROM achievements ORDER BY unlocked DESC, xp_reward DESC"
        )

        grid = QGridLayout()
        grid.setSpacing(14)

        for i, a in enumerate(achievements):
            unlocked = bool(a.get('unlocked'))
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame{{
                    background:{THEME['bg_secondary'] if unlocked else THEME['bg_primary']};
                    border:2px solid {THEME['xp_gold'] if unlocked else THEME['border_subtle']};
                    border-radius:14px;
                }}
            """)
            cl2 = QVBoxLayout(card)
            cl2.setContentsMargins(16, 14, 16, 14)
            cl2.setSpacing(8)
            cl2.setAlignment(Qt.AlignmentFlag.AlignCenter)

            ic = QLabel(a.get('icon', '🏆') if unlocked else "🔒")
            ic.setFont(QFont("Segoe UI Emoji", 26))
            icon_color = THEME['xp_gold'] if unlocked else THEME['text_tertiary']
            ic.setStyleSheet(
                f"background:{icon_color}22;border-radius:12px;padding:10px;"
                f"border:1px solid {icon_color}44;"
            )
            ic.setFixedSize(60, 60)
            ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl2.addWidget(ic, alignment=Qt.AlignmentFlag.AlignCenter)

            tl2 = QLabel(a.get('title', ''))
            tl2.setFont(QFont("Segoe UI Variable", 11, QFont.Weight.Bold))
            tl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tl2.setStyleSheet(f"color:{THEME['xp_gold'] if unlocked else THEME['text_tertiary']};background:transparent;border:none;")
            tl2.setWordWrap(True)
            cl2.addWidget(tl2)

            dl2 = QLabel(a.get('description', ''))
            dl2.setFont(QFont("Segoe UI Variable", 9))
            dl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dl2.setStyleSheet(f"color:{THEME['text_tertiary']};background:transparent;border:none;")
            dl2.setWordWrap(True)
            cl2.addWidget(dl2)

            xpl2 = QLabel(f"⭐ {a.get('xp_reward', 0)} XP")
            xpl2.setFont(QFont("Segoe UI Variable", 10, QFont.Weight.Bold))
            xpl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
            xpl2.setStyleSheet(f"color:{THEME['xp_gold'] if unlocked else THEME['text_tertiary']};background:transparent;border:none;")
            cl2.addWidget(xpl2)

            if unlocked and a.get('unlocked_at'):
                dl3 = QLabel(f"🗓️ {a['unlocked_at'][:10]}")
                dl3.setFont(QFont("Segoe UI Variable", 9))
                dl3.setAlignment(Qt.AlignmentFlag.AlignCenter)
                dl3.setStyleSheet(f"color:{THEME['text_tertiary']};background:transparent;border:none;")
                cl2.addWidget(dl3)

            # دکمه‌های عملیات
            btn_row = QHBoxLayout()
            btn_row.setSpacing(4)

            if not unlocked:
                unlock_btn = QPushButton("🔓 باز کن")
                unlock_btn.setFixedHeight(26)
                unlock_btn.setStyleSheet(f"""
                    QPushButton{{background:{THEME['xp_gold']}22;color:{THEME['xp_gold']};
                        border:1px solid {THEME['xp_gold']}44;border-radius:6px;
                        font-size:10px;font-weight:700;padding:0 8px;}}
                    QPushButton:hover{{background:{THEME['xp_gold']};color:white;}}
                """)
                unlock_btn.clicked.connect(lambda _, aid=a['id'], axp=a.get('xp_reward',100), atitle=a.get('title',''): self._manual_unlock(aid, axp, atitle))
                btn_row.addWidget(unlock_btn)

            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(26, 26)
            edit_btn.setStyleSheet(
                f"QPushButton{{background:transparent;border:none;font-size:11px;}}"
                f"QPushButton:hover{{background:{THEME['bg_hover']};border-radius:5px;}}"
            )
            edit_btn.clicked.connect(lambda _, av=a: self._edit_achievement(av))

            del_btn = QPushButton("🗑️")
            del_btn.setFixedSize(26, 26)
            del_btn.setStyleSheet(
                f"QPushButton{{background:transparent;border:none;font-size:11px;}}"
                f"QPushButton:hover{{background:{THEME['danger']}33;border-radius:5px;}}"
            )
            del_btn.clicked.connect(lambda _, aid=a['id']: self._delete_achievement(aid))

            btn_row.addStretch()
            btn_row.addWidget(edit_btn)
            btn_row.addWidget(del_btn)
            cl2.addLayout(btn_row)

            grid.addWidget(card, i // 3, i % 3)

        gw = QWidget()
        gw.setLayout(grid)
        self.cl.addWidget(gw)
        self.cl.addStretch()

    def _new_achievement(self):
        dlg = AchievementDialog(self.db, parent=self)
        if dlg.exec():
            d = dlg.result_data
            try:
                self.db.execute(
                    "INSERT OR IGNORE INTO achievements(key,title,description,icon,xp_reward,unlocked) VALUES(?,?,?,?,?,0)",
                    (d['key'], d['title'], d['description'], d['icon'], d['xp_reward'])
                )
            except Exception as e:
                msg = QMessageBox(self)
                msg.setWindowTitle("خطا")
                msg.setText(f"کلید یکتا قبلاً استفاده شده: {e}")
                msg.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};")
                msg.exec()
                return
            self.refresh()

    def _edit_achievement(self, achievement):
        dlg = AchievementDialog(self.db, achievement=achievement, parent=self)
        if dlg.exec():
            d = dlg.result_data
            self.db.execute(
                "UPDATE achievements SET title=?,description=?,icon=?,xp_reward=? WHERE id=?",
                (d['title'], d['description'], d['icon'], d['xp_reward'], achievement['id'])
            )
            self.refresh()

    def _delete_achievement(self, ach_id):
        msg = QMessageBox(self)
        msg.setWindowTitle("حذف دستاورد")
        msg.setText("آیا مطمئنید؟")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};")
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM achievements WHERE id=?", (ach_id,))
            self.refresh()

    def _manual_unlock(self, ach_id, xp, title):
        self.db.execute(
            "UPDATE achievements SET unlocked=1,unlocked_at=datetime('now') WHERE id=?",
            (ach_id,)
        )
        self.db.execute("UPDATE user_stats SET total_xp=total_xp+?", (xp,))
        self.db.execute(
            "INSERT INTO xp_log(amount,reason) VALUES(?,?)",
            (xp, f"دستاورد: {title}")
        )
        stats = self.db.fetchone("SELECT * FROM user_stats LIMIT 1")
        if stats:
            if stats['total_xp'] >= xp_for_level(stats['level']):
                self.db.execute("UPDATE user_stats SET level=level+1")
        self.refresh()

    def check_and_unlock(self):
        stats = self.db.fetchone("SELECT * FROM user_stats LIMIT 1")
        if not stats: return
        checks = {
            'first_task':   stats.get('tasks_completed', 0) >= 1,
            'tasks_10':     stats.get('tasks_completed', 0) >= 10,
            'tasks_100':    stats.get('tasks_completed', 0) >= 100,
            'streak_7':     stats.get('streak_days', 0) >= 7,
            'streak_30':    stats.get('streak_days', 0) >= 30,
            'study_100h':   stats.get('study_hours_total', 0) >= 100,
            'project_done': stats.get('projects_completed', 0) >= 1,
        }
        for key, condition in checks.items():
            if condition:
                a = self.db.fetchone(
                    "SELECT * FROM achievements WHERE key=? AND unlocked=0", (key,)
                )
                if a:
                    self.db.execute(
                        "UPDATE achievements SET unlocked=1,unlocked_at=datetime('now') WHERE key=?", (key,)
                    )
                    self.db.execute(
                        "UPDATE user_stats SET total_xp=total_xp+?", (a.get('xp_reward', 100),)
                    )
                    self.db.execute(
                        "INSERT INTO xp_log(amount,reason) VALUES(?,?)",
                        (a.get('xp_reward', 100), f"دستاورد: {a.get('title', '')}")
                    )
