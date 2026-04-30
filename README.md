# Muscle Chair

**Web × IoT Makers Challenge PLUS 2025 岡山大会 最優秀賞受賞作品**

## 概要

### プロジェクトの目的

Muscle Chair（マッスルチェア）は、観客の応援を「見える化」し、物理的なフィードバックで応援合戦を盛り上げるインタラクティブなIoTシステムです。スポーツ観戦やイベントにおいて、観客の声援がリアルタイムでスコアに反映され、勝利チームが決まると椅子が動いたり、筋肉風船が膨らんだりするダイナミックな演出が行われます。

### 基本動作

1. **応援検知**: 各チームに設置されたUSBマイクが観客の声援を検知
2. **レベル計測**: RMSベースの音量解析でチアレベル（0.0〜1.0）を算出
3. **イベント送信**: しきい値を超えると`CHEER_TRIGGER`イベントをバックエンドに送信
4. **スコア集計**: 中央サーバーが各種センサーからのポイントを集計
5. **勝利判定**: ゲージが100に達したチームの勝利を判定
6. **演出実行**: 勝利チームに応じた物理演出（モーター、LED、スピーカー、風船）を一斉実行

### 受賞歴

- **Web × IoT Makers Challenge PLUS 2025 岡山大会 最優秀賞**
- 2026年3月 全国大会出場予定

## システムアーキテクチャ

### 全体構成図

```
┌──────────────────────────┐
│     Team A 応援席         │
│  （マイクをここに設置）     │
└──────────┬───────────────┘
           │ 音声
           ▼
┌─────────────────────────┐
│ Raspberry Pi Zero 2 W   │
│ (edge/cheer_mic)        │
│ + USB Mic × 1           │
└──────────┬──────────────┘
           │ HTTP POST /api/cheer/trigger
           │ (team=A, level=xx)
           ▼
┌──────────────────────────┐
│    Raspberry Pi 4        │
│    (backend/main.py)     │
│    ゲームロジック・スコア管理│
└──────────────────────────┘
```

### 各層の役割

| レイヤー | ディレクトリ | 役割 |
|---------|-------------|------|
| **Edge** | `edge/` | Raspberry Pi Zero上でセンサー入力・信号処理を実行。USB マイクからの音声を解析し、チアイベントを検出 |
| **Backend** | `backend/` | 中央サーバー。ゲームロジック（スコア管理、勝利判定）を実行し、出力デバイスへ命令を一斉送信 |
| **Device** | `device/` | 出力側Raspberry PiでのGPIO/I2C制御。モーター、LED、スピーカー、風船ポンプを駆動 |
| **Web** | `web/` | 観客向けリアルタイムスコア表示UI。勝利演出（紙吹雪アニメーション等）を含む |

### データフロー

```
音声入力 → RMS計算 → ノイズゲート → スムージング → 正規化(0-1)
    → しきい値判定 → CheerEvent生成 → HTTP POST → バックエンド
    → ポイント加算 → 勝利判定 → 出力デバイスへ一斉送信 → 物理演出
```

## ディレクトリ構成

```
muscle_chair/
├── edge/                    # エッジデバイス（Raspberry Pi Zero）
│   └── cheer_mic/           # チア検知モジュール
│       ├── main.py          # エントリーポイント（CLI）
│       ├── cheer_detector.py # チア検知ロジック
│       ├── usb_mic_detector.py # USBマイク入力処理
│       ├── sender.py        # HTTP送信モジュール
│       ├── calibrate.py     # キャリブレーションツール
│       └── README.md        # モジュール詳細ドキュメント
│
├── backend/                 # 中央サーバー（Raspberry Pi 4）
│   ├── main.py              # FastAPIメインサーバー（ゲームロジック）
│   ├── output_server.py     # 出力側受信サーバー（汎用）
│   ├── fake_output_server.py # デバッグ用ダミーサーバー
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
├── slide/                   # プレゼンテーション資料
│   └── muscle_chair.pptx    # 発表スライド
│
├── .kiro/                   # Spec-Driven Development設定
│   ├── steering/            # プロジェクト方針
│   └── specs/               # 機能仕様
│
├── CLAUDE.md                # AI開発アシスタント用コンテキスト
├── AGENTS.md                # プロジェクトメモリ（開発ルール）
└── README.md                # このファイル
```

## 技術スタック

### 言語・フレームワーク

| カテゴリ | 技術 | 用途 |
|---------|------|------|
| **サーバーサイド** | Python 3.12 + FastAPI | 中央コントローラー、REST API |
| **エッジ処理** | Python 3 + PyAudio + NumPy | USB マイク音声解析 |
| **デバイス制御** | Node.js + CHIRIMEN | GPIO/I2C制御 |
| **フロントエンド** | HTML/CSS/JavaScript | リアルタイムスコア表示 |

### 主要ライブラリ

