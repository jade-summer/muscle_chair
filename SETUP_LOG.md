# セットアップログ

作業記録・動作確認結果・トラブルシューティングの履歴を残すファイル。
全国大会当日のセットアップ手順書としても活用する。

---

## 2026-03-05 エッジデバイス初期セットアップ・統合テスト

### 環境
| 項目 | 内容 |
|------|------|
| エッジデバイス | Raspberry Pi Zero 2 W |
| OS | CHIRIMEN Lite 最新リリース版 |
| USB マイク | SANWA SUPPLY MM-MCU028K |
| PC | Windows 11 + WSL (Ubuntu) |

### 実施内容

#### 1. OS・Wi-Fi セットアップ
- CHIRIMEN Lite を microSD に書き込み済み
- Web Serial RPi Zero Terminal（Chrome）経由で Wi-Fi 設定・IP アドレス確認
  - IP アドレス: `192.168.11.3`
  - ゲートウェイ: `192.168.11.1`

#### 2. IP アドレスの固定
`/etc/dhcpcd.conf` に以下を追記して固定化：
```
interface wlan0
static ip_address=192.168.11.3/24
static routers=192.168.11.1
static domain_name_servers=192.168.11.1
```

#### 3. SSH の有効化
CHIRIMEN Lite はデフォルトで SSH が無効のため手動で有効化：
```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

次回起動から自動起動される。

#### 4. パスワード変更
デフォルトパスワード `raspberry` からセキュアなパスワードに変更済み：
```bash
passwd
```

#### 5. USB マイクの接続確認
- 接続: `PWR IN` ポートに外部電源、`USB`（OTG）ポートに OTG アダプタ経由でマイクを接続
- `lsusb` で認識確認:
  ```
  Bus 001 Device 002: ID 0d8c:0016 C-Media Electronics, Inc. USB Microphone
  ```
- `arecord -l` でオーディオデバイス確認:
  ```
  カード 1: Microphone [USB Microphone], デバイス 0: USB Audio [USB Audio]
  ```
- 録音テスト: `arecord -D plughw:1,0 -f cd -d 5 test.wav` → 862KB のファイル生成を確認

#### 6. Python 環境セットアップ
```bash
sudo apt install -y portaudio19-dev python3-pyaudio python3-numpy git python3-pip
```
- `import pyaudio` → OK
- `import numpy` → OK

#### 7. リポジトリのクローン
```bash
git clone https://github.com/jade-summer/muscle_chair.git
```

#### 8. 動作確認

**デバッグモード（擬似データ）:**
```bash
python3 -m edge.cheer_mic.main --team A --debug
```
→ `🎉 CHEER DETECTED!` 表示を確認 ✅

**実機マイクモード:**
```bash
python3 -m edge.cheer_mic.main --team A
```
→ 声に反応して Level バーが変動、イベント検知を確認 ✅

**注意事項:**
- PyAudio のデバイスインデックスは `--device` 引数なし（デフォルト）で動作する
- `--device 1` を指定すると Segmentation fault が発生する（PyAudio と ALSA のインデックス番号は異なる）
- ALSA の警告メッセージ（`Unknown PCM front` 等）は CHIRIMEN Lite 環境固有のもので実害なし

#### 9. 統合テスト（エッジ → バックエンド）

ラズパイ 4 が手元にないため、ラズパイ Zero 上でバックエンドも起動して代用。

**バックエンド起動（ターミナル1）:**
```bash
cd ~/muscle_chair/backend
pip3 install fastapi uvicorn pydantic requests --break-system-packages
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**エッジ起動（ターミナル2）:**
```bash
cd ~/muscle_chair
python3 -m edge.cheer_mic.main --team A --backend http://127.0.0.1:8000/api/cheer/trigger
```

**結果:**
```
# バックエンド側ログ
[CHEER_TRIGGER] team=A event=CHEER_TRIGGER level=75.0 ...
INFO: 127.0.0.1 - "POST /api/cheer/trigger HTTP/1.1" 200 OK
```

| チェック項目 | 結果 |
|------------|------|
| USB マイク認識 | ✅ |
| 音声レベル検知 | ✅ |
| しきい値超過でイベント生成 | ✅ |
| HTTP POST 送信 | ✅ |
| バックエンド受信・200 OK | ✅ |
| イベントログ記録 | ✅ |

