"""Habits View v2"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QLineEdit, QComboBox,
    QSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import date, timedelta
from ui.theme import THEME

HABIT_ICONS = ["🏃","📚","🧘","💪","🌍","💻","🎸","✍️","🥗","💧","😴","🧠","🎯","🔬"]
DAYS_SHORT  = ['ش','ی','د','س','چ','پ','ج']

class HabitDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("عادت جدید")
        self.setFixedWidth(420)
        self.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24,24,24,24)
        lay.setSpacing(12)

        def lbl(t):
            l=QLabel(t); l.setFont(QFont("Segoe UI Variable",11,QFont.Weight.Bold))
            l.setStyleSheet(f"color:{THEME['text_secondary']};"); return l

        lay.addWidget(lbl("نام عادت *"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("مثلاً: ۳۰ دقیقه ورزش")
        lay.addWidget(self.name_edit)

        row = QHBoxLayout()
        ic_col = QVBoxLayout(); ic_col.addWidget(lbl("آیکون"))
        self.icon_combo = QComboBox()
        for i in HABIT_ICONS: self.icon_combo.addItem(i, i)
        ic_col.addWidget(self.icon_combo)

        color_col = QVBoxLayout(); color_col.addWidget(lbl("رنگ"))
        self.color_combo = QComboBox()
        for v,n in [('#10b981','سبز'),('#3b82f6','آبی'),('#8b5cf6','بنفش'),
                    ('#f59e0b','زرد'),('#ef4444','قرمز'),('#f97316','نارنجی')]:
            self.color_combo.addItem(n,v)
        color_col.addWidget(self.color_combo)

        xp_col = QVBoxLayout(); xp_col.addWidget(lbl("XP"))
        self.xp_spin = QSpinBox()
        self.xp_spin.setRange(1,100); self.xp_spin.setValue(10)
        xp_col.addWidget(self.xp_spin)

        row.addLayout(ic_col); row.addLayout(color_col); row.addLayout(xp_col)
        lay.addLayout(row)

        btn_row = QHBoxLayout()
        cancel = QPushButton("انصراف")
        cancel.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_primary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:8px 20px;")
        cancel.clicked.connect(self.reject)
        save = QPushButton("🔥 ذخیره")
        save.clicked.connect(self._save)
        btn_row.addStretch(); btn_row.addWidget(cancel); btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _save(self):
        name = self.name_edit.text().strip()
        if not name: return
        self.result_data = {'name':name,'icon':self.icon_combo.currentData(),'color':self.color_combo.currentData(),'xp_reward':self.xp_spin.value()}
        self.accept()

class HabitCard(QFrame):
    def __init__(self, habit, today_done, streak, week_done, on_toggle, on_delete):
        super().__init__()
        self._build(habit, today_done, streak, week_done, on_toggle, on_delete)

    def _build(self, h, done, streak, week_done, on_toggle, on_delete):
        color = h.get('color', THEME['success'])
        self.setStyleSheet(f"""
            QFrame{{background:{color+'15' if done else THEME['bg_secondary']};
                border:1px solid {color if done else THEME['border_subtle']};
                border-radius:14px;margin-bottom:8px;}}
        """)
        lay = QVBoxLayout(self); lay.setContentsMargins(18,14,18,14); lay.setSpacing(8)

        hdr = QHBoxLayout()
        ic = QLabel(h.get('icon','⭐')); ic.setFont(QFont("Segoe UI Emoji",22))
        ic.setStyleSheet(f"background:{color}22;border-radius:10px;padding:8px;border:1px solid {color}44;")
        ic.setFixedSize(48,48); ic.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_col = QVBoxLayout(); name_col.setSpacing(2)
        name_lbl = QLabel(h.get('name',''))
        name_lbl.setFont(QFont("Segoe UI Variable",13,QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;")
        streak_lbl = QLabel(f"🔥 {streak} روز متوالی")
        streak_lbl.setFont(QFont("Segoe UI Variable",10))
        streak_lbl.setStyleSheet(f"color:{THEME['streak_fire']};background:transparent;border:none;")
        name_col.addWidget(name_lbl); name_col.addWidget(streak_lbl)

        hdr.addWidget(ic); hdr.addSpacing(12); hdr.addLayout(name_col); hdr.addStretch()

        done_btn = QPushButton("✨ انجام شد" if done else "✅ انجام شد")
        done_btn.setFixedHeight(36)
        if done:
            done_btn.setStyleSheet(f"QPushButton{{background:{color};color:white;border:none;border-radius:10px;font-size:12px;font-weight:700;padding:0 16px;}}")
            done_btn.setEnabled(False)
        else:
            done_btn.setStyleSheet(f"QPushButton{{background:{color}22;color:{color};border:2px solid {color};border-radius:10px;font-size:12px;font-weight:700;padding:0 16px;}} QPushButton:hover{{background:{color};color:white;}}")
            done_btn.clicked.connect(lambda: on_toggle(h['id']))

        del_btn = QPushButton("🗑️"); del_btn.setFixedSize(32,32)
        del_btn.setStyleSheet(f"QPushButton{{background:transparent;border:none;font-size:13px;}} QPushButton:hover{{background:{THEME['danger']}33;border-radius:6px;}}")
        del_btn.clicked.connect(lambda: on_delete(h['id']))

        hdr.addWidget(done_btn); hdr.addWidget(del_btn)
        lay.addLayout(hdr)

        # Week dots
        week_row = QHBoxLayout(); week_row.setSpacing(6)
        today = date.today()
        for i in range(7):
            d = today - timedelta(days=6-i)
            done_d = d.isoformat() in week_done
            col2 = QVBoxLayout(); col2.setSpacing(2); col2.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            dot = QLabel("●" if done_d else "○")
            dot.setFont(QFont("Segoe UI Variable",14)); dot.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            dot.setStyleSheet(f"color:{color if done_d else THEME['text_tertiary']};background:transparent;border:none;")
            day_lbl = QLabel(DAYS_SHORT[d.weekday() if d.weekday()<6 else 5])
            day_lbl.setFont(QFont("Segoe UI Variable",9)); day_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            day_lbl.setStyleSheet(f"color:{THEME['text_tertiary']};background:transparent;border:none;")
            col2.addWidget(dot); col2.addWidget(day_lbl)
            dw = QWidget(); dw.setLayout(col2); week_row.addWidget(dw)
        week_row.addStretch()
        xp_lbl = QLabel(f"⭐ +{h.get('xp_reward',10)} XP")
        xp_lbl.setFont(QFont("Segoe UI Variable",10,QFont.Weight.Bold))
        xp_lbl.setStyleSheet(f"color:{THEME['xp_gold']};background:transparent;border:none;")
        week_row.addWidget(xp_lbl)
        lay.addLayout(week_row)

class HabitsView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        toolbar = QWidget(); toolbar.setFixedHeight(64)
        toolbar.setStyleSheet(f"background:{THEME['bg_primary']};border-bottom:1px solid {THEME['border_subtle']};")
        tl = QHBoxLayout(toolbar); tl.setContentsMargins(24,0,24,0)
        self.summary_lbl = QLabel(); self.summary_lbl.setStyleSheet(f"color:{THEME['text_secondary']};font-size:13px;")
        tl.addWidget(self.summary_lbl); tl.addStretch()
        add_btn = QPushButton("+ عادت جدید"); add_btn.clicked.connect(self._new_habit)
        tl.addWidget(add_btn); lay.addWidget(toolbar)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content = QWidget()
        self.cl = QVBoxLayout(self.content); self.cl.setContentsMargins(28,20,28,20); self.cl.setSpacing(4)
        scroll.setWidget(self.content); lay.addWidget(scroll)

    def _calc_streak(self, habit_id):
        streak = 0; d = date.today()
        while True:
            r = self.db.fetchone("SELECT completed FROM habit_logs WHERE habit_id=? AND date=? AND completed=1",(habit_id,d.isoformat()))
            if r: streak+=1; d-=timedelta(days=1)
            else: break
        return streak

    def refresh(self):
        while self.cl.count():
            item = self.cl.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        habits = self.db.fetchall("SELECT * FROM habits WHERE active=1 ORDER BY created_at")
        today_str = date.today().isoformat(); done_count = 0
        if not habits:
            empty = QLabel("🔥 هنوز عادتی اضافه نکرده‌اید.\nعادت‌های خوب، زندگی را می‌سازند!")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:15px;padding:60px;")
            self.cl.addWidget(empty)
        else:
            for h in habits:
                log = self.db.fetchone("SELECT * FROM habit_logs WHERE habit_id=? AND date=? AND completed=1",(h['id'],today_str))
                is_done = log is not None
                if is_done: done_count+=1
                streak = self._calc_streak(h['id'])
                week_dates = [(date.today()-timedelta(days=i)).isoformat() for i in range(7)]
                done_logs = self.db.fetchall("SELECT date FROM habit_logs WHERE habit_id=? AND completed=1 AND date>=?",(h['id'],min(week_dates)))
                week_done = {l['date'] for l in done_logs}
                card = HabitCard(h, is_done, streak, week_done, self._toggle, self._delete)
                self.cl.addWidget(card)
        self.cl.addStretch()
        total = len(habits)
        if hasattr(self,'summary_lbl'):
            self.summary_lbl.setText(f"✅ امروز: {done_count}/{total} انجام شده" if total else "عادت‌های روزانه")

    def _toggle(self, habit_id):
        today_str = date.today().isoformat()
        existing = self.db.fetchone("SELECT * FROM habit_logs WHERE habit_id=? AND date=?",(habit_id,today_str))
        h = self.db.fetchone("SELECT * FROM habits WHERE id=?",(habit_id,))
        xp = h.get('xp_reward',10) if h else 10
        if existing:
            self.db.execute("UPDATE habit_logs SET completed=1 WHERE habit_id=? AND date=?",(habit_id,today_str))
        else:
            self.db.execute("INSERT INTO habit_logs(habit_id,date,completed) VALUES(?,?,1)",(habit_id,today_str))
        self.db.execute("UPDATE user_stats SET total_xp=total_xp+?,habits_completed=habits_completed+1",(xp,))
        self.db.execute("INSERT INTO xp_log(amount,reason) VALUES(?,?)",(xp,'عادت روزانه انجام شد'))
        self.refresh()

    def _delete(self, habit_id):
        self.db.execute("UPDATE habits SET active=0 WHERE id=?",(habit_id,))
        self.refresh()

    def _new_habit(self):
        dlg = HabitDialog(self.db, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.result_data
            self.db.execute("INSERT INTO habits(name,icon,color,xp_reward) VALUES(?,?,?,?)",(d['name'],d['icon'],d['color'],d['xp_reward']))
            self.refresh()
