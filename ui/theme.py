"""
Design System v2 — تم‌های متعدد + فونت Segoe UI Variable
"""
from PyQt6.QtGui import QFont, QFontDatabase

THEMES = {
    "dark": {
        "bg_primary":    "#0f0f14",
        "bg_secondary":  "#16161e",
        "bg_tertiary":   "#1e1e2a",
        "bg_hover":      "#252535",
        "bg_active":     "#2d2d42",
        "accent":        "#7c3aed",
        "accent_light":  "#8b5cf6",
        "accent_glow":   "#6d28d9",
        "success":       "#10b981",
        "warning":       "#f59e0b",
        "danger":        "#ef4444",
        "info":          "#3b82f6",
        "xp_gold":       "#f59e0b",
        "xp_platinum":   "#a78bfa",
        "streak_fire":   "#f97316",
        "text_primary":  "#f1f5f9",
        "text_secondary":"#94a3b8",
        "text_tertiary": "#475569",
        "text_accent":   "#a78bfa",
        "border_subtle": "#1e293b",
        "border_default":"#334155",
        "border_focus":  "#7c3aed",
        "priority_critical":"#ef4444",
        "priority_high": "#f97316",
        "priority_medium":"#eab308",
        "priority_low":  "#22c55e",
        "scrollbar_bg":  "#1e1e2a",
        "scrollbar_handle":"#334155",
        "titlebar_bg":   "#0d0d12",
        "titlebar_text": "#f1f5f9",
    },
    "light": {
        "bg_primary":    "#f8fafc",
        "bg_secondary":  "#ffffff",
        "bg_tertiary":   "#f1f5f9",
        "bg_hover":      "#e2e8f0",
        "bg_active":     "#cbd5e1",
        "accent":        "#7c3aed",
        "accent_light":  "#8b5cf6",
        "accent_glow":   "#6d28d9",
        "success":       "#059669",
        "warning":       "#d97706",
        "danger":        "#dc2626",
        "info":          "#2563eb",
        "xp_gold":       "#d97706",
        "xp_platinum":   "#7c3aed",
        "streak_fire":   "#ea580c",
        "text_primary":  "#0f172a",
        "text_secondary":"#475569",
        "text_tertiary": "#94a3b8",
        "text_accent":   "#7c3aed",
        "border_subtle": "#e2e8f0",
        "border_default":"#cbd5e1",
        "border_focus":  "#7c3aed",
        "priority_critical":"#dc2626",
        "priority_high": "#ea580c",
        "priority_medium":"#ca8a04",
        "priority_low":  "#16a34a",
        "scrollbar_bg":  "#f1f5f9",
        "scrollbar_handle":"#cbd5e1",
        "titlebar_bg":   "#f1f5f9",
        "titlebar_text": "#0f172a",
    },
    "midnight": {
        "bg_primary":    "#060608",
        "bg_secondary":  "#0e0e14",
        "bg_tertiary":   "#141420",
        "bg_hover":      "#1a1a28",
        "bg_active":     "#222234",
        "accent":        "#06b6d4",
        "accent_light":  "#22d3ee",
        "accent_glow":   "#0891b2",
        "success":       "#10b981",
        "warning":       "#f59e0b",
        "danger":        "#ef4444",
        "info":          "#6366f1",
        "xp_gold":       "#fbbf24",
        "xp_platinum":   "#22d3ee",
        "streak_fire":   "#f97316",
        "text_primary":  "#e2e8f0",
        "text_secondary":"#94a3b8",
        "text_tertiary": "#475569",
        "text_accent":   "#22d3ee",
        "border_subtle": "#0f172a",
        "border_default":"#1e293b",
        "border_focus":  "#06b6d4",
        "priority_critical":"#ef4444",
        "priority_high": "#f97316",
        "priority_medium":"#eab308",
        "priority_low":  "#22c55e",
        "scrollbar_bg":  "#0e0e14",
        "scrollbar_handle":"#1e293b",
        "titlebar_bg":   "#040406",
        "titlebar_text": "#e2e8f0",
    },
    "forest": {
        "bg_primary":    "#0a110d",
        "bg_secondary":  "#111a14",
        "bg_tertiary":   "#18241c",
        "bg_hover":      "#1f2e24",
        "bg_active":     "#263a2d",
        "accent":        "#22c55e",
        "accent_light":  "#4ade80",
        "accent_glow":   "#16a34a",
        "success":       "#4ade80",
        "warning":       "#facc15",
        "danger":        "#f87171",
        "info":          "#60a5fa",
        "xp_gold":       "#facc15",
        "xp_platinum":   "#86efac",
        "streak_fire":   "#fb923c",
        "text_primary":  "#ecfdf5",
        "text_secondary":"#86efac",
        "text_tertiary": "#4ade80",
        "text_accent":   "#86efac",
        "border_subtle": "#14271a",
        "border_default":"#1a3323",
        "border_focus":  "#22c55e",
        "priority_critical":"#f87171",
        "priority_high": "#fb923c",
        "priority_medium":"#facc15",
        "priority_low":  "#4ade80",
        "scrollbar_bg":  "#111a14",
        "scrollbar_handle":"#1a3323",
        "titlebar_bg":   "#070e09",
        "titlebar_text": "#ecfdf5",
    },
}

