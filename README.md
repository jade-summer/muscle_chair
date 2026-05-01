# Muscle Chair

[![Ruff](https://github.com/jade-summer/muscle_chair/actions/workflows/ruff.yml/badge.svg)](https://github.com/jade-summer/muscle_chair/actions/workflows/ruff.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-red)](https://www.raspberrypi.com/)

**Web × IoT Makers Challenge PLUS 2025 岡山大会 最優秀賞 / 全国大会 人気投票賞受賞作品**

## 概要

### プロジェクトの目的

Muscle Chair（マッスルチェア）は、観客の応援を「見える化」し、物理的なフィードバックで応援合戦を盛り上げるインタラクティブなIoTシステムです。スポーツ観戦やイベントにおいて、観客の声援がリアルタイムでスコアに反映され、勝利チームが決まると椅子が動いたり、筋肉風船が膨らんだりするダイナミックな演出が行われます。

### 基本動作

1. **スコア集計**: 中央サーバーが各種センサーからのポイントを集計
2. **勝利判定**: ゲージが100に達したチームの勝利を判定
3. **演出実行**: 勝利チームに応じた物理演出（モーター、LED、スピーカー、風船）を一斉実行

### 受賞歴

- **Web × IoT Makers Challenge PLUS 2025 岡山大会 最優秀賞**
- **Web × IoT Makers Challenge PLUS 2025 グランプリ決定戦（全国大会） 人気投票賞 / 総合3位**（2026年3月）

## システムアーキテクチャ

### 全体構成図

```
┌──────────────────────────┐
│    トレーニングエリア      │
│ （カメラ＋選手の前に設置） │
└──────────┬───────────────┘
           │ 映像（WebSocket）
           ▼
┌─────────────────────────┐
│ Raspberry Pi Zero 2 W   │
│ (skeleton_cam)          │
│ + Pi Camera             │
└──────────┬──────────────┘
           │ WebSocket(8765)
           │
           │ HTTP POST /add_point
           ▼ (骨格検知→回数カウント)
┌────────────────────────────────────────────┐
│              Raspberry Pi 4                │
│              (backend/main.py)             │
│          ゲームロジック・スコア管理          │
└────────────────────────────────────────────┘
```

### 各層の役割

| レイヤー | ディレクトリ | 役割 |
|---------|-------------|------|
| **Skeleton Cam** | `skeleton_cam/` | Raspberry Pi Zero上でカメラによる骨格検出・筋トレ回数カウントを実行 |
| **Backend** | `backend/` | 中央サーバー。ゲームロジック（スコア管理、勝利判定）を実行し、出力デバイスへ命令を一斉送信 |
| **Device** | `device/` | 出力側Raspberry PiでのGPIO/I2C制御。モーター、LED、スピーカー、風船ポンプを駆動 |
| **Web** | `web/` | 観客向けリアルタイムスコア表示UI。勝利演出（紙吹雪アニメーション等）を含む |

### データフロー

```
カメラ映像 → 骨格検出 → 関節角度計算 → 回数カウント → HTTP POST → バックエンド
    → ポイント加算 → 勝利判定 → 出力デバイスへ一斉送信 → 物理演出
```

## ディレクトリ構成

```
muscle_chair/
├── skeleton_cam/            # 骨格検知モジュール（Pi Camera）
│   ├── server.py            # WebSocketサーバー（Pi側・骨格検出）
│   ├── client.py            # WebSocketクライアント（PC側・回数カウント）
│   ├── requirements-server.txt # Python依存関係（Raspberry Pi）
│   ├── requirements-client.txt # Python依存関係（PC）
│   └── README.md            # モジュール詳細ドキュメント
│
├── backend/                 # 中央サーバー（Raspberry Pi 4）
│   ├── main.py              # FastAPIメインサーバー（ゲームロジック）
│   ├── output_server.py     # 出力側受信サーバー（汎用）
│   ├── dev/
│   │   └── fake_output_server.py # デバッグ用ダミーサーバー
│   └── requirements.txt     # Python依存関係
│
├── device/                  # IoTデバイス制御（Node.js）
│   ├── input/               # 入力デバイス
│   │   └── touch/           # タッチセンサー
│   │       └── input_touch_a.js  # タッチセンサー入力処理
│   └── output/              # 出力デバイス
│       ├── motor/           # サーボモーター制御
│       │   └── output_motor.js   # PCA9685経由サーボ制御
│       ├── led/             # LED制御
│       │   └── output_led.js     # GPIO LED点滅制御
│       ├── speaker/         # スピーカー制御
│       │   └── output_speaker.js # GPIO スピーカー制御
│       └── balloon/         # 風船ポンプ制御
│           └── output_balloon.js # GPIO ファン制御
│
├── web/                     # フロントエンド（静的HTML）
│   └── index.html           # リアルタイムスコア表示UI
│
├── scripts/                 # ヘルパースクリプト
│   └── start_server.sh      # サーバー起動スクリプト
│
├── systemd/                 # systemdサービス定義
│   └── muscle_chair.service # 自動起動用サービスファイル
│
└── README.md                # このファイル
```

## 技術スタック

### 言語・フレームワーク

| カテゴリ | 技術 | 用途 |
|---------|------|------|
| **サーバーサイド** | Python 3.12 + FastAPI | 中央コントローラー、REST API |
| **エッジ処理（映像）** | Python 3 + MediaPipe + Picamera2 | 骨格検出・筋トレ回数カウント |
| **デバイス制御** | Node.js + CHIRIMEN | GPIO/I2C制御 |
| **フロントエンド** | HTML/CSS/JavaScript | リアルタイムスコア表示 |

### 主要ライブラリ

**Python (Backend/Edge)**
| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| fastapi | - | Web API フレームワーク |
| uvicorn | - | ASGI サーバー |
| pydantic | - | データバリデーション |
| numpy | >=1.24.0 | 数値計算（skeleton_cam 映像処理） |
| requests | >=2.31.0 | HTTP クライアント |
| mediapipe | >=0.10.0 | 骨格検出（skeleton_cam） |
| websockets | >=12.0 | WebSocketストリーミング（skeleton_cam） |
| opencv-python | >=4.8.0 | 映像処理・GUI（skeleton_cam client） |

**Node.js (Device)**
| ライブラリ | 用途 |
|-----------|------|
| node-web-gpio | GPIO制御（LED、スピーカー、ファン） |
| node-web-i2c | I2C制御（PCA9685サーボドライバー） |
| @chirimen/pca9685 | サーボモーター制御 |
| node-fetch | HTTP クライアント |

### ハードウェア

| デバイス | 用途 | 台数 |
|---------|------|------|
| Raspberry Pi 4 | 中央コントローラー | 1 |
| Raspberry Pi Zero 2 W | エッジ処理（骨格検出） | 1 |
| Raspberry Pi Zero | 出力制御（モーター/LED/スピーカー/風船） | 4 |
| Raspberry Pi Camera Module | 骨格検出用カメラ | 1 |
| SG90 サーボモーター | 椅子アーム駆動 | - |
| PCA9685 | I2Cサーボドライバー | - |
| LED、リレー、ファン等 | 各種演出用 | - |

## セットアップ

### 必要な環境

- **中央サーバー**: Raspberry Pi 4（Raspberry Pi OS）
- **エッジデバイス**: Raspberry Pi Zero 2 W
- **出力デバイス**: Raspberry Pi Zero
- **ネットワーク**: 同一LAN内で各デバイスが通信可能であること

> **注意**: 本システムは同一LAN内での使用を前提としており、認証機能は実装していません。

### 中央サーバー（Backend）のセットアップ

```bash
# リポジトリをクローン
git clone https://github.com/your-org/muscle_chair.git
cd muscle_chair

# Python仮想環境を作成
python3 -m venv .venv
source .venv/bin/activate

# 依存関係をインストール
pip install -r backend/requirements.txt

# サーバーを起動
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### エッジデバイス（Skeleton Cam）のセットアップ

```bash
# Raspberry Pi側（server.py）
sudo apt install python3-picamera2 python3-opencv python3-numpy
pip install -r skeleton_cam/requirements-server.txt

# サーバーを起動
python3 -m skeleton_cam.server

# PC側（client.py）—— IPアドレスを編集してから実行
# client.py の WEBSOCKET_URI を Raspberry Pi の IP に変更
pip install -r skeleton_cam/requirements-client.txt
python3 -m skeleton_cam.client
```

### 出力デバイス（Device）のセットアップ

```bash
# Node.jsの依存関係をインストール（例: LED担当の場合）
cd device/output/led  # または motor/speaker/balloon
npm install

# リポジトリルートに戻り、出力受信サーバーを起動
cd ../../..
cd backend
uvicorn output_server:app --host 0.0.0.0 --port 5000
```

### systemdサービスとして登録（自動起動）

```bash
# サービスファイルをコピー
sudo cp systemd/muscle_chair.service /etc/systemd/system/

# パスを環境に合わせて編集
sudo nano /etc/systemd/system/muscle_chair.service

# サービスを有効化・起動
sudo systemctl enable muscle_chair
sudo systemctl start muscle_chair
```

### 設定項目

**backend/main.py の主要設定**
```python
# 出力モード切り替え
BROADCAST_MODE = False  # True: 全デバイスに一斉送信, False: デバッグ用単一送信

# 出力デバイスのIPアドレス（本番用）
OUTPUT_DEVICES = {
    "chair_motor":  "http://192.168.x.x:5000/trigger_action",
    "chair_led":    "http://192.168.x.x:5000/trigger_action",
    "balloon_pump": "http://192.168.x.x:5000/trigger_action",
    "speaker":      "http://192.168.x.x:5000/trigger_action",
}

# ゲームバランス
WINNING_THRESHOLD = 100  # 勝利に必要なポイント
COOLDOWN_SECONDS = 10    # 勝利後のクールダウン時間
```

## 使い方

### 起動方法

1. **中央サーバーを起動**
   ```bash
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. **出力デバイスを起動**（各Raspberry Pi Zeroで）
   ```bash
   uvicorn output_server:app --host 0.0.0.0 --port 5000
   ```

3. **エッジデバイスを起動**（Raspberry Pi Zero 2 Wで）
   ```bash
   python3 -m skeleton_cam.server
   ```

4. **Web UIを開く**
   - ブラウザで `http://<サーバーIP>:8000/` にアクセス
   - または `web/index.html` を直接開く場合は、ファイル内の `API_URL` をサーバーのIPアドレスに合わせて変更してください

### デバッグモード

実機がない環境でのテスト用：

```bash
# ダミー出力サーバーを起動
cd backend/dev
uvicorn fake_output_server:app --port 8001
```

### 動作確認方法

1. **Web UI確認**: ゲージがリアルタイムで更新される
2. **勝利演出確認**: ゲージが100に達すると演出が実行される

## ライセンス

[MIT License](LICENSE) — Web × IoT Makers Challenge PLUS 2025 ハッカソン作品

Copyright (c) 2025 jade-summer

## 謝辞

- Web × IoT Makers Challenge PLUS 2025 運営事務局
- 岡山大会 メンター・スタッフの皆様
