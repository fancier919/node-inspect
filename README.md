# NodeInspect

**NodeInspect** は、VS Codeのデバッグサイドバーのように、ネストされた変数やデータ構造（JSON、Pickle、Parquet、DataFrame、ndarray等）をトグル（折りたたみ・展開）でスムーズにインスペクトできる、モダンで軽量なGUIアプリケーションです。

---

## 主な特徴

1. **直感的かつスタイリッシュなVS Code風デザイン**
   - ダークテーマ基調（Dark+ 配色）で目に優しく、長時間のデータ分析やデバッグでも疲れません。
   - データ型ごとのカラーバッジ（`dict`/`list`: 黄色, `int`/`float`: 青, `str`: オレンジ, `bool`: 紫, `ndarray`/`DataFrame`: ターコイズグリーン）。
   - キー名、型名、サマリー/プレビューの3カラム構成。

2. **特殊な型（`ndarray`, `DataFrame`, `parquet`）の遅延展開（Lazy Loading）**
   - 巨大な配列やデータフレームを含むファイルを開いた直後は、全量展開せず**「型名・形状・メモリ消費量・サマリー情報」のみを高速表示**。
   - **ダブルクリック等のトリガー操作**によって、必要なタイミングでのみ詳細情報（属性・統計値・サンプル要素）やスプレッドシート型テーブルビューを展開。

3. **厳格なホワイトリストによる安全なPickle読み込み**
   - `.pkl` 読み込み時にPython標準の `pickle.Unpickler.find_class` をオーバーライド。
   - `os.system` や `subprocess`, `eval` などの任意のコード実行（RCE）を確実にブロックする安全なホワイトリスト方式（`SafeUnpickler`）を標準搭載。

4. **軽快なパフォーマンス & ローディングインジケーター**
   - PySide6（Qt for Python）の仮想化ツリーモデル（`QAbstractItemModel`）を採用し、大規模なネスト構造でも極めて高速・省メモリで動作。
   - ファイルの読み込みやパースはバックグラウンドワーカースレッド（`QThread`）で非同期実行され、アニメーションスピナーにより処理中であることが一目で分かります。

5. **2ペイン構成 & スプレッドシート型詳細インスペクター**
   - 左ペイン: ツリービュー（トグル展開、リアルタイム検索フィルター、コンテキストメニューによる値やパスのコピー）。
   - 右ペイン: 選択したノードの詳細ビュー（DataFrame/ndarrayを表形式スプレッドシートで閲覧できるテーブルタブ、フォーマット済みJSON/Rawビュータブ）。

6. **ドラッグ＆ドロップ対応**
   - アプリケーションウィンドウにファイルをドラッグ＆ドロップするだけで即座にインスペクトできます。

---

## セットアップ & インストール

```bash
pip install -r requirements.txt
```

### 依存パッケージ
- `PySide6`
- `numpy`
- `pandas`
- `pyarrow`

---

## 起動方法

### 1. アプリケーションを直接起動
```bash
python -m node_inspect.main
```
ウィンドウ右上の「📂 Open File」からファイルを選択するか、ファイルをウィンドウに直接ドラッグ＆ドロップしてください。

### 2. コマンドライン引数でファイルパスを指定して起動
```bash
python -m node_inspect.main sample_data/experiment_results.pkl
```

---

## サンプルデータとテスト

本リポジトリには検証用のサンプルデータ生成スクリプトおよび単体テストが用意されています。

### サンプルデータの生成
```bash
python tests/generate_sample_data.py
```
`sample_data/` フォルダ配下に以下のファイルが生成されます：
- `sample_config.json`: ネストの深い設定データ
- `experiment_results.pkl`: `numpy.ndarray` や `pandas.DataFrame` を含むPickle
- `sensor_records.parquet`: Parquet形式のデータ
- `malicious_exploit.pkl`: 不正なコード実行を含む検証用Pickle（安全にブロックされることをテスト可能）

### 単体テストの実行
```bash
# セキュリティテスト（悪意あるPickleの遮断検証）
python -m unittest tests/test_safe_pickle.py

# GUI & データモデルの統合テスト
python -m unittest tests/test_gui.py
```
