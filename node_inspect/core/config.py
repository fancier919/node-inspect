"""Configuration manager for user custom extension mapping."""

import json
import os
from typing import Any, Dict, List, Optional


DEFAULT_CONFIG = {
    "extensions": {
        "json": [".json"],
        "parquet": [".parquet", ".pq"],
        "pickle": [".pkl", ".pickle"],
        "csv": [".csv"],
        "yaml": [".yaml", ".yml"],
    },
    "actions": [],
}


class ConfigManager:
    """Manages configuration stored in ~/.node-inspect/config.json."""

    CONFIG_DIR = os.path.expanduser("~/.node-inspect")
    CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

    @classmethod
    def ensure_config(cls) -> Dict:
        """Ensure config directory and file exist, returning current config."""
        try:
            if not os.path.exists(cls.CONFIG_DIR):
                os.makedirs(cls.CONFIG_DIR, exist_ok=True)

            if not os.path.exists(cls.CONFIG_PATH):
                with open(cls.CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
                return DEFAULT_CONFIG

            with open(cls.CONFIG_PATH, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_CONFIG

    @classmethod
    def get_extension_mapping(cls) -> Dict[str, str]:
        """Return a mapping of lowercase extension -> file type (e.g. '.mqmeta' -> 'parquet')."""
        config = cls.ensure_config()
        mapping = {}
        extensions_section = config.get("extensions", {})

        for file_type, ext_list in extensions_section.items():
            if isinstance(ext_list, list):
                for ext in ext_list:
                    clean_ext = ext.strip().lower()
                    if not clean_ext.startswith("."):
                        clean_ext = "." + clean_ext
                    mapping[clean_ext] = file_type.lower()

        return mapping

    @classmethod
    def get_open_file_filter(cls) -> str:
        """Build QFileDialog filter string reflecting configured extensions."""
        config = cls.ensure_config()
        extensions_section = config.get("extensions", {})

        all_patterns = []
        filter_parts = []

        type_labels = {
            "json": "JSON",
            "parquet": "Parquet",
            "pickle": "Pickle",
            "csv": "CSV",
            "yaml": "YAML",
        }

        for file_type, ext_list in extensions_section.items():
            if isinstance(ext_list, list) and ext_list:
                patterns = []
                for ext in ext_list:
                    clean = ext.strip().lower()
                    if not clean.startswith("."):
                        clean = "." + clean
                    pat = f"*{clean}"
                    patterns.append(pat)
                    all_patterns.append(pat)

                label = type_labels.get(file_type.lower(), file_type.upper())
                pattern_str = " ".join(patterns)
                filter_parts.append(f"{label} ({pattern_str})")

        all_pattern_str = " ".join(all_patterns) if all_patterns else "*.*"
        parts = [f"All Supported Files ({all_pattern_str})"] + filter_parts + ["All Files (*.*)"]
        return ";;".join(parts)

    @classmethod
    def get_file_type(cls, file_path: str) -> Optional[str]:
        """Determine file type from path using configured extension mapping."""
        clean_path = file_path.strip().strip('"').strip("'")
        ext = os.path.splitext(clean_path)[1].lower()
        mapping = cls.get_extension_mapping()
        return mapping.get(ext)

    @classmethod
    def get_actions(cls) -> List[Dict]:
        """Return configured custom actions list."""
        config = cls.ensure_config()
        return config.get("actions", [])

    @classmethod
    def resolve_existing_path(cls, value: Any, base_dir: Optional[str] = None) -> Optional[str]:
        """Check if value is a valid existing file/folder path (str or pathlib.Path)."""
        import pathlib
        path_str = None
        if isinstance(value, (pathlib.Path, pathlib.PurePath)):
            path_str = str(value)
        elif isinstance(value, str):
            path_str = value.strip().strip('"').strip("'")

        if not path_str or len(path_str) > 1024 or "\x00" in path_str:
            return None

        # Check direct existence (absolute or relative to cwd)
        try:
            if os.path.exists(path_str):
                return os.path.abspath(path_str)
        except Exception:
            pass

        # Check relative to currently loaded data file's directory
        if base_dir and not os.path.isabs(path_str):
            try:
                candidate = os.path.join(base_dir, path_str)
                if os.path.exists(candidate):
                    return os.path.abspath(candidate)
            except Exception:
                pass

        return None

    @classmethod
    def find_matching_action(cls, key: str, value: Any) -> Optional[Dict]:
        """Find the first matching custom action for a given key and value."""
        import re
        val_str = str(value)
        actions = cls.get_actions()

        for action in actions:
            if not isinstance(action, dict):
                continue

            k_pattern = action.get("key")
            v_pattern = action.get("value_pattern")

            # Check key pattern (exact match or regex)
            if k_pattern:
                try:
                    if not (key == k_pattern or re.fullmatch(k_pattern, key)):
                        continue
                except Exception:
                    if key != k_pattern:
                        continue

            # Check value pattern (if specified)
            if v_pattern:
                try:
                    if not (val_str == v_pattern or re.fullmatch(v_pattern, val_str) or re.search(v_pattern, val_str)):
                        continue
                except Exception:
                    if val_str != v_pattern:
                        continue

            return action

        return None

