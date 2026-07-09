"""Goals View v3 — ThemedDialog"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QTextEdit, QComboBox,
    QSpinBox, QProgressBar, QMessageBox, QColorDialog, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from ui.theme import THEME
from ui.widgets.themed_dialog import ThemedDialog
from core.jalali import today_jalali, format_jalali, jalali_to_iso, to_jalali
from ui.views.projects_view import JalaliDateWidget

TIMEFRAMES = [
    ('daily','📅 روزانه'),('weekly','📆 هفتگی'),('monthly','🗓️ ماهانه'),
    ('yearly','🎯 سالانه'),('5years','🚀 ۵ ساله'),('10years','🌟 ۱۰ ساله'),
]


class CategoryManagerDialog(ThemedDialog):
    def __init__(self, db, parent=None):
        super().__init__("⚙️ مدیریت دسته‌بندی اهداف", parent)
        self.db = db; self.color_val = '#6366f1'
        self.setMinimumWidth(420)
        self._build(); self._load()

    def _build(self):
        lay = self.content_layout()
        add_row = QHBoxLayout()
        self.new_icon = QLineEdit("🎯"); self.new_icon.setFixedWidth(54)
        self.new_name = QLineEdit(); self.new_name.setPlaceholderText("نام دسته‌بندی جدید...")
        self.color_btn = QPushButton("رنگ"); self.color_btn.setFixedWidth(60)
        self.color_btn.setStyleSheet(f"background:{self.color_val};color:white;border-radius:6px;padding:4px;border:none;")
        self.color_btn.clicked.connect(self._pick_color)
        add_btn = QPushButton("+"); add_btn.setFixedWidth(36); add_btn.clicked.connect(self._add)
        add_row.addWidget(self.new_icon); add_row.addWidget(self.new_name); add_row.addWidget(self.color_btn); add_row.addWidget(add_btn)
        lay.addLayout(add_row)
        self.list_lay = QVBoxLayout(); self.list_lay.setSpacing(4); lay.addLayout(self.list_lay)
        lay.addStretch()
        close_btn = QPushButton("✓ بستن"); close_btn.clicked.connect(self.accept); lay.addWidget(close_btn)

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self.color_val), self)
        if c.isValid():
            self.color_val = c.name()
            self.color_btn.setStyleSheet(f"background:{self.color_val};color:white;border-radius:6px;padding:4px;border:none;")

    def _load(self):
        while self.list_lay.count():
            item = self.list_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for cat in self.db.fetchall("SELECT * FROM goal_categories ORDER BY name"):
            row = QFrame(); row.setStyleSheet(f"background:{THEME['bg_tertiary']};border-radius:8px;margin-bottom:2px;")
            rl = QHBoxLayout(row); rl.setContentsMargins(12,6,12,6)
            lbl = QLabel(f"{cat.get('icon','🎯')}  {cat['name']}"); lbl.setStyleSheet(f"color:{cat.get('color',THEME['accent'])};background:transparent;border:none;font-size:13px;")
            del_btn = QPushButton("🗑️"); del_btn.setFixedSize(26,26)
            del_btn.setStyleSheet(f"QPushButton{{background:transparent;border:none;font-size:11px;}} QPushButton:hover{{background:{THEME['danger']}33;border-radius:5px;}}")
            del_btn.clicked.connect(lambda _,cid=cat['id']: self._delete(cid))
            rl.addWidget(lbl); rl.addStretch(); rl.addWidget(del_btn)
            self.list_lay.addWidget(row)

    def _add(self):
        name = self.new_name.text().strip()
        if not name: return
        try: self.db.execute("INSERT OR IGNORE INTO goal_categories(name,color,icon) VALUES(?,?,?)",(name,self.color_val,self.new_icon.text() or '🎯'))
        except Exception: pass
        self.new_name.clear(); self._load()

    def _delete(self, cid):
        self.db.execute("DELETE FROM goal_categories WHERE id=?",(cid,)); self._load()


class GoalDialog(ThemedDialog):
    def __init__(self, db, goal=None, parent=None):
        super().__init__("🎯 هدف جدید" if not goal else "✏️ ویرایش هدف", parent)
        self.db = db; self.goal = goal
        self.setMinimumWidth(500); self._build_form()
        if goal: self._fill(goal)

    def _build_form(self):
        lay = self.content_layout()
        def lbl(t):
            l=QLabel(t); l.setFont(QFont("Segoe UI Variable",11,QFont.Weight.Bold)); l.setStyleSheet(f"color:{THEME['text_secondary']};"); return l

        lay.addWidget(lbl("عنوان هدف *"))
        self.title_edit = QLineEdit(); self.title_edit.setPlaceholderText("می‌خواهم..."); lay.addWidget(self.title_edit)

        lay.addWidget(lbl("چرا این هدف مهم است؟"))
        self.reason_edit = QTextEdit(); self.reason_edit.setMaximumHeight(70); self.reason_edit.setPlaceholderText("دلیل و انگیزه..."); lay.addWidget(self.reason_edit)

        row = QHBoxLayout()
        tf_col = QVBoxLayout(); tf_col.addWidget(lbl("بازه زمانی"))
        self.tf_combo = QComboBox()
        for v,l in TIMEFRAMES: self.tf_combo.addItem(l,v)
        self.tf_combo.setCurrentIndex(3); tf_col.addWidget(self.tf_combo)

        cat_col = QVBoxLayout(); cat_col.addWidget(lbl("دسته‌بندی"))
        self.cat_combo = QComboBox(); self._load_cats()
        cat_col.addWidget(self.cat_combo)

        manage_btn = QPushButton("⚙️"); manage_btn.setFixedSize(34,34)
        manage_btn.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_secondary']};border:1px solid {THEME['border_default']};border-radius:8px;font-size:13px;")
        manage_btn.clicked.connect(self._manage_cats)

        row.addLayout(tf_col); row.addLayout(cat_col); row.addWidget(manage_btn)
        row.setAlignment(manage_btn, Qt.AlignmentFlag.AlignBottom)
        lay.addLayout(row)

        lay.addWidget(lbl("📅 تاریخ هدف (شمسی)"))
        jy,jm,jd = today_jalali()
        self.target_date = JalaliDateWidget(jy+1,jm,jd); lay.addWidget(self.target_date)

        btn_row = QHBoxLayout()
        cancel = QPushButton("انصراف")
        cancel.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_primary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:8px 20px;")
        cancel.clicked.connect(self.reject)
        save = QPushButton("🎯 ذخیره هدف"); save.clicked.connect(self._save)
        btn_row.addStretch(); btn_row.addWidget(cancel); btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _load_cats(self, keep=None):
        self.cat_combo.clear()
        for c in self.db.fetchall("SELECT * FROM goal_categories ORDER BY name"):
            self.cat_combo.addItem(f"{c.get('icon','🎯')} {c['name']}",c['name'])
        if keep:
            idx = self.cat_combo.findData(keep)
            if idx >= 0: self.cat_combo.setCurrentIndex(idx)

    def _manage_cats(self):
        current = self.cat_combo.currentData()
        dlg = CategoryManagerDialog(self.db, parent=self); dlg.exec()
        self._load_cats(keep=current)

    def _fill(self, g):
        self.title_edit.setText(g.get('title',''))
        self.reason_edit.setPlainText(g.get('reason','') or '')
        idx = self.tf_combo.findData(g.get('timeframe','yearly'))
        if idx>=0: self.tf_combo.setCurrentIndex(idx)
        idx = self.cat_combo.findData(g.get('category','شخصی'))
        if idx>=0: self.cat_combo.setCurrentIndex(idx)
        if g.get('target_date'): self.target_date.set_from_iso(g['target_date'])

    def _save(self):
        title = self.title_edit.text().strip()
        if not title: return
        self.result_data = {'title':title,'reason':self.reason_edit.toPlainText(),'timeframe':self.tf_combo.currentData(),'category':self.cat_combo.currentData(),'target_date':self.target_date.get_iso()}
        self.accept()


class ProgressDialog(ThemedDialog):
    def __init__(self, goal, parent=None):
        super().__init__("📊 بروزرسانی پیشرفت", parent)
        self.setFixedWidth(340)
        lay = self.content_layout()
        lbl = QLabel(goal.get('title','')); lbl.setFont(QFont("Segoe UI Variable",13,QFont.Weight.Bold)); lbl.setWordWrap(True); lbl.setStyleSheet(f"color:{THEME['text_primary']};"); lay.addWidget(lbl)
        self.spin = QSpinBox(); self.spin.setRange(0,100); self.spin.setValue(goal.get('progress',0)); self.spin.setSuffix("%"); self.spin.setFont(QFont("Segoe UI Variable",18)); lay.addWidget(self.spin)
        btn = QPushButton("💾 ذخیره"); btn.clicked.connect(self.accept); lay.addWidget(btn)


class GoalsView(QWidget):
    def __init__(self, db):
        super().__init__(); self.db=db; self._filter='all'; self._build(); self.refresh()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        toolbar=QWidget(); toolbar.setFixedHeight(64)
        toolbar.setStyleSheet(f"background:{THEME['bg_primary']};border-bottom:1px solid {THEME['border_subtle']};")
        tl=QHBoxLayout(toolbar); tl.setContentsMargins(20,0,20,0); tl.setSpacing(8)
        self._filter_btns={}
        for val,label in [('all','همه'),('yearly','سالانه'),('monthly','ماهانه'),('weekly','هفتگی'),('daily','روزانه')]:
            btn=QPushButton(label); btn.setCheckable(True); btn.setChecked(val=='all')
            btn.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{THEME['text_secondary']};padding:5px 12px;border-radius:8px;font-size:12px;}} QPushButton:checked{{background:{THEME['accent']};color:white;font-weight:700;}} QPushButton:hover:!checked{{background:{THEME['bg_hover']};color:{THEME['text_primary']};}}")
            btn.clicked.connect(lambda _,v=val: self._set_filter(v)); self._filter_btns[val]=btn; tl.addWidget(btn)
        tl.addStretch()
        manage_btn=QPushButton("⚙️ دسته‌بندی‌ها")
        manage_btn.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_secondary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:6px 12px;font-size:12px;")
        manage_btn.clicked.connect(self._manage_cats); tl.addWidget(manage_btn)
        add_btn=QPushButton("+ هدف جدید"); add_btn.clicked.connect(self._new_goal); tl.addWidget(add_btn)
        lay.addWidget(toolbar)
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content=QWidget(); self.cl=QVBoxLayout(self.content); self.cl.setContentsMargins(28,20,28,20); self.cl.setSpacing(8)
        scroll.setWidget(self.content); lay.addWidget(scroll)

    def _set_filter(self, key):
        for k,b in self._filter_btns.items(): b.setChecked(k==key)
        self._filter=key; self.refresh()

    def _manage_cats(self):
        dlg=CategoryManagerDialog(self.db,parent=self); dlg.exec(); self.refresh()

    def refresh(self):
        while self.cl.count():
            item=self.cl.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        goals = self.db.fetchall("SELECT * FROM goals ORDER BY timeframe,created_at DESC") if self._filter=='all' else self.db.fetchall("SELECT * FROM goals WHERE timeframe=? ORDER BY created_at DESC",(self._filter,))
        cat_colors={c['name']:c.get('color',THEME['accent']) for c in self.db.fetchall("SELECT name,color FROM goal_categories")}
        if not goals:
            empty=QLabel("🎯 هنوز هدفی ندارید.\nاهداف مشخص، مسیر را روشن می‌کنند!")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter); empty.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:15px;padding:60px;"); self.cl.addWidget(empty)
        else:
            current_tf=None; tf_dict=dict(TIMEFRAMES)
            for goal in goals:
                tf=goal.get('timeframe','yearly')
                if tf!=current_tf:
                    current_tf=tf
                    sec=QLabel(tf_dict.get(tf,tf)); sec.setFont(QFont("Segoe UI Variable",12,QFont.Weight.Bold)); sec.setStyleSheet(f"color:{THEME['text_secondary']};margin-top:14px;margin-bottom:4px;"); self.cl.addWidget(sec)
                color=cat_colors.get(goal.get('category',''),THEME['accent'])
                card=self._make_card(goal,color); self.cl.addWidget(card)
        self.cl.addStretch()

    def _make_card(self, goal, color):
        card=QFrame(); card.setStyleSheet(f"QFrame{{background:{THEME['bg_secondary']};border:1px solid {THEME['border_subtle']};border-left:4px solid {color};border-radius:12px;margin-bottom:4px;}}")
        lay=QVBoxLayout(card); lay.setContentsMargins(18,14,18,14); lay.setSpacing(8)
        hdr=QHBoxLayout()
        cat=goal.get('category','')
        cat_lbl=QLabel(cat); cat_lbl.setStyleSheet(f"color:{color};background:{color}22;border-radius:6px;padding:3px 8px;font-size:11px;font-weight:700;border:none;")
        hdr.addWidget(cat_lbl); hdr.addStretch()
        for sym,fn,hc in [('✏️',lambda _,g=goal:self._edit_goal(g),THEME['bg_hover']),('🗑️',lambda _,gid=goal['id']:self._delete_goal(gid),THEME['danger']+'33')]:
            b=QPushButton(sym); b.setFixedSize(28,28); b.setStyleSheet(f"QPushButton{{background:transparent;border:none;font-size:12px;}} QPushButton:hover{{background:{hc};border-radius:5px;}}"); b.clicked.connect(fn); hdr.addWidget(b)
        lay.addLayout(hdr)
        title=QLabel(goal.get('title','')); title.setFont(QFont("Segoe UI Variable",14,QFont.Weight.Bold)); title.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;"); title.setWordWrap(True); lay.addWidget(title)
        reason=goal.get('reason','') or ''
        if reason:
            rl=QLabel(f"💡 {reason[:100]}"); rl.setStyleSheet(f"color:{THEME['text_secondary']};font-size:12px;background:transparent;border:none;"); rl.setWordWrap(True); lay.addWidget(rl)
        progress=goal.get('progress',0)
        pr_row=QHBoxLayout()
        pr_lbl=QLabel(f"پیشرفت: {progress}%"); pr_lbl.setStyleSheet(f"color:{THEME['text_secondary']};font-size:11px;background:transparent;border:none;")
        upd_btn=QPushButton("بروزرسانی"); upd_btn.setFixedHeight(26)
        upd_btn.setStyleSheet(f"QPushButton{{background:{color}22;color:{color};border:1px solid {color}44;border-radius:6px;font-size:11px;font-weight:700;padding:0 10px;}} QPushButton:hover{{background:{color}44;}}")
        upd_btn.clicked.connect(lambda _,g=goal: self._update_progress(g))
        pr_row.addWidget(pr_lbl); pr_row.addStretch(); pr_row.addWidget(upd_btn); lay.addLayout(pr_row)
        bar=QProgressBar(); bar.setValue(progress); bar.setFixedHeight(7); bar.setTextVisible(False)
        bar.setStyleSheet(f"QProgressBar{{background:{THEME['bg_primary']};border:none;border-radius:3px;}} QProgressBar::chunk{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {color},stop:1 {color}88);border-radius:3px;}}"); lay.addWidget(bar)
        target=goal.get('target_date','')
        if target:
            try:
                from datetime import date as _d; d=_d.fromisoformat(target[:10]); jy,jm,jd=to_jalali(d.year,d.month,d.day); target_str=format_jalali(jy,jm,jd)
            except Exception: target_str=target[:10]
            dl=QLabel(f"📅 هدف: {target_str}"); dl.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:10px;background:transparent;border:none;"); lay.addWidget(dl)
        return card

    def _new_goal(self):
        dlg=GoalDialog(self.db,parent=self)
        if dlg.exec():
            d=dlg.result_data; self.db.execute("INSERT INTO goals(title,reason,timeframe,category,target_date) VALUES(?,?,?,?,?)",(d['title'],d['reason'],d['timeframe'],d['category'],d['target_date'])); self.refresh()

    def _edit_goal(self, goal):
        dlg=GoalDialog(self.db,goal=goal,parent=self)
        if dlg.exec():
            d=dlg.result_data; self.db.execute("UPDATE goals SET title=?,reason=?,timeframe=?,category=?,target_date=? WHERE id=?",(d['title'],d['reason'],d['timeframe'],d['category'],d['target_date'],goal['id'])); self.refresh()

    def _delete_goal(self, gid):
        msg=QMessageBox(self); msg.setWindowTitle("حذف هدف"); msg.setText("آیا مطمئنید؟"); msg.setStandardButtons(QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No); msg.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};")
        if msg.exec()==QMessageBox.StandardButton.Yes: self.db.execute("DELETE FROM goals WHERE id=?",(gid,)); self.refresh()

    def _update_progress(self, goal):
        dlg=ProgressDialog(goal,parent=self)
        if dlg.exec():
            nv=dlg.spin.value(); self.db.execute("UPDATE goals SET progress=? WHERE id=?",(nv,goal['id']))
            if nv>=100: self.db.execute("UPDATE user_stats SET total_xp=total_xp+50")
            self.refresh()