**Python (Backend/Edge)**
| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| fastapi | - | Web API フレームワーク |
| uvicorn | - | ASGI サーバー |
| pydantic | - | データバリデーション |
| pyaudio | >=0.2.13 | 音声入力キャプチャ |
| numpy | >=1.24.0 | 数値計算（RMS算出） |
| requests | - | HTTP クライアント |

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
| Raspberry Pi Zero 2 W | エッジ処理（マイク入力） | 1 |
| Raspberry Pi Zero | 出力制御（モーター/LED/スピーカー/風船） | 4 |
| SANWA SUPPLY MM-MCU028K | USBマイク（応援検知） | 1 |
| SG90 サーボモーター | 椅子アーム駆動 | - |
| PCA9685 | I2Cサーボドライバー | - |
| LED、リレー、ファン等 | 各種演出用 | - |

## セットアップ

### 必要な環境

- **中央サーバー**: Raspberry Pi 4（Raspberry Pi OS）
- **エッジデバイス**: Raspberry Pi Zero 2 W
- **出力デバイス**: Raspberry Pi Zero
- **ネットワーク**: 同一LAN内で各デバイスが通信可能であること

### 中央サーバー（Backend）のセットアップ

```bash
# リポジトリをクローン
git clone https://github.com/your-org/muscle_chair.git
cd muscle_chair

# Python仮想環境を作成
python3 -m venv .venv
source .venv/bin/activate

# 依存関係をインストール
pip install fastapi uvicorn pydantic requests

# サーバーを起動
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### エッジデバイス（Cheer Mic）のセットアップ

```bash
# システムパッケージをインストール（Raspberry Pi）
sudo apt update
sudo apt install portaudio19-dev python3-pyaudio python3-numpy

# Pythonパッケージをインストール
pip install pyaudio numpy

# USBマイクの接続確認
arecord -l

# チア検知を起動
python3 -m edge.cheer_mic.main --team A --backend http://<中央サーバーIP>:8000/api/cheer/trigger
```

### 出力デバイス（Device）のセットアップ

```bash
# Node.jsのセットアップ（Raspberry Pi Zero）
cd device/output/led  # または motor/speaker/balloon

# 依存関係をインストール
npm install

# 出力サーバーを起動
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
   # シングルマイク・Team A 検知（全国大会仕様）
   python3 -m edge.cheer_mic.main --team A --backend http://<サーバーIP>:8000/api/cheer/trigger
   ```

4. **Web UIを開く**
   - ブラウザで `http://<サーバーIP>:8000/` にアクセス
   - または `web/index.html` を直接開き、API_URLを設定

### デバッグモード

実機がない環境でのテスト用：

```bash
# ダミー出力サーバーを起動
cd backend
uvicorn fake_output_server:app --port 8001

# 疑似データモードでチア検知を起動
python3 -m edge.cheer_mic.main --team A --debug
```

### キャリブレーション

USBマイクのパラメータ調整：

```bash
# オーディオデバイスの一覧表示
python3 -m edge.cheer_mic.usb_mic_detector

# キャリブレーションツールを起動
python3 -m edge.cheer_mic.calibrate
```

### 動作確認方法

1. **マイク入力確認**: ターミナルにリアルタイムレベルバーが表示される
2. **イベント送信確認**: `CHEER DETECTED!` メッセージとHTTP送信成功表示
3. **Web UI確認**: ゲージがリアルタイムで更新される
4. **勝利演出確認**: ゲージが100に達すると演出が実行される

## 開発状況

### 実装済み機能

- [x] USBマイクによるリアルタイム音声入力（16kHz）
- [x] RMSベースの音量計算とノイズゲート
- [x] スムージングフィルタによるジッター低減
- [x] HTTP経由のチアイベント送信
- [x] FastAPIによるゲームロジック（スコア管理、勝利判定）
- [x] SSEによるリアルタイムログ配信
- [x] 出力デバイスへのブロードキャスト送信
- [x] サーボモーター制御（PCA9685経由）
- [x] LED点滅パターン制御
- [x] スピーカー出力制御
- [x] 風船ファン制御
- [x] Web UIでのリアルタイムスコア表示
- [x] 勝利演出（紙吹雪アニメーション）
- [x] systemdサービス化対応
- [x] デバッグ用ダミーサーバー
- [x] キャリブレーションツール

### 今後の予定（全国大会に向けた改良点）

- [ ] マイク感度の自動キャリブレーション機能
- [ ] 複数マイクの同期処理最適化
- [ ] 遅延の更なる削減（目標: 100ms以下）
- [ ] 演出パターンの追加・カスタマイズ機能
- [ ] Web UIのデザイン改善
- [ ] ネットワーク障害時の自動復旧機能
- [ ] モバイル対応UIの追加
- [ ] 録音・再生機能（振り返り用）

## ライセンス

このプロジェクトはWeb × IoT Makers Challenge PLUS 2025のハッカソン作品として開発されました。

## 謝辞

- Web × IoT Makers Challenge PLUS 2025 運営事務局
- 岡山大会 メンター・スタッフの皆様
