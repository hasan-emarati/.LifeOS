"""Ideas View v2"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QLineEdit, QTextEdit, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ui.theme import THEME

IDEA_STATUSES=[('raw','💭 خام','#64748b'),('review','🔍 بررسی',THEME['warning']),('approved','✅ تایید',THEME['success']),('doing','🚀 اجرا',THEME['accent']),('done','🏆 انجام شد',THEME['xp_gold'])]
SM={k:(l,c) for k,l,c in IDEA_STATUSES}

class IdeaDialog(QDialog):
    def __init__(self, db, idea=None, parent=None):
        super().__init__(parent)
        self.db=db; self.setWindowTitle("ایده جدید" if not idea else "ویرایش")
        self.setMinimumWidth(440); self.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};")
        lay=QVBoxLayout(self); lay.setContentsMargins(24,24,24,24); lay.setSpacing(12)
        def lbl(t):
            l=QLabel(t); l.setFont(QFont("Segoe UI Variable",11,QFont.Weight.Bold)); l.setStyleSheet(f"color:{THEME['text_secondary']};"); return l
        lay.addWidget(lbl("عنوان *"))
        self.title_edit=QLineEdit(); self.title_edit.setPlaceholderText("ایده‌ات را بنویس..."); lay.addWidget(self.title_edit)
        lay.addWidget(lbl("توضیحات"))
        self.desc_edit=QTextEdit(); self.desc_edit.setMaximumHeight(100); lay.addWidget(self.desc_edit)
        row=QHBoxLayout()
        cat_col=QVBoxLayout(); cat_col.addWidget(lbl("دسته‌بندی"))
        self.cat_combo=QComboBox()
        for v,n in [('general','عمومی'),('product','محصول'),('research','تحقیق'),('business','کسب‌وکار'),('technical','فنی')]:
            self.cat_combo.addItem(n,v)
        cat_col.addWidget(self.cat_combo)
        st_col=QVBoxLayout(); st_col.addWidget(lbl("وضعیت"))
        self.status_combo=QComboBox()
        for v,l,_ in IDEA_STATUSES: self.status_combo.addItem(l,v)
        st_col.addWidget(self.status_combo)
        row.addLayout(cat_col); row.addLayout(st_col); lay.addLayout(row)
        btn_row=QHBoxLayout()
        cancel=QPushButton("انصراف"); cancel.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_primary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:8px 18px;"); cancel.clicked.connect(self.reject)
        save=QPushButton("💡 ذخیره"); save.clicked.connect(self._save)
        btn_row.addStretch(); btn_row.addWidget(cancel); btn_row.addWidget(save); lay.addLayout(btn_row)
        if idea:
            self.title_edit.setText(idea.get('title','')); self.desc_edit.setPlainText(idea.get('description','') or '')
            idx=self.cat_combo.findData(idea.get('category','general'))
            if idx>=0: self.cat_combo.setCurrentIndex(idx)
            idx=self.status_combo.findData(idea.get('status','raw'))
            if idx>=0: self.status_combo.setCurrentIndex(idx)

    def _save(self):
        title=self.title_edit.text().strip()
        if not title: return
        self.result_data={'title':title,'description':self.desc_edit.toPlainText(),'category':self.cat_combo.currentData(),'status':self.status_combo.currentData()}
        self.accept()

class IdeasView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db=db; self._filter='all'; self._build(); self.refresh()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        toolbar=QWidget(); toolbar.setFixedHeight(64)
        toolbar.setStyleSheet(f"background:{THEME['bg_primary']};border-bottom:1px solid {THEME['border_subtle']};")
        tl=QHBoxLayout(toolbar); tl.setContentsMargins(20,0,20,0); tl.setSpacing(8)
        self._filter_btns={}
        for val,label in [('all','همه')]+[(k,l) for k,l,_ in IDEA_STATUSES]:
            btn=QPushButton(label); btn.setCheckable(True); btn.setChecked(val=='all')
            btn.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{THEME['text_secondary']};padding:5px 12px;border-radius:8px;font-size:12px;}} QPushButton:checked{{background:{THEME['accent']};color:white;font-weight:700;}} QPushButton:hover:!checked{{background:{THEME['bg_hover']};color:{THEME['text_primary']};}}")
            btn.clicked.connect(lambda _,v=val: self._set_filter(v)); self._filter_btns[val]=btn; tl.addWidget(btn)
        tl.addStretch()
        add_btn=QPushButton("+ ایده جدید"); add_btn.clicked.connect(self._new); tl.addWidget(add_btn)
        lay.addWidget(toolbar)
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content=QWidget(); self.cl=QVBoxLayout(self.content); self.cl.setContentsMargins(28,20,28,20); self.cl.setSpacing(4)
        scroll.setWidget(self.content); lay.addWidget(scroll)

    def _set_filter(self, key):
        for k,b in self._filter_btns.items(): b.setChecked(k==key)
        self._filter=key; self.refresh()

    def refresh(self):
        while self.cl.count():
            item=self.cl.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        ideas=self.db.fetchall("SELECT * FROM ideas ORDER BY created_at DESC") if self._filter=='all' else self.db.fetchall("SELECT * FROM ideas WHERE status=? ORDER BY created_at DESC",(self._filter,))
        if not ideas:
            empty=QLabel("💡 هنوز ایده‌ای ثبت نشده!\nایده‌هایت را قبل از فراموشی ذخیره کن!")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter); empty.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:15px;padding:60px;"); self.cl.addWidget(empty)
        else:
            for idea in ideas:
                label,color=SM.get(idea.get('status','raw'),('💭 خام','#64748b'))
                card=QFrame(); card.setStyleSheet(f"QFrame{{background:{THEME['bg_secondary']};border:1px solid {THEME['border_subtle']};border-top:3px solid {color};border-radius:12px;margin-bottom:6px;}} QFrame:hover{{background:{THEME['bg_tertiary']};}}")
                cl=QVBoxLayout(card); cl.setContentsMargins(18,14,18,14); cl.setSpacing(8)
                hdr=QHBoxLayout()
                badge=QLabel(label); badge.setStyleSheet(f"color:{color};background:{color}22;border-radius:6px;padding:3px 8px;font-size:11px;font-weight:700;border:none;")
                hdr.addWidget(badge); hdr.addStretch()
                for sym,fn,hc in [('✏️',lambda _,i=idea:self._edit(i),THEME['bg_hover']),('🗑️',lambda _,iid=idea['id']:self._delete(iid),THEME['danger']+'33')]:
                    b=QPushButton(sym); b.setFixedSize(28,28); b.setStyleSheet(f"QPushButton{{background:transparent;border:none;font-size:12px;}} QPushButton:hover{{background:{hc};border-radius:5px;}}"); b.clicked.connect(fn); hdr.addWidget(b)
                cl.addLayout(hdr)
                title=QLabel(idea.get('title','')); title.setFont(QFont("Segoe UI Variable",13,QFont.Weight.Bold)); title.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;"); title.setWordWrap(True); cl.addWidget(title)
                desc=idea.get('description','') or ''
                if desc:
                    dl=QLabel(desc[:100]+('...' if len(desc)>100 else '')); dl.setStyleSheet(f"color:{THEME['text_secondary']};font-size:12px;background:transparent;border:none;"); dl.setWordWrap(True); cl.addWidget(dl)
                slist=[s for s,_,_ in IDEA_STATUSES]; ci=slist.index(idea.get('status','raw')) if idea.get('status','raw') in slist else 0
                if ci<len(slist)-1:
                    ns=slist[ci+1]; nl,nc=SM.get(ns,('بعدی',THEME['accent']))
                    adv=QPushButton(f"← {nl}"); adv.setFixedHeight(28)
                    adv.setStyleSheet(f"QPushButton{{background:{nc}22;color:{nc};border:1px solid {nc}44;border-radius:6px;font-size:11px;font-weight:700;padding:0 10px;}} QPushButton:hover{{background:{nc}44;}}")
                    adv.clicked.connect(lambda _,iid=idea['id'],s=ns:self._advance(iid,s)); cl.addWidget(adv)
                self.cl.addWidget(card)
        self.cl.addStretch()

    def _advance(self,iid,ns): self.db.execute("UPDATE ideas SET status=? WHERE id=?",(ns,iid)); self.refresh()
    def _new(self):
        dlg=IdeaDialog(self.db,parent=self)
        if dlg.exec()==QDialog.DialogCode.Accepted:
            d=dlg.result_data; self.db.execute("INSERT INTO ideas(title,description,category,status) VALUES(?,?,?,?)",(d['title'],d['description'],d['category'],d['status'])); self.refresh()
    def _edit(self,idea):
        dlg=IdeaDialog(self.db,idea=idea,parent=self)
        if dlg.exec()==QDialog.DialogCode.Accepted:
            d=dlg.result_data; self.db.execute("UPDATE ideas SET title=?,description=?,category=?,status=? WHERE id=?",(d['title'],d['description'],d['category'],d['status'],idea['id'])); self.refresh()
    def _delete(self,iid):
        msg=QMessageBox(self); msg.setWindowTitle("حذف"); msg.setText("آیا مطمئنید?"); msg.setStandardButtons(QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No); msg.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};")
        if msg.exec()==QMessageBox.StandardButton.Yes: self.db.execute("DELETE FROM ideas WHERE id=?",(iid,)); self.refresh()
