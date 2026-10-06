"""Theme and styling for NodeInspect supporting both Soft Gray Light and VS Code Dark+ themes."""

from typing import Dict, Any, Tuple
from PySide6.QtGui import QColor

# 1. Soft Gray Light Theme Palette (Soft neutral gray, glare-free)
LIGHT_COLORS = {
    "bg_main": "#f8f9fa",
    "bg_sidebar": "#f4f4f7",
    "bg_alternate": "#edeff2",
    "bg_panel": "#ffffff",
    "bg_header": "#e4e4e8",
    "bg_toolbar": "#e8e8ec",
    "bg_button": "#f4f4f6",
    "bg_button_hover": "#ffffff",
    "bg_input": "#ffffff",
    "bg_hover": "#eaebee",
    "bg_selected": "#dbeafe",
    "bg_badge": "#ebecef",
    "border": "#d0d0d4",
    "border_light": "#e4e4e7",
    "text_main": "#24292f",
    "text_heading": "#1f2328",
    "text_muted": "#6e7781",
    "accent": "#0969da",
    "accent_hover": "#085ec2",
    "accent_subtle": "#dbeafe",
    "accent_text": "#ffffff",
    "success": "#1a7f37",
    "warning": "#92400e",
    "error": "#cf222e",
}

LIGHT_TYPE_COLORS = {
    "str": ("#b35900", "#fff1e5", "#f5c299"),
    "bytes": ("#b35900", "#fff1e5", "#f5c299"),
    "int": ("#0969da", "#eff6ff", "#bfdbfe"),
    "float": ("#0969da", "#eff6ff", "#bfdbfe"),
    "complex": ("#0969da", "#eff6ff", "#bfdbfe"),
    "bool": ("#1d4ed8", "#eff6ff", "#bfdbfe"),
    "None": ("#8250df", "#f5f3ff", "#ddd6fe"),
    "dict": ("#854d0e", "#fef9c3", "#fde047"),
    "list": ("#854d0e", "#fef9c3", "#fde047"),
    "tuple": ("#854d0e", "#fef9c3", "#fde047"),
    "set": ("#854d0e", "#fef9c3", "#fde047"),
    "ndarray": ("#0f766e", "#e6fffa", "#99f6e4"),
    "DataFrame": ("#0f766e", "#e6fffa", "#99f6e4"),
    "Series": ("#0f766e", "#e6fffa", "#99f6e4"),
    "Table": ("#0f766e", "#e6fffa", "#99f6e4"),
    "unknown": ("#0969da", "#eff6ff", "#bfdbfe"),
}

# 2. VS Code Dark+ Theme Palette
DARK_COLORS = {
    "bg_main": "#1e1e1e",
    "bg_sidebar": "#252526",
    "bg_alternate": "#232324",
    "bg_panel": "#1e1e1e",
    "bg_header": "#2d2d2d",
    "bg_toolbar": "#252526",
    "bg_button": "#333333",
    "bg_button_hover": "#3e3e42",
    "bg_input": "#3c3c3c",
    "bg_hover": "#2a2d2e",
    "bg_selected": "#04395e",
    "bg_badge": "#333333",
    "border": "#3c3c3c",
    "border_light": "#454545",
    "text_main": "#cccccc",
    "text_heading": "#ffffff",
    "text_muted": "#858585",
    "accent": "#007acc",
    "accent_hover": "#1f8ad2",
    "accent_subtle": "#264f78",
    "accent_text": "#ffffff",
    "success": "#89d185",
    "warning": "#cca700",
    "error": "#f14c4c",
}

