/**
 * Mausle Chair - Output Module (Servo Motor)
 * * 中央サーバーからの命令に応じて、PCA9685経由でサーボモーターを制御し、
 * 物理的な演出（アーム展開など）を実行するスクリプト。
 */

import { requestI2CAccess } from "./node_modules/node-web-i2c/index.js";
import PCA9685 from "@chirimen/pca9685";
const sleep = msec => new Promise(resolve => setTimeout(resolve, msec));

// ==============================================================================
//  設定項目 (Configuration)
// ==============================================================================

const CONFIG = {
    // PCA9685 I2Cサーボドライバーの設定
    I2C_PORT: 1,
    I2C_ADDRESS: 0x40,

    // 使用するサーボモーターの仕様 (SG90に合わせた例)
    SERVO_SETTINGS: {
        pulseMin: 0.0005, // 最小パルス幅 (秒)
        pulseMax: 0.0024, // 最大パルス幅 (秒)
        degrees: 180,     // 動作角度
    },

    // 各チームの勝利演出パターン
    PATTERNS: {
        team_a: {
            name: "Team A 勝利 (アーム展開)",
            channel: 0,       // PCA9685のどのチャンネルに接続しているか
            startAngle: -90,  // 開始角度
            endAngle: 90,     // 終了角度
            duration: 1000,   // 片道の移動にかける時間 (ms)
            repeat: 3,        // 往復回数
        },
        team_b: {
            name: "Team B 勝利 (小刻みな動き)",
            channel: 0,
            startAngle: -20,
            endAngle: 20,
            duration: 200,
            repeat: 10,
        },
        default: {
            name: "デフォルト (ゆっくり一往復)",
            channel: 0,
            startAngle: -45,
            endAngle: 45,
            duration: 1500,
            repeat: 1,
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
 * 勝者名に応じたアニメーションパターン設定を返します。
 * @param {string} winner - 勝者チーム名
 * @returns {object}
 */
function getAnimationPattern(winner) {
    return CONFIG.PATTERNS[winner] || CONFIG.PATTERNS.default;
}

/**
 * PCA9685サーボドライバーを初期化します。
 * @returns {Promise<PCA9685>} 初期化済みのPCA9685インスタンス
 */
async function initializeServoDriver() {
    const i2cAccess = await requestI2CAccess();
    const port = i2cAccess.ports.get(CONFIG.I2C_PORT);
    const pca9685 = new PCA9685(port, CONFIG.I2C_ADDRESS);
    await pca9685.init(
        CONFIG.SERVO_SETTINGS.pulseMin,
        CONFIG.SERVO_SETTINGS.pulseMax,
        CONFIG.SERVO_SETTINGS.degrees
    );
    return pca9685;
}

/**
 * 指定されたパターンでサーボモーターのアニメーションを実行します。
 * @param {PCA9685} pca9685 - PCA9685のインスタンス
 * @param {object} pattern - アニメーションパターンの設定
 */
async function runServoAnimation(pca9685, pattern) {
    console.log(`[JS] 演出パターン「${pattern.name}」を ${pattern.repeat} 回実行します。`);
    for (let i = 0; i < pattern.repeat; i++) {
        console.log(`  Cycle ${i + 1}: ${pattern.startAngle} deg`);
        await pca9685.setServo(pattern.channel, pattern.startAngle);
        await sleep(pattern.duration);

        console.log(`  Cycle ${i + 1}: ${pattern.endAngle} deg`);
        await pca9685.setServo(pattern.channel, pattern.endAngle);
        await sleep(pattern.duration);
    }
}

/**
 * サーボモーターを安全に停止・終了処理します。
 * @param {PCA9685} pca9685 - PCA9685のインスタンス
 * @param {number} channel - 停止させるサーボのチャンネル
 */
async function shutdownServo(pca9685, channel) {
    if (!pca9685) return;
    console.log("[JS] 演出完了。サーボを中立に戻し、電源をオフにします。");
    await pca9685.setServo(channel, 0); // 中立位置に戻す
    if (typeof pca9685.allOff === "function") {
        await pca9685.allOff(); // 全チャンネルのPWM信号を停止
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

    const pattern = getAnimationPattern(winner);
    
    let pca9685;
    try {
        // サーボドライバーを初期化
        pca9685 = await initializeServoDriver();

        // アニメーションを実行
        await runServoAnimation(pca9685, pattern);

    } catch (error) {
        console.error("[JS エラー] 処理中にエラーが発生しました:", error);
    } finally {
        // ★★★ プログラムが正常終了しても、エラーで落ちても、必ず実行される後片付け ★★★
        await shutdownServo(pca9685, pattern.channel);
        console.log("[JS] プログラムを終了します。");
    }
}

// アプリケーションを実行
main();
