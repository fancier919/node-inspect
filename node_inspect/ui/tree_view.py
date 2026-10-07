"""VS Code style TreeView with custom delegate, badges, and lazy expansion triggers."""

import json
from typing import Optional
from PySide6.QtCore import Qt, QModelIndex, QRect, Signal, QSortFilterProxyModel
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtWidgets import (
    QTreeView, QStyledItemDelegate, QStyleOptionViewItem,
    QMenu, QApplication, QStyle
)

from node_inspect.core.node_model import NodeItem, NodeTreeModel
from node_inspect.ui.theme import COLORS, get_type_color


class NodeItemDelegate(QStyledItemDelegate):
    """Custom delegate to render VS Code style type badges and values."""

    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        try:
            from node_inspect.ui.theme import ThemeManager
            colors = ThemeManager.get_colors()

            col = index.column()

            # Selection background
            if option.state & QStyle.StateFlag.State_Selected:
                painter.fillRect(option.rect, QColor(colors["bg_selected"]))
            elif option.state & QStyle.StateFlag.State_MouseOver:
                painter.fillRect(option.rect, QColor(colors["bg_hover"]))

            text = index.data(Qt.ItemDataRole.DisplayRole) or ""

            if col == 0:
                # Key / Variable name column
                painter.setPen(QColor(colors["text_heading"]))
                font = QFont(option.font)
                font.setBold(True)
                painter.setFont(font)

                # Draw subtle indent guide line if nested
                level = 0
                p = index.parent()
                while p.isValid():
                    level += 1
                    p = p.parent()

                text_rect = option.rect.adjusted(6, 0, -6, 0)
                painter.drawText(text_rect, int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), text)

            elif col == 1:
                # Type badge column with theme palette (fg, bg, border)
                fg_color, bg_color, bd_color = ThemeManager.get_type_palette(text)

                badge_rect = option.rect.adjusted(2, 2, -2, -2)
                badge_font = QFont(option.font)
                badge_font.setPointSize(8)
                badge_font.setBold(True)
                painter.setFont(badge_font)

                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance(text) + 8
                pill_rect = QRect(badge_rect.left(), badge_rect.top(), min(tw, badge_rect.width()), badge_rect.height())

                painter.setBrush(bg_color)
                painter.setPen(QPen(bd_color, 1))
                painter.drawRoundedRect(pill_rect, 2, 2)

                painter.setPen(fg_color)
                painter.drawText(pill_rect, int(Qt.AlignmentFlag.AlignCenter), text)

            elif col == 2:
                # Summary / Value column
                painter.setFont(option.font)
                item: Optional[NodeItem] = index.data(Qt.ItemDataRole.UserRole)
                if item and item.is_special_lazy and not item.is_explicitly_expanded:
                    painter.setPen(QColor(colors["warning"]))
                else:
                    painter.setPen(QColor(colors["text_main"]))

                text_rect = option.rect.adjusted(6, 0, -6, 0)
                painter.drawText(text_rect, int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), text)

        finally:
            painter.restore()


class FilterProxyModel(QSortFilterProxyModel):
    """Filter model to filter tree nodes by key or type."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRecursiveFilteringEnabled(True)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        regex = self.filterRegularExpression()
        if not regex or regex.pattern() == "":
            return True

        source_model = self.sourceModel()
        # Check Key (Col 0) or Type (Col 1)
        idx_key = source_model.index(source_row, 0, source_parent)
        idx_type = source_model.index(source_row, 1, source_parent)
        idx_val = source_model.index(source_row, 2, source_parent)

        key_str = str(source_model.data(idx_key, Qt.ItemDataRole.DisplayRole) or "")
        type_str = str(source_model.data(idx_type, Qt.ItemDataRole.DisplayRole) or "")
        val_str = str(source_model.data(idx_val, Qt.ItemDataRole.DisplayRole) or "")

        pattern = regex.pattern().lower()
        if pattern in key_str.lower() or pattern in type_str.lower() or pattern in val_str.lower():
            return True

        return super().filterAcceptsRow(source_row, source_parent)


class NodeTreeView(QTreeView):
    """VS Code style TreeView with smooth expansion and context menu."""

    node_selected = Signal(str, object, str, str)  # key, raw_value, type, summary
    special_node_expanded = Signal(str)           # triggered message

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setItemDelegate(NodeItemDelegate(self))
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True)
        self.setAnimated(True)

        self.doubleClicked.connect(self._on_double_clicked)
        self.clicked.connect(self._on_clicked)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _get_node_item(self, index: QModelIndex) -> Optional[NodeItem]:
        if not index.isValid():
            return None
        # Handle proxy model if wrapped
        if isinstance(self.model(), QSortFilterProxyModel):
            src_index = self.model().mapToSource(index)
            return src_index.data(Qt.ItemDataRole.UserRole)
        return index.data(Qt.ItemDataRole.UserRole)

    def _on_clicked(self, index: QModelIndex):
        item = self._get_node_item(index)
        if item:
            self.node_selected.emit(item.key, item.raw_value, item.data_type, item.summary)

    def _on_double_clicked(self, index: QModelIndex):
        """Trigger lazy expansion for special types (ndarray, DataFrame, etc.)."""
        item = self._get_node_item(index)
        if not item:
            return

        model = self.model()
        src_model = model.sourceModel() if isinstance(model, QSortFilterProxyModel) else model
        src_index = model.mapToSource(index) if isinstance(model, QSortFilterProxyModel) else index

        # If it's a special lazy item, expand its children and notify
        if item.is_special_lazy and not item.is_explicitly_expanded:
            if isinstance(src_model, NodeTreeModel):
                src_model.expand_special_node(src_index)
                self.expand(index)
                self.special_node_expanded.emit(f"Expanded details for '{item.key}' ({item.data_type})")
        else:
            # Normal toggle
            if self.isExpanded(index):
                self.collapse(index)
            else:
                self.expand(index)

        self.node_selected.emit(item.key, item.raw_value, item.data_type, item.summary)

    def _show_context_menu(self, pos):
        index = self.indexAt(pos)
        if not index.isValid():
            return

        item = self._get_node_item(index)
        if not item:
            return

        menu = QMenu(self)

        copy_val_action = menu.addAction("Copy Value")
        copy_key_action = menu.addAction("Copy Key Name")
        copy_type_action = menu.addAction("Copy Type")
        menu.addSeparator()

        expand_all_action = menu.addAction("Expand All")
        collapse_all_action = menu.addAction("Collapse All")

        action = menu.exec(self.viewport().mapToGlobal(pos))
        clipboard = QApplication.clipboard()

        if action == copy_val_action:
            try:
                if isinstance(item.raw_value, (dict, list)):
                    clipboard.setText(json.dumps(item.raw_value, indent=2, ensure_ascii=False, default=str))
                else:
                    clipboard.setText(str(item.raw_value))
            except Exception:
                clipboard.setText(str(item.summary))
        elif action == copy_key_action:
            clipboard.setText(item.key)
        elif action == copy_type_action:
            clipboard.setText(item.data_type)
        elif action == expand_all_action:
            self.expandRecursively(index)
        elif action == collapse_all_action:
            self.collapse(index)
