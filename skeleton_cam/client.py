"""
Skeleton Camera Client - PC側

WebSocket経由でラズパイからJPEG映像と角度データを受信し、
OpenCVウィンドウに表示しながら筋トレ回数をカウントする。
カウントアップ時にbackend(/add_point)へポイントを送信する。
"""

import asyncio
import base64
import json
import logging

import cv2
import httpx
import numpy as np
import websockets

logger = logging.getLogger(__name__)

# --- 設定 ---
ANGLE_DOWN_THRESHOLD: int = 100  # この角度を下回ったらダウン判定
ANGLE_UP_THRESHOLD: int = 160  # この角度を超えたらアップ判定

WEBSOCKET_URI: str = "ws://xxx.xxx.xxx.xxx:8765"
BACKEND_URL: str = "http://127.0.0.1:8000/add_point"
TEAM: str = "a"

# --- 状態管理 ---
app_state: int = 0  # 0: START画面, 1: モード選択, 2: トレーニング中
selected_mode: str | None = None


def on_mouse_click(event: int, x: int, y: int, flags: int, param: object) -> None:
    global app_state, selected_mode
    if event != cv2.EVENT_LBUTTONDOWN:
        return

    if app_state == 0:
        if 100 <= x <= 220 and 100 <= y <= 140:
            app_state = 1

    elif app_state == 1:
        if 60 <= x <= 260 and 80 <= y <= 120:
            selected_mode = "Squat"
            app_state = 2
        elif 60 <= x <= 260 and 140 <= y <= 180:
            selected_mode = "Push-up"
            app_state = 2


async def receive_video() -> None:
    global app_state, selected_mode

    counter = 0
    stage = "UP"

    async with websockets.connect(WEBSOCKET_URI) as websocket:
        cv2.namedWindow("Exercise AI", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(
            "Exercise AI", cv2.WND_PROP_ASPECT_RATIO, cv2.WINDOW_KEEPRATIO
        )
        cv2.setMouseCallback("Exercise AI", on_mouse_click)

        while True:
            message = await websocket.recv()
            data = json.loads(message)

            # 映像デコード
            img_data = base64.b64decode(data["image"])
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            angle = data.get("angle", 0)

            if app_state == 0:
                # START ボタン表示
                cv2.rectangle(frame, (100, 100), (220, 140), (0, 255, 0), -1)
                cv2.putText(
                    frame,
                    "START",
                    (125, 125),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 0),
                    2,
                )

            elif app_state == 1:
                # モード選択画面
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (320, 240), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
                cv2.putText(
                    frame,
                    "Training Option",
                    (80, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )
                cv2.rectangle(frame, (60, 80), (260, 120), (255, 255, 0), -1)
                cv2.putText(
                    frame,
                    "Squat",
                    (130, 105),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 0),
                    2,
                )
                cv2.rectangle(frame, (60, 140), (260, 180), (0, 255, 255), -1)
                cv2.putText(
                    frame,
                    "Push Up",
                    (120, 165),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 0),
                    2,
                )

            elif app_state == 2:
                # モード送信
                await websocket.send(json.dumps({"mode": selected_mode}))

                # 筋トレ判定ロジック
                if angle < ANGLE_DOWN_THRESHOLD and stage == "UP":
                    stage = "DOWN"
                    logger.info("DOWN!")

                if angle > ANGLE_UP_THRESHOLD and stage == "DOWN":
                    stage = "UP"
                    counter += 1
                    logger.info("UP! 回数: %d", counter)

                    # バックエンドへポイント送信
                    try:
                        async with httpx.AsyncClient() as client:
                            await client.post(
                                BACKEND_URL,
                                json={
                                    "source": "pushup_sensor",
                                    "value": 1,
                                    "team": TEAM,
                                },
                                timeout=0.5,
                            )
                    except httpx.RequestError:
                        pass  # 送信失敗は無視（ゲームの継続を優先）

                # HUD表示
                cv2.rectangle(frame, (0, 0), (220, 90), (0, 0, 0), -1)
                cv2.putText(
                    frame,
                    f"MODE: {selected_mode}",
                    (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )
                cv2.putText(
                    frame,
                    f"COUNT: {counter}",
                    (10, 55),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    2,
                )
                cv2.putText(
                    frame,
                    f"ANGLE: {angle}",
                    (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1,
                )

                # DOWN状態インジケーター
                if stage == "DOWN":
                    cv2.circle(frame, (300, 30), 15, (0, 0, 255), -1)

            cv2.imshow("Exercise AI", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(receive_video())
