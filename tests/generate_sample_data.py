"""Generate various sample data files for testing NodeInspect."""

import json
import os
import pickle
import numpy as np
import pandas as pd


def generate_samples(output_dir: str = "sample_data"):
    os.makedirs(output_dir, exist_ok=True)

    # 1. Complex nested JSON
    json_data = {
        "project": "NodeInspect",
        "version": "1.0.0",
        "description": "VS Code style lightweight tree inspector",
        "settings": {
            "theme": "dark_plus",
            "fontSize": 13,
            "lazy_loading": True,
            "max_preview_rows": 5000,
            "features": ["tree_view", "type_badges", "dataframe_viewer", "safe_pickle"],
        },
        "contributors": [
            {"id": 1, "name": "Alice", "role": "Core Dev", "active": True},
            {"id": 2, "name": "Bob", "role": "UI Designer", "active": False},
            {"id": 3, "name": "Charlie", "role": "Security Engineer", "active": True},
        ],
        "metrics": {
            "latency_ms": 1.25,
            "memory_usage_mb": 42.8,
            "tags": ["python", "pyside6", "debugger", "gui"],
        },
        "null_val": None,
    }
    json_path = os.path.join(output_dir, "sample_config.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    print(f"Generated: {json_path}")

    # 2. Pickle containing numpy.ndarray and pandas.DataFrame
    np.random.seed(42)
    large_matrix = np.random.randn(200, 10).astype(np.float32)
    labels_1d = np.array([f"class_{i % 5}" for i in range(100)])

    df_data = {
        "id": range(1, 101),
        "temperature": np.random.uniform(20.0, 35.0, 100),
        "pressure": np.random.uniform(990.0, 1025.0, 100),
        "status": np.random.choice(["OK", "WARNING", "CRITICAL"], 100),
        "is_active": np.random.choice([True, False], 100),
    }
    df = pd.DataFrame(df_data)

    pickle_payload = {
        "dataset_name": "Sensor Experiment Batch #14",
        "created_at": "2026-10-04",
        "features_matrix": large_matrix,
        "labels": labels_1d,
        "measurements_df": df,
        "parameters": {
            "learning_rate": 0.001,
            "batch_size": 64,
            "optimizer": "adam",
            "loss_history": [0.85, 0.62, 0.45, 0.31, 0.22, 0.18],
        },
    }
    pkl_path = os.path.join(output_dir, "experiment_results.pkl")
    with open(pkl_path, "wb") as f:
        pickle.dump(pickle_payload, f)
    print(f"Generated: {pkl_path}")

    # 3. Parquet file with rich custom metadata
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.Table.from_pandas(df, preserve_index=False)
    custom_metadata = {
        "author": "Kaneko",
        "experiment_id": "EXP-2026-10",
        "description": "Industrial sensor time-series benchmark",
        "config": json.dumps({"sampling_rate_hz": 50, "calibration_status": "VALID", "channels": 5}),
    }
    existing_meta = table.schema.metadata or {}
    combined_meta = {
        **existing_meta,
        **{k.encode("utf-8"): str(v).encode("utf-8") for k, v in custom_metadata.items()},
    }
    table = table.replace_schema_metadata(combined_meta)

    parquet_path = os.path.join(output_dir, "sensor_records.parquet")
    pq.write_table(table, parquet_path)
    print(f"Generated: {parquet_path}")

    # 4. Malicious pickle for security testing
    class ExploitDemo:
        def __reduce__(self):
            return (os.system, ("echo WARNING: Unsafe code execution attempt!",))

    malicious_path = os.path.join(output_dir, "malicious_exploit.pkl")
    with open(malicious_path, "wb") as f:
        pickle.dump(ExploitDemo(), f)
    print(f"Generated (malicious security demo): {malicious_path}")


if __name__ == "__main__":
    generate_samples()
