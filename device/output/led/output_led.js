/**
 * Mausle Chair - Output Module (LED Decoration)
 * * 中央サーバーからの命令に応じて、指定されたパターンのLED点滅演出を実行するスクリプト。
 * 勝利チームによって、点滅の速度や回数が変化します。
 */

import { requestGPIOAccess } from "./node_modules/node-web-gpio/dist/index.js";
const sleep = msec => new Promise(resolve => setTimeout(resolve, msec));

// ==============================================================================
//  設定項目 (Configuration)
// ==============================================================================

const CONFIG = {
    GPIO_PIN: 26, // LEDを接続したGPIOピン番号

    // 各チームの勝利演出パターン
    PATTERNS: {
        team_a: {
            name: "Team A 勝利 (高速点滅)",
            onTime: 50,    // LEDが点灯している時間 (ms)
            offTime: 50,   // LEDが消灯している時間 (ms)
            count: 50,     // 点滅回数
        },
        team_b: {
            name: "Team B 勝利 (ゆっくり点滅)",
            onTime: 500,
            offTime: 500,
            count: 5,
        },
        default: {
            name: "デフォルト (通常点滅)",
            onTime: 200,
            offTime: 200,
            count: 10,
        }
    }
};

// ==============================================================================
//  ビジネスロジック (Helper Functions)
// ==============================================================================

/**
 * コマンドライン引数から勝者チーム名を取得します。
 * @returns {string} 勝者チーム名 ('team_a', 'team_b', 'default')
 */
function getWinnerFromArgs() {
    // process.argv[2] に最初のコマンドライン引数が入ります
    const winnerArg = process.argv[2];
    if (winnerArg === 'team_a' || winnerArg === 'team_b') {
        return winnerArg;
    }
    return "default";
}

/**
 * 勝者名に応じた点滅パターン設定を返します。
 * @param {string} winner - 勝者チーム名
 * @returns {{name: string, onTime: number, offTime: number, count: number}}
 */
function getBlinkPattern(winner) {
    return CONFIG.PATTERNS[winner] || CONFIG.PATTERNS.default;
}

/**
 * 指定されたパターンでLEDの点滅ループを実行します。
 * @param {import("node-web-gpio").GPIO_Port} port - GPIOポートのインスタンス
 * @param {{onTime: number, offTime: number, count: number}} pattern - 点滅パターンの設定
 */
async function runBlinkLoop(port, pattern) {
    console.log(`[JS] 演出パターン「${pattern.name}」を ${pattern.count} 回実行します。`);
    for (let i = 0; i < pattern.count; i++) {
        await port.write(1); // 点灯
        await sleep(pattern.onTime);
        await port.write(0); // 消灯
        await sleep(pattern.offTime);
    }
}


// ==============================================================================
//  メイン処理 (Main Logic)
// ==============================================================================

/**
 * アプリケーションのメインエントリーポイント
 */
async function main() {
    const winner = getWinnerFromArgs();
    console.log(`[JS] 実行部隊、作戦開始！ 勝者: ${winner}`);

    const pattern = getBlinkPattern(winner);
    
    let port; // try...finallyブロックの外で参照できるように宣言
    try {
        // GPIOポートを初期化
        const gpioAccess = await requestGPIOAccess();
        port = gpioAccess.ports.get(CONFIG.GPIO_PIN);
        await port.export("out");

        // 点滅ループを実行
        await runBlinkLoop(port, pattern);

    } catch (error) {
        console.error("[JS エラー] 処理中にエラーが発生しました:", error);
    } finally {
        // ★★★ プログラムが正常終了しても、エラーで落ちても、必ず実行される後片付け ★★★
        if (port) {
            console.log("[JS] 演出完了。ポートを解放します。");
            await port.unexport();
        }
        console.log("[JS] プログラムを終了します。");
    }
}

// アプリケーションを実行
main();
