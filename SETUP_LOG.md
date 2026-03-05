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

## 残作業（全国大会に向けて）

- [ ] ラズパイ 4（本番バックエンド）との統合テスト
- [ ] キャリブレーション（会場の環境音に合わせた感度・しきい値調整）
- [ ] systemd サービス登録（自動起動設定）
- [ ] 出力デバイス（モーター・LED・スピーカー・風船）との結合テスト