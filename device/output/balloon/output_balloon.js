/**
 * Muscle Chair - Output Module (Balloon Fan)
 * * 中央サーバーからの命令に応じて、GPIO経由でファンを制御し、
 * 筋肉風船を膨らませる演出を実行するスクリプト。
 */

import { requestGPIOAccess } from "./node_modules/node-web-gpio/dist/index.js";
const sleep = msec => new Promise(resolve => setTimeout(resolve, msec));

// ==============================================================================
//  設定項目 (Configuration)
// ==============================================================================

const CONFIG = {
    // ファンを制御するリレーやモータードライバを接続したGPIOピン番号
    FAN_PIN: 26,

    // 各チームの勝利演出パターン
    PATTERNS: {
        team_a: {
            name: "Team A 勝利 (全力膨張)",
            duration: 30000, // 30秒間ファンを回転
        },
        team_b: {
            name: "Team B 勝利 (短時間膨張)",
            duration: 15000, // 15秒間ファンを回転
        },
        default: {
            name: "デフォルト (テスト膨張)",
            duration: 5000, // 5秒間ファンを回転
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
    const winnerArg = process.argv[2];
    if (winnerArg === 'team_a' || winnerArg === 'team_b') {
        return winnerArg;
    }
    return "default";
}

/**
 * 勝者名に応じたファン回転パターン設定を返します。
 * @param {string} winner - 勝者チーム名
 * @returns {{name: string, duration: number}}
 */
function getInflationPattern(winner) {
    return CONFIG.PATTERNS[winner] || CONFIG.PATTERNS.default;
}

/**
 * 指定された時間、ファンを回転させます。
 * @param {import("node-web-gpio").GPIO_Port} port - GPIOポートのインスタンス
 * @param {{name: string, duration: number}} pattern - ファン回転パターンの設定
 */
async function runFan(port, pattern) {
    console.log(`[JS] 演出パターン「${pattern.name}」を ${pattern.duration / 1000} 秒間実行します。`);
    
    await port.write(1); // ファンON
    await sleep(pattern.duration);
    await port.write(0); // ファンOFF
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

    const pattern = getInflationPattern(winner);
    
    let port; // try...finallyブロックの外で参照できるように宣言
    try {
        // GPIOポートを初期化
        const gpioAccess = await requestGPIOAccess();
        port = gpioAccess.ports.get(CONFIG.FAN_PIN);
        await port.export("out");

        // ファンを回転
        await runFan(port, pattern);

    } catch (error) {
        console.error("[JS エラー] 処理中にエラーが発生しました:", error);
    } finally {
        if (port) {
            console.log("[JS] 演出完了。ポートを解放します。");
            // 念のため、最後にもう一度OFFにしておく
            await port.write(0);
            await port.unexport();
        }
        console.log("[JS] プログラムを終了します。");
    }
}

// アプリケーションを実行
main();
