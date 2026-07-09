"""
Skills View v2 — با ساعت استاد شدن و پیشرفت خودکار از گزارش کار
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QLineEdit, QComboBox,
    QDoubleSpinBox, QSlider, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from ui.theme import THEME


class SkillBar(QFrame):
    def __init__(self, skill: dict, on_edit, on_delete):
        super().__init__()
        self._build(skill, on_edit, on_delete)

    def _build(self, s, on_edit, on_delete):
        color   = s.get('color', THEME['accent'])
        level   = float(s.get('level', 0))
        mastery = float(s.get('mastery_hours', 0) or 0)
        total   = float(s.get('total_hours', 0) or 0)

        self.setStyleSheet(f"""
            QFrame {{
                background:{THEME['bg_secondary']};
                border:1px solid {THEME['border_subtle']};
                border-radius:12px; margin-bottom:6px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # آیکون دسته‌بندی
        cat_icons = {'technical':'💻','language':'🌍','soft':'🤝',
                     'creative':'🎨','physical':'💪','academic':'📚'}
        icon = QLabel(cat_icons.get(s.get('category','technical'),'⚡'))
        icon.setFont(QFont("Segoe UI Emoji", 16))
        icon.setStyleSheet(
            f"background:{color}22;border-radius:8px;padding:6px;"
            f"border:1px solid {color}44;"
        )
        icon.setFixedSize(42, 42)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        info = QVBoxLayout()
        info.setSpacing(5)

        # نام + درصد
        name_row = QHBoxLayout()
        name_lbl = QLabel(s.get('name',''))
        name_lbl.setFont(QFont("Segoe UI Variable", 13, QFont.Weight.Bold))
        name_lbl.setStyleSheet(
            f"color:{THEME['text_primary']};background:transparent;border:none;"
        )
        pct_lbl = QLabel(f"{level:.0f}%")
        pct_lbl.setFont(QFont("Segoe UI Variable", 13, QFont.Weight.Bold))
        pct_lbl.setStyleSheet(
            f"color:{color};background:transparent;border:none;"
        )
        name_row.addWidget(name_lbl)
        name_row.addStretch()
        name_row.addWidget(pct_lbl)
        info.addLayout(name_row)

        # Progress bar
        bar = QProgressBar()
        bar.setValue(int(level))
        bar.setFixedHeight(8)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar {{background:{THEME['bg_primary']};border:none;border-radius:4px;}}
            QProgressBar::chunk {{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {color}, stop:1 {color}88);
                border-radius:4px;
            }}
        """)
        info.addWidget(bar)

        # ساعت‌ها
        level_str = ('مبتدی' if level<20 else 'پایه' if level<40 else
                     'متوسط' if level<60 else 'پیشرفته' if level<80 else
                     'حرفه‌ای' if level<95 else '🎓 استاد')
        hrs_lbl = QLabel(
            f"{level_str}  |  {total:.1f}h / {mastery:.0f}h  انجام شده"
        )
        hrs_lbl.setFont(QFont("Segoe UI Variable", 10))
        hrs_lbl.setStyleSheet(
            f"color:{THEME['text_tertiary']};background:transparent;border:none;"
        )
        info.addWidget(hrs_lbl)
        layout.addLayout(info, 1)

        # دکمه‌ها
        for sym, fn, hover_color in [
            ('✏️', lambda _,sk=s: on_edit(sk),   THEME['bg_hover']),
            ('🗑️', lambda _,sid=s['id']: on_delete(sid), THEME['danger']+'33'),
        ]:
            b = QPushButton(sym)
            b.setFixedSize(30, 30)
            b.setStyleSheet(
                f"QPushButton{{background:transparent;border:none;font-size:13px;}}"
                f"QPushButton:hover{{background:{hover_color};border-radius:6px;}}"
            )
            b.clicked.connect(fn)
            layout.addWidget(b)


class SkillDialog(QDialog):
    def __init__(self, db, skill=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.skill = skill
        self.setWindowTitle("مهارت جدید" if not skill else "ویرایش مهارت")
        self.setMinimumWidth(460)
        self.setStyleSheet(
            f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};"
        )
        self._build()
        if skill:
            self._fill(skill)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)

        def lbl(t):
            l = QLabel(t)
            l.setFont(QFont("Segoe UI Variable", 11, QFont.Weight.Bold))
            l.setStyleSheet(f"color:{THEME['text_secondary']};")
            return l

        lay.addWidget(lbl("نام مهارت *"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("مثلاً: Python, STM32, FPGA")
        lay.addWidget(self.name_edit)

        row = QHBoxLayout()
        cat_col = QVBoxLayout()
        cat_col.addWidget(lbl("دسته‌بندی"))
        self.cat_combo = QComboBox()
        for v, n in [('technical','فنی'),('language','زبان'),('soft','مهارت نرم'),
                     ('creative','خلاقانه'),('physical','جسمانی'),('academic','دانشگاهی')]:
            self.cat_combo.addItem(n, v)
        cat_col.addWidget(self.cat_combo)

        color_col = QVBoxLayout()
        color_col.addWidget(lbl("رنگ"))
        self.color_combo = QComboBox()
        for v, n in [('#8b5cf6','بنفش'),('#3b82f6','آبی'),('#10b981','سبز'),
                     ('#f59e0b','زرد'),('#ef4444','قرمز'),('#6366f1','ایندیگو'),
                     ('#06b6d4','فیروزه‌ای'),('#f97316','نارنجی')]:
            self.color_combo.addItem(n, v)
        color_col.addWidget(self.color_combo)

        row.addLayout(cat_col)
        row.addLayout(color_col)
        lay.addLayout(row)

        # ساعت استاد شدن — مهم‌ترین فیلد
        lay.addWidget(lbl("⏱️ ساعت لازم برای استاد شدن"))
        self.mastery_spin = QDoubleSpinBox()
        self.mastery_spin.setRange(1, 10000)
        self.mastery_spin.setValue(1000)
        self.mastery_spin.setSuffix(" ساعت")
        self.mastery_spin.setFont(QFont("Segoe UI Variable", 14))
        hint = QLabel("با قانون ۱۰۰۰۰ ساعت متخصص شوید. برای مهارت‌های ساده‌تر کمتر تنظیم کنید.")
        hint.setStyleSheet(
            f"color:{THEME['text_tertiary']};font-size:10px;"
            f"background:transparent;border:none;"
        )
        hint.setWordWrap(True)
        lay.addWidget(self.mastery_spin)
        lay.addWidget(hint)

        # ساعت انجام‌شده (قابل ویرایش)
        lay.addWidget(lbl("⌛ ساعت انجام‌شده تاکنون"))
        self.total_spin = QDoubleSpinBox()
        self.total_spin.setRange(0, 10000)
        self.total_spin.setValue(0)
        self.total_spin.setSuffix(" ساعت")
        self.total_spin.setFont(QFont("Segoe UI Variable", 13))
        lay.addWidget(self.total_spin)

        # مهارت والد
        lay.addWidget(lbl("مهارت والد (اختیاری)"))
        self.parent_combo = QComboBox()
        self.parent_combo.addItem("بدون والد", None)
        for sk in self.db.fetchall("SELECT id, name FROM skills"):
            if not self.skill or sk['id'] != self.skill.get('id'):
                self.parent_combo.addItem(sk['name'], sk['id'])
        lay.addWidget(self.parent_combo)

        btn_row = QHBoxLayout()
        cancel = QPushButton("انصراف")
        cancel.setStyleSheet(
            f"background:{THEME['bg_tertiary']};color:{THEME['text_primary']};"
            f"border:1px solid {THEME['border_default']};border-radius:8px;padding:8px 20px;"
        )
        cancel.clicked.connect(self.reject)
        save = QPushButton("⚡ ذخیره مهارت")
        save.clicked.connect(self._save)
        btn_row.addStretch()
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _fill(self, s):
        self.name_edit.setText(s.get('name',''))
        idx = self.cat_combo.findData(s.get('category','technical'))
        if idx>=0: self.cat_combo.setCurrentIndex(idx)
        idx = self.color_combo.findData(s.get('color','#8b5cf6'))
        if idx>=0: self.color_combo.setCurrentIndex(idx)
        self.mastery_spin.setValue(s.get('mastery_hours',1000) or 1000)
        self.total_spin.setValue(s.get('total_hours',0) or 0)
        idx = self.parent_combo.findData(s.get('parent_id'))
        if idx>=0: self.parent_combo.setCurrentIndex(idx)

    def _save(self):
        name = self.name_edit.text().strip()
        if not name: return
        mastery = self.mastery_spin.value()
        total   = self.total_spin.value()
        level   = min(100, round((total / mastery) * 100, 1)) if mastery > 0 else 0
        self.result_data = {
            'name': name,
            'category': self.cat_combo.currentData(),
            'color': self.color_combo.currentData(),
            'mastery_hours': mastery,
            'total_hours': total,
            'level': level,
            'parent_id': self.parent_combo.currentData(),
        }
        self.accept()


class SkillsView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build()
        self.refresh()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QWidget()
        toolbar.setFixedHeight(64)
        toolbar.setStyleSheet(
            f"background:{THEME['bg_primary']};"
            f"border-bottom:1px solid {THEME['border_subtle']};"
        )
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(24,0,24,0)

        # Stats
        self.stats_lbl = QLabel()
        self.stats_lbl.setStyleSheet(f"color:{THEME['text_secondary']};font-size:12px;")
        tl.addWidget(self.stats_lbl)
        tl.addStretch()

        add_btn = QPushButton("+ مهارت جدید")
        add_btn.clicked.connect(self._new_skill)
        tl.addWidget(add_btn)
        layout.addWidget(toolbar)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content = QWidget()
        self.cl = QVBoxLayout(self.content)
        self.cl.setContentsMargins(24,20,24,20)
        self.cl.setSpacing(4)
        scroll.setWidget(self.content)
        layout.addWidget(scroll)

    def refresh(self):
        while self.cl.count():
            item = self.cl.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        skills = self.db.fetchall(
            "SELECT * FROM skills ORDER BY level DESC, name"
        )

        total = len(skills)
        mastered = len([s for s in skills if float(s.get('level',0))>=100])
        adv = len([s for s in skills if 50<=float(s.get('level',0))<100])
        avg = sum(float(s.get('level',0)) for s in skills)/max(total,1)
        self.stats_lbl.setText(
            f"⚡ {total} مهارت  |  🎓 {mastered} استاد  |  "
            f"🏆 {adv} پیشرفته  |  📊 میانگین {avg:.0f}%"
        )

        if not skills:
            empty = QLabel(
                "⚡ هنوز مهارتی اضافه نکرده‌اید.\n"
                "مهارت‌هایت را تعریف کن و با ثبت ساعت در گزارش روزانه پیشرفت کن!"
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                f"color:{THEME['text_tertiary']};font-size:14px;padding:60px;"
            )
            self.cl.addWidget(empty)
        else:
            # گروه‌بندی
            cats = {}
            for s in skills:
                c = s.get('category','technical')
                cats.setdefault(c, []).append(s)

            cat_names = {
                'technical':'💻 فنی','language':'🌍 زبان','soft':'🤝 مهارت نرم',
                'creative':'🎨 خلاقانه','physical':'💪 جسمانی','academic':'📚 دانشگاهی'
            }
            for cat, cat_skills in cats.items():
                lbl = QLabel(cat_names.get(cat, cat))
                lbl.setFont(QFont("Segoe UI Variable", 12, QFont.Weight.Bold))
                lbl.setStyleSheet(
                    f"color:{THEME['text_secondary']};margin-top:12px;margin-bottom:4px;"
                )
                self.cl.addWidget(lbl)
                for skill in cat_skills:
                    bar = SkillBar(skill, self._edit_skill, self._delete_skill)
                    self.cl.addWidget(bar)

        self.cl.addStretch()

    def _new_skill(self):
        dlg = SkillDialog(self.db, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.result_data
            self.db.execute(
                "INSERT INTO skills (name,category,color,mastery_hours,total_hours,level,parent_id) "
                "VALUES (?,?,?,?,?,?,?)",
                (d['name'],d['category'],d['color'],d['mastery_hours'],
                 d['total_hours'],d['level'],d['parent_id'])
            )
            self.refresh()

    def _edit_skill(self, skill):
        dlg = SkillDialog(self.db, skill=skill, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.result_data
            self.db.execute(
                "UPDATE skills SET name=?,category=?,color=?,mastery_hours=?,"
                "total_hours=?,level=?,parent_id=? WHERE id=?",
                (d['name'],d['category'],d['color'],d['mastery_hours'],
                 d['total_hours'],d['level'],d['parent_id'],skill['id'])
            )
            self.refresh()

    def _delete_skill(self, skill_id):
        msg = QMessageBox(self)
        msg.setWindowTitle("حذف مهارت")
        msg.setText("آیا مطمئنید؟")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg.setStyleSheet(
            f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};"
        )
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM skills WHERE id=?", (skill_id,))
            self.refresh()
