"""Detail inspector view for displaying tables (DataFrame, ndarray) and formatted raw values."""

import json
from typing import Any, Optional
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal, QSize
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QTableView, QPlainTextEdit, QPushButton, QHeaderView, QApplication,
    QSizePolicy
)

from node_inspect.ui.theme import COLORS, get_type_color


class DataFrameTableModel(QAbstractTableModel):
    """Virtual table model for Pandas DataFrame and Series with fast pagination limit."""

    def __init__(self, df: Any, parent=None, max_rows: int = 5000):
        super().__init__(parent)
        self.max_rows = max_rows
        # If it's a Series, convert to DataFrame
        if hasattr(df, "to_frame"):
            df = df.to_frame()

        self._full_rows = len(df)
        self.df = df.iloc[:max_rows] if len(df) > max_rows else df
        self.columns = [str(c) for c in self.df.columns]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.df)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.columns)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if 0 <= section < len(self.columns):
                    return self.columns[section]
            elif orientation == Qt.Orientation.Vertical:
                return str(self.df.index[section])
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            try:
                val = self.df.iat[index.row(), index.column()]
                if val is None or (isinstance(val, float) and str(val) == "nan"):
                    return "NaN"
                return str(val)
            except Exception:
                return ""
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        return None


class NdarrayTableModel(QAbstractTableModel):
    """Virtual table model for 1D / 2D NumPy ndarrays."""

    def __init__(self, arr: Any, parent=None, max_rows: int = 5000, max_cols: int = 100):
        super().__init__(parent)
        self.arr = arr
        self.max_rows = max_rows
        self.max_cols = max_cols

        if arr.ndim == 1:
            self.rows = min(len(arr), max_rows)
            self.cols = 1
        elif arr.ndim == 2:
            self.rows = min(arr.shape[0], max_rows)
            self.cols = min(arr.shape[1], max_cols)
        else:
            self.rows = 0
            self.cols = 0

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return self.rows

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return self.cols

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return f"[{section}]" if self.arr.ndim == 2 else "Value"
            elif orientation == Qt.Orientation.Vertical:
                return f"[{section}]"
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            try:
                r, c = index.row(), index.column()
                if self.arr.ndim == 1:
                    return str(self.arr[r])
                elif self.arr.ndim == 2:
                    return str(self.arr[r, c])
            except Exception:
                return ""
        return None


