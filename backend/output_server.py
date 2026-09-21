"""
Muscle Chair - Output Server (Generic)

中央コントローラー(main.py)からの命令を受け取り、
このラズパイに割り当てられた役割（JSスクリプト）を実行する受付係サーバー。

設定で呼び出すスクリプト名を変更することで、
LED担当、モーター担当など、どの役割にも対応できます。
"""

import logging
import subprocess
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# --- 設定項目 ---
# このラズパイが担当する、実行部隊のJavaScriptファイルを設定します。
# 例: "device/output/motor/output_motor.js", "device/output/speaker/output_speaker.js"
# デプロイ時に担当デバイスのスクリプトに変更すること
JAVASCRIPT_SCRIPT_PATH: str = "device/output/led/output_led.js"

# 起動時のカレントディレクトリに依存しないよう、リポジトリルートを基準に解決する
REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
script_path = REPOSITORY_ROOT / JAVASCRIPT_SCRIPT_PATH

VALID_WINNERS: frozenset[str] = frozenset({"team_a", "team_b", "default"})


class WinnerData(BaseModel):
    winner: str | None = None


app = FastAPI(
    title="Muscle Chair Output Controller",
    description="中央サーバーからの命令に応じて、割り当てられた物理演出を実行します。",
)


@app.post("/trigger_action", summary="中央コントローラーからの命令を受信")
async def receive_trigger_from_main_server(data: WinnerData) -> dict[str, str]:
    winner_team = data.winner if data.winner in VALID_WINNERS else "default"
    logger.info("[Python] 中央サーバーから命令受信！ 勝者: %s", winner_team)
    logger.info("[Python] 実行部隊 (%s) を呼び出します...", script_path)

    command = ["sudo", "node", str(script_path), winner_team]

    try:
        subprocess.run(command, check=True, text=True)
        logger.info("[Python] %s の実行が完了しました。", script_path)
        return {"status": "ok"}

    except FileNotFoundError:
        error_message = (
            f"【エラー】'{' '.join(command)}' の実行に失敗しました。"
            "'node'コマンドまたはスクリプトが見つかりません。"
        )
        logger.error("%s", error_message)
        return {"status": "error", "message": error_message}

    except subprocess.CalledProcessError as e:
        error_message = (
            "【エラー】JavaScriptの実行中にエラーが発生しました "
            f"(終了コード: {e.returncode})"
        )
        logger.error("%s", error_message)
        return {"status": "error", "message": error_message}
