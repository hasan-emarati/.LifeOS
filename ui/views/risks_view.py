"""Risks View v2"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QLineEdit, QTextEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from ui.theme import THEME
PROB_MAP={'low':('پایین',THEME['priority_low']),'medium':('متوسط',THEME['priority_medium']),'high':('بالا',THEME['priority_high'])}
STATUS_MAP={'open':('باز',THEME['danger']),'mitigated':('کاهش یافته',THEME['warning']),'closed':('بسته',THEME['success'])}

class RiskDialog(QDialog):
    def __init__(self, db, risk=None, parent=None):
        super().__init__(parent); self.db=db; self.risk=risk
        self.setWindowTitle("ریسک جدید" if not risk else "ویرایش"); self.setMinimumWidth(460)
        self.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};")
        lay=QVBoxLayout(self); lay.setContentsMargins(24,24,24,24); lay.setSpacing(12)
        def lbl(t):
            l=QLabel(t); l.setFont(QFont("Segoe UI Variable",11,QFont.Weight.Bold)); l.setStyleSheet(f"color:{THEME['text_secondary']};"); return l
        lay.addWidget(lbl("عنوان ریسک *"))
        self.title_edit=QLineEdit(); self.title_edit.setPlaceholderText("چه خطری وجود دارد?"); lay.addWidget(self.title_edit)
        lay.addWidget(lbl("توضیحات"))
        self.desc_edit=QTextEdit(); self.desc_edit.setMaximumHeight(70); lay.addWidget(self.desc_edit)
        row1=QHBoxLayout()
        proj_col=QVBoxLayout(); proj_col.addWidget(lbl("پروژه *"))
        self.proj_combo=QComboBox()
        for p in self.db.fetchall("SELECT id,name FROM projects WHERE archived=0"): self.proj_combo.addItem(p['name'],p['id'])
        proj_col.addWidget(self.proj_combo)
        prob_col=QVBoxLayout(); prob_col.addWidget(lbl("احتمال"))
        self.prob_combo=QComboBox()
        for v,(n,_) in PROB_MAP.items(): self.prob_combo.addItem(n,v)
        self.prob_combo.setCurrentIndex(1); prob_col.addWidget(self.prob_combo)
        imp_col=QVBoxLayout(); imp_col.addWidget(lbl("تأثیر"))
        self.imp_combo=QComboBox()
        for v,(n,_) in PROB_MAP.items(): self.imp_combo.addItem(n,v)
        self.imp_combo.setCurrentIndex(1); imp_col.addWidget(self.imp_combo)
        row1.addLayout(proj_col,2); row1.addLayout(prob_col,1); row1.addLayout(imp_col,1); lay.addLayout(row1)
        lay.addWidget(lbl("راهکار پیشگیری"))
        self.mit_edit=QTextEdit(); self.mit_edit.setMaximumHeight(80); lay.addWidget(self.mit_edit)
        lay.addWidget(lbl("وضعیت"))
        self.status_combo=QComboBox()
        for v,(n,_) in STATUS_MAP.items(): self.status_combo.addItem(n,v)
        lay.addWidget(self.status_combo)
        btn_row=QHBoxLayout()
        cancel=QPushButton("انصراف"); cancel.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_primary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:8px 20px;"); cancel.clicked.connect(self.reject)
        save=QPushButton("⚠️ ذخیره"); save.clicked.connect(self._save)
        btn_row.addStretch(); btn_row.addWidget(cancel); btn_row.addWidget(save); lay.addLayout(btn_row)
        if risk:
            self.title_edit.setText(risk.get('title','')); self.desc_edit.setPlainText(risk.get('description','') or ''); self.mit_edit.setPlainText(risk.get('mitigation','') or '')
            idx=self.prob_combo.findData(risk.get('probability','medium'))
            if idx>=0: self.prob_combo.setCurrentIndex(idx)
            idx=self.imp_combo.findData(risk.get('impact','medium'))
            if idx>=0: self.imp_combo.setCurrentIndex(idx)
            idx=self.status_combo.findData(risk.get('status','open'))
            if idx>=0: self.status_combo.setCurrentIndex(idx)
            idx=self.proj_combo.findData(risk.get('project_id'))
            if idx>=0: self.proj_combo.setCurrentIndex(idx)

    def _save(self):
        title=self.title_edit.text().strip()
        if not title: return
        self.result_data={'title':title,'description':self.desc_edit.toPlainText(),'mitigation':self.mit_edit.toPlainText(),'probability':self.prob_combo.currentData(),'impact':self.imp_combo.currentData(),'status':self.status_combo.currentData(),'project_id':self.proj_combo.currentData()}
        self.accept()

class RisksView(QWidget):
    def __init__(self, db):
        super().__init__(); self.db=db; self._build(); self.refresh()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        toolbar=QWidget(); toolbar.setFixedHeight(64)
        toolbar.setStyleSheet(f"background:{THEME['bg_primary']};border-bottom:1px solid {THEME['border_subtle']};")
        tl=QHBoxLayout(toolbar); tl.setContentsMargins(20,0,20,0); tl.setSpacing(12)
        self.status_filter=QComboBox(); self.status_filter.addItem("همه","all")
        for v,(n,_) in STATUS_MAP.items(): self.status_filter.addItem(n,v)
        self.status_filter.currentIndexChanged.connect(self.refresh); tl.addWidget(self.status_filter); tl.addStretch()
        add_btn=QPushButton("⚠️ ریسک جدید"); add_btn.clicked.connect(self._new); tl.addWidget(add_btn)
        lay.addWidget(toolbar)
        self.strip=QWidget(); self.strip.setFixedHeight(72)
        self.strip.setStyleSheet(f"background:{THEME['bg_secondary']};border-bottom:1px solid {THEME['border_subtle']};")
        self.strip_lay=QHBoxLayout(self.strip); self.strip_lay.setContentsMargins(24,12,24,12)
        lay.addWidget(self.strip)
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        content=QWidget(); cl=QVBoxLayout(content); cl.setContentsMargins(20,16,20,16)
        self.table=QTableWidget(); self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["پروژه","عنوان ریسک","احتمال","تأثیر","امتیاز","وضعیت","عملیات"])
        self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False); self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); cl.addWidget(self.table)
        scroll.setWidget(content); lay.addWidget(scroll)

    def _score(self, prob, imp):
        m={'low':1,'medium':2,'high':3}; return m.get(prob,1)*m.get(imp,1)

    def refresh(self):
        while self.strip_lay.count():
            item=self.strip_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        all_r=self.db.fetchall("SELECT * FROM risks"); open_r=[r for r in all_r if r.get('status')=='open']
        high_r=[r for r in open_r if self._score(r.get('probability'),r.get('impact'))>=6]
        med_r=[r for r in open_r if self._score(r.get('probability'),r.get('impact')) in (3,4)]
        low_r=[r for r in open_r if self._score(r.get('probability'),r.get('impact'))<=2]
        for label,count,color in [("🔴 بحرانی",len(high_r),THEME['danger']),("🟡 متوسط",len(med_r),THEME['warning']),("🟢 پایین",len(low_r),THEME['success'])]:
            col=QVBoxLayout()
            v=QLabel(str(count)); v.setFont(QFont("Segoe UI Variable",20,QFont.Weight.Bold)); v.setStyleSheet(f"color:{color};background:transparent;border:none;"); v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l=QLabel(label); l.setFont(QFont("Segoe UI Variable",10)); l.setStyleSheet(f"color:{THEME['text_secondary']};background:transparent;border:none;"); l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(v); col.addWidget(l); self.strip_lay.addLayout(col)
            sep=QFrame(); sep.setFixedWidth(1); sep.setStyleSheet(f"background:{THEME['border_subtle']};"); self.strip_lay.addWidget(sep)
        self.strip_lay.addStretch()
        fstatus=self.status_filter.currentData() if hasattr(self,'status_filter') else 'all'
        risks=self.db.fetchall("SELECT * FROM risks ORDER BY created_at DESC") if fstatus=='all' else self.db.fetchall("SELECT * FROM risks WHERE status=? ORDER BY created_at DESC",(fstatus,))
        projs={p['id']:p['name'] for p in self.db.fetchall("SELECT id,name FROM projects")}
        self.table.setRowCount(len(risks))
        for row,r in enumerate(risks):
            pn,pc=PROB_MAP.get(r.get('probability','medium'),('متوسط',THEME['warning']))
            sn,sc=STATUS_MAP.get(r.get('status','open'),('باز',THEME['danger']))
            score=self._score(r.get('probability'),r.get('impact'))
            sc2=['#22c55e','#84cc16','#eab308','#f97316','','#ef4444','','','#dc2626']
            score_color=sc2[score-1] if 1<=score<=9 and sc2[score-1] else THEME['warning']
            cells=[(projs.get(r.get('project_id'),'—'),THEME['text_secondary']),(r.get('title',''),THEME['text_primary']),(pn,pc),(pn,pc),(f"{'★'*score} {score}",score_color),(sn,sc),('',THEME['text_secondary'])]
            for col_i,(text,fc) in enumerate(cells):
                item=QTableWidgetItem(text); item.setForeground(QColor(fc)); item.setFlags(item.flags()&~Qt.ItemFlag.ItemIsEditable); item.setData(Qt.ItemDataRole.UserRole,r['id']); self.table.setItem(row,col_i,item)
            aw=QWidget(); al=QHBoxLayout(aw); al.setContentsMargins(4,2,4,2); al.setSpacing(6)
            eb=QPushButton("✏️"); eb.setFixedSize(28,28); eb.setStyleSheet("QPushButton{background:transparent;border:none;font-size:12px;} QPushButton:hover{background:#333;border-radius:5px;}"); eb.clicked.connect(lambda _,rv=r:self._edit(rv))
            db=QPushButton("🗑️"); db.setFixedSize(28,28); db.setStyleSheet(f"QPushButton{{background:transparent;border:none;font-size:12px;}} QPushButton:hover{{background:{THEME['danger']}33;border-radius:5px;}}"); db.clicked.connect(lambda _,rid=r['id']:self._delete(rid))
            al.addWidget(eb); al.addWidget(db); self.table.setCellWidget(row,6,aw); self.table.setRowHeight(row,46)

    def _new(self):
        dlg=RiskDialog(self.db,parent=self)
        if dlg.exec()==QDialog.DialogCode.Accepted:
            d=dlg.result_data; self.db.execute("INSERT INTO risks(title,description,probability,impact,mitigation,status,project_id) VALUES(?,?,?,?,?,?,?)",(d['title'],d['description'],d['probability'],d['impact'],d['mitigation'],d['status'],d['project_id'])); self.refresh()
    def _edit(self,risk):
        dlg=RiskDialog(self.db,risk=risk,parent=self)
        if dlg.exec()==QDialog.DialogCode.Accepted:
            d=dlg.result_data; self.db.execute("UPDATE risks SET title=?,description=?,probability=?,impact=?,mitigation=?,status=?,project_id=? WHERE id=?",(d['title'],d['description'],d['probability'],d['impact'],d['mitigation'],d['status'],d['project_id'],risk['id'])); self.refresh()
    def _delete(self,rid):
        msg=QMessageBox(self); msg.setWindowTitle("حذف"); msg.setText("آیا مطمئنید?"); msg.setStandardButtons(QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No); msg.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};")
        if msg.exec()==QMessageBox.StandardButton.Yes: self.db.execute("DELETE FROM risks WHERE id=?",(rid,)); self.refresh()