---

## 2026-03-10 出力デバイス用ラズパイ Zero セットアップ

### 環境
| 番号 | 担当デバイス | IP アドレス |
|------|------------|-----------|
| 5番 | motor（サーボモーター） | 192.168.11.6 |
| 6番 | led | 192.168.11.8 |
| 7番 | speaker | 192.168.11.2 |
| 8番 | balloon | 192.168.11.9 |

### 共通セットアップ手順（全4台）

#### 1. IP アドレスの固定
```bash
sudo tee -a /etc/dhcpcd.conf << 'EOF'

interface wlan0
static ip_address=<各ラズパイのIP>/24
static routers=192.168.11.1
static domain_name_servers=192.168.11.1
EOF
```

#### 2. SSH の有効化
```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

#### 3. git インストール・リポジトリクローン
```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/jade-summer/muscle_chair.git
```

#### 4. npm install（全4デバイス分まとめて実行）
```bash
cd ~/muscle_chair/device/output/led && npm init -y && npm pkg set type=module && npm install node-web-gpio && cd ../speaker && npm init -y && npm pkg set type=module && npm install node-web-gpio && cd ../balloon && npm init -y && npm pkg set type=module && npm install node-web-gpio && cd ../motor && npm init -y && npm pkg set type=module && npm install node-web-i2c @chirimen/pca9685
```

#### 5. Python 依存関係のインストール
```bash
sudo apt install -y python3-pip
pip3 install fastapi uvicorn --break-system-packages
```

#### 6. output_server.py の設定変更
担当デバイスに応じて `JAVASCRIPT_SCRIPT_NAME` を変更：

| 番号 | 変更後の値 |
|------|-----------|
| 5番 | `/home/pi/muscle_chair/device/output/motor/output_motor.js` |
| 6番 | `/home/pi/muscle_chair/device/output/led/output_led.js` |
| 7番 | `/home/pi/muscle_chair/device/output/speaker/output_speaker.js` |
| 8番 | `/home/pi/muscle_chair/device/output/balloon/output_balloon.js` |

```bash
sed -i 's|JAVASCRIPT_SCRIPT_NAME = "main-isd1820.js"|JAVASCRIPT_SCRIPT_NAME = "/home/pi/muscle_chair/device/output/<デバイス名>/output_<デバイス名>.js"|' ~/muscle_chair/backend/output_server.py
```

#### 7. start_server.sh の作成
```bash
cat > ~/muscle_chair/scripts/start_server.sh << 'EOF'
#!/bin/bash
cd /home/pi/muscle_chair/backend
python3 -m uvicorn output_server:app --host 0.0.0.0 --port 5000
EOF

chmod +x ~/muscle_chair/scripts/start_server.sh
```

#### 8. systemd サービス登録
```bash
sudo tee /etc/systemd/system/muscle_chair.service << 'EOF'
[Unit]
Description=Muscle Chair Output Server
After=network.target

[Service]
ExecStart=/home/pi/muscle_chair/scripts/start_server.sh
WorkingDirectory=/home/pi/muscle_chair/backend
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable muscle_chair
sudo systemctl start muscle_chair
sudo systemctl status muscle_chair
```

### 動作確認

**サーボモーター（5番）手動テスト:**
```bash
cd ~/muscle_chair/device/output/motor
sudo node output_motor.js team_a
```
→ サーボモーターの動作を確認 ✅

### 注意事項
- SSH 接続は WSL からではなく PowerShell から行う（WSL のネットワーク問題）
- `sudo` はリダイレクト（`>`）に効かないため `sudo tee` を使う
- CHIRIMEN OS には Node.js v20・npm v10 が同梱済みのため別途インストール不要

---

## 残作業（全国大会に向けて）

- [ ] ラズパイ 4 のセットアップ（OS・SSH・IP 固定・依存関係インストール）
- [ ] `main.py` の `OUTPUT_DEVICES` IP アドレス更新・`BROADCAST_MODE = True` に変更
- [ ] ラズパイ 4（本番バックエンド）との統合テスト
- [ ] キャリブレーション（会場の環境音に合わせた感度・しきい値調整）
- [ ] 出力デバイス（モーター・LED・スピーカー・風船）とのエンドツーエンドテスト