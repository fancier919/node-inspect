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

### 常駐サーバーモード（爆速起動）
あらかじめバックグラウンドで `pandas` 等をロードした常駐プロセスを待機させておくことで、ファイルを開く際の起動時間を数ミリ秒〜瞬時に短縮できます。

```bash
# 常駐サーバーをバックグラウンド起動 (スタートアップ等)
pythonw run.py --server

# サーバー起動中に通常通りファイルを開く (数ミリ秒で即座に新規ウィンドウがポップアップ)
python run.py path/to/file.parquet

# 常駐サーバーの停止
python run.py --stop
```

---

## 設定ファイル (`~/.node-inspect/config.json`)

設定ファイルにより、独自拡張子のマッピングおよび特定キー／ファイルパスに対するカスタムアクション（スクリプト実行等）を定義できます。

```json
{
  "extensions": {
    "json": [".json", ".myjson"],
    "parquet": [".parquet", ".pq", ".mypq"],
    "pickle": [".pkl", ".pickle"],
    "csv": [".csv"],
    "yaml": [".yaml", ".yml"]
  },
  "actions": [
    {
      "name": "モデル評価スクリプト実行",
      "key": "model_path",
      "command": "python C:/tools/eval.py {value}"
    },
    {
      "name": "実験ビューア起動",
      "key": "^exp_.*",
      "value_pattern": "^active$",
      "command": "python C:/tools/viewer.py --exp {key} --file {file_path}"
    }
  ]
}
```

### プレースホルダー一覧
- `{value}`: ノードの値（ファイルパスの場合は絶対パスに解決）
- `{key}`: ノードのキー名
- `{file_path}`: 現在開いているファイルのパス
- `{base_dir}`: 現在開いているファイルの親ディレクトリパス

### アクション実行方法
1. **ファイルパス（文字列または `pathlib.Path`）:**
   - ダブルクリック、または右クリックメニューの「🚀 Open in Default App」から Windows の既定プログラムで開くことができます。
2. **カスタムアクション:**
   - キーや値が一致するノードをダブルクリック、または右クリックメニューから指定した外部スクリプト・コマンドを起動できます。

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
