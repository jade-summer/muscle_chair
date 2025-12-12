/**
 * Muscle Chair - Input Module (Touch Sensor)
 * * タッチセンサーからの入力を検知し、中央サーバーにイベントを報告するスクリプト。
 * チャタリング防止のためのクールダウン（デバウンス）機能を持つ。
 */

import { requestGPIOAccess } from "./node_modules/node-web-gpio/dist/index.js";
import fetch from "node-fetch";

// ==============================================================================
//  設定項目 (Configuration)
// ==============================================================================

const CONFIG = {
    // 中央サーバー(ラズパイ4)のIPアドレスとポート
    API_URL: "http://<ラズパイ4のIPアドレス>:8000/add_point", 
    // このセンサーが所属するチームID ('team_a' または 'team_b')
    TEAM_ID: "team_a",
    // センサーを接続したGPIOピン番号
    SENSOR_PIN: 5,
    // 一度検知した後のクールダウン時間（ミリ秒）
    COOLDOWN_MS: 1000, // 1秒
    // 中央サーバーに報告する際のセンサー名
    SENSOR_SOURCE_NAME: "pushup_sensor",
};

// ==============================================================================
//  ビジネスロジック (Helper Functions)
// ==============================================================================

/**
 * 中央サーバーにイベントを送信します。
 * @returns {Promise<void>}
 */
async function sendEventToServer() {
    const payload = {
        source: CONFIG.SENSOR_SOURCE_NAME,
        value: 1,
        team: CONFIG.TEAM_ID
    };

    try {
        console.log(`[送信！] Team: ${CONFIG.TEAM_ID} の ${CONFIG.SENSOR_SOURCE_NAME} を検知しました！`);
        const response = await fetch(CONFIG.API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            console.error(`[エラー] 送信失敗: ${response.status} ${response.statusText}`);
        }
    } catch (err) {
        console.error(`[エラー] 通信エラー: ${err.message}`);
    }
}

/**
 * GPIOのonchangeイベントハンドラ。タッチされた瞬間（値が1になった時）にのみ反応します。
 * @param {{value: 0 | 1}} event - GPIOポートから渡されるイベントオブジェクト
 */
function handleTouchEvent(event) {
    // タッチセンサーは、押した瞬間(1)と離した瞬間(0)の両方でイベントが発生するため、
    // 「押した瞬間」のイベントのみを処理の対象とします。
    if (event.value === 1) {
        sendEventToServer();
    }
}

/**
 * 指定されたクールダウン時間の間、関数の連続実行を防ぐ高階関数（デバウンサ）。
 * @param {Function} func - 実行する関数
 * @param {number} cooldownMs - クールダウン時間（ミリ秒）
 * @returns {Function} クールダウン機能が追加された新しい関数
 */
function createDebouncedHandler(func, cooldownMs) {
    let lastCallTime = 0;

    return function(...args) {
        const now = Date.now();
        if ((now - lastCallTime) < cooldownMs) {
            console.log("[無視] クールダウン中です。");
            return; // クールダウン中は何もしない
        }
        lastCallTime = now;
        func(...args);
    };
}

// ==============================================================================
//  アプリケーション初期化 (Initialization)
// ==============================================================================

/**
 * アプリケーションのメインエントリーポイント
 */
async function main() {
    console.log("タッチセンサーの監視を開始します...");
    console.log(`送信先: ${CONFIG.API_URL}`);

    // GPIOポートを初期化
    const gpioAccess = await requestGPIOAccess();
    const port = gpioAccess.ports.get(CONFIG.SENSOR_PIN);
    await port.export("in");
    
    // クールダウン機能付きのイベントハンドラを作成
    const debouncedTouchHandler = createDebouncedHandler(handleTouchEvent, CONFIG.COOLDOWN_MS);

    // ピンの状態が変化するたびに、クールダウン機能付きのハンドラを呼び出す
    port.onchange = debouncedTouchHandler;

    console.log(`GPIO ${CONFIG.SENSOR_PIN}番ピンを監視中... Ctrl+Cで終了します。`);
}

// アプリケーションを実行
main().catch(err => {
    console.error("[起動エラー] プログラムの起動に失敗しました:", err);
    process.exit(1); // エラーで終了
});
