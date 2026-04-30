"""
Macho Support Chair - 中央コントローラー (最終リファクタリング版)

入力側の各種センサからのイベント報告を集約かつ応援合戦のゲームロジックを管理し，
勝利条件が満たされた際に、登録されている全ての出力側ラズパイZeroに
一斉に命令を送信するFastAPIサーバ
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List

import requests
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError

# ==============================================================================
# 設定項目 (Configuration)
# ==============================================================================

# --- ★★★ 出力モードの切り替えスイッチ ★★★ ---
# True:  複数の出力先 (OUTPUT_DEVICES) に一斉送信します（本番用）
# False: 単一の出力先 (SINGLE_OUTPUT_DEVICE_URL) に送信します（デバッグ用）
BROADCAST_MODE: bool = False

# --- 複数の出力先（本番用） ---
# 各出力側ラズパイZeroに、役割に応じた名前を付け、IPアドレスを管理します。
OUTPUT_DEVICES: Dict[str, str] = {
    "chair_motor": "http://192.168.188.138:5000/trigger_action",
    "chair_led": "http://192.168.188.176:5000/trigger_action",
    "balloon_pump": "http://192.168.188.179:5000/trigger_action",
    "speaker": "http://192.168.188.175:5000/trigger_action",
}

# --- 単一の出力先（デバッグ用） ---
SINGLE_OUTPUT_DEVICE_URL: str = "http://127.0.0.1:8001/trigger_action"


# --- ゲームバランス設定 ---
WINNING_THRESHOLD: int = 100
COOLDOWN_SECONDS: int = 10
POINT_MAPPING: Dict[str, float] = {
    "pushup_sensor": 10.0,
    "microphone_cheer": 1.0,
    "bicycle_sensor": 0.5,
    "gps_run": 0.2,
}


# ==============================================================================
# Pydanticモデル定義 (Data Models)
# ==============================================================================
class InputData(BaseModel):
    source: str
    value: int
    team: str


class CheerTriggerPayload(BaseModel):
    team: str
    event: str
    level: float = Field(ge=0, le=100)
    ts: int = Field(ge=0)


# ==============================================================================
# アプリケーションの状態管理 (Application State)
# ==============================================================================
game_state: Dict[str, any] = {
    "team_a_gauge": 0.0,
    "team_b_gauge": 0.0,
    "last_win_time": 0.0,
    "last_winner": None,
}

log_subscribers: List[asyncio.Queue] = []

# ==============================================================================
# FastAPIアプリケーションの初期化 (Application Instance)
# ==============================================================================
app = FastAPI(
    title="Macho Support Chair Controller",
    description="各種センサからの入力を集計し，応援合戦を管理する中央サーバです．",
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# ビジネスロジック (Helper Functions)
# ==============================================================================
def convert_to_point(source: str, value: int) -> float:
    """センサの種類と値から，獲得ポイントを計算"""
    return POINT_MAPPING.get(source, 0.0) * value


def reset_gauges_after_win():
    """勝利後にゲームのゲージを初期化"""
    global game_state
    game_state["team_a_gauge"] = 0.0
    game_state["team_b_gauge"] = 0.0
    print("--- ゲージがリセットされました ---")


def _send_command(device_name: str, url: str, winner: str):
    """単一のデバイスに命令を送信する内部関数"""
    print(f"  -> {device_name} ({url}) へ送信中...")
    try:
        requests.post(url, json={"winner": winner}, timeout=2)
    except requests.RequestException as e:
        print(f"【エラー】{device_name} への命令送信に失敗しました: {e}")


def handle_victory(winner: str):
    """勝利が確定した際の全ての処理をまとめた関数"""
    global game_state

    print(f"🎉🎉🎉 勝者決定！ Team: {winner} 🎉🎉🎉")
    game_state["last_winner"] = winner
    game_state["last_win_time"] = time.time()

    # --- ★★★ 設定に応じて、送信先を切り替えます ★★★ ---
    if BROADCAST_MODE:
        print("ブロードキャストモード：全ての出力装置に命令を送信します...")
        for device_name, url in OUTPUT_DEVICES.items():
            _send_command(device_name, url, winner)
    else:
        print("シングルモード：単一の出力装置に命令を送信します...")
        _send_command("single_device", SINGLE_OUTPUT_DEVICE_URL, winner)

    reset_gauges_after_win()


def push_log_event(event_type: str, payload: Dict[str, Any]):
    """SSEに流すログイベントを生成して配信"""
    entry = {
        "type": event_type,
        "payload": payload,
        "logged_at": datetime.utcnow().isoformat() + "Z",
    }
    print(f"[LOG][{event_type}] {json.dumps(entry, ensure_ascii=False)}")
    for queue in list(log_subscribers):
        try:
            queue.put_nowait(entry)
        except asyncio.QueueFull:
            if queue in log_subscribers:
                log_subscribers.remove(queue)


# ==============================================================================
# APIエンドポイント (API Endpoints)
# ==============================================================================
@app.get("/api/logs/stream", summary="SSEログ配信")
async def stream_logs(request: Request):
    """Web UI向けのログストリーム"""
    queue: asyncio.Queue = asyncio.Queue()
    log_subscribers.append(queue)

    async def event_generator():
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                if await request.is_disconnected():
                    break
        except asyncio.CancelledError:
            pass
        finally:
            if queue in log_subscribers:
                log_subscribers.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/cheer/trigger", summary="応援トリガーの受信")
async def cheer_trigger(body: Dict[str, Any] = Body(...)):
    """エッジ側からの応援トリガーイベントの受信"""
    required_keys = {"team", "event", "level", "ts"}
    missing_keys = [key for key in required_keys if key not in body]
    if missing_keys:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {', '.join(sorted(missing_keys))}",
        )

    try:
        payload = CheerTriggerPayload(**body)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors())

    ts_iso = datetime.utcfromtimestamp(payload.ts / 1000).isoformat() + "Z"
    log_payload = {
        "team": payload.team,
        "event": payload.event,
        "level": payload.level,
        "ts": ts_iso,
        "ts_ms": payload.ts,
        "received_at": datetime.utcnow().isoformat() + "Z",
    }
    print(
        f"[CHEER_TRIGGER] team={payload.team} event={payload.event} "
        f"level={payload.level} ts={ts_iso}"
    )
    push_log_event("CHEER_TRIGGER", log_payload)

    return {"status": "received"}


@app.post("/add_point", summary="センサからポイントを追加")
async def add_point(data: InputData):
    """入力側のラズパイZeroからイベント報告を受け取り，ゲームロジックを処理"""
    global game_state

    point = convert_to_point(data.source, data.value)

    gauge_key = f"team_{data.team}_gauge"
    if gauge_key in game_state:
        game_state[gauge_key] += point

    print(
        f"Team A: {game_state['team_a_gauge']:.1f} | Team B: {game_state['team_b_gauge']:.1f}"
    )

    current_time = time.time()
    is_cooldown = (current_time - game_state["last_win_time"]) < COOLDOWN_SECONDS

    if not is_cooldown:
        winner = None
        if game_state["team_a_gauge"] >= WINNING_THRESHOLD:
            winner = "team_a"
        elif game_state["team_b_gauge"] >= WINNING_THRESHOLD:
            winner = "team_b"

        if winner:
            handle_victory(winner)

    return {"status": "success"}


@app.get("/status", summary="現在のゲージ状況を取得")
async def get_status():
    """現在の両チームのゲージ状況を返却．観客席のUI表示などに利用可能"""
    global game_state

    current_time = time.time()
    is_cooldown = (current_time - game_state["last_win_time"]) < COOLDOWN_SECONDS

    if not is_cooldown:
        game_state["last_winner"] = None

    return {**game_state, "is_cooldown": is_cooldown}
