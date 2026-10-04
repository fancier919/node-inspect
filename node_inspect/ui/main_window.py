"""Main Application Window for NodeInspect."""

import os
import time
from typing import Optional
from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QAction, QIcon, QKeySequence, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFileDialog, QMessageBox, QLineEdit, QLabel, QPushButton,
    QStatusBar, QToolBar
)

from node_inspect.core.node_model import NodeTreeModel
from node_inspect.core.loader import FileLoadWorker
from node_inspect.ui.tree_view import NodeTreeView, FilterProxyModel
from node_inspect.ui.detail_inspector import DetailInspectorWidget
from node_inspect.ui.spinner import LoadingIndicator
from node_inspect.ui.theme import COLORS, VSCODE_STYLE_SHEET


class MainWindow(QMainWindow):
    """Main application window for NodeInspect."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NodeInspect - Variable & Data Structure Inspector")
        self.resize(1100, 720)
        self.setAcceptDrops(True)

        self.current_file_path: Optional[str] = None
        self.load_worker: Optional[FileLoadWorker] = None
        self.start_time: float = 0

        self._init_ui()
        self.setStyleSheet(VSCODE_STYLE_SHEET)

    def _init_ui(self):
        # Central Widget & Main Layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top Action & Filter Bar
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Open File Action
        open_action = QAction("📂 Open File", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip("Open data file (.json, .pkl, .parquet, etc.)")
        open_action.triggered.connect(self._browse_and_open_file)
        toolbar.addAction(open_action)

        toolbar.addSeparator()

        # Expand / Collapse actions
        expand_all_btn = QPushButton("Expand All")
        expand_all_btn.clicked.connect(lambda: self.tree_view.expandAll())
        toolbar.addWidget(expand_all_btn)

        collapse_all_btn = QPushButton("Collapse All")
        collapse_all_btn.clicked.connect(lambda: self.tree_view.collapseAll())
        toolbar.addWidget(collapse_all_btn)

        toolbar.addSeparator()

        # Filter Box
        filter_label = QLabel(" 🔍 Filter: ")
        filter_label.setStyleSheet("color: #858585; font-weight: 500;")
        toolbar.addWidget(filter_label)

        self.filter_edit = QLineEdit(self)
        self.filter_edit.setPlaceholderText("Filter by key, type or value...")
        self.filter_edit.setFixedWidth(260)
        self.filter_edit.textChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.filter_edit)

        toolbar.addSeparator()

        # Loading Spinner Indicator
        self.loading_indicator = LoadingIndicator(self)
        toolbar.addWidget(self.loading_indicator)

        # 2. Main 2-Pane Splitter (Left: Tree, Right: Inspector)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Tree View with Filter Proxy
        self.tree_model = NodeTreeModel()
        self.proxy_model = FilterProxyModel(self)
        self.proxy_model.setSourceModel(self.tree_model)

        self.tree_view = NodeTreeView(self)
        self.tree_view.setModel(self.proxy_model)
        self.tree_view.header().resizeSection(0, 240)
        self.tree_view.header().resizeSection(1, 100)
        self.tree_view.header().resizeSection(2, 280)

        # Connect signals
        self.tree_view.node_selected.connect(self._on_node_selected)
        self.tree_view.special_node_expanded.connect(self._on_special_expanded)

        splitter.addWidget(self.tree_view)

        # Detail Inspector
        self.detail_inspector = DetailInspectorWidget(self)
        splitter.addWidget(self.detail_inspector)

        # 55% Tree, 45% Detail
        splitter.setSizes([600, 500])
        main_layout.addWidget(splitter)

        # 3. Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Drop a .json, .pkl, or .parquet file to inspect.")

    def _browse_and_open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Data File",
            "",
            "All Supported Files (*.json *.pkl *.pickle *.parquet *.pq *.csv *.yaml *.yml);;"
            "JSON (*.json);;Pickle (*.pkl *.pickle);;Parquet (*.parquet *.pq);;All Files (*.*)"
        )
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path: str):
        """Asynchronously load a data file in a background worker."""
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "Error", f"File not found: {file_path}")
            return

        self.current_file_path = file_path
        self.start_time = time.time()
        filename = os.path.basename(file_path)

        # Start loading animation
        self.loading_indicator.show_loading(f"Loading {filename}...")
        self.status_bar.showMessage(f"Loading {filename}...")

        # Terminate any existing worker
        if self.load_worker and self.load_worker.isRunning():
            self.load_worker.terminate()

        # Start background worker
        self.load_worker = FileLoadWorker(file_path)
        self.load_worker.finished.connect(self._on_file_loaded)
        self.load_worker.error.connect(self._on_file_load_error)
        self.load_worker.start()

    def _on_file_loaded(self, data):
        self.loading_indicator.hide_loading()
        elapsed = (time.time() - self.start_time) * 1000

        self.tree_model.set_data(data)
        self.tree_view.expandToDepth(0)

        filename = os.path.basename(self.current_file_path)
        self.setWindowTitle(f"NodeInspect - {filename}")
        self.status_bar.showMessage(
            f"Loaded {filename} successfully in {elapsed:.1f} ms | Pickle Security: Safe Whitelist Active"
        )

    def _on_file_load_error(self, title: str, message: str):
        self.loading_indicator.hide_loading()
        self.status_bar.showMessage(f"Failed to load: {title}")
        QMessageBox.warning(self, title, message)

    def _on_filter_changed(self, text: str):
        regex = QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.proxy_model.setFilterRegularExpression(regex)
        if text.strip():
            self.tree_view.expandAll()

    def _on_node_selected(self, key: str, value: object, data_type: str, summary: str):
        self.detail_inspector.display_node(key, value, data_type, summary)

    def _on_special_expanded(self, msg: str):
        self.status_bar.showMessage(msg, 4000)

    # Drag and Drop support
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if os.path.isfile(file_path):
                self.load_file(file_path)
                event.acceptProposedAction()
