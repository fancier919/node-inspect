"""Test custom file extension configuration and custom parquet metadata parsing."""

import json
import os
import tempfile
import unittest
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from node_inspect.core.config import ConfigManager
from node_inspect.core.loader import DataLoader


class TestCustomConfigAndLoader(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.test_dir = self.tmpdir.name

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_custom_extension_json(self):
        custom_json_file = os.path.join(self.test_dir, "data.myjson")
        payload = {"model": "transformer", "layers": 12, "active": True}
        with open(custom_json_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        # Before mapping: loaded as raw string fallback
        raw = DataLoader.load_file(custom_json_file)
        self.assertIsInstance(raw, str)

        # Mock extension mapping to include .myjson
        original_mapping = ConfigManager.get_extension_mapping
        try:
            ConfigManager.get_extension_mapping = classmethod(lambda cls: {".myjson": "json"})
            parsed = DataLoader.load_file(f'"{custom_json_file}"')  # Test quote handling too
            self.assertIsInstance(parsed, dict)
            self.assertEqual(parsed["model"], "transformer")
            self.assertEqual(parsed["layers"], 12)
        finally:
            ConfigManager.get_extension_mapping = original_mapping

    def test_custom_parquet_with_metadata(self):
        custom_pq_file = os.path.join(self.test_dir, "data.mypq")
        df = pd.DataFrame({"colA": [10, 20, 30], "colB": ["x", "y", "z"]})
        meta = {
            "title": "experiment_run",
            "hyperparams": {"batch_size": 32, "lr": 0.001}
        }
        table = pa.Table.from_pandas(df, preserve_index=False)
        table = table.replace_schema_metadata({b"custom_info": json.dumps(meta).encode()})
        pq.write_table(table, custom_pq_file, compression="zstd")

        # Mock extension mapping to include .mypq
        original_mapping = ConfigManager.get_extension_mapping
        try:
            ConfigManager.get_extension_mapping = classmethod(lambda cls: {".mypq": "parquet"})
            loaded = DataLoader.load_file(custom_pq_file)
            self.assertIsInstance(loaded, dict)
            self.assertIn("metadata", loaded)
            self.assertIn("data", loaded)

            # Check custom metadata decoded and parsed as nested dictionary
            custom_meta = loaded["metadata"]["custom_metadata"]
            self.assertIn("custom_info", custom_meta)
            self.assertIsInstance(custom_meta["custom_info"], dict)
            self.assertEqual(custom_meta["custom_info"]["hyperparams"]["batch_size"], 32)
            self.assertEqual(custom_meta["custom_info"]["hyperparams"]["lr"], 0.001)

            # Check dataframe content
            self.assertEqual(len(loaded["data"]), 3)
        finally:
            ConfigManager.get_extension_mapping = original_mapping

    def test_open_file_filter_reflects_custom_extensions(self):
        original_ensure = ConfigManager.ensure_config
        try:
            ConfigManager.ensure_config = classmethod(lambda cls: {
                "extensions": {
                    "json": [".json", ".myjson"],
                    "parquet": [".parquet", ".mypq"]
                }
            })
            filter_str = ConfigManager.get_open_file_filter()
            self.assertIn("*.myjson", filter_str)
            self.assertIn("*.mypq", filter_str)
            self.assertIn("JSON (*.json *.myjson)", filter_str)
            self.assertIn("Parquet (*.parquet *.mypq)", filter_str)
            self.assertTrue(filter_str.startswith("All Supported Files (*.json *.myjson *.parquet *.mypq)"))
        finally:
            ConfigManager.ensure_config = original_ensure

    def test_pathlib_pickle_and_resolution(self):
        import pathlib
        from node_inspect.core.safe_pickle import safe_load_pickle
        import pickle

        test_file = os.path.join(self.test_dir, "sample.txt")
        with open(test_file, "w") as f:
            f.write("hello")

        p = pathlib.Path(test_file)
        pickled_data = pickle.dumps(p)
        loaded_p = safe_load_pickle(pickled_data)
        self.assertIsInstance(loaded_p, pathlib.Path)

        resolved = ConfigManager.resolve_existing_path(loaded_p)
        self.assertEqual(resolved, os.path.abspath(test_file))

        # Relative path resolution with base_dir
        rel_resolved = ConfigManager.resolve_existing_path("sample.txt", base_dir=self.test_dir)
        self.assertEqual(rel_resolved, os.path.abspath(test_file))

    def test_custom_action_matching(self):
        original_actions = ConfigManager.get_actions
        try:
            ConfigManager.get_actions = classmethod(lambda cls: [
                {
                    "name": "View Model",
                    "key": "model_path",
                    "command": "python view.py {value}"
                },
                {
                    "name": "Run Eval",
                    "key": "^exp_.*",
                    "value_pattern": "^active$",
                    "command": "python eval.py {key}"
                }
            ])
            # Exact key match
            act1 = ConfigManager.find_matching_action("model_path", "weights.bin")
            self.assertIsNotNone(act1)
            self.assertEqual(act1["name"], "View Model")

            # Regex key + value match
            act2 = ConfigManager.find_matching_action("exp_102", "active")
            self.assertIsNotNone(act2)
            self.assertEqual(act2["name"], "Run Eval")

            # Non-matching value
            act3 = ConfigManager.find_matching_action("exp_102", "disabled")
            self.assertIsNone(act3)
        finally:
            ConfigManager.get_actions = original_actions


if __name__ == "__main__":
    unittest.main()
