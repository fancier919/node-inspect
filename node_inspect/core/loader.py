"""File loaders with asynchronous background thread support."""

import json
import os
from typing import Any, Optional
from PySide6.QtCore import QObject, QThread, Signal

from node_inspect.core.safe_pickle import safe_load_pickle, PickleSecurityError


class DataLoader:
    """Synchronous file loaders for various formats."""

    @staticmethod
    def load_file(file_path: str, allow_pickle_numpy: bool = True, allow_pickle_pandas: bool = True) -> Any:
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)

        elif ext in (".pkl", ".pickle"):
            with open(file_path, "rb") as f:
                data = f.read()
            return safe_load_pickle(data, allow_numpy=allow_pickle_numpy, allow_pandas=allow_pickle_pandas)

        elif ext in (".parquet", ".pq"):
            try:
                import pandas as pd
                return pd.read_parquet(file_path)
            except Exception:
                import pyarrow.parquet as pq
                return pq.read_table(file_path)

        elif ext in (".yaml", ".yml"):
            try:
                import ruamel.yaml as yaml
                y = yaml.YAML(typ="safe")
                with open(file_path, "r", encoding="utf-8") as f:
                    return y.load(f)
            except ImportError:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()

        elif ext == ".csv":
            import pandas as pd
            return pd.read_csv(file_path)

        else:
            # Fallback text or binary
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            except UnicodeDecodeError:
                with open(file_path, "rb") as f:
                    return f.read()


class FileLoadWorker(QThread):
    """Background worker thread to load files without blocking the GUI."""

    finished = Signal(object)      # Loaded data
    error = Signal(str, str)       # error_type, message
    status_updated = Signal(str)   # status message

    def __init__(self, file_path: str, allow_pickle_numpy: bool = True, allow_pickle_pandas: bool = True, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.allow_pickle_numpy = allow_pickle_numpy
        self.allow_pickle_pandas = allow_pickle_pandas

    def run(self):
        try:
            self.status_updated.emit(f"Reading {os.path.basename(self.file_path)}...")
            data = DataLoader.load_file(
                self.file_path,
                allow_pickle_numpy=self.allow_pickle_numpy,
                allow_pickle_pandas=self.allow_pickle_pandas
            )
            self.finished.emit(data)
        except PickleSecurityError as e:
            self.error.emit("Security Alert", str(e))
        except Exception as e:
            self.error.emit("Load Error", f"Failed to load file: {type(e).__name__}: {str(e)}")