THEME = THEMES["dark"].copy()   # active theme (mutable)
_current_theme_name = "dark"


def apply_theme(name: str):
    global THEME, _current_theme_name
    if name in THEMES:
        THEME.clear()
        THEME.update(THEMES[name])
        _current_theme_name = name


def current_theme_name() -> str:
    return _current_theme_name


def get_stylesheet() -> str:
    t = THEME
    return f"""
* {{
    font-family: 'Segoe UI Variable', 'Segoe UI', 'B Nazanin', Tahoma, sans-serif;
    outline: none;
}}
QMainWindow, QWidget {{
    background-color: {t['bg_primary']};
    color: {t['text_primary']};
}}
QLabel {{
    color: {t['text_primary']};
    background: transparent;
}}

/* ── Scrollbars ─────────────────────────────────── */
QScrollBar:vertical {{
    background:{t['scrollbar_bg']}; width:7px; border-radius:3px;
}}
QScrollBar::handle:vertical {{
    background:{t['scrollbar_handle']}; border-radius:3px; min-height:32px;
}}
QScrollBar::handle:vertical:hover {{ background:{t['accent']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
QScrollBar:horizontal {{
    background:{t['scrollbar_bg']}; height:7px; border-radius:3px;
}}
QScrollBar::handle:horizontal {{
    background:{t['scrollbar_handle']}; border-radius:3px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width:0; }}

/* ── Buttons ─────────────────────────────────────── */
QPushButton {{
    background:{t['accent']}; color:white; border:none;
    border-radius:8px; padding:8px 18px;
    font-size:13px; font-weight:600;
}}
QPushButton:hover  {{ background:{t['accent_light']}; }}
QPushButton:pressed {{ background:{t['accent_glow']}; }}
QPushButton.secondary {{
    background:{t['bg_tertiary']}; color:{t['text_primary']};
    border:1px solid {t['border_default']};
}}
QPushButton.secondary:hover {{
    background:{t['bg_hover']}; border-color:{t['accent']};
}}
QPushButton.danger  {{ background:{t['danger']}; }}
QPushButton.success {{ background:{t['success']}; }}

/* ── Inputs ──────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
    background:{t['bg_tertiary']}; color:{t['text_primary']};
    border:1px solid {t['border_default']}; border-radius:8px;
    padding:8px 12px; font-size:13px;
    selection-background-color:{t['accent']};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color:{t['accent']}; background:{t['bg_hover']};
}}
QSpinBox:focus, QDoubleSpinBox:focus {{ border-color:{t['accent']}; }}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background:{t['bg_hover']}; border:none; width:16px;
}}

/* ── ComboBox ────────────────────────────────────── */
QComboBox {{
    background:{t['bg_tertiary']}; color:{t['text_primary']};
    border:1px solid {t['border_default']}; border-radius:8px;
    padding:6px 12px; font-size:13px; min-width:120px;
}}
QComboBox:hover {{ border-color:{t['accent']}; }}
QComboBox::drop-down {{ border:none; width:22px; }}
QComboBox::down-arrow {{
    border-left:5px solid transparent; border-right:5px solid transparent;
    border-top:5px solid {t['text_secondary']}; width:0; height:0;
}}
QComboBox QAbstractItemView {{
    background:{t['bg_secondary']}; color:{t['text_primary']};
    border:1px solid {t['border_default']}; border-radius:8px;
    selection-background-color:{t['accent']}; padding:4px;
}}

/* ── Tables / Lists / Trees ──────────────────────── */
QTableWidget, QTreeWidget, QListWidget {{
    background:{t['bg_secondary']}; color:{t['text_primary']};
    border:1px solid {t['border_subtle']}; border-radius:10px;
    gridline-color:{t['border_subtle']}; font-size:13px;
}}
QTableWidget::item, QTreeWidget::item, QListWidget::item {{
    padding:8px; border-bottom:1px solid {t['border_subtle']};
}}
QTableWidget::item:selected, QListWidget::item:selected {{
    background:{t['accent']}; color:white;
}}
QTableWidget::item:hover, QListWidget::item:hover {{
    background:{t['bg_hover']};
}}
QHeaderView::section {{
    background:{t['bg_tertiary']}; color:{t['text_secondary']};
    border:none; border-bottom:1px solid {t['border_default']};
    padding:10px 8px; font-size:11px; font-weight:700;
    letter-spacing:0.5px;
}}

/* ── Tabs ────────────────────────────────────────── */
QTabWidget::pane {{
    border:1px solid {t['border_subtle']}; border-radius:10px;
    background:{t['bg_secondary']}; top:-1px;
}}
QTabBar::tab {{
    background:transparent; color:{t['text_secondary']}; border:none;
    padding:10px 20px; font-size:13px; font-weight:500;
    border-radius:8px; margin-right:4px;
}}
QTabBar::tab:selected {{ background:{t['accent']}; color:white; font-weight:700; }}
QTabBar::tab:hover:!selected {{ background:{t['bg_hover']}; color:{t['text_primary']}; }}

/* ── Progress Bars ───────────────────────────────── */
QProgressBar {{
    background:{t['bg_tertiary']}; border:none; border-radius:5px;
    height:8px; color:transparent;
}}
QProgressBar::chunk {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {t['accent']}, stop:1 {t['accent_light']});
    border-radius:5px;
}}

/* ── Checkboxes ──────────────────────────────────── */
QCheckBox {{ color:{t['text_primary']}; spacing:8px; font-size:13px; }}
QCheckBox::indicator {{
    width:18px; height:18px; border-radius:5px;
    border:2px solid {t['border_default']}; background:{t['bg_tertiary']};
}}
QCheckBox::indicator:checked {{
    background:{t['accent']}; border-color:{t['accent']};
}}
QCheckBox::indicator:hover {{ border-color:{t['accent']}; }}

/* ── DateEdit ────────────────────────────────────── */
QDateEdit, QTimeEdit, QDateTimeEdit {{
    background:{t['bg_tertiary']}; color:{t['text_primary']};
    border:1px solid {t['border_default']}; border-radius:8px;
    padding:6px 12px; font-size:13px;
}}
QDateEdit:focus, QTimeEdit:focus {{ border-color:{t['accent']}; }}
QCalendarWidget {{
    background:{t['bg_secondary']}; color:{t['text_primary']};
}}
QCalendarWidget QToolButton {{
    background:{t['accent']}; color:white; border-radius:6px; padding:4px 8px;
}}
QCalendarWidget QAbstractItemView {{
    background:{t['bg_secondary']}; color:{t['text_primary']};
    selection-background-color:{t['accent']};
}}

/* ── Dialogs ─────────────────────────────────────── */
QDialog {{ background:{t['bg_secondary']}; color:{t['text_primary']}; }}

/* ── Splitter ────────────────────────────────────── */
QSplitter::handle {{ background:{t['border_subtle']}; width:2px; }}

/* ── Slider ──────────────────────────────────────── */
QSlider::groove:horizontal {{
    border-radius:4px; height:6px; background:{t['bg_tertiary']};
}}
QSlider::handle:horizontal {{
    background:{t['accent']}; border-radius:9px;
    width:18px; height:18px; margin:-6px 0;
}}
QSlider::sub-page:horizontal {{
    background:{t['accent']}; border-radius:4px;
}}

/* ── Tooltip ─────────────────────────────────────── */
QToolTip {{
    background:{t['bg_tertiary']}; color:{t['text_primary']};
    border:1px solid {t['border_default']}; border-radius:6px; padding:6px 10px;
    font-size:12px;
}}

/* ── Menu ────────────────────────────────────────── */
QMenu {{
    background:{t['bg_secondary']}; border:1px solid {t['border_default']};
    border-radius:10px; padding:6px;
}}
QMenu::item {{
    padding:8px 16px; border-radius:6px;
    color:{t['text_primary']}; font-size:13px;
}}
QMenu::item:selected {{ background:{t['accent']}; color:white; }}
QMenu::separator {{ height:1px; background:{t['border_subtle']}; margin:4px 0; }}

/* ── GroupBox ────────────────────────────────────── */
QGroupBox {{
    border:1px solid {t['border_default']}; border-radius:10px;
    margin-top:16px; padding:16px; font-size:13px; font-weight:600;
    color:{t['text_secondary']};
}}
QGroupBox::title {{
    subcontrol-origin:margin; left:12px; top:-8px;
    background:{t['bg_secondary']}; padding:0 6px;
}}

/* ── MessageBox ──────────────────────────────────── */
QMessageBox {{
    background:{t['bg_secondary']}; color:{t['text_primary']};
}}
QMessageBox QPushButton {{ min-width:80px; }}
"""
