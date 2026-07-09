"""Finance View v3 — حسابداری کامل با فرمت ایرانی"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QComboBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QTabWidget, QColorDialog, QSpinBox,
    QGridLayout, QProgressBar, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from ui.theme import THEME
from ui.widgets.themed_dialog import ThemedDialog
from ui.views.projects_view import JalaliDateWidget
from core.jalali import (
    today_jalali, to_jalali, to_gregorian, format_jalali,
    jalali_to_iso, jalali_month_len, JALALI_MONTHS
)


def fmt_rial(amount: float) -> str:
    """فرمت ایرانی: ۴۳،۰۰۰ تومان"""
    try:
        n = int(amount)
        s = f"{n:,}"
        return f"{s} تومان"
    except Exception:
        return f"{amount} تومان"


# ── چرخه‌ی مالی ماهانه: هر دوره از روز ۶ تا روز ۵ ماه بعد ────────────
def current_cycle_anchor():
    """(jy, jm) ماهی که دوره‌ی مالی جاری از روز ۶ آن شروع شده است."""
    jy, jm, jd = today_jalali()
    if jd >= 6:
        return jy, jm
    if jm == 1:
        return jy - 1, 12
    return jy, jm - 1


def cycle_bounds(jy: int, jm: int):
    """بازه‌ی ISO [شروع، پایان) برای دوره‌ای که از روز ۶ ماه (jy,jm) شروع می‌شود."""
    start_iso = jalali_to_iso(jy, jm, 6)
    ny, nm = (jy + 1, 1) if jm == 12 else (jy, jm + 1)
    end_iso = jalali_to_iso(ny, nm, 6)
    return start_iso, end_iso, (ny, nm)


def cycle_label(jy: int, jm: int) -> str:
    _, _, (ny, nm) = cycle_bounds(jy, jm)
    end_day_jy, end_day_jm = (ny, nm)
    # روز پایانی نمایشی = ۵ ماه بعد
    return f"۶ {JALALI_MONTHS[jm-1]} {jy}  تا  ۵ {JALALI_MONTHS[end_day_jm-1]} {end_day_jy}"


# ── Account Dialog ───────────────────────────────────────────────────
class AccountDialog(ThemedDialog):
    def __init__(self, db, account=None, parent=None):
        super().__init__("🏦 حساب بانکی جدید" if not account else "✏️ ویرایش حساب", parent)
        self.db = db
        self.color_val = account.get('color', '#10b981') if account else '#10b981'
        self.setFixedWidth(400)
        self._build_form()
        if account:
            self._fill(account)

    def _build_form(self):
        lay = self.content_layout()

        def lbl(t):
            l = QLabel(t); l.setFont(QFont("Segoe UI Variable", 11, QFont.Weight.Bold))
            l.setStyleSheet(f"color:{THEME['text_secondary']};"); return l

        lay.addWidget(lbl("نام حساب *"))
        self.name_edit = QLineEdit(); self.name_edit.setPlaceholderText("مثلاً: ملت، پاسارگاد، نقدی")
        lay.addWidget(self.name_edit)

        lay.addWidget(lbl("نام بانک"))
        self.bank_edit = QLineEdit(); self.bank_edit.setPlaceholderText("نام بانک...")
        lay.addWidget(self.bank_edit)

        lay.addWidget(lbl("شماره حساب / کارت (اختیاری)"))
        self.account_num = QLineEdit(); self.account_num.setPlaceholderText("۶۲۱۹ ۸۶۱۰ ...")
        lay.addWidget(self.account_num)

        lay.addWidget(lbl("موجودی اولیه (تومان)"))
        self.balance_spin = QDoubleSpinBox()
        self.balance_spin.setMaximum(999_999_999_999); self.balance_spin.setSuffix(" تومان")
        self.balance_spin.setFont(QFont("Segoe UI Variable", 13))
        lay.addWidget(self.balance_spin)

        color_row = QHBoxLayout()
        color_lbl = QLabel("رنگ حساب:"); color_lbl.setStyleSheet(f"color:{THEME['text_secondary']};font-size:11px;font-weight:700;")
        self.color_btn = QPushButton("  انتخاب رنگ")
        self.color_btn.setStyleSheet(f"background:{self.color_val};color:white;border-radius:8px;padding:6px 12px;border:none;")
        self.color_btn.clicked.connect(self._pick_color)
        color_row.addWidget(color_lbl); color_row.addWidget(self.color_btn); color_row.addStretch()
        lay.addLayout(color_row)

        btn_row = QHBoxLayout()
        cancel = QPushButton("انصراف")
        cancel.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_primary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:8px 18px;")
        cancel.clicked.connect(self.reject)
        save = QPushButton("💾 ذخیره حساب"); save.clicked.connect(self._save)
        btn_row.addStretch(); btn_row.addWidget(cancel); btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self.color_val), self)
        if c.isValid():
            self.color_val = c.name()
            self.color_btn.setStyleSheet(f"background:{self.color_val};color:white;border-radius:8px;padding:6px 12px;border:none;")

    def _fill(self, a):
        self.name_edit.setText(a.get('name', ''))
        self.bank_edit.setText(a.get('bank', '') or '')
        self.account_num.setText(a.get('account_num', '') or '')
        self.balance_spin.setValue(a.get('balance', 0) or 0)

    def _save(self):
        name = self.name_edit.text().strip()
        if not name: return
        self.result_data = {
            'name': name, 'bank': self.bank_edit.text(),
            'account_num': self.account_num.text(),
            'balance': self.balance_spin.value(), 'color': self.color_val,
        }
        self.accept()


# ── Category Manager ─────────────────────────────────────────────────
class FinanceCategoryDialog(ThemedDialog):
    def __init__(self, db, parent=None):
        super().__init__("📂 مدیریت دسته‌بندی مالی", parent)
        self.db = db; self.color_val = '#ef4444'
        self.setMinimumWidth(480)
        self._build(); self._load()

    def _build(self):
        lay = self.content_layout()
        row = QHBoxLayout()
        self.new_icon = QLineEdit("💸"); self.new_icon.setFixedWidth(54)
        self.new_name = QLineEdit(); self.new_name.setPlaceholderText("نام دسته‌بندی...")
        self.type_combo = QComboBox()
        self.type_combo.addItem("💸 هزینه", "expense"); self.type_combo.addItem("💰 درآمد", "income")
        self.color_btn = QPushButton("رنگ"); self.color_btn.setFixedWidth(56)
        self.color_btn.setStyleSheet(f"background:{self.color_val};color:white;border-radius:6px;padding:4px;border:none;")
        self.color_btn.clicked.connect(self._pick_color)
        add_btn = QPushButton("+"); add_btn.setFixedWidth(36); add_btn.clicked.connect(self._add)
        row.addWidget(self.new_icon); row.addWidget(self.new_name); row.addWidget(self.type_combo)
        row.addWidget(self.color_btn); row.addWidget(add_btn)
        lay.addLayout(row)
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
        cats = self.db.fetchall("SELECT * FROM finance_categories ORDER BY type,name")
        for cat in cats:
            row = QFrame(); row.setStyleSheet(f"background:{THEME['bg_tertiary']};border-radius:8px;margin-bottom:2px;")
            rl = QHBoxLayout(row); rl.setContentsMargins(12,6,12,6)
            color_dot = QLabel("●"); color_dot.setStyleSheet(f"color:{cat.get('color',THEME['accent'])};font-size:16px;background:transparent;border:none;")
            name_lbl = QLabel(f"{cat.get('icon','💸')}  {cat['name']}  ({'هزینه' if cat.get('type')=='expense' else 'درآمد'})")
            name_lbl.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;font-size:12px;")
            del_btn = QPushButton("🗑️"); del_btn.setFixedSize(26,26)
            del_btn.setStyleSheet(f"QPushButton{{background:transparent;border:none;font-size:11px;}} QPushButton:hover{{background:{THEME['danger']}33;border-radius:5px;}}")
            del_btn.clicked.connect(lambda _,cid=cat['id']: self._delete(cid))
            rl.addWidget(color_dot); rl.addWidget(name_lbl); rl.addStretch(); rl.addWidget(del_btn)
            self.list_lay.addWidget(row)

    def _add(self):
        name = self.new_name.text().strip()
        if not name: return
        try:
            self.db.execute("INSERT OR IGNORE INTO finance_categories(name,type,color,icon) VALUES(?,?,?,?)",
                           (name, self.type_combo.currentData(), self.color_val, self.new_icon.text() or '💸'))
        except Exception: pass
        self.new_name.clear(); self._load()

    def _delete(self, cid):
        self.db.execute("DELETE FROM finance_categories WHERE id=?", (cid,)); self._load()


# ── Finance Entry Dialog ─────────────────────────────────────────────
class FinanceEntryDialog(ThemedDialog):
    def __init__(self, db, parent=None):
        super().__init__("💳 ثبت تراکنش مالی", parent)
        self.db = db; self.setMinimumWidth(500)
        self._build_form()

    def _build_form(self):
        lay = self.content_layout()

        def lbl(t):
            l = QLabel(t); l.setFont(QFont("Segoe UI Variable", 11, QFont.Weight.Bold))
            l.setStyleSheet(f"color:{THEME['text_secondary']};"); return l

        lay.addWidget(lbl("توضیحات *"))
        self.desc_edit = QLineEdit(); self.desc_edit.setPlaceholderText("بابت چه هزینه/درآمدی؟")
        lay.addWidget(self.desc_edit)

        lay.addWidget(lbl("طرف حساب"))
        self.payee_edit = QLineEdit(); self.payee_edit.setPlaceholderText("نام فرد یا شرکت...")
        lay.addWidget(self.payee_edit)

        row1 = QHBoxLayout()
        type_col = QVBoxLayout(); type_col.addWidget(lbl("نوع"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("💸 هزینه", "expense"); self.type_combo.addItem("💰 درآمد", "income")
        self.type_combo.currentIndexChanged.connect(self._update_cats)
        type_col.addWidget(self.type_combo)

        cat_col = QVBoxLayout(); cat_col.addWidget(lbl("دسته‌بندی"))
        self.cat_combo = QComboBox()
        cat_col.addWidget(self.cat_combo)

        manage_cats_btn = QPushButton("⚙️"); manage_cats_btn.setFixedSize(36, 36)
        manage_cats_btn.setToolTip("مدیریت دسته‌بندی‌ها")
        manage_cats_btn.setStyleSheet(f"background:{THEME['bg_tertiary']};border:1px solid {THEME['border_default']};border-radius:8px;font-size:14px;color:{THEME['text_secondary']};")
        manage_cats_btn.clicked.connect(self._manage_cats)

        row1.addLayout(type_col, 1); row1.addLayout(cat_col, 2); row1.addWidget(manage_cats_btn)
        row1.setAlignment(manage_cats_btn, Qt.AlignmentFlag.AlignBottom)
        lay.addLayout(row1)
        self._update_cats()

        lay.addWidget(lbl("حساب بانکی"))
        self.account_combo = QComboBox()
        self.account_combo.addItem("بدون حساب", None)
        for a in self.db.fetchall("SELECT id,name,bank FROM bank_accounts"):
            self.account_combo.addItem(f"{a['name']} — {a.get('bank','')}", a['id'])
        lay.addWidget(self.account_combo)

        row2 = QHBoxLayout()
        amt_col = QVBoxLayout(); amt_col.addWidget(lbl("مبلغ (تومان) *"))
        self.amount_edit = QLineEdit(); self.amount_edit.setPlaceholderText("مثلاً: 43000")
        self.amount_edit.setFont(QFont("Segoe UI Variable", 14))
        self.amount_edit.textChanged.connect(self._format_amount)
        self.amount_preview = QLabel("")
        self.amount_preview.setStyleSheet(f"color:{THEME['accent_light']};font-size:11px;background:transparent;border:none;")
        amt_col.addWidget(self.amount_edit); amt_col.addWidget(self.amount_preview)

        proj_col = QVBoxLayout(); proj_col.addWidget(lbl("پروژه"))
        self.proj_combo = QComboBox(); self.proj_combo.addItem("بدون پروژه", None)
        for p in self.db.fetchall("SELECT id,name FROM projects WHERE archived=0"):
            self.proj_combo.addItem(p['name'], p['id'])
        proj_col.addWidget(self.proj_combo)

        row2.addLayout(amt_col, 2); row2.addLayout(proj_col, 1)
        lay.addLayout(row2)

        lay.addWidget(lbl("📅 تاریخ (شمسی)"))
        self.date_widget = JalaliDateWidget()
        lay.addWidget(self.date_widget)

        btn_row = QHBoxLayout()
        cancel = QPushButton("انصراف")
        cancel.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_primary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:8px 18px;")
        cancel.clicked.connect(self.reject)
        save = QPushButton("💾 ثبت تراکنش"); save.clicked.connect(self._save)
        btn_row.addStretch(); btn_row.addWidget(cancel); btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _format_amount(self, text):
        clean = text.replace(',', '').replace('،', '').strip()
        try:
            n = int(float(clean))
            self.amount_preview.setText(fmt_rial(n))
        except Exception:
            self.amount_preview.setText("")

    def _update_cats(self):
        ftype = self.type_combo.currentData()
        self.cat_combo.clear()
        cats = self.db.fetchall("SELECT * FROM finance_categories WHERE type=? ORDER BY name", (ftype,))
        for c in cats:
            self.cat_combo.addItem(f"{c.get('icon','')} {c['name']}", c['id'])

    def _manage_cats(self):
        current = self.cat_combo.currentData()
        ftype = self.type_combo.currentData()
        dlg = FinanceCategoryDialog(self.db, parent=self)
        dlg.exec()
        self._update_cats()

    def _save(self):
        desc = self.desc_edit.text().strip()
        raw  = self.amount_edit.text().replace(',','').replace('،','').strip()
        try:
            amt = float(raw)
        except Exception:
            return
        if not desc or amt <= 0: return
        self.result_data = {
            'description': desc, 'payee': self.payee_edit.text(),
            'type': self.type_combo.currentData(),
            'category_id': self.cat_combo.currentData(),
            'account_id': self.account_combo.currentData(),
            'project_id': self.proj_combo.currentData(),
            'amount': amt, 'date': self.date_widget.get_iso(),
        }
        self.accept()


# ── Payroll Dialog ───────────────────────────────────────────────────
class PayrollDialog(ThemedDialog):
    def __init__(self, db, entry=None, parent=None):
        super().__init__("👥 ثبت حقوق / بدهی", parent)
        self.db = db; self.setFixedWidth(420)
        self._build_form()
        if entry: self._fill(entry)

    def _build_form(self):
        lay = self.content_layout()

        def lbl(t):
            l = QLabel(t); l.setFont(QFont("Segoe UI Variable", 11, QFont.Weight.Bold))
            l.setStyleSheet(f"color:{THEME['text_secondary']};"); return l

        lay.addWidget(lbl("نام شخص *"))
        self.person_edit = QLineEdit(); self.person_edit.setPlaceholderText("نام کارمند / فریلنسر...")
        lay.addWidget(self.person_edit)

        lay.addWidget(lbl("نقش"))
        self.role_edit = QLineEdit(); self.role_edit.setPlaceholderText("توسعه‌دهنده، طراح...")
        lay.addWidget(self.role_edit)

        row = QHBoxLayout()
        amt_col = QVBoxLayout(); amt_col.addWidget(lbl("مبلغ (تومان)"))
        self.amount_edit = QLineEdit(); self.amount_edit.setPlaceholderText("مثلاً: 5000000")
        self.amount_edit.setFont(QFont("Segoe UI Variable", 13))
        self.amount_edit.textChanged.connect(self._fmt)
        self.amt_preview = QLabel("")
        self.amt_preview.setStyleSheet(f"color:{THEME['accent_light']};font-size:10px;background:transparent;border:none;")
        amt_col.addWidget(self.amount_edit); amt_col.addWidget(self.amt_preview)

        per_col = QVBoxLayout(); per_col.addWidget(lbl("دوره"))
        self.period_combo = QComboBox()
        for v,l in [('monthly','ماهانه'),('weekly','هفتگی'),('daily','روزانه'),('project','پروژه‌ای')]:
            self.period_combo.addItem(l, v)
        per_col.addWidget(self.period_combo)

        row.addLayout(amt_col, 2); row.addLayout(per_col, 1)
        lay.addLayout(row)

        lay.addWidget(lbl("پروژه"))
        self.proj_combo = QComboBox(); self.proj_combo.addItem("بدون پروژه", None)
        for p in self.db.fetchall("SELECT id,name FROM projects WHERE archived=0"):
            self.proj_combo.addItem(p['name'], p['id'])
        lay.addWidget(self.proj_combo)

        lay.addWidget(lbl("📅 تاریخ سررسید (شمسی)"))
        self.due_date = JalaliDateWidget(); lay.addWidget(self.due_date)

        lay.addWidget(lbl("یادداشت"))
        self.notes_edit = QLineEdit(); lay.addWidget(self.notes_edit)

        btn_row = QHBoxLayout()
        cancel = QPushButton("انصراف")
        cancel.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_primary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:8px 18px;")
        cancel.clicked.connect(self.reject)
        save = QPushButton("💾 ذخیره"); save.clicked.connect(self._save)
        btn_row.addStretch(); btn_row.addWidget(cancel); btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _fmt(self, text):
        clean = text.replace(',','').replace('،','').strip()
        try:
            self.amt_preview.setText(fmt_rial(int(float(clean))))
        except Exception:
            self.amt_preview.setText("")

    def _fill(self, e):
        self.person_edit.setText(e.get('person',''))
        self.role_edit.setText(e.get('role','') or '')
        self.amount_edit.setText(str(int(e.get('amount',0) or 0)))
        idx = self.period_combo.findData(e.get('period','monthly'))
        if idx >= 0: self.period_combo.setCurrentIndex(idx)
        self.notes_edit.setText(e.get('notes','') or '')

    def _save(self):
        person = self.person_edit.text().strip()
        raw = self.amount_edit.text().replace(',','').replace('،','').strip()
        try: amt = float(raw)
        except Exception: amt = 0
        if not person: return
        self.result_data = {
            'person':person,'role':self.role_edit.text(),'amount':amt,
            'period':self.period_combo.currentData(),'project_id':self.proj_combo.currentData(),
            'due_date':self.due_date.get_iso(),'notes':self.notes_edit.text(),
        }
        self.accept()


# ── Finance View ─────────────────────────────────────────────────────
class FinanceView(QWidget):
    def __init__(self, db):
        super().__init__(); self.db = db
        self._cy_jy, self._cy_jm = current_cycle_anchor()
        self._build(); self.refresh()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        toolbar = QWidget(); toolbar.setFixedHeight(64)
        toolbar.setStyleSheet(f"background:{THEME['bg_primary']};border-bottom:1px solid {THEME['border_subtle']};")
        tl = QHBoxLayout(toolbar); tl.setContentsMargins(20,0,20,0); tl.setSpacing(10)

        add_btn = QPushButton("+ تراکنش"); add_btn.clicked.connect(self._new_entry)
        tl.addWidget(add_btn)

        acc_btn = QPushButton("🏦 حساب جدید")
        acc_btn.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_secondary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:6px 12px;")
        acc_btn.clicked.connect(self._new_account); tl.addWidget(acc_btn)

        pay_btn = QPushButton("👥 حقوق / بدهی")
        pay_btn.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_secondary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:6px 12px;")
        pay_btn.clicked.connect(self._new_payroll); tl.addWidget(pay_btn)

        cats_btn = QPushButton("📂 دسته‌بندی‌ها")
        cats_btn.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_secondary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:6px 12px;")
        cats_btn.clicked.connect(self._manage_cats); tl.addWidget(cats_btn)

        tl.addStretch()
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("همه","all")
        self.filter_combo.addItem("💸 هزینه","expense")
        self.filter_combo.addItem("💰 درآمد","income")
        self.filter_combo.currentIndexChanged.connect(self.refresh)
        tl.addWidget(self.filter_combo)
        lay.addWidget(toolbar)

        self.tabs = QTabWidget(); lay.addWidget(self.tabs)

        # ── Tab 1: خلاصه ─────────────────────────────
        sum_w = QWidget(); sl = QVBoxLayout(sum_w); sl.setContentsMargins(0,0,0,0)

        cycle_bar = QWidget(); cycle_bar.setFixedHeight(48)
        cycle_bar.setStyleSheet(f"background:{THEME['bg_primary']};border-bottom:1px solid {THEME['border_subtle']};")
        cbl = QHBoxLayout(cycle_bar); cbl.setContentsMargins(16,0,16,0); cbl.setSpacing(8)
        prev_cy = QPushButton("◀"); next_cy = QPushButton("▶")
        for b in (prev_cy, next_cy):
            b.setFixedSize(32,32)
            b.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_secondary']};border:1px solid {THEME['border_default']};border-radius:8px;font-weight:700;")
        prev_cy.clicked.connect(self._prev_cycle); next_cy.clicked.connect(self._next_cycle)
        self.cycle_lbl = QLabel()
        self.cycle_lbl.setFont(QFont("Segoe UI Variable",12,QFont.Weight.Bold))
        self.cycle_lbl.setStyleSheet(f"color:{THEME['accent_light']};")
        self.cycle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cur_cy_btn = QPushButton("📆 دوره جاری")
        cur_cy_btn.setStyleSheet(f"background:{THEME['bg_tertiary']};color:{THEME['text_secondary']};border:1px solid {THEME['border_default']};border-radius:8px;padding:0 12px;")
        cur_cy_btn.clicked.connect(self._go_current_cycle)
        cbl.addWidget(prev_cy); cbl.addWidget(self.cycle_lbl,1); cbl.addWidget(next_cy); cbl.addWidget(cur_cy_btn)
        sl.addWidget(cycle_bar)

        sum_scroll = QScrollArea(); sum_scroll.setWidgetResizable(True); sum_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.sum_content = QWidget(); self.sum_layout = QVBoxLayout(self.sum_content)
        self.sum_layout.setContentsMargins(24,18,24,18); self.sum_layout.setSpacing(16)
        sum_scroll.setWidget(self.sum_content); sl.addWidget(sum_scroll)
        self.tabs.addTab(sum_w, "📊 خلاصه")

        # ── Tab 2: تراکنش‌ها ──────────────────────────
        entry_w = QWidget(); el = QVBoxLayout(entry_w); el.setContentsMargins(16,12,16,12)
        self.entries_table = QTableWidget(); self.entries_table.setColumnCount(7)
        self.entries_table.setHorizontalHeaderLabels(["تاریخ","توضیحات","طرف حساب","نوع","دسته","حساب","مبلغ"])
        self.entries_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.entries_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.entries_table.verticalHeader().setVisible(False); self.entries_table.setShowGrid(False)
        self.entries_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        el.addWidget(self.entries_table)
        del_btn = QPushButton("🗑️ حذف ردیف انتخاب‌شده")
        del_btn.setStyleSheet(f"background:{THEME['danger']}22;color:{THEME['danger']};border:1px solid {THEME['danger']}44;border-radius:8px;padding:6px 14px;font-size:12px;")
        del_btn.clicked.connect(self._delete_entry); el.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        self.tabs.addTab(entry_w, "💳 تراکنش‌ها")

        # ── Tab 3: حساب‌ها ────────────────────────────
        acc_w = QWidget(); acl = QVBoxLayout(acc_w); acl.setContentsMargins(16,12,16,12)
        self.accounts_table = QTableWidget(); self.accounts_table.setColumnCount(5)
        self.accounts_table.setHorizontalHeaderLabels(["نام حساب","بانک","موجودی اولیه","موجودی فعلی","عملیات"])
        self.accounts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.accounts_table.verticalHeader().setVisible(False); self.accounts_table.setShowGrid(False)
        self.accounts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        acl.addWidget(self.accounts_table)
        self.tabs.addTab(acc_w, "🏦 حساب‌ها")

        # ── Tab 4: حقوق ───────────────────────────────
        pay_w = QWidget(); pwl = QVBoxLayout(pay_w); pwl.setContentsMargins(16,12,16,12)
        hint = QLabel("💡 دابل‌کلیک روی ردیف: تغییر وضعیت پرداخت")
        hint.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:11px;")
        pwl.addWidget(hint)
        self.payroll_table = QTableWidget(); self.payroll_table.setColumnCount(7)
        self.payroll_table.setHorizontalHeaderLabels(["نام","نقش","مبلغ","دوره","پروژه","سررسید","وضعیت"])
        self.payroll_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.payroll_table.verticalHeader().setVisible(False); self.payroll_table.setShowGrid(False)
        self.payroll_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.payroll_table.doubleClicked.connect(self._toggle_paid)
        pwl.addWidget(self.payroll_table)
        self.tabs.addTab(pay_w, "👥 حقوق")

    def refresh(self):
        self._update_summary()
        self._update_entries()
        self._update_accounts()
        self._update_payroll()

    # ── ناوبری دوره‌ی مالی ─────────────────────────────
    def _prev_cycle(self):
        if self._cy_jm == 1:
            self._cy_jy -= 1; self._cy_jm = 12
        else:
            self._cy_jm -= 1
        self._update_summary()

    def _next_cycle(self):
        if self._cy_jm == 12:
            self._cy_jy += 1; self._cy_jm = 1
        else:
            self._cy_jm += 1
        self._update_summary()

    def _go_current_cycle(self):
        self._cy_jy, self._cy_jm = current_cycle_anchor()
        self._update_summary()

    # ── Summary ──────────────────────────────────────
    def _update_summary(self):
        while self.sum_layout.count():
            item = self.sum_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        start_iso, end_iso, _ = cycle_bounds(self._cy_jy, self._cy_jm)
        is_current = (self._cy_jy, self._cy_jm) == current_cycle_anchor()
        prefix = "📆 دوره جاری: " if is_current else "📆 "
        self.cycle_lbl.setText(prefix + cycle_label(self._cy_jy, self._cy_jm))

        inc_r = self.db.fetchone("SELECT SUM(amount) as s FROM finance_entries WHERE type='income' AND date>=? AND date<?", (start_iso, end_iso))
        exp_r = self.db.fetchone("SELECT SUM(amount) as s FROM finance_entries WHERE type='expense' AND date>=? AND date<?", (start_iso, end_iso))
        pay_r = self.db.fetchone("SELECT SUM(amount) as s FROM payroll WHERE paid=0")
        inc  = inc_r['s'] or 0 if inc_r else 0
        exp  = exp_r['s'] or 0 if exp_r else 0
        debt = pay_r['s'] or 0 if pay_r else 0
        bal  = inc - exp

        # KPI cards
        grid = QGridLayout(); grid.setSpacing(12)
        for i,(icon,title,val,color) in enumerate([
            ("💰","درآمد این دوره",    inc,  THEME['success']),
            ("💸","هزینه این دوره",   exp,  THEME['danger']),
            ("⚖️","موجودی خالص دوره",bal,  THEME['accent'] if bal>=0 else THEME['danger']),
            ("👥","حقوق معوق",  debt, THEME['warning']),
        ]):
            card = QFrame(); card.setStyleSheet(f"QFrame{{background:{THEME['bg_secondary']};border:1px solid {THEME['border_subtle']};border-top:3px solid {color};border-radius:12px;}}")
            cl = QVBoxLayout(card); cl.setContentsMargins(16,12,16,12); cl.setSpacing(6)
            ic = QLabel(icon); ic.setFont(QFont("Segoe UI Emoji",18))
            ic.setStyleSheet(f"background:{color}22;border-radius:8px;padding:6px;border:1px solid {color}44;"); ic.setFixedSize(40,40); ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vl = QLabel(fmt_rial(val)); vl.setFont(QFont("Segoe UI Variable",16,QFont.Weight.Bold)); vl.setStyleSheet(f"color:{color};background:transparent;border:none;")
            tl2 = QLabel(f"{icon} {title}"); tl2.setStyleSheet(f"color:{THEME['text_secondary']};background:transparent;border:none;font-size:11px;")
            cl.addWidget(ic); cl.addWidget(vl); cl.addWidget(tl2)
            grid.addWidget(card,0,i)
        kw = QWidget(); kw.setLayout(grid); self.sum_layout.addWidget(kw)

        note = QLabel("💡 خلاصه‌ی بالا فقط تراکنش‌های همین دورهٔ مالی (۶ تا ۶) را نشان می‌دهد. تاریخچه‌ی کامل در تب «تراکنش‌ها» باقی می‌ماند.")
        note.setWordWrap(True)
        note.setStyleSheet(f"color:{THEME['text_tertiary']};font-size:11px;")
        self.sum_layout.addWidget(note)

        # هزینه به تفکیک دسته
        cat_lbl = QLabel("📊 هزینه به تفکیک دسته‌بندی (این دوره)")
        cat_lbl.setFont(QFont("Segoe UI Variable",13,QFont.Weight.Bold)); cat_lbl.setStyleSheet(f"color:{THEME['text_primary']};")
        self.sum_layout.addWidget(cat_lbl)
        cat_data = self.db.fetchall("""
            SELECT fc.name,fc.color,fc.icon,SUM(fe.amount) as total
            FROM finance_entries fe JOIN finance_categories fc ON fe.category_id=fc.id
            WHERE fe.type='expense' AND fe.date>=? AND fe.date<?
            GROUP BY fc.id ORDER BY total DESC LIMIT 8
        """, (start_iso, end_iso))
        for cd in cat_data:
            row = QFrame(); row.setStyleSheet(f"background:{THEME['bg_secondary']};border-radius:8px;border:1px solid {THEME['border_subtle']};margin-bottom:3px;")
            rl = QHBoxLayout(row); rl.setContentsMargins(14,8,14,8)
            nl = QLabel(f"{cd.get('icon','')} {cd.get('name','')}"); nl.setStyleSheet(f"color:{cd.get('color',THEME['accent'])};background:transparent;border:none;font-size:12px;font-weight:700;"); nl.setFixedWidth(150)
            bar = QProgressBar(); pct = int((cd['total']/exp*100)) if exp>0 else 0; bar.setValue(pct); bar.setFixedHeight(6); bar.setTextVisible(False)
            bar.setStyleSheet(f"QProgressBar{{background:{THEME['bg_primary']};border:none;border-radius:3px;}} QProgressBar::chunk{{background:{cd.get('color',THEME['accent'])};border-radius:3px;}}")
            vl = QLabel(fmt_rial(cd['total'])); vl.setFixedWidth(140); vl.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
            vl.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;font-size:12px;font-weight:700;")
            rl.addWidget(nl); rl.addWidget(bar,1); rl.addWidget(vl)
            self.sum_layout.addWidget(row)

        # حساب‌ها
        acc_lbl = QLabel("🏦 موجودی حساب‌ها")
        acc_lbl.setFont(QFont("Segoe UI Variable",13,QFont.Weight.Bold)); acc_lbl.setStyleSheet(f"color:{THEME['text_primary']};margin-top:8px;")
        self.sum_layout.addWidget(acc_lbl)
        for acc in self.db.fetchall("SELECT * FROM bank_accounts"):
            color = acc.get('color',THEME['success'])
            inc_a = self.db.fetchone("SELECT SUM(amount) as s FROM finance_entries WHERE account_id=? AND type='income'",(acc['id'],))
            exp_a = self.db.fetchone("SELECT SUM(amount) as s FROM finance_entries WHERE account_id=? AND type='expense'",(acc['id'],))
            net = (acc.get('balance',0) or 0) + (inc_a['s'] or 0 if inc_a else 0) - (exp_a['s'] or 0 if exp_a else 0)
            row = QFrame(); row.setStyleSheet(f"background:{THEME['bg_secondary']};border-left:3px solid {color};border-radius:8px;border:1px solid {THEME['border_subtle']};margin-bottom:3px;")
            rl = QHBoxLayout(row); rl.setContentsMargins(14,10,14,10)
            nl = QLabel(f"🏦 {acc['name']}"); nl.setFont(QFont("Segoe UI Variable",12,QFont.Weight.Bold)); nl.setStyleSheet(f"color:{THEME['text_primary']};background:transparent;border:none;")
            vl = QLabel(fmt_rial(net)); vl.setFont(QFont("Segoe UI Variable",13,QFont.Weight.Bold)); vl.setStyleSheet(f"color:{color};background:transparent;border:none;")
            rl.addWidget(nl); rl.addStretch(); rl.addWidget(vl)
            self.sum_layout.addWidget(row)

        self.sum_layout.addStretch()

    # ── Entries ───────────────────────────────────────
    def _update_entries(self):
        ftype = self.filter_combo.currentData() if hasattr(self,'filter_combo') else 'all'
        base = "SELECT fe.*,fc.name as cat_name,fc.color as cat_color,fc.icon as cat_icon,ba.name as acc_name FROM finance_entries fe LEFT JOIN finance_categories fc ON fe.category_id=fc.id LEFT JOIN bank_accounts ba ON fe.account_id=ba.id"
        if ftype == 'all':
            entries = self.db.fetchall(f"{base} ORDER BY fe.date DESC LIMIT 100")
        else:
            entries = self.db.fetchall(f"{base} WHERE fe.type=? ORDER BY fe.date DESC LIMIT 100",(ftype,))

        self.entries_table.setRowCount(len(entries))
        for r,e in enumerate(entries):
            is_inc = e.get('type')=='income'
            acolor = THEME['success'] if is_inc else THEME['danger']
            sign   = '+' if is_inc else '-'
            dt = e.get('date','')
            if dt:
                try:
                    from datetime import date as _d; d=_d.fromisoformat(dt[:10]); jy,jm,jd=to_jalali(d.year,d.month,d.day); dt=format_jalali(jy,jm,jd)
                except Exception: pass
            cells = [
                (dt,                                                   THEME['text_secondary']),
                (e.get('description',''),                              THEME['text_primary']),
                (e.get('payee','') or '—',                            THEME['text_secondary']),
                ('💰 درآمد' if is_inc else '💸 هزینه',               acolor),
                (f"{e.get('cat_icon','')} {e.get('cat_name','—')}",  e.get('cat_color',THEME['text_secondary'])),
                (e.get('acc_name','—') or '—',                        THEME['text_secondary']),
                (f"{sign}{fmt_rial(e.get('amount',0))}",              acolor),
            ]
            for col,(text,fc) in enumerate(cells):
                item=QTableWidgetItem(text); item.setForeground(QColor(fc))
                item.setFlags(item.flags()&~Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole,e['id']); self.entries_table.setItem(r,col,item)
            self.entries_table.setRowHeight(r,40)

    # ── Accounts ──────────────────────────────────────
    def _update_accounts(self):
        accounts = self.db.fetchall("SELECT * FROM bank_accounts")
        self.accounts_table.setRowCount(len(accounts))
        for r,acc in enumerate(accounts):
            color = acc.get('color',THEME['success'])
            inc_a = self.db.fetchone("SELECT SUM(amount) as s FROM finance_entries WHERE account_id=? AND type='income'",(acc['id'],))
            exp_a = self.db.fetchone("SELECT SUM(amount) as s FROM finance_entries WHERE account_id=? AND type='expense'",(acc['id'],))
            net   = (acc.get('balance',0) or 0) + (inc_a['s'] or 0 if inc_a else 0) - (exp_a['s'] or 0 if exp_a else 0)
            cells = [
                (acc.get('name',''),        color),
                (acc.get('bank','') or '—', THEME['text_secondary']),
                (fmt_rial(acc.get('balance',0) or 0), THEME['text_secondary']),
                (fmt_rial(net),             THEME['success'] if net>=0 else THEME['danger']),
                ('',                         THEME['text_secondary']),
            ]
            for col,(text,fc) in enumerate(cells):
                item=QTableWidgetItem(text); item.setForeground(QColor(fc))
                item.setFlags(item.flags()&~Qt.ItemFlag.ItemIsEditable)
                self.accounts_table.setItem(r,col,item)
            aw=QWidget(); al=QHBoxLayout(aw); al.setContentsMargins(4,2,4,2); al.setSpacing(4)
            eb=QPushButton("✏️"); eb.setFixedSize(28,28); eb.setStyleSheet("QPushButton{background:transparent;border:none;font-size:12px;} QPushButton:hover{background:#333;border-radius:5px;}"); eb.clicked.connect(lambda _,a=acc:self._edit_account(a))
            db2=QPushButton("🗑️"); db2.setFixedSize(28,28); db2.setStyleSheet(f"QPushButton{{background:transparent;border:none;font-size:12px;}} QPushButton:hover{{background:{THEME['danger']}33;border-radius:5px;}}"); db2.clicked.connect(lambda _,aid=acc['id']:self._delete_account(aid))
            al.addWidget(eb); al.addWidget(db2); self.accounts_table.setCellWidget(r,4,aw)
            self.accounts_table.setRowHeight(r,44)

    # ── Payroll ───────────────────────────────────────
    def _update_payroll(self):
        entries = self.db.fetchall("SELECT * FROM payroll ORDER BY paid,due_date")
        projs   = {p['id']:p['name'] for p in self.db.fetchall("SELECT id,name FROM projects")}
        self.payroll_table.setRowCount(len(entries))
        period_labels = {'monthly':'ماهانه','weekly':'هفتگی','daily':'روزانه','project':'پروژه‌ای'}
        for r,e in enumerate(entries):
            due = e.get('due_date','')
            if due:
                try:
                    from datetime import date as _d; d=_d.fromisoformat(due[:10]); jy,jm,jd=to_jalali(d.year,d.month,d.day); due=format_jalali(jy,jm,jd)
                except Exception: pass
            paid = bool(e.get('paid',0)); color = THEME['success'] if paid else THEME['danger']
            cells = [
                (e.get('person',''),                              THEME['text_primary']),
                (e.get('role','') or '—',                        THEME['text_secondary']),
                (fmt_rial(e.get('amount',0) or 0),               THEME['warning']),
                (period_labels.get(e.get('period','monthly'),''),THEME['text_secondary']),
                (projs.get(e.get('project_id'),'—'),             THEME['text_secondary']),
                (due or '—',                                      THEME['text_tertiary']),
                ('✅ پرداخت شد' if paid else '❌ معوق',          color),
            ]
            for col,(text,fc) in enumerate(cells):
                item=QTableWidgetItem(text); item.setForeground(QColor(fc))
                item.setFlags(item.flags()&~Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole,e['id']); self.payroll_table.setItem(r,col,item)
            self.payroll_table.setRowHeight(r,40)

    def _toggle_paid(self, idx):
        item = self.payroll_table.item(idx.row(),0)
        if not item: return
        eid = item.data(Qt.ItemDataRole.UserRole)
        if not eid: return
        entry = self.db.fetchone("SELECT * FROM payroll WHERE id=?",(eid,))
        if not entry: return
        new_paid = 0 if entry.get('paid',0) else 1
        self.db.execute("UPDATE payroll SET paid=? WHERE id=?",(new_paid,eid))
        self._update_payroll()

    # ── CRUD ─────────────────────────────────────────
    def _new_entry(self):
        dlg = FinanceEntryDialog(self.db, parent=self)
        if dlg.exec():
            d = dlg.result_data
            self.db.execute("INSERT INTO finance_entries(description,payee,type,category_id,account_id,project_id,amount,date) VALUES(?,?,?,?,?,?,?,?)",(d['description'],d['payee'],d['type'],d['category_id'],d['account_id'],d['project_id'],d['amount'],d['date']))
            self.refresh()

    def _delete_entry(self):
        item = self.entries_table.item(self.entries_table.currentRow(),0)
        if item:
            eid = item.data(Qt.ItemDataRole.UserRole)
            if eid: self.db.execute("DELETE FROM finance_entries WHERE id=?",(eid,)); self.refresh()

    def _new_account(self):
        dlg = AccountDialog(self.db, parent=self)
        if dlg.exec():
            d = dlg.result_data
            self.db.execute("INSERT INTO bank_accounts(name,bank,balance,color) VALUES(?,?,?,?)",(d['name'],d['bank'],d['balance'],d['color']))
            self.refresh()

    def _edit_account(self, acc):
        dlg = AccountDialog(self.db, account=acc, parent=self)
        if dlg.exec():
            d = dlg.result_data
            self.db.execute("UPDATE bank_accounts SET name=?,bank=?,balance=?,color=? WHERE id=?",(d['name'],d['bank'],d['balance'],d['color'],acc['id']))
            self.refresh()

    def _delete_account(self, aid):
        msg=QMessageBox(self); msg.setWindowTitle("حذف حساب"); msg.setText("آیا مطمئنید؟")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        msg.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};")
        if msg.exec()==QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM bank_accounts WHERE id=?",(aid,)); self.refresh()

    def _new_payroll(self):
        dlg = PayrollDialog(self.db, parent=self)
        if dlg.exec():
            d = dlg.result_data
            self.db.execute("INSERT INTO payroll(person,role,amount,period,project_id,due_date,notes) VALUES(?,?,?,?,?,?,?)",(d['person'],d['role'],d['amount'],d['period'],d['project_id'],d['due_date'],d['notes']))
            self.refresh()

    def _manage_cats(self):
        dlg = FinanceCategoryDialog(self.db, parent=self)
        dlg.exec(); self.refresh()
