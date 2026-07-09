"""Custom frameless title bar with native icons"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QStyle
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import QFont, QMouseEvent, QPainter, QColor, QIcon
from ui.theme import THEME


class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos = QPoint()
        self.setFixedHeight(42)
        self._build()

    def _build(self):
        self.setStyleSheet(f"""
            QWidget {{
                background:{THEME['titlebar_bg']};
                border-bottom:1px solid {THEME['border_subtle']};
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 8, 0)
        lay.setSpacing(8)

        icon = QLabel("🧠")
        icon.setFont(QFont("Segoe UI Emoji", 14))
        icon.setStyleSheet("background:transparent;border:none;")

        title = QLabel("LifeOS")
        title.setFont(QFont("Segoe UI Variable", 12, QFont.Weight.Bold))
        title.setStyleSheet(
            f"color:{THEME['titlebar_text']};background:transparent;border:none;"
        )

        lay.addWidget(icon)
        lay.addWidget(title)
        lay.addStretch()

        buttons = [
            (QStyle.StandardPixmap.SP_TitleBarMinButton,  "کوچک کردن", "#f59e0b", self._minimize),
            (QStyle.StandardPixmap.SP_TitleBarMaxButton,  "بزرگ/کوچک", "#10b981", self._maximize),
            (QStyle.StandardPixmap.SP_TitleBarCloseButton,"بستن",       "#ef4444", self._close),
        ]

        for icon_type, tip, hover_color, fn in buttons:
            btn = QPushButton()
            std_icon = self.style().standardIcon(icon_type)
            pixmap = std_icon.pixmap(18, 18)
            painter = QPainter(pixmap)
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceIn
            )
            painter.fillRect(pixmap.rect(), QColor("white"))
            painter.end()
            btn.setIcon(QIcon(pixmap))
            btn.setIconSize(QSize(18, 18))
            btn.setFixedSize(32, 32)
            btn.setToolTip(tip)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background:transparent;
                    border:none;
                    border-radius:6px;
                }}
                QPushButton:hover {{
                    background:{hover_color};
                }}
            """)
            btn.clicked.connect(fn)
            lay.addWidget(btn)

    def _minimize(self): self.window().showMinimized()
    def _maximize(self):
        w = self.window()
        w.showNormal() if w.isMaximized() else w.showMaximized()
    def _close(self): self.window().close()

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                e.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, e: QMouseEvent):
        if e.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.window().move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseDoubleClickEvent(self, e): self._maximize()
