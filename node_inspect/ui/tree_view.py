"""VS Code style TreeView with custom delegate, badges, and lazy expansion triggers."""

import json
import os
from typing import Optional
from PySide6.QtCore import Qt, QModelIndex, QRect, Signal, QSortFilterProxyModel
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtWidgets import (
    QTreeView, QStyledItemDelegate, QStyleOptionViewItem,
    QMenu, QApplication, QStyle
)

from node_inspect.core.node_model import NodeItem, NodeTreeModel
from node_inspect.core.config import ConfigManager
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
    action_triggered = Signal(str)                # user feedback message

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

    def _get_base_dir(self) -> Optional[str]:
        """Get directory of currently opened file from main window parent if available."""
        main_win = self.window()
        if hasattr(main_win, "current_file_path") and main_win.current_file_path:
            return os.path.dirname(main_win.current_file_path)
        return None

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

    def _execute_custom_action(self, action: dict, item: NodeItem):
        """Execute configured action command replacing placeholders."""
        import subprocess
        base_dir = self._get_base_dir()
        current_file = getattr(self.window(), "current_file_path", "") or ""

        cmd_template = action.get("command", "")
        if not cmd_template:
            return

        resolved_path = ConfigManager.resolve_existing_path(item.raw_value, base_dir) or str(item.raw_value)

        # Placeholders
        cmd = cmd_template.replace("{value}", str(resolved_path))
        cmd = cmd.replace("{key}", str(item.key))
        cmd = cmd.replace("{file_path}", str(current_file))
        cmd = cmd.replace("{base_dir}", str(base_dir or ""))

        try:
            subprocess.Popen(cmd, shell=True)
            self.action_triggered.emit(f"Executed: {cmd}")
        except Exception as e:
            self.action_triggered.emit(f"Failed to execute action: {e}")

    def _open_in_default_program(self, path: str):
        """Open file or folder in OS default program."""
        try:
            os.startfile(path)
            self.action_triggered.emit(f"Opened: {os.path.basename(path)}")
        except Exception as e:
            self.action_triggered.emit(f"Failed to open '{path}': {e}")

    def _on_double_clicked(self, index: QModelIndex):
        """Handle double-click: trigger custom action / default program or lazy expand."""
        item = self._get_node_item(index)
        if not item:
            return

        base_dir = self._get_base_dir()

        # 1. Check if matching custom action is configured
        matched_action = ConfigManager.find_matching_action(item.key, item.raw_value)
        if matched_action:
            self._execute_custom_action(matched_action, item)
            self.node_selected.emit(item.key, item.raw_value, item.data_type, item.summary)
            return

        # 2. Check if item value is a valid file or folder path
        resolved_path = ConfigManager.resolve_existing_path(item.raw_value, base_dir)
        if resolved_path:
            self._open_in_default_program(resolved_path)
            self.node_selected.emit(item.key, item.raw_value, item.data_type, item.summary)
            return

        # 3. Otherwise standard tree expansion
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

        base_dir = self._get_base_dir()
        resolved_path = ConfigManager.resolve_existing_path(item.raw_value, base_dir)
        matched_action = ConfigManager.find_matching_action(item.key, item.raw_value)

        menu = QMenu(self)

        # Context action: Open with Default Program
        if resolved_path:
            open_default_action = menu.addAction(f"🚀 Open in Default App ({os.path.basename(resolved_path)})")
        else:
            open_default_action = None

        # Context action: Execute Custom Script
        if matched_action:
            label = matched_action.get("name") or "⚡ Run Custom Action"
            custom_action = menu.addAction(label)
        else:
            custom_action = None

        if open_default_action or custom_action:
            menu.addSeparator()

        copy_val_action = menu.addAction("Copy Value")
        copy_key_action = menu.addAction("Copy Key Name")
        copy_type_action = menu.addAction("Copy Type")
        if resolved_path:
            copy_path_action = menu.addAction("Copy Full Path")
        else:
            copy_path_action = None

        menu.addSeparator()

        expand_all_action = menu.addAction("Expand All")
        collapse_all_action = menu.addAction("Collapse All")

        action = menu.exec(self.viewport().mapToGlobal(pos))
        clipboard = QApplication.clipboard()

        if open_default_action and action == open_default_action:
            self._open_in_default_program(resolved_path)
        elif custom_action and action == custom_action:
            self._execute_custom_action(matched_action, item)
        elif action == copy_val_action:
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
        elif copy_path_action and action == copy_path_action:
            clipboard.setText(resolved_path)
        elif action == expand_all_action:
            self.expandRecursively(index)
        elif action == collapse_all_action:
            self.collapse(index)

