"""XP sidebar widget"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ui.theme import THEME

def xp_for_level(level: int) -> int:
    return level * 100 + (level - 1) * 50

class XPWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build()
        self.refresh()

    def _build(self):
        self.setStyleSheet(f"""
            QWidget {{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {THEME['accent']}22, stop:1 {THEME['bg_tertiary']});
                border:1px solid {THEME['accent']}44;
                border-radius:10px;margin:8px 12px;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(5)

        level_row = QHBoxLayout()
        self.level_lbl = QLabel("⭐ سطح ۱")
        self.level_lbl.setFont(QFont("Segoe UI Variable", 11, QFont.Weight.Bold))
        self.level_lbl.setStyleSheet(
            f"color:{THEME['xp_gold']};background:transparent;border:none;"
        )
        self.xp_lbl = QLabel("0 XP")
        self.xp_lbl.setFont(QFont("Segoe UI Variable", 10))
        self.xp_lbl.setStyleSheet(
            f"color:{THEME['text_secondary']};background:transparent;border:none;"
        )
        level_row.addWidget(self.level_lbl)
        level_row.addStretch()
        level_row.addWidget(self.xp_lbl)
        lay.addLayout(level_row)

        self.xp_bar = QProgressBar()
        self.xp_bar.setFixedHeight(6)
        self.xp_bar.setTextVisible(False)
        self.xp_bar.setStyleSheet(f"""
            QProgressBar{{background:{THEME['bg_primary']};border:none;border-radius:3px;}}
            QProgressBar::chunk{{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {THEME['xp_gold']}, stop:1 {THEME['accent_light']});
                border-radius:3px;
            }}
        """)
        lay.addWidget(self.xp_bar)

        self.streak_lbl = QLabel("🔥 ۰ روز متوالی")
        self.streak_lbl.setFont(QFont("Segoe UI Variable", 10))
        self.streak_lbl.setStyleSheet(
            f"color:{THEME['streak_fire']};background:transparent;border:none;"
        )
        lay.addWidget(self.streak_lbl)

    def refresh(self):
        stats = self.db.fetchone("SELECT * FROM user_stats LIMIT 1")
        if not stats:
            return
        level     = stats.get('level', 1)
        total_xp  = stats.get('total_xp', 0)
        streak    = stats.get('streak_days', 0)
        xp_needed = xp_for_level(level)
        xp_prev   = xp_for_level(level - 1) if level > 1 else 0
        progress  = total_xp - xp_prev
        needed    = xp_needed - xp_prev
        pct       = int((progress / max(needed, 1)) * 100)

        self.level_lbl.setText(f"⭐ سطح {level}")
        self.xp_lbl.setText(f"{total_xp:,} XP")
        self.xp_bar.setValue(min(pct, 100))
        self.streak_lbl.setText(f"🔥 {streak} روز متوالی")
