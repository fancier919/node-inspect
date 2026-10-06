"""Offscreen headless test to verify MainWindow and data tree operations."""

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtWidgets import QApplication
from node_inspect.ui.main_window import MainWindow
from node_inspect.core.loader import DataLoader
from node_inspect.core.node_model import NodeTreeModel, NodeItem

app = QApplication.instance()
if not app:
    app = QApplication([])


class TestGuiHeadless(unittest.TestCase):
    def setUp(self):
        self.window = MainWindow()

    def test_sync_dataloader(self):
        # 1. JSON
        json_data = DataLoader.load_file("sample_data/sample_config.json")
        self.assertIn("project", json_data)

        # 2. Pickle
        pkl_data = DataLoader.load_file("sample_data/experiment_results.pkl")
        self.assertIn("features_matrix", pkl_data)
        self.assertIn("measurements_df", pkl_data)

        # 3. Parquet with metadata
        pq_data = DataLoader.load_file("sample_data/sensor_records.parquet")
        self.assertIn("metadata", pq_data)
        self.assertIn("data", pq_data)
        self.assertEqual(len(pq_data["data"]), 100)
        custom_meta = pq_data["metadata"]["custom_metadata"]
        self.assertEqual(custom_meta["author"], "Kaneko")
        self.assertEqual(custom_meta["experiment_id"], "EXP-2026-10")
        self.assertIsInstance(custom_meta["config"], dict)  # Parsed JSON
        self.assertEqual(custom_meta["config"]["channels"], 5)

    def test_tree_model_and_lazy_expansion(self):
        pkl_data = DataLoader.load_file("sample_data/experiment_results.pkl")
        model = NodeTreeModel(pkl_data)

        # Root items count: 6 keys
        self.assertEqual(model.rowCount(), 6)

        # Find features_matrix (ndarray)
        matrix_idx = None
        for r in range(model.rowCount()):
            idx = model.index(r, 0)
            if idx.data() == "features_matrix":
                matrix_idx = idx
                break

        self.assertIsNotNone(matrix_idx)
        item: NodeItem = matrix_idx.data(256)  # UserRole is 256
        self.assertEqual(item.data_type, "ndarray")
        self.assertTrue(item.is_special_lazy)
        self.assertFalse(item.is_explicitly_expanded)

        # Initially children shouldn't be loaded
        self.assertEqual(item.child_count(), 0)

        # Trigger lazy expansion
        expanded = model.expand_special_node(matrix_idx)
        self.assertTrue(expanded)
        self.assertTrue(item.is_explicitly_expanded)
        # Now it has children (shape, dtype, min, max, mean, row previews, etc.)
        self.assertGreater(item.child_count(), 0)

    def test_detail_inspector(self):
        pkl_data = DataLoader.load_file("sample_data/experiment_results.pkl")
        df = pkl_data["measurements_df"]
        self.window.detail_inspector.display_node("measurements_df", df, "DataFrame", "(100 rows × 5 cols)")
        self.assertEqual(self.window.detail_inspector.type_badge.text(), "DataFrame")
        self.assertEqual(self.window.detail_inspector.tab_widget.currentIndex(), 0)  # Table View active

    def test_delegate_paint(self):
        from PySide6.QtGui import QPainter, QImage
        from PySide6.QtWidgets import QStyleOptionViewItem

        model = NodeTreeModel({"alpha": 123, "beta": "text", "gamma": [1, 2, 3]})
        delegate = self.window.tree_view.itemDelegate()

        img = QImage(300, 100, QImage.Format.Format_RGB32)
        painter = QPainter(img)
        opt = QStyleOptionViewItem()
        opt.rect = img.rect()

        for col in range(3):
            idx = model.index(0, col)
            delegate.paint(painter, opt, idx)
        painter.end()

    def test_inspector_initially_hidden(self):
        """Verify right panel is initially hidden."""
        self.assertFalse(self.window.detail_inspector.isVisible())

    def test_inspector_size_stability(self):
        """Verify right panel size is preserved across content changes."""
        self.window.resize(920, 580)
        self.window.show()
        # Trigger selection
        self.window._on_node_selected("short_key", 123, "int", "123")
        self.assertTrue(self.window.detail_inspector.isVisible())
        sizes_before = self.window.splitter.sizes()

        # Update with a very long summary string
        huge_str = "x" * 2000
        self.window._on_node_selected("long_key", huge_str, "str", huge_str)
        sizes_after = self.window.splitter.sizes()

        # Splitter right pane width should not have blown up
        self.assertEqual(sizes_before[1], sizes_after[1])

    def test_theme_toggle(self):
        from node_inspect.ui.theme import ThemeManager
        # Default is light
        self.assertFalse(ThemeManager.is_dark())

        # Toggle to dark
        self.window._toggle_theme()
        self.assertTrue(ThemeManager.is_dark())

        # Toggle back to light
        self.window._toggle_theme()
        self.assertFalse(ThemeManager.is_dark())


if __name__ == "__main__":
    unittest.main()
