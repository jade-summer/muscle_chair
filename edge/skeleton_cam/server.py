"""
Skeleton Camera Server - ラズパイ側

Picamera2でRGB映像を取得し、MediaPipeで骨格検出（角度算出）を行い、
WebSocket経由でクライアントPCにJPEG圧縮映像と角度データを送信する。
"""

import asyncio
import base64
import json
import math

import cv2
import mediapipe as mp
import websockets
from picamera2 import Picamera2

# --- MediaPipe初期化 ---
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

pose = mp_pose.Pose(
    model_complexity=0,  # 負荷軽減のため0に設定
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

# --- カメラ初期化 (Picamera2) ---
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"format": "RGB888", "size": (540, 750)}
)
picam2.configure(config)
picam2.start()


def calculate_angle(a: list, b: list, c: list) -> float:
    """3点の座標(x, y)から頂点bの角度を算出"""
    rad = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    angle = abs(rad * 180.0 / math.pi)
    if angle > 180.0:
        angle = 360 - angle
    return round(angle, 1)


async def handle_communication(websocket):
    print("PCが接続されました。映像配信とコマンド受信を開始します。")
    current_mode = "WAITING"

    try:
        while True:
            # 1. PCからの制御信号をチェック（非ブロッキング）
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=0.001)
                rcv_data = json.loads(message)
                new_mode = rcv_data.get("mode")
                if new_mode:
                    current_mode = new_mode
                    print(f"モード切り替え: {current_mode}")
            except (asyncio.TimeoutError, json.JSONDecodeError):
                pass

            # 2. 映像取得
            image_rgb = picam2.capture_array()
            angle = 0

            # 3. モードに応じた骨格解析
            if current_mode != "WAITING":
                results = pose.process(image_rgb)

                if results.pose_landmarks:
                    lm = results.pose_landmarks.landmark

                    # 骨格を映像上に描画
                    mp_drawing.draw_landmarks(
                        image_rgb,
                        results.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style(),
                    )

                    if current_mode == "Squat":
                        # 右股関節(24), 右膝(26), 右足首(28)
                        a = [lm[24].x, lm[24].y]
                        b = [lm[26].x, lm[26].y]
                        c = [lm[28].x, lm[28].y]
                        angle = calculate_angle(a, b, c)

                    elif current_mode == "Push-up":
                        # 右肩(12), 右肘(14), 右手首(16)
                        a = [lm[12].x, lm[12].y]
                        b = [lm[14].x, lm[14].y]
                        c = [lm[16].x, lm[16].y]
                        angle = calculate_angle(a, b, c)

            # 4. JPEG圧縮してBase64化（RGB→BGRに変換してからエンコード）
            image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
            _, buffer = cv2.imencode(".jpg", image_bgr, [cv2.IMWRITE_JPEG_QUALITY, 50])
            jpg_as_text = base64.b64encode(buffer).decode("utf-8")

            # 5. JSONデータの構築と送信
            payload = {
                "image": jpg_as_text,
                "angle": angle,
                "mode": current_mode,
            }
            await websocket.send(json.dumps(payload))

            # フレームレート調整（約30fps）
            await asyncio.sleep(0.03)

    except websockets.exceptions.ConnectionClosed:
        print("PCとの接続が終了しました。")
    finally:
        current_mode = "WAITING"


async def main():
    async with websockets.serve(handle_communication, "0.0.0.0", 8765):
        print("--- Skeleton Camera WebSocket Server ---")
        print("ポート 8765 で待機中...")
        await asyncio.Future()  # 永久待機


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nサーバーを停止します。")
    finally:
        picam2.stop()