DARK_TYPE_COLORS = {
    "str": ("#ce9178", "#2b2b2b", "#ce9178"),
    "bytes": ("#ce9178", "#2b2b2b", "#ce9178"),
    "int": ("#4fc1ff", "#2b2b2b", "#4fc1ff"),
    "float": ("#4fc1ff", "#2b2b2b", "#4fc1ff"),
    "complex": ("#4fc1ff", "#2b2b2b", "#4fc1ff"),
    "bool": ("#569cd6", "#2b2b2b", "#569cd6"),
    "None": ("#c586c0", "#2b2b2b", "#c586c0"),
    "dict": ("#dcdcaa", "#2b2b2b", "#dcdcaa"),
    "list": ("#dcdcaa", "#2b2b2b", "#dcdcaa"),
    "tuple": ("#dcdcaa", "#2b2b2b", "#dcdcaa"),
    "set": ("#dcdcaa", "#2b2b2b", "#dcdcaa"),
    "ndarray": ("#4ec9b0", "#2b2b2b", "#4ec9b0"),
    "DataFrame": ("#4ec9b0", "#2b2b2b", "#4ec9b0"),
    "Series": ("#4ec9b0", "#2b2b2b", "#4ec9b0"),
    "Table": ("#4ec9b0", "#2b2b2b", "#4ec9b0"),
    "unknown": ("#9cdcfe", "#2b2b2b", "#9cdcfe"),
}


class ThemeManager:
    """Manages active theme state and colors."""

    CURRENT_THEME = "light"  # Default to Soft Gray Light

    @classmethod
    def set_theme(cls, theme_name: str):
        if theme_name in ("light", "dark"):
            cls.CURRENT_THEME = theme_name

    @classmethod
    def is_dark(cls) -> bool:
        return cls.CURRENT_THEME == "dark"

    @classmethod
    def get_colors(cls) -> Dict[str, str]:
        return DARK_COLORS if cls.is_dark() else LIGHT_COLORS

    @classmethod
    def get_type_palette(cls, type_name: str) -> Tuple[QColor, QColor, QColor]:
        """Return (text_color, bg_color, border_color)."""
        color_map = DARK_TYPE_COLORS if cls.is_dark() else LIGHT_TYPE_COLORS
        fg, bg, bd = color_map.get(type_name, (cls.get_colors()["accent"], cls.get_colors()["bg_badge"], cls.get_colors()["border"]))
        return QColor(fg), QColor(bg), QColor(bd)


# Global helper references for backward compatibility
COLORS = LIGHT_COLORS


def get_type_color(type_name: str) -> QColor:
    fg, _, _ = ThemeManager.get_type_palette(type_name)
    return fg


