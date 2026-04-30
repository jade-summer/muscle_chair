#!/bin/bash
# このスクリプトは、systemdから呼び出され、
# FastAPIサーバーを正しい仮想環境で起動します。

# スクリプトがあるディレクトリに移動（これにより、相対パスが正しく機能します）
cd /home/pi/muscle_chair

# Pythonの仮想環境を有効化
source /home/pi/muscle_chair/venv/bin/activate

# FastAPIサーバーを起動
# --host 0.0.0.0 で、ネットワーク上の他のデバイスからのアクセスを許可します
/home/pi/muscle_chair/venv/bin/uvicorn output_server:app --host 0.0.0.0 --port 5000