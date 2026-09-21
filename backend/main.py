"""
Muscle Chair - 中央コントローラー

各種センサからのポイント報告を集約してゲームロジックを管理し、
勝利条件が満たされた際に出力側デバイスへ命令を送信する FastAPI サーバー。
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Literal, TypedDict

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# --- 出力モードの切り替えスイッチ ---
# True:  複数の出力先 (OUTPUT_DEVICES) に一斉送信します（本番用）
# False: 単一の出力先 (SINGLE_OUTPUT_DEVICE_URL) に送信します（デバッグ用）
BROADCAST_MODE: bool = False

# --- 複数の出力先（本番用） ---
OUTPUT_DEVICES: dict[str, str] = {
    "chair_motor": "http://xxx.xxx.xxx.xxx:5000/trigger_action",
    "chair_led": "http://xxx.xxx.xxx.xxx:5000/trigger_action",
    "balloon_pump": "http://xxx.xxx.xxx.xxx:5000/trigger_action",
    "speaker": "http://xxx.xxx.xxx.xxx:5000/trigger_action",
}

# --- 単一の出力先（デバッグ用） ---
SINGLE_OUTPUT_DEVICE_URL: str = "http://127.0.0.1:8001/trigger_action"

# --- ゲームバランス設定 ---
WINNING_THRESHOLD: int = 100
COOLDOWN_SECONDS: int = 10
POINT_MAPPING: dict[str, float] = {
    "pushup_sensor": 10.0,
    "squat_sensor": 10.0,
    "bicycle_sensor": 0.5,
    "gps_run": 0.2,
}

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


class InputData(BaseModel):
    source: str
    value: int = Field(ge=1)
    team: Literal["a", "b"]


class GameState(TypedDict):
    team_a_gauge: float
    team_b_gauge: float
    last_win_time: float
    last_winner: str | None


game_state: GameState = {
    "team_a_gauge": 0.0,
    "team_b_gauge": 0.0,
    "last_win_time": 0.0,
    "last_winner": None,
}

app = FastAPI(
    title="Muscle Chair Controller",
    description="各種センサからの入力を集計し、応援合戦を管理する中央サーバー。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def convert_to_point(source: str, value: int) -> float:
    return POINT_MAPPING.get(source, 0.0) * value


def _reset_gauges() -> None:
    game_state["team_a_gauge"] = 0.0
    game_state["team_b_gauge"] = 0.0
    logger.info("--- ゲージがリセットされました ---")


async def _send_command(device_name: str, url: str, winner: str) -> None:
    logger.info("  -> %s (%s) へ送信中...", device_name, url)
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"winner": winner}, timeout=2.0)
    except httpx.RequestError as e:
        logger.error("【エラー】%s への命令送信に失敗しました: %s", device_name, e)


async def handle_victory(winner: str) -> None:
    logger.info("🎉🎉🎉 勝者決定！ Team: %s 🎉🎉🎉", winner)
    game_state["last_winner"] = winner
    game_state["last_win_time"] = time.time()

    if BROADCAST_MODE:
        logger.info("ブロードキャストモード：全ての出力装置に命令を送信します...")
        await asyncio.gather(
            *[_send_command(name, url, winner) for name, url in OUTPUT_DEVICES.items()]
        )
    else:
        logger.info("シングルモード：単一の出力装置に命令を送信します...")
        await _send_command("single_device", SINGLE_OUTPUT_DEVICE_URL, winner)

    _reset_gauges()


@app.post("/add_point", summary="センサからポイントを追加")
async def add_point(data: InputData) -> dict[str, str]:
    point = convert_to_point(data.source, data.value)

    if data.team == "a":
        game_state["team_a_gauge"] += point
    else:
        game_state["team_b_gauge"] += point

    logger.info(
        "Team A: %.1f | Team B: %.1f",
        game_state["team_a_gauge"],
        game_state["team_b_gauge"],
    )

    current_time = time.time()
    is_cooldown = (current_time - game_state["last_win_time"]) < COOLDOWN_SECONDS

    if not is_cooldown:
        if game_state["team_a_gauge"] >= WINNING_THRESHOLD:
            await handle_victory("team_a")
        elif game_state["team_b_gauge"] >= WINNING_THRESHOLD:
            await handle_victory("team_b")

    return {"status": "success"}


@app.get("/status", summary="現在のゲージ状況を取得")
async def get_status() -> dict[str, Any]:
    current_time = time.time()
    is_cooldown = (current_time - game_state["last_win_time"]) < COOLDOWN_SECONDS
    # クールダウン終了後は last_winner を返さない（状態は変異させず読み取り時に判断）
    effective_winner = game_state["last_winner"] if is_cooldown else None
    return {**game_state, "last_winner": effective_winner, "is_cooldown": is_cooldown}


# 観客向けUIを同一オリジンで配信する。APIルートより後にマウントすること
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
