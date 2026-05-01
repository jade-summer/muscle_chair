# Skeleton Camera モジュール

Raspberry Pi カメラと MediaPipe を使ったリアルタイム骨格検出システム。

## 概要

Raspberry Pi カメラ（Picamera2）から映像を取得し、MediaPipe でポーズ推定を行い、関節角度データとともに映像を WebSocket 経由で PC クライアントへ配信する。PC クライアントは筋トレ回数をカウントし、バックエンドサーバーにポイントを送信する。

## アーキテクチャ

システムは2つのコンポーネントで構成される。

1. **WebSocket サーバー** (`server.py`) — Raspberry Pi 上で動作。映像取得・骨格検出・データ配信を担当
2. **OpenCV クライアント** (`client.py`) — PC 上で動作。映像受信・表示・回数カウント・ポイント送信を担当

```
[Raspberry Pi]                    [PC]                      [Backend]
  Picamera2                         |                           |
     ↓                              |                           |
  MediaPipe Pose                    |                           |
     ↓                              |                           |
  server.py  ---WebSocket(8765)--→ client.py ---HTTP POST--→ /add_point
             ←--- モードコマンド ---
```

## ハードウェア要件

- **カメラ**: Raspberry Pi カメラモジュール（世代不問）
- **プラットフォーム**: Raspberry Pi（Zero 2 W で動作確認済み）
- **PC**: OpenCV が動作するマシンであれば何でも可

## ソフトウェア依存関係

### Raspberry Pi

```bash
# システムパッケージ
sudo apt install python3-picamera2 python3-opencv python3-numpy

# Python パッケージ（picamera2 は apt でインストール済み）
pip install -r skeleton_cam/requirements-server.txt
```

### PC

```bash
pip install -r skeleton_cam/requirements-client.txt
```

## 使い方

### 1. Raspberry Pi でサーバーを起動

```bash
python3 -m skeleton_cam.server
```

### 2. client.py の IP アドレスを更新

```python
# client.py
WEBSOCKET_URI = "ws://<Raspberry Pi の IP>:8765"
```

### 3. PC でクライアントを起動

```bash
python3 -m skeleton_cam.client
```

### 4. 操作方法

| 状態 | 操作 |
|------|------|
| START 画面 | **START** ボタンをクリック |
| モード選択 | **Squat** または **Push Up** をクリック |
| トレーニング中 | カメラの前で運動する（回数は自動カウント） |
| 終了 | `q` キーを押す |

## 対応トレーニングモード

| モード | 計測関節 | ダウン判定 | アップ判定 |
|--------|---------|-----------|----------|
| スクワット | 股関節(24) → 膝(26) → 足首(28) | angle < 100° | angle > 160° |
| プッシュアップ | 肩(12) → 肘(14) → 手首(16) | angle < 100° | angle > 160° |

## バックエンド連携

1回のカウントアップごとに、クライアントはバックエンドへ POST リクエストを送信する。

```json
POST /add_point
{
  "source": "pushup_sensor",
  "value": 1,
  "team": "a"
}
```

チームやバックエンド URL を変更する場合は、`client.py` 冒頭の定数を編集する。

```python
WEBSOCKET_URI = "ws://xxx.xxx.xxx.xxx:8765"
BACKEND_URL = "http://127.0.0.1:8000/add_point"
TEAM = "a"
```
