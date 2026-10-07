# NodeInspect

ネストされたデータ構造（JSON、Pickle、Parquet、DataFrame、ndarray等）を階層ツリーで探索・閲覧するための PySide6 製 GUI アプリケーション。

---

## 機能一覧

- **対応ファイル形式:** `.json`, `.pkl`, `.parquet`, `.csv`, `.yaml`
- **遅延展開 (Lazy Loading):**
  - `numpy.ndarray` や `pandas.DataFrame` などの特殊型は、開いた直後はサマリー情報（型、形状、メモリ使用量等）のみを表示。
  - ダブルクリックにより、詳細プロパティやスプレッドシート型テーブルビューをオンデマンドで展開。
- **Parquet メタデータの抽出:**
  - PyArrow の `schema.metadata`（Key-Value メタデータ）を自動デコードし、JSON 文字列は階層構造としてツリーに展開。
  - ファイル仕様（RowGroup 数、行数、列数等）とテーブル本体を整理して表示。
- **Pickle のホワイトリスト検証:**
  - `SafeUnpickler` により、許可された安全なデータ型のみをデシリアライズ（任意コード実行コードの読み込みを遮断）。
- **2ペイン構成:**
  - 左ペイン: ツリービュー（トグル展開、リアルタイム絞り込みフィルター、値やパスのコピー）。
  - 右ペイン: 詳細インスペクター（テーブルビュー、Raw/JSON テキストビュー）。
  - テーマ切り替え（Soft Gray Light / Dark+）。
- **ドラッグ＆ドロップ:** ファイルのドラッグ＆ドロップによる読み込みに対応。

---

## 依存パッケージ & インストール

### 必要要件
- Python >= 3.10
- PySide6
- numpy
- pandas
- pyarrow

### インストール
```bash
pip install -r requirements.txt
```

---

## 起動方法

```bash
# アプリケーションを起動 (run.py または -m)
python run.py
# または
python -m node_inspect.main

# ファイルを指定して起動
python run.py path/to/file.parquet

# コンソール非表示で起動 (Windows / ランチャー用)
pythonw run.py path/to/file.parquet
```

---

## 独自拡張子の設定

Windows の「既定のプログラム」等で独自拡張子を関連付けて起動する場合、ユーザーホームディレクトリ配下の設定ファイルで拡張子とファイル形式のマッピングを指定できます。

設定ファイルパス: `~/.node-inspect/config.json`（初回起動時に自動生成されます）

```json
{
  "extensions": {
    "json": [".json", ".myjson"],
    "parquet": [".parquet", ".pq", ".mypq"],
    "pickle": [".pkl", ".pickle"],
    "csv": [".csv"],
    "yaml": [".yaml", ".yml"]
  }
}
```

---

## テスト

```bash
# サンプルデータの生成
python tests/generate_sample_data.py

# 単体テストの実行
python -m unittest discover tests
```

---

## ライセンス

[MIT License](LICENSE)
