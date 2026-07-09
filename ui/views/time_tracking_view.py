"""Time Tracking + Pomodoro View"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QComboBox, QDialog, QLineEdit,
    QDoubleSpinBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, date, timedelta
from ui.theme import THEME

POMODORO_WORK = 25*60; POMODORO_BREAK = 5*60

class PomodoroWidget(QFrame):
    def __init__(self, db):
        super().__init__(); self.db=db; self._seconds=POMODORO_WORK; self._running=False; self._is_break=False
        self._timer=QTimer(); self._timer.timeout.connect(self._tick); self._sessions=0; self._start_time=None
        self._selected_task_id=None; self._build()

    def _build(self):
        self.setStyleSheet(f"QFrame{{background:{THEME['bg_secondary']};border:1px solid {THEME['border_subtle']};border-radius:16px;}}")
        lay=QVBoxLayout(self); lay.setContentsMargins(28,24,28,24); lay.setSpacing(14); lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_lbl=QLabel("🍅 پومودورو — تمرکز"); self.mode_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_lbl.setStyleSheet(f"color:{THEME['accent_light']};font-size:13px;font-weight:700;background:transparent;border:none;"); lay.addWidget(self.mode_lbl)
        self.clock_lbl=QLabel("25:00"); self.clock_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock_lbl.setFont(QFont("Segoe UI Variable",56,QFont.Weight.Bold))
        self.clock_lbl.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;"); lay.addWidget(self.clock_lbl)
        self.session_lbl=QLabel("جلسه ۱"); self.session_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.session_lbl.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:12px;background:transparent;border:none;"); lay.addWidget(self.session_lbl)
        task_row=QHBoxLayout()
        tl=QLabel("تسک:"); tl.setStyleSheet(f"color:{THEME['text_secondary']};font-size:12px;background:transparent;border:none;")
        self.task_combo=QComboBox(); self.task_combo.addItem("بدون تسک",None)
        for t in self.db.fetchall("SELECT id,title FROM tasks WHERE status!='done' LIMIT 30"):
            self.task_combo.addItem(t['title'][:36],t['id'])
        self.task_combo.currentIndexChanged.connect(lambda: setattr(self,'_selected_task_id',self.task_combo.currentData()))
        task_row.addWidget(tl); task_row.addWidget(self.task_combo,1); lay.addLayout(task_row)
        btn_row=QHBoxLayout(); btn_row.setSpacing(12)
        self.start_btn=QPushButton("▶ شروع"); self.start_btn.setFixedHeight(44)
        self.start_btn.setFont(QFont("Segoe UI Variable",13,QFont.Weight.Bold))
        self.start_btn.setStyleSheet(f"QPushButton{{background:{THEME['success']};color:white;border-radius:12px;border:none;padding:0 24px;}} QPushButton:hover{{background:#059669;}}")
        self.start_btn.clicked.connect(self._toggle)
        reset_btn=QPushButton("↺ ریست"); reset_btn.setFixedHeight(44)
        reset_btn.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_secondary']};border:1px solid {THEME['border_default']};border-radius:12px;padding:0 18px;")
        reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(self.start_btn); btn_row.addWidget(reset_btn); lay.addLayout(btn_row)
        self.dots_row=QHBoxLayout(); self.dots_row.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addLayout(self.dots_row)
        self._draw_dots()

    def _draw_dots(self):
        while self.dots_row.count():
            item=self.dots_row.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for i in range(4):
            dot=QLabel("●" if i<self._sessions else "○"); dot.setFont(QFont("Segoe UI Variable",16))
            dot.setStyleSheet(f"color:{THEME['streak_fire'] if i<self._sessions else THEME['text_tertiary']};background:transparent;border:none;")
            self.dots_row.addWidget(dot)

    def _toggle(self):
        if self._running:
            self._timer.stop(); self._running=False; self.start_btn.setText("▶ ادامه")
            self.start_btn.setStyleSheet(f"QPushButton{{background:{THEME['warning']};color:white;border-radius:12px;border:none;padding:0 24px;}}")
        else:
            self._running=True; self._start_time=datetime.now(); self._timer.start(1000)
            self.start_btn.setText("⏸ مکث"); self.start_btn.setStyleSheet(f"QPushButton{{background:{THEME['danger']};color:white;border-radius:12px;border:none;padding:0 24px;}} QPushButton:hover{{background:#dc2626;}}")

    def _tick(self):
        self._seconds-=1; m,s=divmod(max(0,self._seconds),60); self.clock_lbl.setText(f"{m:02d}:{s:02d}")
        if self._seconds<=0: self._timer.stop(); self._running=False; self._on_done()

    def _on_done(self):
        if not self._is_break:
            dur=POMODORO_WORK/60
            if self._start_time:
                self.db.execute("INSERT INTO time_entries(task_id,description,start_time,end_time,duration_minutes,is_pomodoro) VALUES(?,?,?,?,?,1)",(self._selected_task_id,"پومودورو",self._start_time.isoformat(),datetime.now().isoformat(),dur))
                self.db.execute("UPDATE user_stats SET total_xp=total_xp+15"); self.db.execute("INSERT INTO xp_log(amount,reason) VALUES(15,'پومودورو کامل شد')")
            self._sessions=(self._sessions+1)%4; self._draw_dots(); self._is_break=True; self._seconds=POMODORO_BREAK
            self.mode_lbl.setText("☕ استراحت — ۵ دقیقه"); self.clock_lbl.setStyleSheet(f"color:{THEME['success']};background:transparent;border:none;")
        else:
            self._is_break=False; self._seconds=POMODORO_WORK; self.mode_lbl.setText("🍅 پومودورو — تمرکز")
            self.clock_lbl.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;")
        m,s=divmod(self._seconds,60); self.clock_lbl.setText(f"{m:02d}:{s:02d}")
        self.start_btn.setText("▶ شروع"); self.start_btn.setStyleSheet(f"QPushButton{{background:{THEME['success']};color:white;border-radius:12px;border:none;padding:0 24px;}} QPushButton:hover{{background:#059669;}}")

    def _reset(self):
        self._timer.stop(); self._running=False; self._is_break=False; self._seconds=POMODORO_WORK
        self.clock_lbl.setText("25:00"); self.clock_lbl.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;")
        self.mode_lbl.setText("🍅 پومودورو — تمرکز"); self.start_btn.setText("▶ شروع")
        self.start_btn.setStyleSheet(f"QPushButton{{background:{THEME['success']};color:white;border-radius:12px;border:none;padding:0 24px;}} QPushButton:hover{{background:#059669;}}")

class TimeTrackingView(QWidget):
    def __init__(self, db):
        super().__init__(); self.db=db; self._build(); self.refresh()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        toolbar=QWidget(); toolbar.setFixedHeight(64)
        toolbar.setStyleSheet(f"background:{THEME['bg_primary']};border-bottom:1px solid {THEME['border_subtle']};")
        tl=QHBoxLayout(toolbar); tl.setContentsMargins(24,0,24,0); tl.addStretch()
        manual_btn=QPushButton("+ ثبت دستی"); manual_btn.clicked.connect(self._manual)
        tl.addWidget(manual_btn); lay.addWidget(toolbar)
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        container=QWidget(); cl=QVBoxLayout(container); cl.setContentsMargins(24,20,24,20); cl.setSpacing(18)
        top_row=QHBoxLayout(); top_row.setSpacing(18)
        self.pomodoro=PomodoroWidget(self.db); top_row.addWidget(self.pomodoro,1)
        today_card=QFrame(); today_card.setStyleSheet(f"QFrame{{background:{THEME['bg_secondary']};border:1px solid {THEME['border_subtle']};border-radius:16px;}}")
        self.today_lay=QVBoxLayout(today_card); self.today_lay.setContentsMargins(24,18,24,18); self.today_lay.setSpacing(14)
        top_row.addWidget(today_card,1); cl.addLayout(top_row)
        log_lbl=QLabel("📋 لاگ زمان"); log_lbl.setFont(QFont("Segoe UI Variable",13,QFont.Weight.Bold)); log_lbl.setStyleSheet(f"color:{THEME['text_primary']};"); cl.addWidget(log_lbl)
        self.table=QTableWidget(); self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["تاریخ","تسک","توضیحات","مدت","نوع"])
        self.table.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False); self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); cl.addWidget(self.table); cl.addStretch()
        scroll.setWidget(container); lay.addWidget(scroll)

    def refresh(self):
        while self.today_lay.count():
            item=self.today_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        title=QLabel("📊 امروز"); title.setFont(QFont("Segoe UI Variable",13,QFont.Weight.Bold)); title.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;"); self.today_lay.addWidget(title)
        today_str=date.today().isoformat()
        total=self.db.fetchone("SELECT SUM(duration_minutes) as s FROM time_entries WHERE date(start_time)=?",(today_str,))
        pomo=self.db.fetchone("SELECT COUNT(*) as c FROM time_entries WHERE date(start_time)=? AND is_pomodoro=1",(today_str,))
        tm=int(total['s'] or 0) if total else 0; h,m=divmod(tm,60)
        for icon,val,label,color in [("⏱️",f"{h}h {m}m","زمان کل",THEME['accent']),("🍅",str(pomo['c'] if pomo else 0),"پومودورو",THEME['streak_fire'])]:
            row=QHBoxLayout()
            ic=QLabel(icon); ic.setFont(QFont("Segoe UI Emoji",18)); ic.setStyleSheet(f"background:{color}22;border-radius:8px;padding:6px;border:1px solid {color}44;"); ic.setFixedSize(38,38); ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info=QVBoxLayout(); info.setSpacing(2)
            vl=QLabel(val); vl.setFont(QFont("Segoe UI Variable",18,QFont.Weight.Bold)); vl.setStyleSheet(f"color:{color};background:transparent;border:none;")
            ll=QLabel(label); ll.setFont(QFont("Segoe UI Variable",10)); ll.setStyleSheet(f"color:{THEME['text_secondary']};background:transparent;border:none;")
            info.addWidget(vl); info.addWidget(ll); row.addWidget(ic); row.addSpacing(10); row.addLayout(info); row.addStretch(); self.today_lay.addLayout(row)
        self.today_lay.addStretch()
        entries=self.db.fetchall("SELECT te.*,t.title as task_title FROM time_entries te LEFT JOIN tasks t ON te.task_id=t.id ORDER BY te.created_at DESC LIMIT 60")
        self.table.setRowCount(len(entries))
        for row,e in enumerate(entries):
            dm=int(e.get('duration_minutes',0)); h2,m2=divmod(dm,60); dur_str=f"{h2}h {m2}m" if h2 else f"{m2}m"
            cells=[(str(e.get('start_time',''))[:10],THEME['text_tertiary']),(e.get('task_title') or '—',THEME['text_primary']),(e.get('description','') or '',THEME['text_secondary']),(dur_str,THEME['accent_light']),("🍅 پومودورو" if e.get('is_pomodoro') else "✍️ دستی",THEME['streak_fire'] if e.get('is_pomodoro') else THEME['text_secondary'])]
            for col,(text,fc) in enumerate(cells):
                item=QTableWidgetItem(text); item.setForeground(QColor(fc)); item.setFlags(item.flags()&~Qt.ItemFlag.ItemIsEditable); self.table.setItem(row,col,item)
            self.table.setRowHeight(row,42)

    def _manual(self):
        dlg=QDialog(self); dlg.setWindowTitle("ثبت دستی"); dlg.setFixedWidth(380)
        dlg.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};")
        lay=QVBoxLayout(dlg); lay.setContentsMargins(24,24,24,24); lay.setSpacing(12)
        def lbl(t):
            l=QLabel(t); l.setFont(QFont("Segoe UI Variable",11,QFont.Weight.Bold)); l.setStyleSheet(f"color:{THEME['text_secondary']};"); return l
        lay.addWidget(lbl("تسک"))
        tc=QComboBox(); tc.addItem("بدون تسک",None)
        for t in self.db.fetchall("SELECT id,title FROM tasks ORDER BY created_at DESC LIMIT 50"): tc.addItem(t['title'][:36],t['id'])
        lay.addWidget(tc)
        lay.addWidget(lbl("توضیحات"))
        dc=QLineEdit(); dc.setPlaceholderText("بابت چه کاری?"); lay.addWidget(dc)
        lay.addWidget(lbl("مدت زمان (دقیقه)"))
        sp=QDoubleSpinBox(); sp.setRange(1,1440); sp.setValue(30); sp.setSuffix(" دقیقه"); sp.setFont(QFont("Segoe UI Variable",14)); lay.addWidget(sp)
        btn_row=QHBoxLayout()
        cancel=QPushButton("انصراف"); cancel.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_primary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:8px 18px;"); cancel.clicked.connect(dlg.reject)
        save=QPushButton("⏱️ ثبت"); save.clicked.connect(dlg.accept)
        btn_row.addStretch(); btn_row.addWidget(cancel); btn_row.addWidget(save); lay.addLayout(btn_row)
        if dlg.exec()==QDialog.DialogCode.Accepted:
            now=datetime.now(); start=now-timedelta(minutes=sp.value())
            self.db.execute("INSERT INTO time_entries(task_id,description,start_time,end_time,duration_minutes,is_pomodoro) VALUES(?,?,?,?,?,0)",(tc.currentData(),dc.text(),start.isoformat(),now.isoformat(),sp.value()))
            if tc.currentData(): self.db.execute("UPDATE tasks SET actual_hours=actual_hours+? WHERE id=?",(sp.value()/60,tc.currentData()))
            self.refresh()
