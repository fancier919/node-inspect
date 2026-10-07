"""Configuration manager for user custom extension mapping."""

import json
import os
from typing import Dict, List, Optional


DEFAULT_CONFIG = {
    "extensions": {
        "json": [".json"],
        "parquet": [".parquet", ".pq"],
        "pickle": [".pkl", ".pickle"],
        "csv": [".csv"],
        "yaml": [".yaml", ".yml"],
    }
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
    def get_file_type(cls, file_path: str) -> Optional[str]:
        """Determine file type from path using configured extension mapping."""
        clean_path = file_path.strip().strip('"').strip("'")
        ext = os.path.splitext(clean_path)[1].lower()
        mapping = cls.get_extension_mapping()
        return mapping.get(ext)
