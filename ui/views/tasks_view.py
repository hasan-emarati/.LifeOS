"""Tasks View v3 — sort + ThemedDialog"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QTextEdit, QComboBox,
    QDoubleSpinBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QSizePolicy, QStackedWidget,
    QListWidget, QListWidgetItem, QCheckBox, QTimeEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QTime
from PyQt6.QtGui import QFont, QColor
from datetime import date
from ui.theme import THEME
from ui.widgets.themed_dialog import ThemedDialog
from core.jalali import today_jalali, to_jalali, format_jalali, jalali_to_iso
from ui.views.projects_view import JalaliDateWidget

KANBAN_COLS = [
    ('todo',   '📋 انجام نشده', THEME['info']),
    ('doing',  '⚡ در حال انجام', THEME['warning']),
    ('review', '👁️ بررسی',      THEME['accent']),
    ('done',   '✅ انجام شده',  THEME['success']),
]
PRIORITY_COLORS = {
    'critical':THEME['priority_critical'],'high':THEME['priority_high'],
    'medium':THEME['priority_medium'],'low':THEME['priority_low'],
}
PRIORITY_LABELS = {
    'critical':'🔴 بحرانی','high':'🟠 بالا','medium':'🟡 متوسط','low':'🟢 پایین',
}


class TaskDialog(ThemedDialog):
    def __init__(self, db, task=None, parent=None):
        title = "✏️ ویرایش تسک" if task else "✅ تسک جدید"
        super().__init__(title, parent)
        self.db = db; self.task = task
        self.setMinimumWidth(620)
        self.setMinimumHeight(560)
        self.resize(640, 720)
        self._build_form()
        if task: self._fill(task)

    def _build_form(self):
        # همه‌ی فرم داخل یک QScrollArea قرار می‌گیره تا در صفحه‌های کوچیک‌تر
        # هیچ فیلد یا متنی بریده/ناقص نمایش داده نشه و کاربر بتونه اسکرول کنه
        outer = self.content_layout()
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        form_widget = QWidget()
        form_widget.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(form_widget)
        lay.setContentsMargins(24, 20, 24, 24)
        lay.setSpacing(12)

        scroll.setWidget(form_widget)
        outer.addWidget(scroll)

        def lbl(t):
            l = QLabel(t); l.setFont(QFont("Segoe UI Variable",11,QFont.Weight.Bold))
            l.setStyleSheet(f"color:{THEME['text_secondary']};"); return l

        lay.addWidget(lbl("عنوان تسک *"))
        self.title_edit = QLineEdit(); self.title_edit.setPlaceholderText("چه کاری باید انجام بشه؟")
        lay.addWidget(self.title_edit)

        lay.addWidget(lbl("توضیحات"))
        self.desc_edit = QTextEdit(); self.desc_edit.setMaximumHeight(70)
        lay.addWidget(self.desc_edit)

        row1 = QHBoxLayout()
        proj_col = QVBoxLayout(); proj_col.addWidget(lbl("پروژه"))
        self.project_combo = QComboBox()
        self.project_combo.addItem("بدون پروژه", None)
        for p in self.db.fetchall("SELECT id,name FROM projects WHERE archived=0 ORDER BY name"):
            self.project_combo.addItem(p['name'], p['id'])
        proj_col.addWidget(self.project_combo)

        st_col = QVBoxLayout(); st_col.addWidget(lbl("وضعیت"))
        self.status_combo = QComboBox()
        for v,l in [('todo','انجام نشده'),('doing','در حال انجام'),('review','بررسی'),('done','انجام شده')]:
            self.status_combo.addItem(l,v)
        st_col.addWidget(self.status_combo)

        pr_col = QVBoxLayout(); pr_col.addWidget(lbl("اولویت"))
        self.priority_combo = QComboBox()
        for v,l in [('low','🟢 پایین'),('medium','🟡 متوسط'),('high','🟠 بالا'),('critical','🔴 بحرانی')]:
            self.priority_combo.addItem(l,v)
        self.priority_combo.setCurrentIndex(1)
        pr_col.addWidget(self.priority_combo)

        row1.addLayout(proj_col,2); row1.addLayout(st_col,1); row1.addLayout(pr_col,1)
        lay.addLayout(row1)

        row2 = QHBoxLayout()
        due_col = QVBoxLayout(); due_col.addWidget(lbl("📅 مهلت (شمسی)"))
        self.due_date = JalaliDateWidget(); due_col.addWidget(self.due_date)

        est_col = QVBoxLayout(); est_col.addWidget(lbl("⏱️ ساعت تخمینی"))
        self.est_hours = QDoubleSpinBox(); self.est_hours.setRange(0,9999); self.est_hours.setSingleStep(0.5); self.est_hours.setSuffix(" h")
        est_col.addWidget(self.est_hours)

        xp_col = QVBoxLayout(); xp_col.addWidget(lbl("⭐ XP"))
        self.xp_spin = QSpinBox(); self.xp_spin.setRange(1,1000); self.xp_spin.setValue(10)
        xp_col.addWidget(self.xp_spin)

        wt_col = QVBoxLayout(); wt_col.addWidget(lbl("⚖️ وزن"))
        self.weight_spin = QSpinBox(); self.weight_spin.setRange(1,100); self.weight_spin.setValue(1)
        wt_col.addWidget(self.weight_spin)

        row2.addLayout(due_col,2); row2.addLayout(est_col,1); row2.addLayout(xp_col,1); row2.addLayout(wt_col,1)
        lay.addLayout(row2)

        self.daily_check = QCheckBox("🔁 این یک تسک روزانه است (جداگانه در «کارهای روزانه» نمایش داده می‌شود)")
        self.daily_check.setStyleSheet(f"color:{THEME['text_primary']};font-size:12px;")
        lay.addWidget(self.daily_check)

        alarm_row = QHBoxLayout()
        time_col = QVBoxLayout(); time_col.addWidget(lbl("⏰ ساعت مشخص (اختیاری)"))
        self.due_time_edit = QTimeEdit(QTime(9, 0))
        self.due_time_edit.setDisplayFormat("HH:mm")
        time_col.addWidget(self.due_time_edit)
        alarm_row.addLayout(time_col, 1)

        alarm_col = QVBoxLayout(); alarm_col.addWidget(lbl(" "))
        self.alarm_check = QCheckBox("🔔 سر همین ساعت آلارم و نوتیفیکیشن بده")
        self.alarm_check.setStyleSheet(f"color:{THEME['text_primary']};font-size:12px;")
        alarm_col.addWidget(self.alarm_check)
        alarm_row.addLayout(alarm_col, 2)
        lay.addLayout(alarm_row)

        lay.addWidget(lbl("🏷️ تگ‌ها (با کاما)"))
        self.tags_edit = QLineEdit(); self.tags_edit.setPlaceholderText("#backend, #urgent")
        lay.addWidget(self.tags_edit)

        lay.addWidget(lbl("🔗 وابستگی‌ها (این تسک بعد از کدام‌ها شروع شود؟)"))
        self.deps_list = QListWidget(); self.deps_list.setMaximumHeight(80)
        self.deps_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.deps_list.setStyleSheet(f"QListWidget{{background:{THEME['bg_tertiary']};border:1px solid {THEME['border_default']};border-radius:8px;}} QListWidget::item{{padding:4px 8px;color:{THEME['text_primary']};}} QListWidget::item:selected{{background:{THEME['accent']};color:white;}}")
        for t in self.db.fetchall("SELECT id,title FROM tasks ORDER BY created_at DESC LIMIT 40"):
            if not self.task or t['id'] != self.task.get('id'):
                item = QListWidgetItem(t['title'][:50]); item.setData(Qt.ItemDataRole.UserRole,t['id'])
                self.deps_list.addItem(item)
        lay.addWidget(self.deps_list)

        btn_row = QHBoxLayout()
        cancel = QPushButton("انصراف")
        cancel.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_primary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:8px 20px;")
        cancel.clicked.connect(self.reject)
        save = QPushButton("💾 ذخیره تسک"); save.clicked.connect(self._save)
        btn_row.addStretch(); btn_row.addWidget(cancel); btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _fill(self, t):
        self.title_edit.setText(t.get('title',''))
        self.desc_edit.setPlainText(t.get('description','') or '')
        idx = self.status_combo.findData(t.get('status','todo'))
        if idx>=0: self.status_combo.setCurrentIndex(idx)
        idx = self.priority_combo.findData(t.get('priority','medium'))
        if idx>=0: self.priority_combo.setCurrentIndex(idx)
        idx = self.project_combo.findData(t.get('project_id'))
        if idx>=0: self.project_combo.setCurrentIndex(idx)
        if t.get('due_date'): self.due_date.set_from_iso(t['due_date'])
        self.est_hours.setValue(t.get('estimated_hours',0) or 0)
        self.xp_spin.setValue(t.get('xp_reward',10) or 10)
        self.weight_spin.setValue(t.get('weight',1) or 1)
        self.tags_edit.setText(t.get('tags','') or '')
        self.daily_check.setChecked(bool(t.get('is_daily', 0)))
        if t.get('due_time'):
            try:
                hh, mm = t['due_time'].split(':')[:2]
                self.due_time_edit.setTime(QTime(int(hh), int(mm)))
            except Exception:
                pass
        self.alarm_check.setChecked(bool(t.get('alarm_enabled', 0)))
        if t.get('id'):
            deps = self.db.fetchall("SELECT depends_on FROM task_dependencies WHERE task_id=?",(t['id'],))
            dep_ids = {d['depends_on'] for d in deps}
            for i in range(self.deps_list.count()):
                item = self.deps_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) in dep_ids:
                    item.setSelected(True)

    def _save(self):
        title = self.title_edit.text().strip()
        if not title: return
        deps = []
        for i in range(self.deps_list.count()):
            item = self.deps_list.item(i)
            if item.isSelected(): deps.append(item.data(Qt.ItemDataRole.UserRole))
        self.result_data = {
            'title':title,'description':self.desc_edit.toPlainText(),
            'project_id':self.project_combo.currentData(),'status':self.status_combo.currentData(),
            'priority':self.priority_combo.currentData(),'due_date':self.due_date.get_iso(),
            'estimated_hours':self.est_hours.value(),'xp_reward':self.xp_spin.value(),
            'weight':self.weight_spin.value(),'tags':self.tags_edit.text(),'dependencies':deps,
            'is_daily': 1 if self.daily_check.isChecked() else 0,
            'due_time': self.due_time_edit.time().toString("HH:mm"),
            'alarm_enabled': 1 if self.alarm_check.isChecked() else 0,
        }
        self.accept()


class KanbanCard(QFrame):
    complete_clicked = pyqtSignal(int)
    edit_clicked     = pyqtSignal(int)
    delete_clicked   = pyqtSignal(int)

    def __init__(self, task, projects):
        super().__init__(); self.task = task; self._build(projects)

    def _build(self, projects):
        color = PRIORITY_COLORS.get(self.task.get('priority','medium'),THEME['priority_medium'])
        is_done = self.task.get('status')=='done'
        self.setStyleSheet(f"QFrame{{background:{THEME['bg_secondary']};border:1px solid {THEME['border_subtle']};border-left:3px solid {color};border-radius:10px;margin-bottom:5px;}} QFrame:hover{{background:{THEME['bg_hover']};}}")
        lay = QVBoxLayout(self); lay.setContentsMargins(12,10,12,10); lay.setSpacing(6)
        badges = ("🔁 " if self.task.get('is_daily') else "") + ("⏰ " if self.task.get('alarm_enabled') else "")
        title = QLabel(badges + self.task.get('title',''))
        title.setFont(QFont("Segoe UI Variable",12,QFont.Weight.Bold))
        title.setStyleSheet(f"color:{'#64748b' if is_done else THEME['text_primary']};background:transparent;border:none;" + ("text-decoration:line-through;" if is_done else ""))
        title.setWordWrap(True); lay.addWidget(title)
        proj_id = self.task.get('project_id')
        if proj_id and proj_id in projects:
            pb = QLabel(f"📁 {projects[proj_id][:20]}"); pb.setStyleSheet(f"color:{THEME['accent_light']};font-size:10px;background:transparent;border:none;"); lay.addWidget(pb)
        meta = QHBoxLayout()
        due = self.task.get('due_date','')
        if due:
            try:
                d = date.fromisoformat(due[:10]); jy,jm,jd = to_jalali(d.year,d.month,d.day); due_str = format_jalali(jy,jm,jd)
                due_color = THEME['danger'] if d < date.today() and not is_done else THEME['text_tertiary']
            except: due_str = due[:10]; due_color = THEME['text_tertiary']
            dl = QLabel(f"🗓️ {due_str}"); dl.setFont(QFont("Segoe UI Variable",9)); dl.setStyleSheet(f"color:{due_color};background:transparent;border:none;"); meta.addWidget(dl)
        meta.addStretch()
        xp_lbl = QLabel(f"⭐{self.task.get('xp_reward',10)}"); xp_lbl.setFont(QFont("Segoe UI Variable",9,QFont.Weight.Bold)); xp_lbl.setStyleSheet(f"color:{THEME['xp_gold']};background:transparent;border:none;"); meta.addWidget(xp_lbl)
        lay.addLayout(meta)
        if not is_done:
            actions = QHBoxLayout(); actions.setSpacing(4)
            done_btn = QPushButton("✅ انجام شد"); done_btn.setFixedHeight(26)
            done_btn.setStyleSheet(f"QPushButton{{background:{THEME['success']}22;color:{THEME['success']};border:1px solid {THEME['success']}44;border-radius:6px;font-size:10px;font-weight:700;padding:0 8px;}} QPushButton:hover{{background:{THEME['success']};color:white;}}")
            done_btn.clicked.connect(lambda: self.complete_clicked.emit(self.task['id']))
            actions.addWidget(done_btn); actions.addStretch()
            for sym,sig,hc in [('✏️',self.edit_clicked,THEME['bg_hover']),('🗑️',self.delete_clicked,THEME['danger']+'33')]:
                b = QPushButton(sym); b.setFixedSize(26,26)
                b.setStyleSheet(f"QPushButton{{background:transparent;border:none;font-size:12px;}} QPushButton:hover{{background:{hc};border-radius:5px;}}")
                b.clicked.connect(lambda _,s=sig,tid=self.task['id']: s.emit(tid)); actions.addWidget(b)
            lay.addLayout(actions)


class KanbanColumn(QFrame):
    def __init__(self, status, title, color, tasks, projects, on_complete, on_edit, on_delete):
        super().__init__()
        self.setStyleSheet(f"QFrame{{background:{THEME['bg_secondary']};border:1px solid {THEME['border_subtle']};border-radius:14px;min-width:230px;}}")
        self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        lay = QVBoxLayout(self); lay.setContentsMargins(10,10,10,10); lay.setSpacing(0)
        hdr = QHBoxLayout()
        dot = QLabel("●"); dot.setStyleSheet(f"color:{color};font-size:14px;background:transparent;border:none;")
        tl2 = QLabel(title); tl2.setFont(QFont("Segoe UI Variable",12,QFont.Weight.Bold)); tl2.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;")
        cnt = QLabel(str(len(tasks))); cnt.setStyleSheet(f"color:{color};background:{color}22;border-radius:10px;padding:2px 8px;font-size:11px;font-weight:700;border:none;")
        hdr.addWidget(dot); hdr.addWidget(tl2); hdr.addStretch(); hdr.addWidget(cnt)
        lay.addLayout(hdr); lay.addSpacing(8)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame); scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        cards_w = QWidget(); cards_lay = QVBoxLayout(cards_w); cards_lay.setContentsMargins(0,0,0,0); cards_lay.setSpacing(5)
        for task in tasks:
            card = KanbanCard(task,projects)
            card.complete_clicked.connect(on_complete); card.edit_clicked.connect(on_edit); card.delete_clicked.connect(on_delete)
            cards_lay.addWidget(card)
        cards_lay.addStretch(); scroll.setWidget(cards_w); lay.addWidget(scroll)


class TasksView(QWidget):
    def __init__(self, db):
        super().__init__(); self.db = db
        self._view_mode = "kanban"; self._filter_project = None
        self._filter_priority = "all"; self._sort_by = "priority"
        self._build(); self.refresh()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        toolbar = QWidget(); toolbar.setFixedHeight(64)
        toolbar.setStyleSheet(f"background:{THEME['bg_primary']};border-bottom:1px solid {THEME['border_subtle']};")
        tl = QHBoxLayout(toolbar); tl.setContentsMargins(20,0,20,0); tl.setSpacing(10)

        self.kanban_btn = QPushButton("📋 Kanban"); self.kanban_btn.setCheckable(True); self.kanban_btn.setChecked(True)
        self.list_btn   = QPushButton("📃 لیست");   self.list_btn.setCheckable(True)
        for btn in [self.kanban_btn, self.list_btn]:
            btn.setFixedHeight(34)
            btn.setStyleSheet(f"QPushButton{{background:{THEME['bg_tertiary']};color:{THEME['text_secondary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:0 14px;font-size:12px;}} QPushButton:checked{{background:{THEME['accent']};color:white;border-color:{THEME['accent']};font-weight:700;}}")
        self.kanban_btn.clicked.connect(self._to_kanban); self.list_btn.clicked.connect(self._to_list)
        tl.addWidget(self.kanban_btn); tl.addWidget(self.list_btn); tl.addSpacing(10)

        self.proj_filter = QComboBox(); self.proj_filter.addItem("همه پروژه‌ها",None)
        for p in self.db.fetchall("SELECT id,name FROM projects WHERE archived=0 ORDER BY name"):
            self.proj_filter.addItem(p['name'],p['id'])
        self.proj_filter.currentIndexChanged.connect(lambda: self._set_proj(self.proj_filter.currentData()))
        tl.addWidget(self.proj_filter)

        self.pri_filter = QComboBox(); self.pri_filter.addItem("همه اولویت‌ها","all")
        for v,l in [('critical','🔴 بحرانی'),('high','🟠 بالا'),('medium','🟡 متوسط'),('low','🟢 پایین')]:
            self.pri_filter.addItem(l,v)
        self.pri_filter.currentIndexChanged.connect(lambda: self._set_pri(self.pri_filter.currentData()))
        tl.addWidget(self.pri_filter)

        # مرتب‌سازی
        sort_lbl = QLabel("مرتب‌سازی:")
        sort_lbl.setStyleSheet(f"color:{THEME['text_secondary']};font-size:12px;background:transparent;border:none;")
        tl.addWidget(sort_lbl)
        self.sort_combo = QComboBox()
        for v,l in [('priority','اولویت'),('due_date','مهلت تحویل'),('status','وضعیت'),('created_at','تاریخ ایجاد'),('title','عنوان')]:
            self.sort_combo.addItem(l,v)
        self.sort_combo.currentIndexChanged.connect(lambda: self._set_sort(self.sort_combo.currentData()))
        tl.addWidget(self.sort_combo)

        tl.addStretch()
        add_btn = QPushButton("+ تسک جدید"); add_btn.clicked.connect(self._new_task); tl.addWidget(add_btn)
        lay.addWidget(toolbar)

        self.stack = QStackedWidget()
        kanban_w = QWidget()
        self.kanban_scroll = QScrollArea(); self.kanban_scroll.setWidgetResizable(True); self.kanban_scroll.setFrameShape(QFrame.Shape.NoFrame); self.kanban_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.kanban_inner = QWidget(); self.kanban_layout = QHBoxLayout(self.kanban_inner); self.kanban_layout.setContentsMargins(20,18,20,18); self.kanban_layout.setSpacing(14)
        self.kanban_scroll.setWidget(self.kanban_inner)
        kl = QVBoxLayout(kanban_w); kl.setContentsMargins(0,0,0,0); kl.addWidget(self.kanban_scroll)
        self.stack.addWidget(kanban_w)

        list_w = QWidget(); ll = QVBoxLayout(list_w); ll.setContentsMargins(20,16,20,16)
        self.task_table = QTableWidget(); self.task_table.setColumnCount(8)
        self.task_table.setHorizontalHeaderLabels(["عنوان","پروژه","وضعیت","اولویت","مهلت","ساعت","وزن","XP"])
        self.task_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        self.task_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.task_table.verticalHeader().setVisible(False); self.task_table.setShowGrid(False)
        self.task_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.task_table.doubleClicked.connect(self._edit_from_table); ll.addWidget(self.task_table)
        act_row = QHBoxLayout()
        done_btn2 = QPushButton("✅ انجام شد"); done_btn2.setStyleSheet(f"background:{THEME['success']}22;color:{THEME['success']};border:1px solid {THEME['success']}44;border-radius:8px;padding:6px 14px;font-size:12px;font-weight:700;"); done_btn2.clicked.connect(self._done_selected)
        del_btn2  = QPushButton("🗑️ حذف");     del_btn2.setStyleSheet(f"background:{THEME['danger']}22;color:{THEME['danger']};border:1px solid {THEME['danger']}44;border-radius:8px;padding:6px 14px;font-size:12px;"); del_btn2.clicked.connect(self._delete_selected)
        act_row.addWidget(done_btn2); act_row.addWidget(del_btn2); act_row.addStretch(); ll.addLayout(act_row)
        self.stack.addWidget(list_w)
        lay.addWidget(self.stack)

    def _to_kanban(self): self._view_mode="kanban"; self.kanban_btn.setChecked(True); self.list_btn.setChecked(False); self.stack.setCurrentIndex(0)
    def _to_list(self):   self._view_mode="list";   self.list_btn.setChecked(True);   self.kanban_btn.setChecked(False); self.stack.setCurrentIndex(1)
    def _set_proj(self, pid): self._filter_project = pid; self.refresh()
    def _set_pri(self, pri):  self._filter_priority = pri; self.refresh()
    def _set_sort(self, s):   self._sort_by = s; self.refresh()

    def _get_tasks(self):
        conditions = []; params = []
        if self._filter_project is not None:
            conditions.append("project_id=?"); params.append(self._filter_project)
        if self._filter_priority != "all":
            conditions.append("priority=?"); params.append(self._filter_priority)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        # Build ORDER BY
        sort_map = {
            'priority': "CASE priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END",
            'due_date':  "CASE WHEN due_date IS NULL OR due_date='' THEN '9999' ELSE due_date END ASC",
            'status':    "CASE status WHEN 'doing' THEN 0 WHEN 'review' THEN 1 WHEN 'todo' THEN 2 ELSE 3 END",
            'created_at':"created_at DESC",
            'title':     "title ASC",
        }
        order = sort_map.get(self._sort_by, sort_map['priority'])
        return self.db.fetchall(f"SELECT * FROM tasks {where} ORDER BY {order}", params)

    def refresh(self):
        tasks = self._get_tasks()
        projects = {p['id']:p['name'] for p in self.db.fetchall("SELECT id,name FROM projects")}
        self._update_kanban(tasks, projects)
        self._update_list(tasks, projects)

    def _update_kanban(self, tasks, projects):
        while self.kanban_layout.count():
            item = self.kanban_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for status,title,color in KANBAN_COLS:
            col_tasks = [t for t in tasks if t.get('status')==status]
            col = KanbanColumn(status,f"{title} ({len(col_tasks)})",color,col_tasks,projects,self._complete_task,self._edit_task,self._delete_task)
            self.kanban_layout.addWidget(col)

    def _update_list(self, tasks, projects):
        status_icons = {'todo':'📋','doing':'⚡','review':'👁️','done':'✅'}
        self.task_table.setRowCount(len(tasks))
        for r,task in enumerate(tasks):
            due = task.get('due_date','')
            if due:
                try:
                    d = date.fromisoformat(due[:10]); jy,jm,jd = to_jalali(d.year,d.month,d.day)
                    due_str = format_jalali(jy,jm,jd)
                    due_color = THEME['danger'] if d<date.today() and task.get('status')!='done' else THEME['text_secondary']
                except: due_str = due[:10]; due_color = THEME['text_secondary']
            else:
                due_str = '—'; due_color = THEME['text_tertiary']
            pc = PRIORITY_COLORS.get(task.get('priority','medium'),THEME['warning'])
            cells = [
                (task.get('title',''),THEME['text_primary']),
                (projects.get(task.get('project_id'),'—'),THEME['text_secondary']),
                (f"{status_icons.get(task.get('status','todo'),'')} {task.get('status','')}",THEME['success'] if task.get('status')=='done' else THEME['text_primary']),
                (PRIORITY_LABELS.get(task.get('priority','medium'),''),pc),
                (due_str,due_color),
                (f"{task.get('estimated_hours',0)}h",THEME['text_secondary']),
                (str(task.get('weight',1)),THEME['accent_light']),
                (f"⭐{task.get('xp_reward',10)}",THEME['xp_gold']),
            ]
            for col,(text,fc) in enumerate(cells):
                item = QTableWidgetItem(text); item.setForeground(QColor(fc))
                item.setFlags(item.flags()&~Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole,task['id']); self.task_table.setItem(r,col,item)
            self.task_table.setRowHeight(r,42)

    def _new_task(self):
        dlg = TaskDialog(self.db, parent=self)
        if dlg.exec():
            d = dlg.result_data
            cur = self.db.execute("INSERT INTO tasks(title,description,project_id,status,priority,due_date,estimated_hours,xp_reward,weight,tags,is_daily,due_time,alarm_enabled,alarm_notified) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,0)",(d['title'],d['description'],d['project_id'],d['status'],d['priority'],d['due_date'],d['estimated_hours'],d['xp_reward'],d['weight'],d['tags'],d['is_daily'],d['due_time'],d['alarm_enabled']))
            tid = cur.lastrowid
            for dep_id in d.get('dependencies',[]):
                try: self.db.execute("INSERT INTO task_dependencies(task_id,depends_on) VALUES(?,?)",(tid,dep_id))
                except: pass
            self.refresh()

    def _edit_task(self, task_id):
        task = self.db.fetchone("SELECT * FROM tasks WHERE id=?",(task_id,))
        if not task: return
        dlg = TaskDialog(self.db, task=task, parent=self)
        if dlg.exec():
            d = dlg.result_data
            # اگر تاریخ/ساعت مهلت یا وضعیت آلارم تغییر کرده، دوباره مجاز به اعلان شود
            notified = task.get('alarm_notified', 0) or 0
            if (task.get('due_date') != d['due_date'] or
                    (task.get('due_time') or '') != (d['due_time'] or '') or
                    (task.get('alarm_enabled') or 0) != d['alarm_enabled']):
                notified = 0
            self.db.execute("UPDATE tasks SET title=?,description=?,project_id=?,status=?,priority=?,due_date=?,estimated_hours=?,xp_reward=?,weight=?,tags=?,is_daily=?,due_time=?,alarm_enabled=?,alarm_notified=?,updated_at=datetime('now') WHERE id=?",(d['title'],d['description'],d['project_id'],d['status'],d['priority'],d['due_date'],d['estimated_hours'],d['xp_reward'],d['weight'],d['tags'],d['is_daily'],d['due_time'],d['alarm_enabled'],notified,task_id))
            self.db.execute("DELETE FROM task_dependencies WHERE task_id=?",(task_id,))
            for dep_id in d.get('dependencies',[]):
                try: self.db.execute("INSERT INTO task_dependencies(task_id,depends_on) VALUES(?,?)",(task_id,dep_id))
                except: pass
            self.refresh()

    def _edit_from_table(self, idx):
        item = self.task_table.item(idx.row(),0)
        if item:
            tid = item.data(Qt.ItemDataRole.UserRole)
            if tid: self._edit_task(tid)

    def _complete_task(self, task_id):
        task = self.db.fetchone("SELECT * FROM tasks WHERE id=?",(task_id,))
        if not task: return
        xp = task.get('xp_reward',10)
        self.db.execute("UPDATE tasks SET status='done',completed_at=datetime('now') WHERE id=?",(task_id,))
        self.db.execute("UPDATE user_stats SET total_xp=total_xp+?,tasks_completed=tasks_completed+1",(xp,))
        self.db.execute("INSERT INTO xp_log(amount,reason) VALUES(?,?)",(xp,f"تسک تکمیل شد: {task.get('title','')}"))
        stats = self.db.fetchone("SELECT * FROM user_stats LIMIT 1")
        if stats:
            from ui.widgets.xp_widget import xp_for_level
            if stats['total_xp'] >= xp_for_level(stats['level']):
                self.db.execute("UPDATE user_stats SET level=level+1")
        self._show_xp_toast(xp); self.refresh()

    def _done_selected(self):
        item = self.task_table.item(self.task_table.currentRow(),0)
        if item:
            tid = item.data(Qt.ItemDataRole.UserRole)
            if tid: self._complete_task(tid)

    def _delete_task(self, task_id):
        msg = QMessageBox(self); msg.setWindowTitle("حذف تسک"); msg.setText("آیا مطمئنید؟")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        msg.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};")
        if msg.exec()==QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM tasks WHERE id=?",(task_id,)); self.refresh()

    def _delete_selected(self):
        item = self.task_table.item(self.task_table.currentRow(),0)
        if item:
            tid = item.data(Qt.ItemDataRole.UserRole)
            if tid: self._delete_task(tid)

    def _show_xp_toast(self, xp):
        toast = QLabel(f"🎉 +{xp} XP کسب کردید!", self)
        toast.setStyleSheet(f"background:{THEME['success']};color:white;border-radius:12px;padding:12px 24px;font-size:14px;font-weight:700;")
        toast.setAlignment(Qt.AlignmentFlag.AlignCenter); toast.adjustSize()
        toast.move(self.width()-toast.width()-20, self.height()-toast.height()-20)
        toast.show(); toast.raise_()
        QTimer.singleShot(2500, toast.deleteLater)
