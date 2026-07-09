"""
Base dialog with custom title bar — همه dialog های برنامه از این ارث می‌برند
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QStyle, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import QFont, QMouseEvent, QPainter, QColor, QIcon
from ui.theme import THEME


class ThemedTitleBar(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._drag_pos = QPoint()
        self.setFixedHeight(40)
        self._build(title)

    def _build(self, title: str):
        self.setStyleSheet(f"""
            QWidget {{
                background:{THEME['titlebar_bg']};
                border-bottom:1px solid {THEME['border_subtle']};
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 8, 0)
        lay.setSpacing(10)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI Variable", 12, QFont.Weight.Bold))
        title_lbl.setStyleSheet(
            f"color:{THEME['titlebar_text']};background:transparent;border:none;"
        )
        lay.addWidget(title_lbl)
        lay.addStretch()

        close_btn = QPushButton()
        std_icon = self.style().standardIcon(
            QStyle.StandardPixmap.SP_TitleBarCloseButton
        )
        px = std_icon.pixmap(16, 16)
        painter = QPainter(px)
        painter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_SourceIn
        )
        painter.fillRect(px.rect(), QColor("white"))
        painter.end()
        close_btn.setIcon(QIcon(px))
        close_btn.setIconSize(QSize(16, 16))
        close_btn.setFixedSize(30, 30)
        close_btn.setToolTip("بستن")
        close_btn.setStyleSheet("""
            QPushButton { background:transparent; border:none; border-radius:6px; }
            QPushButton:hover { background:#ef4444; }
        """)
        close_btn.clicked.connect(self.window().close)
        lay.addWidget(close_btn)

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                e.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, e: QMouseEvent):
        if e.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.window().move(e.globalPosition().toPoint() - self._drag_pos)


class ThemedDialog(QDialog):
    """Base dialog with frameless + custom titlebar.

    برای اینکه پنجره‌های باز شونده از پس‌زمینه‌ی پنجره‌ی اصلی متمایز و
    زیباتر به نظر برسند، به‌جای پس‌زمینه‌ی صاف قبلی، یک کارت گرد با
    گرادیان و سایه‌ی نرم دور محتوا کشیده می‌شود.
    """
    def __init__(self, title: str = "LifeOS", parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Dialog
        )
        # پس‌زمینه‌ی خود QDialog کاملاً شفاف می‌شود تا فقط "کارت" گرد داخلش دیده بشه
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # فاصله‌ی بیرونی برای جا دادن سایه‌ی نرم دور کارت
        shadow_margin = 18

        outer = QVBoxLayout(self)
        outer.setContentsMargins(shadow_margin, shadow_margin, shadow_margin, shadow_margin)
        outer.setSpacing(0)

        # کارت اصلی: گرادیان بین bg_tertiary و bg_secondary + بوردر ملایم
        self._card = QWidget(objectName="themedDialogCard")
        self._card.setStyleSheet(f"""
            #themedDialogCard {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {THEME['bg_tertiary']},
                    stop:1 {THEME['bg_secondary']}
                );
                border: 1px solid {THEME['border_default']};
                border-radius: 14px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self._card)
        shadow.setBlurRadius(36)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 160))
        self._card.setGraphicsEffect(shadow)
        outer.addWidget(self._card)

        self._card_lay = QVBoxLayout(self._card)
        self._card_lay.setContentsMargins(0, 0, 0, 0)
        self._card_lay.setSpacing(0)

        self._title_bar = ThemedTitleBar(title, self)
        # گوشه‌های بالای تایتل‌بار هم‌راستا با گردی کارت
        self._title_bar.setStyleSheet(self._title_bar.styleSheet().replace(
            "border-bottom", "border-top-left-radius:14px;border-top-right-radius:14px;border-bottom"
        ))
        self._card_lay.addWidget(self._title_bar)

        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._content_lay = QVBoxLayout(self._content)
        self._content_lay.setContentsMargins(24, 20, 24, 24)
        self._content_lay.setSpacing(12)
        self._card_lay.addWidget(self._content)

    def content_layout(self):
        return self._content_lay

    def set_title(self, title: str):
        for i in range(self._title_bar.layout().count()):
            w = self._title_bar.layout().itemAt(i).widget()
            if isinstance(w, QLabel):
                w.setText(title)
                break
