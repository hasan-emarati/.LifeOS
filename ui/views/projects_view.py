"""Projects View v3 — edit support + ThemedDialog"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QTextEdit, QComboBox,
    QDoubleSpinBox, QSpinBox, QProgressBar, QMessageBox,
    QGridLayout, QColorDialog, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from ui.theme import THEME
from ui.widgets.themed_dialog import ThemedDialog
from core.jalali import (today_jalali, to_gregorian, to_jalali,
                          format_jalali, jalali_to_iso, JALALI_MONTHS)

STATUSES = [
    ('planning','📋 برنامه‌ریزی',THEME['info']),
    ('active',  '🚀 فعال',       THEME['success']),
    ('paused',  '⏸️ متوقف',      THEME['warning']),
    ('done',    '✅ تکمیل',      THEME['accent']),
    ('cancelled','❌ لغو شده',   THEME['danger']),
]
PRIORITIES = [
    ('low',     '🟢 پایین',  THEME['priority_low']),
    ('medium',  '🟡 متوسط',  THEME['priority_medium']),
    ('high',    '🟠 بالا',   THEME['priority_high']),
    ('critical','🔴 بحرانی', THEME['priority_critical']),
]
S_MAP = {k:(l,c) for k,l,c in STATUSES}
P_MAP = {k:(l,c) for k,l,c in PRIORITIES}


class JalaliDateWidget(QWidget):
    def __init__(self, jy=None, jm=None, jd=None):
        super().__init__()
        lay = QHBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
        if jy is None:
            jy, jm, jd = today_jalali()
        self.year_spin = QSpinBox(); self.year_spin.setRange(1300,1500); self.year_spin.setValue(jy); self.year_spin.setFixedWidth(80)
        sep1 = QLabel("/"); sep1.setStyleSheet(f"color:{THEME['text_secondary']};background:transparent;border:none;")
        self.month_spin = QSpinBox(); self.month_spin.setRange(1,12); self.month_spin.setValue(jm); self.month_spin.setFixedWidth(56)
        sep2 = QLabel("/"); sep2.setStyleSheet(f"color:{THEME['text_secondary']};background:transparent;border:none;")
        self.day_spin = QSpinBox(); self.day_spin.setRange(1,31); self.day_spin.setValue(jd); self.day_spin.setFixedWidth(56)
        lay.addWidget(self.year_spin); lay.addWidget(sep1); lay.addWidget(self.month_spin); lay.addWidget(sep2); lay.addWidget(self.day_spin); lay.addStretch()

    def get_iso(self):
        return jalali_to_iso(self.year_spin.value(), self.month_spin.value(), self.day_spin.value())

    def set_from_iso(self, iso_str):
        if not iso_str: return
        try:
            from datetime import date
            d = date.fromisoformat(iso_str[:10])
            jy,jm,jd = to_jalali(d.year,d.month,d.day)
            self.year_spin.setValue(jy); self.month_spin.setValue(jm); self.day_spin.setValue(jd)
        except Exception: pass


class ProjectDialog(ThemedDialog):
    def __init__(self, db, project=None, parent=None):
        title = "✏️ ویرایش پروژه" if project else "📁 پروژه جدید"
        super().__init__(title, parent)
        self.db = db
        self.project = project
        self.selected_color = project.get('color','#6366f1') if project else '#6366f1'
        self.setMinimumWidth(560)
        self._fill_form()
        if project:
            self._fill(project)

    def _fill_form(self):
        lay = self.content_layout()

        def lbl(t):
            l = QLabel(t); l.setFont(QFont("Segoe UI Variable",11,QFont.Weight.Bold))
            l.setStyleSheet(f"color:{THEME['text_secondary']};"); return l

        lay.addWidget(lbl("نام پروژه *"))
        self.name_edit = QLineEdit(); self.name_edit.setPlaceholderText("نام پروژه...")
        lay.addWidget(self.name_edit)

        lay.addWidget(lbl("توضیحات"))
        self.desc_edit = QTextEdit(); self.desc_edit.setMaximumHeight(70)
        lay.addWidget(self.desc_edit)

        row1 = QHBoxLayout()
        st_col = QVBoxLayout(); st_col.addWidget(lbl("وضعیت"))
        self.status_combo = QComboBox()
        for k,l,_ in STATUSES: self.status_combo.addItem(l,k)
        st_col.addWidget(self.status_combo)

        pr_col = QVBoxLayout(); pr_col.addWidget(lbl("اولویت"))
        self.priority_combo = QComboBox()
        for k,l,_ in PRIORITIES: self.priority_combo.addItem(l,k)
        self.priority_combo.setCurrentIndex(1)
        pr_col.addWidget(self.priority_combo)

        row1.addLayout(st_col); row1.addLayout(pr_col)
        lay.addLayout(row1)

        row2 = QHBoxLayout()
        s_col = QVBoxLayout(); s_col.addWidget(lbl("📅 تاریخ شروع (شمسی)"))
        self.start_date = JalaliDateWidget(); s_col.addWidget(self.start_date)
        e_col = QVBoxLayout(); e_col.addWidget(lbl("📅 تاریخ پایان (شمسی)"))
        self.end_date = JalaliDateWidget(); e_col.addWidget(self.end_date)
        row2.addLayout(s_col); row2.addLayout(e_col)
        lay.addLayout(row2)

        row3 = QHBoxLayout()
        b_col = QVBoxLayout(); b_col.addWidget(lbl("بودجه (تومان)"))
        self.budget_spin = QDoubleSpinBox(); self.budget_spin.setMaximum(999_999_999); self.budget_spin.setSuffix(" ت")
        b_col.addWidget(self.budget_spin)

        h_col = QVBoxLayout(); h_col.addWidget(lbl("⏱️ ساعت کار برنامه‌ریزی"))
        self.work_hours_spin = QDoubleSpinBox(); self.work_hours_spin.setMaximum(99999); self.work_hours_spin.setSuffix(" ساعت")
        h_col.addWidget(self.work_hours_spin)

        row3.addLayout(b_col); row3.addLayout(h_col)
        lay.addLayout(row3)

        row4 = QHBoxLayout()
        ic_col = QVBoxLayout(); ic_col.addWidget(lbl("آیکون"))
        self.icon_edit = QLineEdit("📁"); self.icon_edit.setMaximumWidth(70)
        ic_col.addWidget(self.icon_edit)

        c_col = QVBoxLayout(); c_col.addWidget(lbl("رنگ"))
        self.color_btn = QPushButton("  انتخاب رنگ")
        self.color_btn.setStyleSheet(f"background:{self.selected_color};color:white;border-radius:8px;padding:6px;")
        self.color_btn.clicked.connect(self._pick_color)
        c_col.addWidget(self.color_btn)

        row4.addLayout(ic_col); row4.addLayout(c_col); row4.addStretch()
        lay.addLayout(row4)

        btn_row = QHBoxLayout()
        cancel = QPushButton("انصراف")
        cancel.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_primary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:8px 20px;")
        cancel.clicked.connect(self.reject)
        save = QPushButton("💾 ذخیره پروژه")
        save.clicked.connect(self._save)
        btn_row.addStretch(); btn_row.addWidget(cancel); btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self.selected_color), self)
        if c.isValid():
            self.selected_color = c.name()
            self.color_btn.setStyleSheet(f"background:{self.selected_color};color:white;border-radius:8px;padding:6px;")

    def _fill(self, p):
        self.name_edit.setText(p.get('name',''))
        self.desc_edit.setPlainText(p.get('description','') or '')
        idx = self.status_combo.findData(p.get('status','planning'))
        if idx>=0: self.status_combo.setCurrentIndex(idx)
        idx = self.priority_combo.findData(p.get('priority','medium'))
        if idx>=0: self.priority_combo.setCurrentIndex(idx)
        self.start_date.set_from_iso(p.get('start_date',''))
        self.end_date.set_from_iso(p.get('end_date',''))
        self.budget_spin.setValue(p.get('budget',0) or 0)
        self.work_hours_spin.setValue(p.get('work_hours',0) or 0)
        self.icon_edit.setText(p.get('icon','📁'))

    def _save(self):
        name = self.name_edit.text().strip()
        if not name: return
        self.result_data = {
            'name': name, 'description': self.desc_edit.toPlainText(),
            'status': self.status_combo.currentData(), 'priority': self.priority_combo.currentData(),
            'start_date': self.start_date.get_iso(), 'end_date': self.end_date.get_iso(),
            'budget': self.budget_spin.value(), 'work_hours': self.work_hours_spin.value(),
            'icon': self.icon_edit.text() or '📁', 'color': self.selected_color,
        }
        self.accept()


class TaskWeightDialog(ThemedDialog):
    def __init__(self, task, parent=None):
        super().__init__("⚖️ وزن تسک", parent)
        self.setFixedWidth(340)
        lay = self.content_layout()
        lbl = QLabel(f"تسک:\n{task.get('title','')}")
        lbl.setFont(QFont("Segoe UI Variable",12,QFont.Weight.Bold)); lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color:{THEME['text_primary']};")
        lay.addWidget(lbl)
        hint = QLabel("وزن تعیین می‌کند این تسک چند درصد از پروژه را نشان می‌دهد.")
        hint.setStyleSheet(f"color:{THEME['text_secondary']};font-size:11px;"); hint.setWordWrap(True)
        lay.addWidget(hint)
        self.weight_spin = QSpinBox(); self.weight_spin.setRange(1,100); self.weight_spin.setValue(task.get('weight',1))
        self.weight_spin.setSuffix("  واحد وزن"); self.weight_spin.setFont(QFont("Segoe UI Variable",14))
        lay.addWidget(self.weight_spin)
        btn = QPushButton("💾 ذخیره"); btn.clicked.connect(self.accept)
        lay.addWidget(btn)


class ProjectTasksDialog(ThemedDialog):
    def __init__(self, db, project, parent=None):
        super().__init__(f"📋 تسک‌های پروژه: {project.get('name','')}", parent)
        self.db = db; self.project = project
        self.setMinimumSize(720, 540)
        self._build_content()
        self._load()

    def _build_content(self):
        lay = self.content_layout()
        lay.setContentsMargins(16,12,16,16)

        hdr = QHBoxLayout()
        title = QLabel(f"📁  {self.project.get('name','')}")
        title.setFont(QFont("Segoe UI Variable",15,QFont.Weight.Bold))
        title.setStyleSheet(f"color:{THEME['text_primary']};")
        self.progress_lbl = QLabel("0%")
        self.progress_lbl.setFont(QFont("Segoe UI Variable",20,QFont.Weight.Bold))
        self.progress_lbl.setStyleSheet(f"color:{self.project.get('color',THEME['accent'])};")
        hdr.addWidget(title); hdr.addStretch(); hdr.addWidget(self.progress_lbl)
        lay.addLayout(hdr)

        color = self.project.get('color', THEME['accent'])
        self.progress_bar = QProgressBar(); self.progress_bar.setFixedHeight(10); self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"QProgressBar{{background:{THEME['bg_primary']};border:none;border-radius:5px;}} QProgressBar::chunk{{background:{color};border-radius:5px;}}")
        lay.addWidget(self.progress_bar)

        tb = QHBoxLayout()
        add_btn = QPushButton("+ تسک جدید"); add_btn.clicked.connect(self._add_task)
        tb.addWidget(add_btn); tb.addStretch()
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("همه","all")
        for v,l in [('todo','انجام نشده'),('doing','در حال انجام'),('review','بررسی'),('done','انجام شده')]:
            self.filter_combo.addItem(l,v)
        self.filter_combo.currentIndexChanged.connect(self._load)
        tb.addWidget(self.filter_combo); lay.addLayout(tb)

        self.table = QTableWidget(); self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["عنوان","وضعیت","اولویت","وزن","ساعت تخمین","مهلت","عملیات"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False); self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.table)

    def _load(self):
        filt = self.filter_combo.currentData()
        if filt == 'all':
            tasks = self.db.fetchall("SELECT * FROM tasks WHERE project_id=? ORDER BY priority DESC,created_at",(self.project['id'],))
        else:
            tasks = self.db.fetchall("SELECT * FROM tasks WHERE project_id=? AND status=? ORDER BY priority DESC",(self.project['id'],filt))
        self.table.setRowCount(len(tasks))
        status_icons = {'todo':'📋','doing':'⚡','review':'👁️','done':'✅'}
        priority_colors = {'critical':THEME['priority_critical'],'high':THEME['priority_high'],'medium':THEME['priority_medium'],'low':THEME['priority_low']}
        priority_labels = {'critical':'🔴 بحرانی','high':'🟠 بالا','medium':'🟡 متوسط','low':'🟢 پایین'}
        for r, task in enumerate(tasks):
            due = task.get('due_date','')
            if due:
                try:
                    from datetime import date
                    d = date.fromisoformat(due[:10]); jy,jm,jd = to_jalali(d.year,d.month,d.day); due = format_jalali(jy,jm,jd)
                except: pass
            pc = priority_colors.get(task.get('priority','medium'),THEME['warning'])
            cells = [
                (task.get('title',''),THEME['text_primary']),
                (f"{status_icons.get(task.get('status','todo'),'')} {task.get('status','')}",THEME['success'] if task.get('status')=='done' else THEME['text_primary']),
                (priority_labels.get(task.get('priority','medium'),''),pc),
                (str(task.get('weight',1)),THEME['accent_light']),
                (f"{task.get('estimated_hours',0)}h",THEME['text_secondary']),
                (due or '—',THEME['text_tertiary']),
                ('',THEME['text_secondary']),
            ]
            for col,(text,fc) in enumerate(cells):
                item = QTableWidgetItem(text); item.setForeground(QColor(fc))
                item.setFlags(item.flags()&~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(r,col,item)

            aw = QWidget(); al = QHBoxLayout(aw); al.setContentsMargins(4,2,4,2); al.setSpacing(4)
            for sym,fn,hc in [
                ('✅',lambda _,tid=task['id']:self._toggle_done(tid),THEME['success']+'33'),
                ('⚖️',lambda _,t=task:self._set_weight(t),THEME['bg_hover']),
                ('🗑️',lambda _,tid=task['id']:self._delete_task(tid),THEME['danger']+'33'),
            ]:
                b = QPushButton(sym); b.setFixedSize(28,28)
                b.setStyleSheet(f"QPushButton{{background:transparent;border:none;font-size:12px;}} QPushButton:hover{{background:{hc};border-radius:5px;}}")
                b.clicked.connect(fn); al.addWidget(b)
            self.table.setCellWidget(r,6,aw); self.table.setRowHeight(r,44)
        self._refresh_progress()

    def _refresh_progress(self):
        tasks = self.db.fetchall("SELECT status,weight FROM tasks WHERE project_id=?",(self.project['id'],))
        if not tasks: self.progress_bar.setValue(0); self.progress_lbl.setText("0%"); return
        total = sum(t.get('weight',1) or 1 for t in tasks)
        done  = sum(t.get('weight',1) or 1 for t in tasks if t.get('status')=='done')
        pct   = int((done/total)*100) if total else 0
        self.progress_bar.setValue(pct); self.progress_lbl.setText(f"{pct}%")
        self.db.execute("UPDATE projects SET progress=? WHERE id=?",(pct,self.project['id']))

    def _toggle_done(self, tid):
        task = self.db.fetchone("SELECT * FROM tasks WHERE id=?",(tid,))
        if not task: return
        new_status = 'todo' if task.get('status')=='done' else 'done'
        self.db.execute("UPDATE tasks SET status=?,completed_at=? WHERE id=?",(new_status,'now' if new_status=='done' else None,tid))
        if new_status == 'done':
            xp = task.get('xp_reward',10)
            self.db.execute("UPDATE user_stats SET total_xp=total_xp+?,tasks_completed=tasks_completed+1",(xp,))
            self.db.execute("INSERT INTO xp_log(amount,reason) VALUES(?,?)",(xp,f"تسک: {task.get('title','')}"))
        self._load()

    def _set_weight(self, task):
        dlg = TaskWeightDialog(task, self)
        if dlg.exec():
            self.db.execute("UPDATE tasks SET weight=? WHERE id=?",(dlg.weight_spin.value(),task['id']))
            self._load()

    def _delete_task(self, tid):
        self.db.execute("DELETE FROM tasks WHERE id=?",(tid,)); self._load()

    def _add_task(self):
        from ui.views.tasks_view import TaskDialog
        dlg = TaskDialog(self.db, parent=self)
        idx = dlg.project_combo.findData(self.project['id'])
        if idx >= 0: dlg.project_combo.setCurrentIndex(idx)
        if dlg.exec():
            d = dlg.result_data
            self.db.execute(
                "INSERT INTO tasks(title,description,project_id,status,priority,due_date,estimated_hours,xp_reward,weight,tags) VALUES(?,?,?,?,?,?,?,?,?,1)",
                (d['title'],d['description'],self.project['id'],d['status'],d['priority'],d['due_date'],d['estimated_hours'],d['xp_reward'],d.get('tags',''))
            )
            self._load()


class ProjectCard(QFrame):
    def __init__(self, project, db, on_edit, on_delete, on_open):
        super().__init__()
        self.project = project; self.db = db
        self._build(on_edit, on_delete, on_open)

    def _calc_progress(self):
        tasks = self.db.fetchall("SELECT status,weight FROM tasks WHERE project_id=?",(self.project['id'],))
        if not tasks: return self.project.get('progress',0) or 0
        total = sum(t.get('weight',1) or 1 for t in tasks)
        done  = sum(t.get('weight',1) or 1 for t in tasks if t.get('status')=='done')
        pct   = int((done/total)*100) if total else 0
        self.db.execute("UPDATE projects SET progress=? WHERE id=?",(pct,self.project['id']))
        return pct

    def _build(self, on_edit, on_delete, on_open):
        color = self.project.get('color', THEME['accent'])
        progress = self._calc_progress()
        self.setStyleSheet(f"""
            QFrame{{background:{THEME['bg_secondary']};border:1px solid {THEME['border_subtle']};
                border-top:3px solid {color};border-radius:14px;}}
            QFrame:hover{{background:{THEME['bg_tertiary']};}}
        """)

        lay = QVBoxLayout(self); lay.setContentsMargins(18,16,18,16); lay.setSpacing(10)

        hdr = QHBoxLayout()
        icon = QLabel(self.project.get('icon','📁')); icon.setFont(QFont("Segoe UI Emoji",20)); icon.setStyleSheet("background:transparent;border:none;")
        hdr.addWidget(icon); hdr.addStretch()
        for sym,fn,hc in [
            ('✏️',lambda _,p=self.project:on_edit(p),THEME['bg_hover']),
            ('🗑️',lambda _,pid=self.project['id']:on_delete(pid),THEME['danger']+'33'),
        ]:
            b = QPushButton(sym); b.setFixedSize(28,28)
            b.setStyleSheet(f"QPushButton{{background:transparent;border:none;font-size:12px;}} QPushButton:hover{{background:{hc};border-radius:5px;}}")
            b.clicked.connect(fn); hdr.addWidget(b)
        lay.addLayout(hdr)

        name = QLabel(self.project.get('name',''))
        name.setFont(QFont("Segoe UI Variable",14,QFont.Weight.Bold))
        name.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;"); name.setWordWrap(True)
        lay.addWidget(name)

        desc = (self.project.get('description','') or '')[:80]
        if desc:
            dl = QLabel(desc+('…' if len(desc)==80 else ''))
            dl.setStyleSheet(f"color:{THEME['text_secondary']};background:transparent;border:none;font-size:11px;"); dl.setWordWrap(True)
            lay.addWidget(dl)

        badges = QHBoxLayout()
        sl,sc = S_MAP.get(self.project.get('status','planning'),('📋 برنامه‌ریزی',THEME['info']))
        sb = QLabel(sl); sb.setStyleSheet(f"color:{sc};background:{sc}22;border-radius:6px;padding:3px 8px;font-size:11px;font-weight:700;border:none;")
        pl,pc = P_MAP.get(self.project.get('priority','medium'),('🟡 متوسط',THEME['warning']))
        pb = QLabel(pl); pb.setStyleSheet(f"color:{pc};background:{pc}22;border-radius:6px;padding:3px 8px;font-size:11px;font-weight:700;border:none;")
        badges.addWidget(sb); badges.addWidget(pb); badges.addStretch()
        lay.addLayout(badges)

        bar = QProgressBar(); bar.setValue(progress); bar.setFixedHeight(7); bar.setTextVisible(False)
        bar.setStyleSheet(f"QProgressBar{{background:{THEME['bg_primary']};border:none;border-radius:3px;}} QProgressBar::chunk{{background:{color};border-radius:3px;}}")
        lay.addWidget(bar)

        footer = QHBoxLayout()
        end_iso = self.project.get('end_date','')
        if end_iso:
            try:
                from datetime import date
                d = date.fromisoformat(end_iso[:10]); jy,jm,jd = to_jalali(d.year,d.month,d.day); date_str = format_jalali(jy,jm,jd)
            except: date_str = end_iso[:10]
        else:
            date_str = 'نامشخص'
        date_lbl = QLabel(f"🗓️ {date_str}"); date_lbl.setStyleSheet(f"color:{THEME['text_tertiary']};background:transparent;border:none;font-size:10px;")
        tc = self.db.fetchone("SELECT COUNT(*) as c FROM tasks WHERE project_id=?",(self.project['id'],))
        dc = self.db.fetchone("SELECT COUNT(*) as c FROM tasks WHERE project_id=? AND status='done'",(self.project['id'],))
        tc_lbl = QLabel(f"✅ {dc['c'] if dc else 0}/{tc['c'] if tc else 0} تسک")
        tc_lbl.setStyleSheet(f"color:{THEME['text_tertiary']};background:transparent;border:none;font-size:10px;")
        pct_lbl = QLabel(f"{progress}%"); pct_lbl.setFont(QFont("Segoe UI Variable",12,QFont.Weight.Bold)); pct_lbl.setStyleSheet(f"color:{color};background:transparent;border:none;")
        footer.addWidget(date_lbl); footer.addStretch(); footer.addWidget(tc_lbl); footer.addWidget(pct_lbl)
        lay.addLayout(footer)

        open_btn = QPushButton("📋 مدیریت تسک‌ها →"); open_btn.setFixedHeight(32)
        open_btn.setStyleSheet(f"QPushButton{{background:{color}22;color:{color};border:1px solid {color}44;border-radius:8px;font-size:11px;font-weight:700;}} QPushButton:hover{{background:{color}44;}}")
        open_btn.clicked.connect(lambda: on_open(self.project))
        lay.addWidget(open_btn)


class ProjectsView(QWidget):
    def __init__(self, db):
        super().__init__(); self.db = db; self._filter = 'all'; self._build(); self.refresh()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        toolbar = QWidget(); toolbar.setFixedHeight(64)
        toolbar.setStyleSheet(f"background:{THEME['bg_primary']};border-bottom:1px solid {THEME['border_subtle']};")
        tl = QHBoxLayout(toolbar); tl.setContentsMargins(20,0,20,0); tl.setSpacing(8)
        self._filter_btns = {}
        for val,label in [('all','همه'),('active','فعال'),('done','تکمیل'),('archived','آرشیو')]:
            btn = QPushButton(label); btn.setCheckable(True); btn.setChecked(val=='all')
            btn.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{THEME['text_secondary']};padding:6px 14px;border-radius:8px;font-size:13px;}} QPushButton:checked{{background:{THEME['accent']};color:white;font-weight:700;}} QPushButton:hover:!checked{{background:{THEME['bg_hover']};color:{THEME['text_primary']};}}")
            btn.clicked.connect(lambda _,v=val: self._set_filter(v))
            self._filter_btns[val] = btn; tl.addWidget(btn)
        tl.addStretch()
        add_btn = QPushButton("+ پروژه جدید"); add_btn.clicked.connect(self._new_project)
        tl.addWidget(add_btn); lay.addWidget(toolbar)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.grid_container = QWidget(); self.grid = QGridLayout(self.grid_container)
        self.grid.setContentsMargins(24,24,24,24); self.grid.setSpacing(18)
        scroll.setWidget(self.grid_container); lay.addWidget(scroll)

    def _set_filter(self, key):
        for k,b in self._filter_btns.items(): b.setChecked(k==key)
        self._filter = key; self.refresh()

    def refresh(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if self._filter == 'all':
            projects = self.db.fetchall("SELECT * FROM projects WHERE archived=0 ORDER BY priority DESC,created_at DESC")
        elif self._filter == 'active':
            projects = self.db.fetchall("SELECT * FROM projects WHERE status='active' AND archived=0")
        elif self._filter == 'done':
            projects = self.db.fetchall("SELECT * FROM projects WHERE status='done'")
        else:
            projects = self.db.fetchall("SELECT * FROM projects WHERE archived=1")
        if not projects:
            empty = QLabel("📁 هنوز پروژه‌ای وجود ندارد.\nروی «+ پروژه جدید» کلیک کنید!")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter); empty.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:15px;padding:60px;")
            self.grid.addWidget(empty,0,0); return
        cols = 3
        for i,proj in enumerate(projects):
            card = ProjectCard(proj,self.db,self._edit_project,self._delete_project,self._open_tasks)
            self.grid.addWidget(card,i//cols,i%cols)

    def _new_project(self):
        dlg = ProjectDialog(self.db, parent=self)
        if dlg.exec():
            d = dlg.result_data
            self.db.execute("INSERT INTO projects(name,description,status,priority,start_date,end_date,budget,work_hours,icon,color) VALUES(?,?,?,?,?,?,?,?,?,?)",(d['name'],d['description'],d['status'],d['priority'],d['start_date'],d['end_date'],d['budget'],d['work_hours'],d['icon'],d['color']))
            self.refresh()

    def _edit_project(self, project):
        dlg = ProjectDialog(self.db, project=project, parent=self)
        if dlg.exec():
            d = dlg.result_data
            self.db.execute("UPDATE projects SET name=?,description=?,status=?,priority=?,start_date=?,end_date=?,budget=?,work_hours=?,icon=?,color=?,updated_at=datetime('now') WHERE id=?",(d['name'],d['description'],d['status'],d['priority'],d['start_date'],d['end_date'],d['budget'],d['work_hours'],d['icon'],d['color'],project['id']))
            self.refresh()

    def _delete_project(self, pid):
        msg = QMessageBox(self); msg.setWindowTitle("حذف پروژه"); msg.setText("آیا مطمئنید؟ این عمل قابل برگشت نیست.")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        msg.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};")
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM projects WHERE id=?",(pid,)); self.refresh()

    def _open_tasks(self, project):
        dlg = ProjectTasksDialog(self.db, project, parent=self)
        dlg.exec(); self.refresh()