def generate_stylesheet(theme_name: str = "light") -> str:
    c = DARK_COLORS if theme_name == "dark" else LIGHT_COLORS
    is_light = theme_name == "light"

    return f"""
QMainWindow {{
    background-color: {c["bg_main"]};
    color: {c["text_main"]};
}}

QWidget {{
    font-family: 'Segoe UI', 'SF Pro Text', 'Helvetica Neue', 'Noto Sans', sans-serif;
    font-size: 11px;
    color: {c["text_main"]};
    background-color: transparent;
}}

/* Toolbar */
QToolBar {{
    background-color: {c["bg_toolbar"]};
    border-bottom: 1px solid {c["border"]};
    padding: 2px 4px;
    spacing: 4px;
}}

QToolButton, QPushButton {{
    background-color: {c["bg_button"]};
    border: 1px solid {c["border"]};
    border-radius: 3px;
    padding: 2px 7px;
    color: {c["text_main"]};
    font-size: 11px;
    font-weight: 500;
}}

QToolButton:hover, QPushButton:hover {{
    background-color: {c["bg_button_hover"]};
    border-color: {c["accent"]};
    color: {c["text_heading"]};
}}

QToolButton:pressed, QPushButton:pressed {{
    background-color: {c["accent"]};
    color: {c["accent_text"]};
}}

/* Search and Inputs */
QLineEdit {{
    background-color: {c["bg_input"]};
    border: 1px solid {c["border"]};
    border-radius: 3px;
    padding: 2px 6px;
    font-size: 11px;
    color: {c["text_heading"]};
    selection-background-color: {c["accent"]};
}}

QLineEdit:focus {{
    border: 1px solid {c["accent"]};
}}

/* Tree View */
QTreeView {{
    background-color: {c["bg_sidebar"]};
    alternate-background-color: {c["bg_alternate"]};
    border: none;
    border-right: 1px solid {c["border"]};
    show-decoration-selected: 1;
    font-family: 'Cascadia Code', 'Consolas', 'Segoe UI Mono', monospace;
    font-size: 11px;
    color: {c["text_main"]};
}}

QTreeView::item {{
    height: 20px;
    padding: 1px 2px;
    border-radius: 2px;
}}

QTreeView::item:hover {{
    background-color: {c["bg_hover"]};
}}

QTreeView::item:selected {{
    background-color: {c["bg_selected"]};
    color: {c["text_heading"]};
}}

QHeaderView::section {{
    background-color: {c["bg_header"]};
    color: {c["text_muted"]};
    padding: 2px 6px;
    border: none;
    border-right: 1px solid {c["border"]};
    border-bottom: 1px solid {c["border"]};
    font-weight: 600;
    font-size: 10px;
    text-transform: uppercase;
}}

/* Splitter */
QSplitter::handle {{
    background-color: {c["border"]};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

QSplitter::handle:hover {{
    background-color: {c["accent"]};
}}

/* Detail Inspector Pane */
QWidget#detailInspector {{
    background-color: {c["bg_main"]};
}}

QWidget#inspectorHeader {{
    background-color: {c["bg_header"]};
    border-bottom: 1px solid {c["border"]};
    border-radius: 3px;
}}

QLabel#inspectorTitle {{
    font-size: 11px;
    font-weight: bold;
    color: {c["text_heading"]};
}}

QLabel#inspectorSummary {{
    font-size: 10px;
    color: {c["text_muted"]};
}}

/* Table View in Detail Inspector */
QTableView {{
    background-color: {c["bg_panel"]};
    border: none;
    gridline-color: {c["border_light"]};
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 11px;
    color: {c["text_main"]};
    selection-background-color: {c["accent_subtle"]};
    selection-color: {c["text_heading"]};
}}

QTableView::item {{
    padding: 2px 4px;
}}

QTableView::item:hover {{
    background-color: {c["bg_hover"]};
}}

/* Raw Text Inspector */
QPlainTextEdit {{
    background-color: {c["bg_panel"]};
    color: {c["text_main"]};
    border: none;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 11px;
    selection-background-color: {c["accent_subtle"]};
}}

/* Scrollbars */
QScrollBar:vertical {{
    border: none;
    background: {c["bg_sidebar"]};
    width: 8px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {"#c5c5ca" if is_light else "#424242"};
    min-height: 16px;
    border-radius: 3px;
    margin: 1px;
}}

QScrollBar::handle:vertical:hover {{
    background: {"#a5a5aa" if is_light else "#4f4f4f"};
}}

QScrollBar:horizontal {{
    border: none;
    background: {c["bg_sidebar"]};
    height: 8px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background: {"#c5c5ca" if is_light else "#424242"};
    min-width: 16px;
    border-radius: 3px;
    margin: 1px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {"#a5a5aa" if is_light else "#4f4f4f"};
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0px;
    height: 0px;
}}

/* Status Bar */
QStatusBar {{
    background-color: {c["accent"]};
    color: {c["accent_text"]};
    font-size: 11px;
    font-weight: 500;
    min-height: 18px;
}}

QStatusBar QLabel {{
    color: {c["accent_text"]};
    padding: 0 6px;
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {c["border"]};
    background-color: {c["bg_panel"]};
}}

QTabBar::tab {{
    background-color: {c["bg_header"]};
    color: {c["text_muted"]};
    padding: 3px 10px;
    border-top-left-radius: 3px;
    border-top-right-radius: 3px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {c["bg_panel"]};
    color: {c["accent"] if is_light else c["text_heading"]};
    border-top: 2px solid {c["accent"]};
    font-weight: 600;
}}

QTabBar::tab:hover:!selected {{
    background-color: {c["bg_hover"]};
    color: {c["text_main"]};
}}

/* Menu */
QMenu {{
    background-color: {c["bg_panel"]};
    color: {c["text_main"]};
    border: 1px solid {c["border"]};
    padding: 2px;
}}

QMenu::item {{
    padding: 3px 18px 3px 16px;
    border-radius: 2px;
}}

QMenu::item:selected {{
    background-color: {c["accent"]};
    color: {c["accent_text"]};
}}

QMenu::separator {{
    height: 1px;
    background: {c["border"]};
    margin: 2px 4px;
}}
"""


# Default stylesheet is soft gray light
VSCODE_STYLE_SHEET = generate_stylesheet("light")
