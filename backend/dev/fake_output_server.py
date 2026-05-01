"""
Fake Output Server for Muscle Chair

このスクリプトは、中央コントローラー(main.py)のデバッグを目的とした、
出力側ラズパイZeroのダミー（偽物）サーバー。

中央コントローラーからの勝利演出命令(/trigger_action)を受け取ると、
ターミナルに成功メッセージを表示。
これにより、出力側の実機がなくても、中央コントローラーが正しく命令を
送信できるかを確認可能。
"""

import logging

from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WinnerData(BaseModel):
    winner: str | None = None


app = FastAPI(
    title="Fake Output Server",
    description="中央コントローラーからの命令受信をシミュレートするダミーサーバーです。",
)


@app.post("/trigger_action", summary="中央コントローラーからの命令を受信")
async def receive_trigger_from_main_server(data: WinnerData) -> dict[str, str]:
    logger.info("=" * 50)
    logger.info("      🎉🎉🎉 成功！中央サーバーから命令を受信しました！ 🎉🎉🎉")
    logger.info("      勝者チーム: %s", data.winner)
    logger.info("=" * 50)
    return {"status": "ok", "message": "Command successfully received by fake server."}
