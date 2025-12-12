"""
Mausle Chair - Output Server (Generic)

中央コントローラー(main.py)からの命令を受け取り、
このラズパイに割り当てられた役割（JSスクリプト）を実行する受付係サーバー。

設定で呼び出すスクリプト名を変更することで、
LED担当、モーター担当など、どの役割にも対応できます。
"""

import subprocess
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

# ==============================================================================
# ★★★ 設定項目 (Configuration) ★★★
# ==============================================================================
# このラズパイが担当する、実行部隊のJavaScriptファイル名を設定します。
# 例: "output_led.js", "output_motor.js", "output_speaker.js", "output_balloon.js"
JAVASCRIPT_SCRIPT_NAME = "main-isd1820.js" 

# ==============================================================================
# Pydanticモデル定義 (Data Models)
# ==============================================================================
# 中央コントローラーから送られてくるJSONの構造を定義
class WinnerData(BaseModel):
    winner: Optional[str] = None

# ==============================================================================
# FastAPIアプリケーションの初期化 (Application Instance)
# ==============================================================================
app = FastAPI(
    title="Macho Chair Output Controller",
    description="中央サーバーからの命令に応じて、割り当てられた物理演出を実行します。"
)

# ==============================================================================
# APIエンドポイント (API Endpoints)
# ==============================================================================
@app.post("/trigger_action", summary="中央コントローラーからの命令を受信")
async def receive_trigger_from_main_server(data: WinnerData):
    """
    中央サーバーからの命令を受け取り、指定されたJSスクリプトを実行する。
    """
    # 1. 受信したデータから勝者チーム名を取得（なければ"default"とする）
    winner_team = data.winner or "default"
    print(f"\n[Python] 中央サーバーから命令受信！ 勝者: {winner_team}")
    print(f"[Python] 実行部隊 ({JAVASCRIPT_SCRIPT_NAME}) を呼び出します...")

    # 2. 実行するコマンドをリストとして作成
    #    sudo を使うことで、GPIOなどのハードウェアにアクセスする権限を確保します。
    command = ['sudo', 'node', JAVASCRIPT_SCRIPT_NAME, winner_team]

    # 3. 外部のJavaScriptスクリプトを実行
    try:
        # subprocess.runで、外部のコマンド（nodeスクリプト）を実行
        # check=True: もしJSスクリプトがエラーで終了した場合、Python側もエラーとして扱います
        # text=True: 標準出力/エラーをテキストとして扱います
        subprocess.run(command, check=True, text=True)
        print(f"[Python] {JAVASCRIPT_SCRIPT_NAME} の実行が完了しました。")
        return {"status": "ok"}
        
    except FileNotFoundError:
        # 'node'コマンドや、指定されたJSファイルが見つからない場合のエラー
        error_message = f"【エラー】'{' '.join(command)}' の実行に失敗しました。'node'コマンドまたはスクリプトが見つかりません。"
        print(error_message)
        return {"status": "error", "message": error_message}
        
    except subprocess.CalledProcessError as e:
        # JavaScriptの実行中に、何らかのエラーが発生して異常終了した場合
        error_message = f"【エラー】JavaScriptの実行中にエラーが発生しました (終了コード: {e.returncode})"
        print(error_message)
        return {"status": "error", "message": error_message}

# ==============================================================================
# サーバ起動コマンド
# uvicorn output_server:app --host 0.0.0.0 --port 5000
# ==============================================================================
