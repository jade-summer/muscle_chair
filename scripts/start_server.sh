#!/bin/bash
# このスクリプトは、systemdから呼び出され、
# FastAPIサーバーを正しい仮想環境で起動します。

# Raspberry Pi のデフォルトユーザー名 pi を前提としています
# 異なるユーザー名の場合はパスを変更してください
cd /home/pi/muscle_chair

# Pythonの仮想環境を有効化
# Raspberry Pi のデフォルトユーザー名 pi を前提としています
# 異なるユーザー名の場合はパスを変更してください
source /home/pi/muscle_chair/venv/bin/activate

# FastAPIサーバーを起動
# --host 0.0.0.0 で、ネットワーク上の他のデバイスからのアクセスを許可します
# Raspberry Pi のデフォルトユーザー名 pi を前提としています
# 異なるユーザー名の場合はパスを変更してください
/home/pi/muscle_chair/venv/bin/uvicorn output_server:app --host 0.0.0.0 --port 5000
