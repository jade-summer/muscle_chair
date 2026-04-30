"""
Fake Output Server for Muscle Chair

このスクリプトは，中央コントローラー(main.py)のデバッグを目的とした，
出力側ラズパイZeroのダミー（偽物）サーバ

中央コントローラーからの勝利演出命令(/trigger_action)を受け取ると，
ターミナルに成功メッセージを表示
これにより，出力側の実機がなくても，中央コントローラーが正しく命令を
送信できるかを確認可能
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional


# Pydanticモデル定義
# 中央コントローラーから送られてくるJSONの構造を定義
class WinnerData(BaseModel):
    winner: Optional[str] = None


# FastAPIアプリケーションの初期化
app = FastAPI(
    title="Fake Output Server",
    description="中央コントローラーからの命令受信をシミュレートするダミーサーバーです．",
)


# APIエンドポイント
@app.post("/trigger_action", summary="中央コントローラーからの命令を受信")
async def receive_trigger_from_main_server(data: WinnerData):
    """
    中央コントローラーからの命令を受け取るためのダミーのエンドポイント
    リクエストを受け取ったら，成功メッセージをコンソールに表示するだけ
    """
    print("\n" + "=" * 50)
    print("      🎉🎉🎉 成功！中央サーバーから命令を受信しました！ 🎉🎉🎉")
    print(f"      勝者チーム: {data.winner}")
    print("=" * 50 + "\n")

    return {"status": "ok", "message": "Command successfully received by fake server."}


# サーバ起動コマンド: uvicorn fake_output_server:app --port 8001
