"""Tree data model and lazy loading nodes for NodeInspect."""

from __future__ import annotations
import math
from typing import Any, List, Optional
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt


def format_bytes(num_bytes: int) -> str:
    """Format bytes to human readable string."""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    elif num_bytes < 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{num_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_type_and_summary(value: Any) -> tuple[str, str, bool, bool]:
    """Inspect a value and return (type_name, summary, is_container, is_special_lazy).

    Returns:
        type_name: Readable type name.
        summary: Short summary preview string.
        is_container: Whether it can have child nodes in the tree.
        is_special_lazy: Whether it is a special type (ndarray, DataFrame, etc.) requiring explicit expansion.
    """
    val_type = type(value).__name__

    # 1. Check None
    if value is None:
        return "None", "None", False, False

    # 2. Check Booleans
    if isinstance(value, bool):
        return "bool", str(value), False, False

    # 3. Check Numerics
    if isinstance(value, (int, float, complex)):
        if isinstance(value, float):
            return "float", f"{value:.6g}", False, False
        return type(value).__name__, str(value), False, False

    # 4. Check Strings & Bytes & Path
    import pathlib
    if isinstance(value, (pathlib.Path, pathlib.PurePath)):
        p_str = str(value)
        short = p_str if len(p_str) <= 60 else p_str[:57] + "..."
        return "Path", f'"{short}"', False, False

    if isinstance(value, str):
        short = value if len(value) <= 60 else value[:57] + "..."
        return "str", f'"{short}" ({len(value)} chars)', False, False

    if isinstance(value, (bytes, bytearray)):
        return type(value).__name__, f"<{len(value)} bytes>", False, False

    # 5. Check NumPy ndarray
    if hasattr(value, "__class__") and value.__class__.__name__ == "ndarray" and hasattr(value, "shape"):
        shape_str = str(value.shape)
        dtype_str = str(getattr(value, "dtype", "unknown"))
        nbytes = getattr(value, "nbytes", 0)
        size_str = format_bytes(nbytes)
        summary = f"shape={shape_str}, dtype={dtype_str}, {size_str}"
        return "ndarray", summary, True, True

    # 6. Check Pandas DataFrame
    if hasattr(value, "__class__") and value.__class__.__name__ == "DataFrame" and hasattr(value, "shape"):
        rows, cols = value.shape
        try:
            mem = value.memory_usage(deep=False).sum()
            mem_str = f", mem={format_bytes(mem)}"
        except Exception:
            mem_str = ""
        summary = f"({rows} rows × {cols} cols){mem_str}"
        return "DataFrame", summary, True, True

    # 7. Check Pandas Series
    if hasattr(value, "__class__") and value.__class__.__name__ == "Series" and hasattr(value, "shape"):
        size = len(value)
        dtype_str = str(getattr(value, "dtype", "unknown"))
        summary = f"({size} items, dtype={dtype_str})"
        return "Series", summary, True, True

    # 8. Check PyArrow Table
    if hasattr(value, "__class__") and "Table" in value.__class__.__name__ and hasattr(value, "num_rows"):
        summary = f"({value.num_rows} rows × {value.num_columns} cols)"
        return "Table", summary, True, True

    # 9. Standard Dict / Mapping
    if isinstance(value, dict):
        count = len(value)
        summary = f"{{{count} {'entry' if count == 1 else 'entries'}}}"
        return "dict", summary, count > 0, False

    # 10. Standard List / Tuple / Set
    if isinstance(value, (list, tuple, set, frozenset)):
        count = len(value)
        t_name = type(value).__name__
        summary = f"[{count} {'item' if count == 1 else 'items'}]" if t_name == "list" else f"({count} items)"
        return t_name, summary, count > 0, False

    # Fallback for generic objects
    rep = str(value)
    if len(rep) > 60:
        rep = rep[:57] + "..."
    return val_type, rep, hasattr(value, "__dict__"), False


class NodeItem:
    """A node in the hierarchical tree structure supporting lazy child loading."""

    def __init__(self, key: str, value: Any, parent: Optional[NodeItem] = None):
        self.key: str = str(key)
        self.raw_value: Any = value
        self.parent: Optional[NodeItem] = parent
        self.children: List[NodeItem] = []

        type_name, summary, is_container, is_special_lazy = get_type_and_summary(value)
        self.data_type: str = type_name
        self.summary: str = summary
        self.is_container: bool = is_container
        self.is_special_lazy: bool = is_special_lazy

        # Has children been generated?
        self.is_loaded: bool = False
        # If special lazy, has user explicitly triggered expansion (double-click)?
        self.is_explicitly_expanded: bool = not is_special_lazy

    def child_count(self) -> int:
        self._ensure_loaded()
        return len(self.children)

    def child(self, row: int) -> Optional[NodeItem]:
        self._ensure_loaded()
        if 0 <= row < len(self.children):
            return self.children[row]
        return None

    def row(self) -> int:
        if self.parent:
            return self.parent.children.index(self)
        return 0

    def trigger_special_expand(self) -> bool:
        """User explicitly triggered expansion (e.g. double click)."""
        if self.is_special_lazy and not self.is_explicitly_expanded:
            self.is_explicitly_expanded = True
            self.is_loaded = False
            self.children.clear()
            self._ensure_loaded()
            return True
        return False

    def _ensure_loaded(self):
        """Populate child nodes on demand."""
        if self.is_loaded or not self.is_container:
            return

        # If it's a special lazy item and user hasn't explicitly expanded it, do not load children yet
        if self.is_special_lazy and not self.is_explicitly_expanded:
            self.is_loaded = True
            return

        self.is_loaded = True
        val = self.raw_value

        # Dict
        if isinstance(val, dict):
            for k, v in val.items():
                self.children.append(NodeItem(k, v, self))
            return

        # List / Tuple / Set
        if isinstance(val, (list, tuple, set, frozenset)):
            items = list(val)
            # If list is very large, partition into chunks of 100 for responsive virtualization
            if len(items) > 100:
                chunk_size = 100
                for start_idx in range(0, len(items), chunk_size):
                    end_idx = min(start_idx + chunk_size, len(items))
                    chunk = items[start_idx:end_idx]
                    chunk_node = NodeItem(f"[{start_idx} .. {end_idx - 1}]", chunk, self)
                    self.children.append(chunk_node)
            else:
                for idx, item in enumerate(items):
                    self.children.append(NodeItem(f"[{idx}]", item, self))
            return

        # NumPy ndarray (when expanded)
        if self.data_type == "ndarray":
            # Add metadata info nodes
            self.children.append(NodeItem("dtype", str(val.dtype), self))
            self.children.append(NodeItem("shape", str(val.shape), self))
            self.children.append(NodeItem("ndim", val.ndim, self))
            self.children.append(NodeItem("size", val.size, self))
            self.children.append(NodeItem("nbytes", format_bytes(val.nbytes), self))

            # Sample elements or stats if numeric
            try:
                if val.size > 0 and val.dtype.kind in "iuf":
                    self.children.append(NodeItem("min", float(val.min()), self))
                    self.children.append(NodeItem("max", float(val.max()), self))
                    self.children.append(NodeItem("mean", float(val.mean()), self))
            except Exception:
                pass

            # Preview first elements if 1D or small
            if val.ndim == 1:
                limit = min(50, val.size)
                for i in range(limit):
                    self.children.append(NodeItem(f"[{i}]", val[i], self))
                if val.size > limit:
                    self.children.append(NodeItem("...", f"<omitted {val.size - limit} elements>", self))
            elif val.ndim == 2:
                rows = min(10, val.shape[0])
                for r in range(rows):
                    row_val = val[r, :min(10, val.shape[1])]
                    self.children.append(NodeItem(f"row [{r}]", row_val, self))
            return

        # Pandas DataFrame (when expanded)
        if self.data_type == "DataFrame":
            # Metadata
            self.children.append(NodeItem("shape", f"{val.shape[0]} rows × {val.shape[1]} cols", self))
            # Column list node
            cols_node = NodeItem(f"columns ({len(val.columns)})", {col: str(val[col].dtype) for col in val.columns}, self)
            self.children.append(cols_node)

            # Sample preview (first 5 rows as records)
            try:
                sample_dict = val.head(5).to_dict(orient="index")
                head_node = NodeItem("head(5)", sample_dict, self)
                self.children.append(head_node)
            except Exception:
                pass
            return

        # Pandas Series (when expanded)
        if self.data_type == "Series":
            self.children.append(NodeItem("dtype", str(val.dtype), self))
            self.children.append(NodeItem("length", len(val), self))
            try:
                head_dict = dict(val.head(10))
                self.children.append(NodeItem("head(10)", head_dict, self))
            except Exception:
                pass
            return

        # Generic Python Object with __dict__
        if hasattr(val, "__dict__"):
            for attr_name, attr_val in vars(val).items():
                if not attr_name.startswith("__"):
                    self.children.append(NodeItem(attr_name, attr_val, self))
            return


class NodeTreeModel(QAbstractItemModel):
    """Virtual tree model for PySide6 QTreeView."""

    COLUMNS = ["Key / Name", "Type", "Summary / Value"]

    def __init__(self, root_data: Any = None, parent=None):
        super().__init__(parent)
        self.root_item = NodeItem("<root>", None)
        if root_data is not None:
            self.set_data(root_data)

    def set_data(self, data: Any):
        self.beginResetModel()
        self.root_item = NodeItem("<root>", None)
        if isinstance(data, dict):
            for k, v in data.items():
                self.root_item.children.append(NodeItem(k, v, self.root_item))
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                self.root_item.children.append(NodeItem(f"[{idx}]", item, self.root_item))
        else:
            self.root_item.children.append(NodeItem("data", data, self.root_item))
        self.root_item.is_loaded = True
        self.endResetModel()

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self.COLUMNS):
                return self.COLUMNS[section]
        return None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()
        return parent_item.child_count()

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        child_item: NodeItem = index.internalPointer()
        parent_item = child_item.parent

        if parent_item is None or parent_item == self.root_item:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        item: NodeItem = index.internalPointer()

        if role == Qt.ItemDataRole.DisplayRole:
            col = index.column()
            if col == 0:
                return item.key
            elif col == 1:
                return item.data_type
            elif col == 2:
                # Add indicator if double-click expansion is available
                if item.is_special_lazy and not item.is_explicitly_expanded:
                    return f"{item.summary}  ▶ [Double-click to expand]"
                return item.summary

        elif role == Qt.ItemDataRole.UserRole:
            # Custom role to retrieve raw node item
            return item

        return None

    def expand_special_node(self, index: QModelIndex) -> bool:
        """Trigger explicit expansion of a special lazy item."""
        if not index.isValid():
            return False
        item: NodeItem = index.internalPointer()
        if item.is_special_lazy and not item.is_explicitly_expanded:
            self.layoutAboutToBeChanged.emit()
            expanded = item.trigger_special_expand()
            self.layoutChanged.emit()
            return expanded
        return False
