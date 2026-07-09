"""Daily Report View v3 — با مدیریت دسته‌بندی حکم کار"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QTextEdit, QSlider, QDoubleSpinBox,
    QCheckBox, QLineEdit, QComboBox, QTimeEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QTabWidget, QDialog, QColorDialog, QSplitter, QGridLayout, QProgressBar
)
from PyQt6.QtCore import Qt, QTime
from PyQt6.QtGui import QFont, QColor
from datetime import date, timedelta
from ui.theme import THEME
from ui.widgets.themed_dialog import ThemedDialog
from core.jalali import today_jalali, to_jalali, to_gregorian, format_jalali, JALALI_MONTHS

MOODS = ['😩','😕','😐','🙂','😊','😄','🤩']
MOOD_LABELS = ['خیلی بد','بد','معمولی','خوب','عالی','فوق‌العاده','استثنایی']


# ── Category Manager ─────────────────────────────────────────────────
class WorkCategoryManagerDialog(ThemedDialog):
    """مدیریت دسته‌بندی‌های حکم کار"""
    def __init__(self, db, parent=None):
        super().__init__("⚙️ مدیریت دسته‌بندی حکم کار", parent)
        self.db = db
        self.setMinimumWidth(460)
        self._build_content()
        self._load()

    def _build_content(self):
        lay = self.content_layout()

        info = QLabel("دسته‌بندی‌های حکم کار را اضافه، ویرایش یا حذف کنید.")
        info.setStyleSheet(f"color:{THEME['text_secondary']};font-size:12px;")
        info.setWordWrap(True)
        lay.addWidget(info)

        # Add new row
        add_row = QHBoxLayout()
        self.new_icon = QLineEdit("💼"); self.new_icon.setFixedWidth(54)
        self.new_name = QLineEdit(); self.new_name.setPlaceholderText("نام دسته‌بندی جدید...")
        self.color_val = '#6366f1'
        self.color_btn = QPushButton("رنگ")
        self.color_btn.setFixedWidth(60)
        self.color_btn.setStyleSheet(f"background:{self.color_val};color:white;border-radius:6px;padding:4px;border:none;")
        self.color_btn.clicked.connect(self._pick_color)
        add_btn = QPushButton("+"); add_btn.setFixedWidth(36); add_btn.clicked.connect(self._add)

        add_row.addWidget(self.new_icon)
        add_row.addWidget(self.new_name)
        add_row.addWidget(self.color_btn)
        add_row.addWidget(add_btn)
        lay.addLayout(add_row)

        # List
        self.list_lay = QVBoxLayout()
        self.list_lay.setSpacing(4)
        lay.addLayout(self.list_lay)
        lay.addStretch()

        close_btn = QPushButton("✓ بستن")
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn)

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self.color_val), self)
        if c.isValid():
            self.color_val = c.name()
            self.color_btn.setStyleSheet(f"background:{self.color_val};color:white;border-radius:6px;padding:4px;border:none;")

    def _load(self):
        while self.list_lay.count():
            item = self.list_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        cats = self.db.fetchall("SELECT * FROM work_categories ORDER BY name")
        for cat in cats:
            row = QFrame()
            row.setStyleSheet(f"background:{THEME['bg_tertiary']};border-radius:8px;margin-bottom:2px;")
            rl = QHBoxLayout(row); rl.setContentsMargins(12,6,12,6)

            color_dot = QLabel("●")
            color_dot.setStyleSheet(f"color:{cat.get('color',THEME['accent'])};font-size:16px;background:transparent;border:none;")

            name_lbl = QLabel(f"{cat.get('icon','💼')}  {cat['name']}")
            name_lbl.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;font-size:13px;")

            del_btn = QPushButton("🗑️"); del_btn.setFixedSize(28,28)
            del_btn.setStyleSheet(f"QPushButton{{background:transparent;border:none;font-size:12px;}} QPushButton:hover{{background:{THEME['danger']}33;border-radius:5px;}}")
            del_btn.clicked.connect(lambda _,cid=cat['id']: self._delete(cid))

            rl.addWidget(color_dot); rl.addWidget(name_lbl); rl.addStretch(); rl.addWidget(del_btn)
            self.list_lay.addWidget(row)

    def _add(self):
        name = self.new_name.text().strip()
        if not name: return
        icon = self.new_icon.text().strip() or '💼'
        try:
            self.db.execute(
                "INSERT OR IGNORE INTO work_categories(name,color,icon) VALUES(?,?,?)",
                (name, self.color_val, icon)
            )
        except Exception: pass
        self.new_name.clear()
        self._load()

    def _delete(self, cat_id):
        self.db.execute("DELETE FROM work_categories WHERE id=?", (cat_id,))
        self._load()


# ── Work Entry Dialog ────────────────────────────────────────────────
class WorkEntryDialog(ThemedDialog):
    def __init__(self, db, entry=None, report_date=None, parent=None):
        super().__init__("📋 ردیف کار جدید" if not entry else "✏️ ویرایش ردیف", parent)
        self.db = db; self.entry = entry
        self.report_date = report_date or date.today().isoformat()
        self.setMinimumWidth(500)
        self._build_form()
        if entry: self._fill(entry)

    def _build_form(self):
        lay = self.content_layout()

        def lbl(t):
            l = QLabel(t); l.setFont(QFont("Segoe UI Variable",11,QFont.Weight.Bold))
            l.setStyleSheet(f"color:{THEME['text_secondary']};"); return l

        # دسته‌بندی + مدیریت
        cat_row = QHBoxLayout()
        cat_col = QVBoxLayout(); cat_col.addWidget(lbl("دسته‌بندی / حکم کار *"))
        self.cat_combo = QComboBox()
        self._reload_cats()
        cat_col.addWidget(self.cat_combo)

        manage_btn = QPushButton("⚙️")
        manage_btn.setFixedSize(36,36)
        manage_btn.setToolTip("مدیریت دسته‌بندی‌ها")
        manage_btn.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_secondary']};border:1px solid {THEME['border_default']};border-radius:8px;font-size:14px;")
        manage_btn.clicked.connect(self._manage_cats)

        cat_row.addLayout(cat_col); cat_row.addWidget(manage_btn)
        cat_row.setAlignment(manage_btn, Qt.AlignmentFlag.AlignBottom)
        lay.addLayout(cat_row)

        # ساعت شروع / پایان
        time_row = QHBoxLayout()
        start_col = QVBoxLayout(); start_col.addWidget(lbl("ساعت شروع"))
        self.start_time = QTimeEdit(QTime(8,0)); self.start_time.setDisplayFormat("HH:mm")
        self.start_time.timeChanged.connect(self._calc_dur)
        start_col.addWidget(self.start_time)

        end_col = QVBoxLayout(); end_col.addWidget(lbl("ساعت پایان"))
        self.end_time = QTimeEdit(QTime(9,0)); self.end_time.setDisplayFormat("HH:mm")
        self.end_time.timeChanged.connect(self._calc_dur)
        end_col.addWidget(self.end_time)

        dur_col = QVBoxLayout(); dur_col.addWidget(lbl("کارکرد"))
        self.dur_lbl = QLabel("01:00")
        self.dur_lbl.setFont(QFont("Segoe UI Variable",16,QFont.Weight.Bold))
        self.dur_lbl.setStyleSheet(f"color:{THEME['accent_light']};background:transparent;border:none;")
        dur_col.addWidget(self.dur_lbl)

        time_row.addLayout(start_col); time_row.addLayout(end_col); time_row.addLayout(dur_col)
        lay.addLayout(time_row)

        # مهارت
        lay.addWidget(lbl("مهارت مرتبط (اختیاری)"))
        self.skill_combo = QComboBox(); self.skill_combo.addItem("بدون مهارت", None)
        for s in self.db.fetchall("SELECT id,name FROM skills ORDER BY name"):
            self.skill_combo.addItem(s['name'], s['id'])
        lay.addWidget(self.skill_combo)

        # پروژه
        lay.addWidget(lbl("پروژه (اختیاری)"))
        self.proj_combo = QComboBox(); self.proj_combo.addItem("بدون پروژه", None)
        for p in self.db.fetchall("SELECT id,name FROM projects WHERE archived=0"):
            self.proj_combo.addItem(p['name'], p['id'])
        lay.addWidget(self.proj_combo)

        # شرح
        lay.addWidget(lbl("شرح عملکرد"))
        self.desc_edit = QLineEdit(); self.desc_edit.setPlaceholderText("چه کاری انجام دادید؟")
        lay.addWidget(self.desc_edit)

        btn_row = QHBoxLayout()
        cancel = QPushButton("انصراف")
        cancel.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_primary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:8px 20px;")
        cancel.clicked.connect(self.reject)
        save = QPushButton("💾 ذخیره"); save.clicked.connect(self._save)
        btn_row.addStretch(); btn_row.addWidget(cancel); btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _reload_cats(self, keep=None):
        self.cat_combo.clear()
        cats = self.db.fetchall("SELECT * FROM work_categories ORDER BY name")
        for c in cats:
            self.cat_combo.addItem(f"{c.get('icon','💼')}  {c['name']}", c['name'])
        if keep:
            idx = self.cat_combo.findData(keep)
            if idx >= 0: self.cat_combo.setCurrentIndex(idx)

    def _manage_cats(self):
        current = self.cat_combo.currentData()
        dlg = WorkCategoryManagerDialog(self.db, parent=self)
        dlg.exec()
        self._reload_cats(keep=current)

    def _calc_dur(self):
        s = self.start_time.time(); e = self.end_time.time()
        mins = s.secsTo(e) // 60
        if mins < 0: mins += 24*60
        h, m = divmod(mins, 60)
        self.dur_lbl.setText(f"{h:02d}:{m:02d}")

    def _fill(self, entry):
        idx = self.cat_combo.findData(entry.get('category'))
        if idx >= 0: self.cat_combo.setCurrentIndex(idx)
        self.start_time.setTime(QTime.fromString(entry.get('start_time','08:00')[:5], "HH:mm"))
        self.end_time.setTime(QTime.fromString(entry.get('end_time','09:00')[:5], "HH:mm"))
        self.desc_edit.setText(entry.get('description','') or '')
        idx = self.skill_combo.findData(entry.get('skill_id'))
        if idx >= 0: self.skill_combo.setCurrentIndex(idx)
        idx = self.proj_combo.findData(entry.get('project_id'))
        if idx >= 0: self.proj_combo.setCurrentIndex(idx)

    def _save(self):
        s = self.start_time.time().toString("HH:mm")
        e = self.end_time.time().toString("HH:mm")
        mins = self.start_time.time().secsTo(self.end_time.time()) // 60
        if mins < 0: mins += 24*60
        self.result_data = {
            'report_date': self.report_date,
            'category': self.cat_combo.currentData(),
            'start_time': s, 'end_time': e, 'duration_min': mins,
            'description': self.desc_edit.text(),
            'skill_id': self.skill_combo.currentData(),
            'project_id': self.proj_combo.currentData(),
        }
        self.accept()


# ── Mood Slider ──────────────────────────────────────────────────────
class MoodSlider(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self); lay.setSpacing(6)
        self.emoji_lbl = QLabel("😊"); self.emoji_lbl.setFont(QFont("Segoe UI Emoji",34))
        self.emoji_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); self.emoji_lbl.setStyleSheet("background:transparent;border:none;")
        self.mood_lbl = QLabel("عالی"); self.mood_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mood_lbl.setStyleSheet(f"color:{THEME['text_secondary']};font-size:12px;background:transparent;border:none;")
        self.slider = QSlider(Qt.Orientation.Horizontal); self.slider.setRange(0,6); self.slider.setValue(4)
        self.slider.valueChanged.connect(self._on)
        lay.addWidget(self.emoji_lbl); lay.addWidget(self.mood_lbl); lay.addWidget(self.slider)

    def _on(self, v):
        self.emoji_lbl.setText(MOODS[v]); self.mood_lbl.setText(MOOD_LABELS[v])

    def value(self): return self.slider.value()
    def set_value(self, v): self.slider.setValue(max(0,min(6,int(v))))


# ── Daily Report View ────────────────────────────────────────────────
class DailyReportView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        jy,jm,jd = today_jalali()
        self._jy=jy; self._jm=jm; self._jd=jd
        self._build(); self.refresh()

    @property
    def _greg_date(self):
        gy,gm,gd = to_gregorian(self._jy,self._jm,self._jd)
        return date(gy,gm,gd)

    @property
    def _date_str(self):
        return self._greg_date.isoformat()

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # Toolbar
        toolbar = QWidget(); toolbar.setFixedHeight(60)
        toolbar.setStyleSheet(f"background:{THEME['bg_primary']};border-bottom:1px solid {THEME['border_subtle']};")
        tl = QHBoxLayout(toolbar); tl.setContentsMargins(20,0,20,0); tl.setSpacing(10)

        for sym,fn in [("◀",self._prev),("▶",self._next)]:
            b = QPushButton(sym); b.setFixedSize(36,36)
            b.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_secondary']};border:1px solid {THEME['border_default']};border-radius:8px;font-size:14px;font-weight:700;")
            b.clicked.connect(fn); tl.addWidget(b)

        self.date_lbl = QLabel()
        self.date_lbl.setFont(QFont("Segoe UI Variable",14,QFont.Weight.Bold))
        self.date_lbl.setStyleSheet(f"color:{THEME['text_primary']};")
        self.date_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tl.addWidget(self.date_lbl,1)

        today_btn = QPushButton("📅 امروز"); today_btn.setFixedHeight(36)
        today_btn.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_secondary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:0 14px;")
        today_btn.clicked.connect(self._go_today); tl.addWidget(today_btn)

        save_btn = QPushButton("💾 ذخیره"); save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self._save_report); tl.addWidget(save_btn)

        root.addWidget(toolbar)

        # Tabs
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        # ── Tab 1: گزارش کار ──────────────────────────
        work_w = QWidget(); wl = QVBoxLayout(work_w); wl.setContentsMargins(16,14,16,14); wl.setSpacing(10)

        top_row = QHBoxLayout()
        self.total_work_lbl = QLabel("00:00")
        self.total_work_lbl.setFont(QFont("Segoe UI Variable",15,QFont.Weight.Bold))
        self.total_work_lbl.setStyleSheet(f"color:{THEME['accent_light']};background:transparent;border:none;")
        top_row.addWidget(QLabel("مجموع کارکرد:"))
        top_row.addWidget(self.total_work_lbl); top_row.addStretch()

        manage_cats_btn = QPushButton("⚙️ دسته‌بندی‌ها")
        manage_cats_btn.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_secondary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:6px 12px;font-size:12px;")
        manage_cats_btn.clicked.connect(self._open_cat_manager)

        add_btn = QPushButton("+ ردیف کار")
        add_btn.clicked.connect(self._add_work_entry)

        top_row.addWidget(manage_cats_btn); top_row.addWidget(add_btn)
        wl.addLayout(top_row)

        self.work_table = QTableWidget(); self.work_table.setColumnCount(8)
        self.work_table.setHorizontalHeaderLabels(["#","تاریخ","روز","دسته‌بندی","شروع","پایان","کارکرد","شرح عملکرد"])
        self.work_table.horizontalHeader().setSectionResizeMode(7,QHeaderView.ResizeMode.Stretch)
        self.work_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.work_table.verticalHeader().setVisible(False); self.work_table.setShowGrid(False)
        self.work_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.work_table.doubleClicked.connect(self._edit_work_entry)
        wl.addWidget(self.work_table)

        del_btn = QPushButton("🗑️ حذف ردیف انتخاب‌شده")
        del_btn.setStyleSheet(f"background:{THEME['danger']}22;color:{THEME['danger']};border:1px solid {THEME['danger']}44;border-radius:8px;padding:6px 14px;font-size:12px;")
        del_btn.clicked.connect(self._delete_work_entry)
        wl.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.tabs.addTab(work_w, "📋 گزارش کار")

        # ── Tab 2: خلاصه زمان (شبیه بخش مالی) ──────────
        time_w = QWidget(); tsl = QVBoxLayout(time_w); tsl.setContentsMargins(0,0,0,0)

        period_row = QWidget(); period_row.setFixedHeight(46)
        prl = QHBoxLayout(period_row); prl.setContentsMargins(16,6,16,6); prl.setSpacing(8)
        prl.addWidget(QLabel("بازه:"))
        self.time_period_combo = QComboBox()
        self.time_period_combo.addItem("📅 امروز", "today")
        self.time_period_combo.addItem("🗓️ این هفته", "week")
        self.time_period_combo.addItem("📆 این ماه", "month")
        self.time_period_combo.currentIndexChanged.connect(self._update_time_summary)
        prl.addWidget(self.time_period_combo)
        prl.addStretch()
        tsl.addWidget(period_row)

        time_scroll = QScrollArea(); time_scroll.setWidgetResizable(True); time_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.time_sum_content = QWidget()
        self.time_sum_layout = QVBoxLayout(self.time_sum_content)
        self.time_sum_layout.setContentsMargins(24,14,24,18); self.time_sum_layout.setSpacing(16)
        time_scroll.setWidget(self.time_sum_content)
        tsl.addWidget(time_scroll)

        self.tabs.addTab(time_w, "📊 خلاصه زمان")

        # ── Tab 3: خلاصه روز ──────────────────────────
        journal_w = QWidget()
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        jl = QVBoxLayout(journal_w); jl.setContentsMargins(0,0,0,0); jl.addWidget(scroll)
        container = QWidget(); cl = QVBoxLayout(container); cl.setContentsMargins(24,18,24,18); cl.setSpacing(12)
        scroll.setWidget(container)

        def section(t):
            l = QLabel(t); l.setFont(QFont("Segoe UI Variable",12,QFont.Weight.Bold))
            l.setStyleSheet(f"color:{THEME['text_secondary']};margin-top:6px;"); return l

        cl.addWidget(section("😊 حال امروزت چطوره؟"))
        self.mood_slider = MoodSlider(); cl.addWidget(self.mood_slider)

        cl.addWidget(section("⚡ سطح انرژی"))
        en_row = QHBoxLayout()
        self.energy_slider = QSlider(Qt.Orientation.Horizontal); self.energy_slider.setRange(1,10); self.energy_slider.setValue(7)
        self.energy_val_lbl = QLabel("7/10"); self.energy_val_lbl.setFixedWidth(48)
        self.energy_val_lbl.setStyleSheet(f"color:{THEME['accent_light']};font-weight:700;font-size:14px;background:transparent;border:none;")
        self.energy_slider.valueChanged.connect(lambda v: self.energy_val_lbl.setText(f"{v}/10"))
        en_row.addWidget(self.energy_slider); en_row.addWidget(self.energy_val_lbl); cl.addLayout(en_row)

        for attr,title,ph in [
            ('summary_edit',    '📋 خلاصه روز',          'امروز چه اتفاقی افتاد؟'),
            ('wins_edit',       '🏆 دستاوردهای امروز',   'چه کارهای خوبی انجام دادی؟'),
            ('challenges_edit', '⚔️ چالش‌های امروز',     'چه مشکلاتی داشتی؟'),
            ('learnings_edit',  '📚 یادگیری‌های امروز',  'چه چیزهای جدیدی یاد گرفتی؟'),
            ('tomorrow_edit',   '🎯 برنامه فردا',         'فردا چه کار مهمی داری؟'),
        ]:
            cl.addWidget(section(title))
            te = QTextEdit(); te.setPlaceholderText(ph); te.setMaximumHeight(80)
            setattr(self, attr, te); cl.addWidget(te)

        cl.addWidget(section("🏋️ ورزش"))
        self.workout_check = QCheckBox("ورزش کردم امروز"); self.workout_check.setStyleSheet(f"color:{THEME['text_primary']};font-size:13px;")
        cl.addWidget(self.workout_check)
        self.workout_details = QLineEdit(); self.workout_details.setPlaceholderText("نوع ورزش، مدت زمان...")
        cl.addWidget(self.workout_details)

        cl.addWidget(section("📖 ساعات مطالعه"))
        self.study_spin = QDoubleSpinBox(); self.study_spin.setRange(0,24); self.study_spin.setSingleStep(0.5)
        self.study_spin.setSuffix(" ساعت"); self.study_spin.setFont(QFont("Segoe UI Variable",14))
        cl.addWidget(self.study_spin); cl.addStretch()

        self.tabs.addTab(journal_w, "📝 خلاصه روز")

    def _open_cat_manager(self):
        dlg = WorkCategoryManagerDialog(self.db, parent=self)
        dlg.exec()

    # ── Navigation ───────────────────────────────────
    def _prev(self):
        from core.jalali import jalali_month_len
        jd = self._jd - 1; jm,jy = self._jm,self._jy
        if jd < 1:
            jm -= 1
            if jm < 1: jm=12; jy-=1
            jd = jalali_month_len(jy,jm)
        self._jy,self._jm,self._jd = jy,jm,jd; self.refresh()

    def _next(self):
        from core.jalali import jalali_month_len
        jd = self._jd+1; jm,jy = self._jm,self._jy
        if jd > jalali_month_len(jy,jm):
            jd=1; jm+=1
            if jm>12: jm=1; jy+=1
        self._jy,self._jm,self._jd = jy,jm,jd; self.refresh()

    def _go_today(self):
        self._jy,self._jm,self._jd = today_jalali(); self.refresh()

    # ── Refresh ──────────────────────────────────────
    def refresh(self):
        jy,jm,jd = self._jy,self._jm,self._jd
        day_names = ['دوشنبه','سه‌شنبه','چهارشنبه','پنج‌شنبه','جمعه','شنبه','یک‌شنبه']
        g = self._greg_date
        day_fa = day_names[g.weekday()]
        self.date_lbl.setText(f"📅  {format_jalali(jy,jm,jd)}  —  {JALALI_MONTHS[jm-1]} {jy}  ({day_fa})")
        self._load_work_entries()
        self._load_journal()
        self._update_time_summary()

    def _load_work_entries(self):
        entries = self.db.fetchall(
            "SELECT * FROM work_entries WHERE report_date=? ORDER BY start_time",
            (self._date_str,)
        )
        self.work_table.setRowCount(len(entries))
        total_min = 0
        jy,jm,jd = self._jy,self._jm,self._jd
        day_names = ['دوشنبه','سه‌شنبه','چهارشنبه','پنج‌شنبه','جمعه','شنبه','یک‌شنبه']
        day_fa = day_names[self._greg_date.weekday()]
        cat_colors = {c['name']:c.get('color',THEME['accent']) for c in self.db.fetchall("SELECT name,color FROM work_categories")}

        for i,e in enumerate(entries):
            dm = int(e.get('duration_min',0)); total_min += dm; h,m = divmod(dm,60)
            color = cat_colors.get(e.get('category',''),THEME['accent'])
            cells = [
                (str(i+1),                         THEME['text_tertiary']),
                (format_jalali(jy,jm,jd),          THEME['text_secondary']),
                (day_fa,                             THEME['text_secondary']),
                (e.get('category',''),               color),
                (e.get('start_time',''),             THEME['text_primary']),
                (e.get('end_time',''),               THEME['text_primary']),
                (f"{h:02d}:{m:02d}",                THEME['accent_light']),
                (e.get('description','') or '',      THEME['text_primary']),
            ]
            for col,(text,fc) in enumerate(cells):
                item = QTableWidgetItem(text); item.setForeground(QColor(fc))
                item.setFlags(item.flags()&~Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole, e['id'])
                self.work_table.setItem(i,col,item)
            self.work_table.setRowHeight(i,42)

        th,tm = divmod(total_min,60)
        self.total_work_lbl.setText(f"{th:02d}:{tm:02d}")

    def _load_journal(self):
        rep = self.db.fetchone("SELECT * FROM daily_reports WHERE date=?",(self._date_str,))
        if rep:
            self.mood_slider.set_value(rep.get('mood',4))
            self.energy_slider.setValue(rep.get('energy',7))
            self.summary_edit.setPlainText(rep.get('summary','') or '')
            self.wins_edit.setPlainText(rep.get('wins','') or '')
            self.challenges_edit.setPlainText(rep.get('challenges','') or '')
            self.learnings_edit.setPlainText(rep.get('learnings','') or '')
            self.tomorrow_edit.setPlainText(rep.get('tomorrow_plan','') or '')
            self.workout_check.setChecked(bool(rep.get('workout_done',0)))
            self.workout_details.setText(rep.get('workout_details','') or '')
            self.study_spin.setValue(rep.get('study_hours',0) or 0)
        else:
            self.mood_slider.set_value(4); self.energy_slider.setValue(7)
            for w in [self.summary_edit,self.wins_edit,self.challenges_edit,self.learnings_edit,self.tomorrow_edit]:
                w.clear()
            self.workout_check.setChecked(False); self.workout_details.clear(); self.study_spin.setValue(0)

    # ── خلاصه زمان (شبیه بخش مالی) ────────────────────
    def _time_period_range(self):
        """بازه‌ی تاریخ (ISO) بر اساس بازه‌ی انتخاب‌شده، نسبت به روز جاری گزارش."""
        period = self.time_period_combo.currentData() if hasattr(self, 'time_period_combo') else 'today'
        end_g = self._greg_date
        if period == 'week':
            start_g = end_g - timedelta(days=6)
        elif period == 'month':
            from core.jalali import jalali_month_len
            gy, gm, gd = to_gregorian(self._jy, self._jm, 1)
            start_g = date(gy, gm, gd)
        else:
            start_g = end_g
        return start_g.isoformat(), end_g.isoformat(), period

    def _update_time_summary(self):
        if not hasattr(self, 'time_sum_layout'):
            return
        while self.time_sum_layout.count():
            item = self.time_sum_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        start_iso, end_iso, period = self._time_period_range()
        rows = self.db.fetchall(
            "SELECT * FROM work_entries WHERE report_date BETWEEN ? AND ?",
            (start_iso, end_iso)
        )
        total_min = sum(r.get('duration_min', 0) or 0 for r in rows)
        entry_count = len(rows)
        period_label = {'today': 'امروز', 'week': 'این هفته', 'month': 'این ماه'}.get(period, '')

        # KPI cards
        days_span = 1
        if period == 'week': days_span = 7
        elif period == 'month':
            from core.jalali import jalali_month_len
            days_span = jalali_month_len(self._jy, self._jm)
        avg_min = total_min / days_span if days_span else 0

        th, tm = divmod(int(total_min), 60)
        ah, am = divmod(int(avg_min), 60)

        grid = QGridLayout(); grid.setSpacing(12)
        for i, (icon, title, val, color) in enumerate([
            ("⏱️", f"مجموع کارکرد {period_label}", f"{th:02d}:{tm:02d}", THEME['accent']),
            ("📋", "تعداد ردیف", str(entry_count), THEME['info']),
            ("📊", "میانگین روزانه", f"{ah:02d}:{am:02d}", THEME['success']),
        ]):
            card = QFrame(); card.setStyleSheet(f"QFrame{{background:{THEME['bg_secondary']};border:1px solid {THEME['border_subtle']};border-top:3px solid {color};border-radius:12px;}}")
            cl = QVBoxLayout(card); cl.setContentsMargins(16,12,16,12); cl.setSpacing(6)
            ic = QLabel(icon); ic.setFont(QFont("Segoe UI Emoji",18))
            ic.setStyleSheet(f"background:{color}22;border-radius:8px;padding:6px;border:1px solid {color}44;"); ic.setFixedSize(40,40); ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vl = QLabel(str(val)); vl.setFont(QFont("Segoe UI Variable",16,QFont.Weight.Bold)); vl.setStyleSheet(f"color:{color};background:transparent;border:none;")
            tl2 = QLabel(f"{icon} {title}"); tl2.setStyleSheet(f"color:{THEME['text_secondary']};background:transparent;border:none;font-size:11px;")
            cl.addWidget(ic); cl.addWidget(vl); cl.addWidget(tl2)
            grid.addWidget(card,0,i)
        kw = QWidget(); kw.setLayout(grid); self.time_sum_layout.addWidget(kw)

        # زمان به تفکیک دسته‌بندی
        cat_lbl = QLabel("📊 زمان به تفکیک دسته‌بندی")
        cat_lbl.setFont(QFont("Segoe UI Variable",13,QFont.Weight.Bold)); cat_lbl.setStyleSheet(f"color:{THEME['text_primary']};")
        self.time_sum_layout.addWidget(cat_lbl)

        cat_colors = {c['name']: c for c in self.db.fetchall("SELECT name,color,icon FROM work_categories")}
        by_cat = {}
        for r in rows:
            cat = r.get('category', 'سایر') or 'سایر'
            by_cat[cat] = by_cat.get(cat, 0) + (r.get('duration_min', 0) or 0)

        if not by_cat:
            empty = QLabel("هنوز ردیفی برای این بازه ثبت نشده.")
            empty.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:12px;")
            self.time_sum_layout.addWidget(empty)
        else:
            for cat_name, mins in sorted(by_cat.items(), key=lambda x: -x[1]):
                cinfo = cat_colors.get(cat_name, {})
                color = cinfo.get('color', THEME['accent'])
                icon = cinfo.get('icon', '💼')
                h, m = divmod(int(mins), 60)
                row = QFrame(); row.setStyleSheet(f"background:{THEME['bg_secondary']};border-radius:8px;border:1px solid {THEME['border_subtle']};margin-bottom:3px;")
                rl = QHBoxLayout(row); rl.setContentsMargins(14,8,14,8)
                nl = QLabel(f"{icon} {cat_name}"); nl.setStyleSheet(f"color:{color};background:transparent;border:none;font-size:12px;font-weight:700;"); nl.setFixedWidth(150)
                bar = QProgressBar(); pct = int((mins/total_min*100)) if total_min>0 else 0; bar.setValue(pct); bar.setFixedHeight(6); bar.setTextVisible(False)
                bar.setStyleSheet(f"QProgressBar{{background:{THEME['bg_primary']};border:none;border-radius:3px;}} QProgressBar::chunk{{background:{color};border-radius:3px;}}")
                vl = QLabel(f"{h:02d}:{m:02d}"); vl.setFixedWidth(80); vl.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                vl.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;font-size:12px;font-weight:700;")
                rl.addWidget(nl); rl.addWidget(bar,1); rl.addWidget(vl)
                self.time_sum_layout.addWidget(row)

        self.time_sum_layout.addStretch()

    # ── Work Entry CRUD ──────────────────────────────
    def _add_work_entry(self):
        dlg = WorkEntryDialog(self.db, report_date=self._date_str, parent=self)
        if dlg.exec():
            d = dlg.result_data
            self.db.execute(
                "INSERT INTO work_entries(report_date,category,start_time,end_time,duration_min,description,skill_id,project_id) VALUES(?,?,?,?,?,?,?,?)",
                (d['report_date'],d['category'],d['start_time'],d['end_time'],d['duration_min'],d['description'],d['skill_id'],d['project_id'])
            )
            if d['skill_id']:
                hrs = d['duration_min']/60
                self.db.execute("UPDATE skills SET total_hours=total_hours+? WHERE id=?",(hrs,d['skill_id']))
                self._update_skill_level(d['skill_id'])
            self._load_work_entries()
            self._update_time_summary()

    def _edit_work_entry(self, idx):
        row = idx.row()
        item = self.work_table.item(row,0)
        if not item: return
        real_id = item.data(Qt.ItemDataRole.UserRole)
        if not real_id: return
        entry = self.db.fetchone("SELECT * FROM work_entries WHERE id=?",(real_id,))
        if not entry: return
        dlg = WorkEntryDialog(self.db, entry=entry, report_date=self._date_str, parent=self)
        if dlg.exec():
            d = dlg.result_data
            if entry.get('skill_id'):
                old_hrs = entry.get('duration_min',0)/60
                self.db.execute("UPDATE skills SET total_hours=MAX(0,total_hours-?) WHERE id=?",(old_hrs,entry['skill_id']))
            self.db.execute(
                "UPDATE work_entries SET category=?,start_time=?,end_time=?,duration_min=?,description=?,skill_id=?,project_id=? WHERE id=?",
                (d['category'],d['start_time'],d['end_time'],d['duration_min'],d['description'],d['skill_id'],d['project_id'],real_id)
            )
            if d['skill_id']:
                hrs = d['duration_min']/60
                self.db.execute("UPDATE skills SET total_hours=total_hours+? WHERE id=?",(hrs,d['skill_id']))
                self._update_skill_level(d['skill_id'])
            self._load_work_entries()
            self._update_time_summary()

    def _delete_work_entry(self):
        row = self.work_table.currentRow()
        if row < 0: return
        item = self.work_table.item(row,0)
        if not item: return
        real_id = item.data(Qt.ItemDataRole.UserRole)
        if not real_id: return
        entry = self.db.fetchone("SELECT * FROM work_entries WHERE id=?",(real_id,))
        if entry and entry.get('skill_id'):
            old_hrs = entry.get('duration_min',0)/60
            self.db.execute("UPDATE skills SET total_hours=MAX(0,total_hours-?) WHERE id=?",(old_hrs,entry['skill_id']))
            self._update_skill_level(entry['skill_id'])
        self.db.execute("DELETE FROM work_entries WHERE id=?",(real_id,))
        self._load_work_entries()
        self._update_time_summary()

    def _update_skill_level(self, skill_id):
        skill = self.db.fetchone("SELECT * FROM skills WHERE id=?",(skill_id,))
        if not skill: return
        mastery = skill.get('mastery_hours',0) or 0
        total   = skill.get('total_hours',0) or 0
        level   = min(100, round((total/mastery)*100,1)) if mastery>0 else min(100,total)
        self.db.execute("UPDATE skills SET level=? WHERE id=?",(level,skill_id))

    # ── Save journal ─────────────────────────────────
    def _save_report(self):
        d = self._date_str
        study = self.study_spin.value()
        existing = self.db.fetchone("SELECT id FROM daily_reports WHERE date=?",(d,))
        vals = (
            self.mood_slider.value(), self.energy_slider.value(),
            self.summary_edit.toPlainText(), self.wins_edit.toPlainText(),
            self.challenges_edit.toPlainText(), self.learnings_edit.toPlainText(),
            self.tomorrow_edit.toPlainText(),
            1 if self.workout_check.isChecked() else 0,
            self.workout_details.text(), study,
        )
        if existing:
            self.db.execute(
                "UPDATE daily_reports SET mood=?,energy=?,summary=?,wins=?,challenges=?,learnings=?,tomorrow_plan=?,workout_done=?,workout_details=?,study_hours=?,updated_at=datetime('now') WHERE date=?",
                vals+(d,)
            )
        else:
            self.db.execute(
                "INSERT INTO daily_reports(date,mood,energy,summary,wins,challenges,learnings,tomorrow_plan,workout_done,workout_details,study_hours) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (d,)+vals
            )
        if study > 0:
            self.db.execute("UPDATE user_stats SET study_hours_total=study_hours_total+?",(study,))
        self.db.execute("UPDATE user_stats SET total_xp=total_xp+5")
        msg = QMessageBox(self); msg.setWindowTitle("✅ ذخیره شد"); msg.setText("گزارش روزانه ذخیره شد! +5 XP 🎉")
        msg.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};"); msg.exec()
