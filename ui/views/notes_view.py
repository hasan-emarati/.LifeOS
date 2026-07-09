"""Notes View v2"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QLineEdit, QTextEdit,
    QComboBox, QSplitter, QListWidget, QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ui.theme import THEME

class NoteDialog(QDialog):
    def __init__(self, db, note=None, parent=None):
        super().__init__(parent)
        self.db = db; self.note = note
        self.setWindowTitle("یادداشت جدید" if not note else "ویرایش")
        self.setMinimumSize(600,500)
        self.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};")
        self._build()
        if note: self._fill(note)

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(24,24,24,24); lay.setSpacing(12)
        def lbl(t):
            l=QLabel(t); l.setFont(QFont("Segoe UI Variable",11,QFont.Weight.Bold))
            l.setStyleSheet(f"color:{THEME['text_secondary']};"); return l
        lay.addWidget(lbl("عنوان *"))
        self.title_edit = QLineEdit(); self.title_edit.setPlaceholderText("عنوان یادداشت...")
        lay.addWidget(self.title_edit)
        row = QHBoxLayout()
        cat_col = QVBoxLayout(); cat_col.addWidget(lbl("دسته‌بندی"))
        self.cat_combo = QComboBox()
        for v,n in [('general','عمومی'),('technical','فنی'),('research','تحقیق'),('idea','ایده'),('meeting','جلسه'),('lesson','درس')]:
            self.cat_combo.addItem(n,v)
        cat_col.addWidget(self.cat_combo)
        proj_col = QVBoxLayout(); proj_col.addWidget(lbl("پروژه"))
        self.proj_combo = QComboBox(); self.proj_combo.addItem("بدون پروژه",None)
        for p in self.db.fetchall("SELECT id,name FROM projects WHERE archived=0"):
            self.proj_combo.addItem(p['name'],p['id'])
        proj_col.addWidget(self.proj_combo)
        row.addLayout(cat_col); row.addLayout(proj_col); lay.addLayout(row)
        lay.addWidget(lbl("تگ‌ها"))
        self.tags_edit = QLineEdit(); self.tags_edit.setPlaceholderText("python, machine-learning")
        lay.addWidget(self.tags_edit)
        lay.addWidget(lbl("محتوا"))
        self.content_edit = QTextEdit(); self.content_edit.setPlaceholderText("یادداشت...")
        self.content_edit.setMinimumHeight(220); lay.addWidget(self.content_edit)
        btn_row = QHBoxLayout()
        cancel=QPushButton("انصراف"); cancel.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_primary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:8px 20px;"); cancel.clicked.connect(self.reject)
        save=QPushButton("📝 ذخیره"); save.clicked.connect(self._save)
        btn_row.addStretch(); btn_row.addWidget(cancel); btn_row.addWidget(save); lay.addLayout(btn_row)

    def _fill(self, n):
        self.title_edit.setText(n.get('title','')); self.content_edit.setPlainText(n.get('content','') or '')
        self.tags_edit.setText(n.get('tags','') or '')
        idx=self.cat_combo.findData(n.get('category','general'))
        if idx>=0: self.cat_combo.setCurrentIndex(idx)
        idx=self.proj_combo.findData(n.get('project_id'))
        if idx>=0: self.proj_combo.setCurrentIndex(idx)

    def _save(self):
        title=self.title_edit.text().strip()
        if not title: return
        self.result_data={'title':title,'content':self.content_edit.toPlainText(),'category':self.cat_combo.currentData(),'tags':self.tags_edit.text(),'project_id':self.proj_combo.currentData()}
        self.accept()

class NotesView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db=db; self._selected=None; self._notes=[]
        self._build(); self.refresh()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        toolbar=QWidget(); toolbar.setFixedHeight(64)
        toolbar.setStyleSheet(f"background:{THEME['bg_primary']};border-bottom:1px solid {THEME['border_subtle']};")
        tl=QHBoxLayout(toolbar); tl.setContentsMargins(24,0,24,0); tl.setSpacing(12)
        self.search_edit=QLineEdit(); self.search_edit.setPlaceholderText("🔍 جستجو..."); self.search_edit.setMaximumWidth(280)
        self.search_edit.textChanged.connect(self.refresh)
        tl.addWidget(self.search_edit); tl.addStretch()
        add_btn=QPushButton("+ یادداشت جدید"); add_btn.clicked.connect(self._new)
        tl.addWidget(add_btn); lay.addWidget(toolbar)
        splitter=QSplitter(Qt.Orientation.Horizontal)
        left=QWidget(); left.setMaximumWidth(280); left.setStyleSheet(f"background:{THEME['bg_secondary']};")
        ll=QVBoxLayout(left); ll.setContentsMargins(10,10,10,10)
        self.note_list=QListWidget()
        self.note_list.setStyleSheet(f"QListWidget{{background:transparent;border:none;}} QListWidget::item{{background:{THEME['bg_tertiary']};border-radius:8px;padding:10px;margin-bottom:4px;border:1px solid {THEME['border_subtle']};color:{THEME['text_primary']};}} QListWidget::item:selected{{background:{THEME['accent']};color:white;border-color:{THEME['accent']};}} QListWidget::item:hover:!selected{{background:{THEME['bg_hover']};}}")
        self.note_list.currentRowChanged.connect(self._show)
        ll.addWidget(self.note_list); splitter.addWidget(left)
        right=QWidget(); right.setStyleSheet(f"background:{THEME['bg_primary']};")
        rl=QVBoxLayout(right); rl.setContentsMargins(24,20,24,20); rl.setSpacing(10)
        self.note_title=QLabel("یک یادداشت انتخاب کنید"); self.note_title.setFont(QFont("Segoe UI Variable",18,QFont.Weight.Bold)); self.note_title.setStyleSheet(f"color:{THEME['text_primary']};")
        self.note_meta=QLabel(""); self.note_meta.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:11px;")
        sep=QFrame(); sep.setFixedHeight(1); sep.setStyleSheet(f"background:{THEME['border_subtle']};")
        self.note_content=QTextEdit(); self.note_content.setReadOnly(True)
        self.note_content.setStyleSheet(f"QTextEdit{{background:transparent;border:none;color:{THEME['text_primary']};font-size:14px;line-height:1.6;}}")
        actions=QHBoxLayout()
        self.edit_btn=QPushButton("✏️ ویرایش"); self.edit_btn.setVisible(False); self.edit_btn.clicked.connect(self._edit)
        self.del_btn=QPushButton("🗑️ حذف"); self.del_btn.setVisible(False)
        self.del_btn.setStyleSheet(f"background:{THEME['danger']}22;color:{THEME['danger']};border:1px solid {THEME['danger']}44;border-radius:8px;padding:6px 14px;")
        self.del_btn.clicked.connect(self._delete)
        actions.addWidget(self.edit_btn); actions.addWidget(self.del_btn); actions.addStretch()
        rl.addWidget(self.note_title); rl.addWidget(self.note_meta); rl.addWidget(sep); rl.addWidget(self.note_content); rl.addLayout(actions)
        splitter.addWidget(right); splitter.setSizes([260,700]); lay.addWidget(splitter)

    def refresh(self):
        self.note_list.clear()
        q=self.search_edit.text().strip() if hasattr(self,'search_edit') else ''
        if q:
            self._notes=self.db.fetchall("SELECT * FROM notes WHERE title LIKE ? OR content LIKE ? OR tags LIKE ? ORDER BY updated_at DESC",(f'%{q}%',f'%{q}%',f'%{q}%'))
        else:
            self._notes=self.db.fetchall("SELECT * FROM notes ORDER BY updated_at DESC")
        cat_icons={'general':'📄','technical':'💻','research':'🔬','idea':'💡','meeting':'🤝','lesson':'📚'}
        for n in self._notes:
            item=QListWidgetItem(f"{cat_icons.get(n.get('category','general'),'📄')}  {n.get('title','')}")
            item.setData(Qt.ItemDataRole.UserRole,n['id']); self.note_list.addItem(item)

    def _show(self, row):
        if row<0 or row>=len(self._notes): return
        n=self._notes[row]; self._selected=n
        self.note_title.setText(n.get('title',''))
        tags=n.get('tags','') or ''; date_str=n.get('updated_at','')[:10]
        self.note_meta.setText(f"📅 {date_str}  •  🏷️ {tags}" if tags else f"📅 {date_str}")
        self.note_content.setPlainText(n.get('content','') or '')
        self.edit_btn.setVisible(True); self.del_btn.setVisible(True)

    def _edit(self):
        if not self._selected: return
        dlg=NoteDialog(self.db,note=self._selected,parent=self)
        if dlg.exec()==QDialog.DialogCode.Accepted:
            d=dlg.result_data
            self.db.execute("UPDATE notes SET title=?,content=?,category=?,tags=?,project_id=?,updated_at=datetime('now') WHERE id=?",(d['title'],d['content'],d['category'],d['tags'],d['project_id'],self._selected['id']))
            self.refresh()

    def _delete(self):
        if not self._selected: return
        msg=QMessageBox(self); msg.setWindowTitle("حذف"); msg.setText("آیا مطمئنید؟")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        msg.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};")
        if msg.exec()==QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM notes WHERE id=?",(self._selected['id'],))
            self._selected=None; self.note_title.setText("یک یادداشت انتخاب کنید"); self.note_content.clear()
            self.edit_btn.setVisible(False); self.del_btn.setVisible(False); self.refresh()

    def _new(self):
        dlg=NoteDialog(self.db,parent=self)
        if dlg.exec()==QDialog.DialogCode.Accepted:
            d=dlg.result_data
            self.db.execute("INSERT INTO notes(title,content,category,tags,project_id) VALUES(?,?,?,?,?)",(d['title'],d['content'],d['category'],d['tags'],d['project_id']))
            self.refresh()