class DetailInspectorWidget(QWidget):
    """Right pane widget to inspect selected node details."""

    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_value: Any = None
        # Allow flexible shrinking so contents do not force resize on parent splitter
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self._init_ui()

    def sizeHint(self) -> QSize:
        return QSize(360, 200)

    def minimumSizeHint(self) -> QSize:
        return QSize(120, 100)

    def _init_ui(self):
        self.setObjectName("detailInspector")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header Info Bar container
        header_container = QWidget(self)
        header_container.setObjectName("inspectorHeader")
        header_bar = QHBoxLayout(header_container)
        header_bar.setContentsMargins(4, 3, 4, 3)
        header_bar.setSpacing(4)

        self.title_label = QLabel("Details", header_container)
        self.title_label.setObjectName("inspectorTitle")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.type_badge = QLabel("", header_container)
        self.type_badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.type_badge.hide()

        self.summary_label = QLabel("", header_container)
        self.summary_label.setObjectName("inspectorSummary")
        self.summary_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)

        self.copy_btn = QPushButton("Copy", header_container)
        self.copy_btn.setFixedSize(45, 20)
        self.copy_btn.clicked.connect(self._copy_content)

        self.close_btn = QPushButton("✕", header_container)
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setToolTip("Close Panel")
        self.close_btn.setStyleSheet(
            "background-color: transparent; border: none; font-size: 11px; font-weight: bold;"
        )
        self.close_btn.clicked.connect(self._on_close_clicked)

        header_bar.addWidget(self.title_label)
        header_bar.addWidget(self.type_badge)
        header_bar.addWidget(self.summary_label)
        header_bar.addWidget(self.copy_btn)
        header_bar.addWidget(self.close_btn)

        layout.addWidget(header_container)

        # Tab Widget for Table and Raw / Text view
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # 1. Table View Tab
        self.table_view = QTableView(self)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_view.horizontalHeader().setDefaultSectionSize(80)
        self.table_view.verticalHeader().setDefaultSectionSize(19)
        self.tab_widget.addTab(self.table_view, "Table")

        # 2. Raw Text / JSON Tab
        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.tab_widget.addTab(self.text_edit, "Raw / JSON")

        self._text_dirty = True
        self._current_data_type = ""

        layout.addWidget(self.tab_widget)

    def _on_close_clicked(self):
        self.hide()
        self.closed.emit()

    def _on_tab_changed(self, index: int):
        """Render text view lazily only when Raw / JSON tab is activated."""
        if index == 1 and self._text_dirty:
            self._update_text_content()

    def _update_text_content(self):
        """Build preview string for Raw / JSON tab."""
        value = self.current_value
        data_type = self._current_data_type
        text_content = ""
        try:
            if isinstance(value, (dict, list)):
                text_content = json.dumps(value, indent=2, ensure_ascii=False, default=str)
            elif data_type == "DataFrame":
                col_preview = list(value.columns)
                if len(col_preview) > 50:
                    col_preview_str = str(col_preview[:50]) + f"\n... ({len(col_preview) - 50} more columns omitted)"
                else:
                    col_preview_str = str(col_preview)

                dtype_preview = str(value.dtypes.head(50))
                if len(value.columns) > 50:
                    dtype_preview += f"\n... ({len(value.columns) - 50} more dtypes omitted)"

                head_preview = str(value.head(10))
                text_content = (
                    f"Shape: {value.shape[0]} rows × {value.shape[1]} cols\n\n"
                    f"Columns:\n{col_preview_str}\n\n"
                    f"Data Types:\n{dtype_preview}\n\n"
                    f"Head (10 rows):\n{head_preview}"
                )
            elif data_type == "Series":
                head_preview = str(value.head(10))
                text_content = (
                    f"Length: {len(value)}, Dtype: {value.dtype}\n\n"
                    f"Head (10 items):\n{head_preview}"
                )
            elif data_type == "ndarray":
                text_content = (
                    f"ndarray details:\n"
                    f"Shape: {value.shape}\n"
                    f"Dtype: {value.dtype}\n"
                    f"Size: {value.size}\n"
                    f"Nbytes: {value.nbytes} bytes\n\n"
                    f"Array representation:\n{str(value)}"
                )
            else:
                text_content = str(value)
        except Exception as e:
            text_content = f"<Error inspecting value: {e}>\n{repr(value)}"

        self.text_edit.setPlainText(text_content)
        self._text_dirty = False

    def display_node(self, key: str, value: Any, data_type: str, summary: str):
        """Update inspector with node information."""
        from node_inspect.ui.theme import ThemeManager
        colors = ThemeManager.get_colors()
        fg, bg, bd = ThemeManager.get_type_palette(data_type)

        self.current_value = value
        self._current_data_type = data_type
        self._text_dirty = True

        self.title_label.setText(f"{key}")
        self.title_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {colors['text_heading']};")

        self.type_badge.setText(data_type)
        self.type_badge.setStyleSheet(
            f"background-color: {bg.name()}; color: {fg.name()}; border: 1px solid {bd.name()}; padding: 1px 5px; border-radius: 3px; font-weight: 600; font-size: 10px;"
        )
        self.type_badge.show()

        self.summary_label.setText(summary)
        self.summary_label.setToolTip(summary)

        # Check if table representation is applicable
        is_table = False

        if data_type in ("DataFrame", "Series") or (hasattr(value, "__class__") and value.__class__.__name__ in ("DataFrame", "Series")):
            try:
                model = DataFrameTableModel(value, self)
                self.table_view.setModel(model)
                is_table = True
            except Exception:
                pass

        elif data_type == "ndarray" or (hasattr(value, "__class__") and value.__class__.__name__ == "ndarray"):
            try:
                if value.ndim in (1, 2):
                    model = NdarrayTableModel(value, self)
                    self.table_view.setModel(model)
                    is_table = True
            except Exception:
                pass

        # Update Tab selection
        if is_table:
            self.tab_widget.setTabVisible(0, True)
            self.tab_widget.setCurrentIndex(0)
        else:
            self.tab_widget.setTabVisible(0, False)
            self.tab_widget.setCurrentIndex(1)
            self._update_text_content()

    def _copy_content(self):
        """Copy current inspector content to clipboard."""
        clipboard = QApplication.clipboard()
        if self.tab_widget.currentIndex() == 0 and hasattr(self.current_value, "to_csv"):
            try:
                clipboard.setText(self.current_value.head(1000).to_csv(index=True))
                return
            except Exception:
                pass
        clipboard.setText(self.text_edit.toPlainText())
