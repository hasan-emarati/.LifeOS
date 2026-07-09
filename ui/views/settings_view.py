"""Settings Dialog v2"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QMessageBox, QWidget, QGridLayout,
    QStyle, QSizePolicy
)
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import QFont, QMouseEvent, QPainter, QColor, QIcon
from ui.theme import THEME, THEMES, apply_theme, current_theme_name, get_stylesheet

THEME_LABELS = {
    "dark":     ("🌙 تاریک",    "#0f0f14"),
    "light":    ("☀️ روشن",     "#f8fafc"),
    "midnight": ("🌌 نیمه‌شب",  "#060608"),
    "forest":   ("🌿 جنگل",     "#0a110d"),
}


class SettingsDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        # Frameless like main window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog
        )
        self.setMinimumWidth(520)
        self.setMinimumHeight(440)
        self.setStyleSheet(
            f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};"
        )
        self._drag_pos = QPoint()
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Custom title bar ─────────────────────────
        titlebar = QWidget()
        titlebar.setFixedHeight(40)
        titlebar.setStyleSheet(
            f"background:{THEME['titlebar_bg']};"
            f"border-bottom:1px solid {THEME['border_subtle']};"
        )
        tbl = QHBoxLayout(titlebar)
        tbl.setContentsMargins(16, 0, 8, 0)
        tbl.setSpacing(8)

        tbl.addWidget(QLabel("⚙️  تنظیمات", font=QFont("Segoe UI Variable", 12, QFont.Weight.Bold),
                             styleSheet=f"color:{THEME['titlebar_text']};background:transparent;border:none;"))
        tbl.addStretch()

        close_btn = QPushButton()
        std_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton)
        px = std_icon.pixmap(16, 16)
        painter = QPainter(px)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(px.rect(), QColor("white"))
        painter.end()
        close_btn.setIcon(QIcon(px))
        close_btn.setIconSize(QSize(16, 16))
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:6px;}"
            "QPushButton:hover{background:#ef4444;}"
        )
        close_btn.clicked.connect(self.accept)
        tbl.addWidget(close_btn)

        titlebar.mousePressEvent  = self._mouse_press
        titlebar.mouseMoveEvent   = self._mouse_move
        root.addWidget(titlebar)

        # ── Content ─────────────────────────────────
        content = QWidget()
        content.setStyleSheet(f"background:{THEME['bg_secondary']};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(28, 22, 28, 22)
        cl.setSpacing(18)

        # ── Theme chooser ────────────────────────────
        th_lbl = QLabel("🎨  انتخاب تم")
        th_lbl.setFont(QFont("Segoe UI Variable", 13, QFont.Weight.Bold))
        th_lbl.setStyleSheet(f"color:{THEME['text_secondary']};")
        cl.addWidget(th_lbl)

        grid = QGridLayout(); grid.setSpacing(12)
        self._theme_btns = {}
        for col_i, (key, (label, preview_bg)) in enumerate(THEME_LABELS.items()):
            btn = QPushButton(label)
            btn.setFixedHeight(54)
            active = (key == current_theme_name())
            self._style_theme_btn(btn, key, preview_bg, active)
            btn.clicked.connect(lambda _, k=key: self._set_theme(k))
            self._theme_btns[key] = btn
            grid.addWidget(btn, 0, col_i)
        cl.addLayout(grid)

        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{THEME['border_subtle']};")
        cl.addWidget(sep)

        # ── Danger zone ──────────────────────────────
        danger_lbl = QLabel("⚠️  منطقه خطر")
        danger_lbl.setFont(QFont("Segoe UI Variable", 13, QFont.Weight.Bold))
        danger_lbl.setStyleSheet(f"color:{THEME['danger']};")
        cl.addWidget(danger_lbl)

        danger_card = QFrame()
        danger_card.setStyleSheet(f"""
            QFrame {{
                background:{THEME['danger']}0d;
                border:1px solid {THEME['danger']}33;
                border-radius:12px;
            }}
        """)
        dcl = QVBoxLayout(danger_card)
        dcl.setContentsMargins(20, 16, 20, 16)
        dcl.setSpacing(10)

        info = QLabel(
            "با پاک‌کردن داده‌ها تمام پروژه‌ها، تسک‌ها، اهداف، عادت‌ها و\n"
            "گزارش‌های شما برای همیشه حذف می‌شوند."
        )
        info.setStyleSheet(f"color:{THEME['text_secondary']};font-size:12px;")
        info.setWordWrap(True)
        dcl.addWidget(info)

        reset_btn = QPushButton("🗑️  پاک‌کردن همه داده‌ها")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background:{THEME['danger']}22; color:{THEME['danger']};
                border:2px solid {THEME['danger']}66; border-radius:10px;
                padding:10px 20px; font-size:13px; font-weight:700;
            }}
            QPushButton:hover {{ background:{THEME['danger']}; color:white; }}
        """)
        reset_btn.clicked.connect(self._confirm_reset)
        dcl.addWidget(reset_btn)
        cl.addWidget(danger_card)
        cl.addStretch()

        close_all = QPushButton("✓  بستن")
        close_all.setFixedHeight(44)
        close_all.clicked.connect(self.accept)
        cl.addWidget(close_all)

        root.addWidget(content)

    def _style_theme_btn(self, btn, key, bg, active):
        border = THEME['accent'] if active else THEME['border_default']
        btn.setStyleSheet(f"""
            QPushButton {{
                background:{bg}; color:white;
                border:2px solid {border}; border-radius:10px;
                font-size:12px; font-weight:{'700' if active else '400'};
            }}
            QPushButton:hover {{ border-color:{THEME['accent_light']}; }}
        """)

    def _set_theme(self, name):
        apply_theme(name)
        self.db.set_setting("theme", name)
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().setStyleSheet(get_stylesheet())
        for key, btn in self._theme_btns.items():
            _, preview_bg = THEME_LABELS[key]
            self._style_theme_btn(btn, key, preview_bg, key == name)

    def _confirm_reset(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("⚠️ تأیید پاک‌کردن")
        msg.setText("آیا کاملاً مطمئنید؟\n\nاین عمل غیرقابل بازگشت است.")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.button(QMessageBox.StandardButton.Yes).setText("بله، پاک کن")
        msg.button(QMessageBox.StandardButton.No).setText("انصراف")
        msg.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};")
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.db.reset_all_data()
            ok = QMessageBox(self)
            ok.setWindowTitle("✅ انجام شد")
            ok.setText("تمام داده‌ها پاک شدند.")
            ok.setStyleSheet(f"background:{THEME['bg_secondary']};color:{THEME['text_primary']};")
            ok.exec()
            self.accept()

    def _mouse_press(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _mouse_move(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(e.globalPosition().toPoint() - self._drag_pos)
