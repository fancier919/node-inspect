"""Theme and styling for NodeInspect with VS Code Dark+ look and feel."""

from PySide6.QtGui import QColor, QFont

# VS Code Dark+ Color Palette
COLORS = {
    "bg_main": "#1e1e1e",
    "bg_sidebar": "#252526",
    "bg_panel": "#181818",
    "bg_header": "#2d2d2d",
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
    "success": "#89d185",
    "warning": "#cca700",
    "error": "#f14c4c",
}

# Type badge colors
TYPE_COLORS = {
    "str": "#ce9178",           # VS Code string orange
    "bytes": "#ce9178",
    "int": "#4fc1ff",           # Light blue
    "float": "#4fc1ff",
    "complex": "#4fc1ff",
    "bool": "#569cd6",          # Keyword blue
    "None": "#c586c0",          # Purple
    "dict": "#dcdcaa",          # Yellowish
    "list": "#dcdcaa",
    "tuple": "#dcdcaa",
    "set": "#dcdcaa",
    "ndarray": "#4ec9b0",        # Teal / Class green
    "DataFrame": "#4ec9b0",
    "Series": "#4ec9b0",
    "Table": "#4ec9b0",
    "unknown": "#9cdcfe",
}


def get_type_color(type_name: str) -> QColor:
    hex_code = TYPE_COLORS.get(type_name, COLORS["accent"])
    return QColor(hex_code)


VSCODE_STYLE_SHEET = """
QMainWindow {
    background-color: #1e1e1e;
    color: #cccccc;
}

QWidget {
    font-family: 'Segoe UI', 'SF Pro Text', 'Helvetica Neue', 'Noto Sans', sans-serif;
    font-size: 13px;
    color: #cccccc;
    background-color: transparent;
}

/* Toolbar & Header */
QToolBar {
    background-color: #252526;
    border-bottom: 1px solid #3c3c3c;
    padding: 4px 8px;
    spacing: 6px;
}

QToolButton {
    background-color: #333333;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 4px 10px;
    color: #cccccc;
    font-weight: 500;
}

QToolButton:hover {
    background-color: #3e3e42;
    border-color: #007acc;
    color: #ffffff;
}

QToolButton:pressed {
    background-color: #007acc;
    color: #ffffff;
}

/* Search and Filter Inputs */
QLineEdit {
    background-color: #3c3c3c;
    border: 1px solid #454545;
    border-radius: 3px;
    padding: 4px 8px;
    color: #ffffff;
    selection-background-color: #007acc;
}

QLineEdit:focus {
    border: 1px solid #007acc;
    background-color: #383838;
}

/* Tree View */
QTreeView {
    background-color: #252526;
    alternate-background-color: #232324;
    border: none;
    border-right: 1px solid #3c3c3c;
    show-decoration-selected: 1;
    font-family: 'Cascadia Code', 'Consolas', 'Segoe UI Mono', monospace;
    font-size: 12px;
}

QTreeView::item {
    height: 26px;
    padding: 2px 4px;
    border-radius: 2px;
}

QTreeView::item:hover {
    background-color: #2a2d2e;
}

QTreeView::item:selected {
    background-color: #04395e;
    color: #ffffff;
}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    image: none;
    border-image: none;
}

QHeaderView::section {
    background-color: #2d2d2d;
    color: #858585;
    padding: 5px 8px;
    border: none;
    border-right: 1px solid #3c3c3c;
    border-bottom: 1px solid #3c3c3c;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
}

/* Splitter */
QSplitter::handle {
    background-color: #3c3c3c;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QSplitter::handle:hover {
    background-color: #007acc;
}

/* Detail Table View */
QTableView {
    background-color: #1e1e1e;
    border: none;
    gridline-color: #2d2d2d;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px;
    selection-background-color: #264f78;
    selection-color: #ffffff;
}

QTableView::item {
    padding: 4px;
}

QTableView::item:hover {
    background-color: #2a2d2e;
}

/* PlainText / JSON Inspector */
QPlainTextEdit {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: none;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px;
    selection-background-color: #264f78;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #1e1e1e;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #424242;
    min-height: 20px;
    border-radius: 4px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background: #4f4f4f;
}

QScrollBar:horizontal {
    border: none;
    background: #1e1e1e;
    height: 10px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #424242;
    min-width: 20px;
    border-radius: 4px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background: #4f4f4f;
}

QScrollBar::add-line, QScrollBar::sub-line {
    width: 0px;
    height: 0px;
}

/* Status Bar */
QStatusBar {
    background-color: #007acc;
    color: #ffffff;
    font-size: 12px;
    font-weight: 500;
    min-height: 22px;
}

QStatusBar QLabel {
    color: #ffffff;
    padding: 0 8px;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #3c3c3c;
    background-color: #1e1e1e;
}

QTabBar::tab {
    background-color: #2d2d2d;
    color: #969696;
    padding: 6px 14px;
    border-top-left-radius: 3px;
    border-top-right-radius: 3px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #1e1e1e;
    color: #ffffff;
    border-top: 2px solid #007acc;
}

QTabBar::tab:hover:!selected {
    background-color: #383838;
    color: #cccccc;
}

/* Menu */
QMenu {
    background-color: #252526;
    border: 1px solid #454545;
    padding: 4px;
}

QMenu::item {
    padding: 5px 24px 5px 20px;
    border-radius: 3px;
}

QMenu::item:selected {
    background-color: #094771;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background: #3c3c3c;
    margin: 4px 8px;
}
"""
