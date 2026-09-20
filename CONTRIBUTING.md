# コントリビューションガイド

Muscle Chair への貢献を検討いただきありがとうございます。本ドキュメントは開発に参加する際の手順をまとめたものです。

## はじめに

本リポジトリは Web × IoT Makers Challenge PLUS 2025 のハッカソン作品を公開したものです。実機（Raspberry Pi・サーボモーター・センサー類）を前提とした部分が多いため、実機がなくても確認できる範囲と、実機が必要な範囲を分けて記載しています。

## 開発環境のセットアップ

実機なしで確認できるのは `backend/` と `tests/` の範囲です。

```bash
git clone https://github.com/jade-summer/muscle_chair.git
cd muscle_chair

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements-dev.txt
```

## 開発フロー

1. Issue を作成して、変更の目的を共有する（小さな修正の場合は省略可）
2. `main` からブランチを切る
3. 変更を加え、後述のチェックを通す
4. Pull Request を作成する

### ブランチ名

`<種別>/<内容>` の形式を推奨します。

```
feat/add-gauge-animation
fix/cooldown-not-reset
docs/update-setup-guide
```

## コーディング規約

### Python

[Ruff](https://docs.astral.sh/ruff/) で lint とフォーマットを統一しています。設定は `pyproject.toml` に記載されています。

```bash
ruff check .          # lint
ruff format .         # フォーマット適用
ruff format --check . # フォーマット確認（CIと同じ）
```

- 型ヒントを付与する
- ログ出力は `print()` ではなく `logging` を使う
- 命名は英語で統一する

### JavaScript（device/）

`device/` 配下は CHIRIMEN 環境で動作する Node.js スクリプトです。実機でしか動作確認できないため、CI の対象外としています。既存ファイルのスタイル（4スペースインデント、`CONFIG` オブジェクトに設定を集約）に合わせてください。

### コメント

「何をしているか」ではなく「なぜそうしたか」を書いてください。

## テスト

```bash
pytest
```

テストの対象は実機に依存しない純粋なロジックです。

| 対象 | ファイル |
|------|---------|
| ゲームロジック（スコア集計・勝利判定・クールダウン） | `tests/test_backend_main.py` |
| 関節角度の計算 | `tests/test_pose_math.py` |

カメラや GPIO に依存するコード（`skeleton_cam/server.py`、`device/`）はテスト対象外です。これらに手を入れる場合は、実機で動作確認したことを Pull Request に記載してください。

## コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/ja/v1.0.0/) 形式で記述してください。

```
feat: 風船ポンプの動作時間を設定可能にする
fix: クールダウン中にゲージがリセットされない問題を修正
docs: セットアップ手順に依存関係の注意点を追記
refactor: 出力デバイスへの送信処理を共通化
test: 勝利判定のクールダウンに関するテストを追加
```

## Pull Request の前に

- [ ] `ruff check .` が通る
- [ ] `ruff format --check .` が通る
- [ ] `pytest` が通る
- [ ] 実機が必要な変更の場合、動作確認した旨を記載した

## セキュリティに関する報告

脆弱性を発見した場合は Issue ではなく [SECURITY.md](SECURITY.md) の手順に従ってください。
