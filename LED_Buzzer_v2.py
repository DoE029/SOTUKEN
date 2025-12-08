import RPi.GPIO as GPIO
import time

# --- ⚙️ GPIOピン設定 ⚙️ ---
LED1_PIN = 17        # 持ち物A用 青LED
LED2_PIN = 27        # 持ち物B用 青LED
RED_LED_PIN = 22     # 不足時 赤LED
BUZZER_PIN = 23      # ブザー

# --- ⚙️ 動作パラメータ ⚙️ ---
BUZZER_DURATION = 0.2   # ブザーが鳴る時間（秒）
BUZZER_SILENCE = 0.5    # ブザーの休止時間（秒）
LED_BLINK_INTERVAL = 0.5 # 赤LED点滅間隔（秒）

# --- GPIO初期化 ---
def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED1_PIN, GPIO.OUT)
    GPIO.setup(LED2_PIN, GPIO.OUT)
    GPIO.setup(RED_LED_PIN, GPIO.OUT)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    # 初期状態はすべてOFF
    GPIO.output(LED1_PIN, GPIO.LOW)
    GPIO.output(LED2_PIN, GPIO.LOW)
    GPIO.output(RED_LED_PIN, GPIO.LOW)
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    print("GPIO初期設定完了")

def cleanup_gpio():
    GPIO.cleanup()
    print("GPIOクリーンアップ完了")

# --- 赤LED点滅処理 ---
def blink_red_led(times=3, interval=LED_BLINK_INTERVAL):
    """不足があるとき赤LEDを点滅させる"""
    for _ in range(times):
        GPIO.output(RED_LED_PIN, GPIO.HIGH)  # 赤LED ON
        time.sleep(interval)
        GPIO.output(RED_LED_PIN, GPIO.LOW)   # 赤LED OFF
        time.sleep(interval)

# --- ブザー警告処理 ---
def buzzer_warning(times=3, duration=BUZZER_DURATION, silence=BUZZER_SILENCE):
    """不足がある間ブザーをピッピッピッと鳴らす"""
    for _ in range(times):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)   # ブザーON
        time.sleep(duration)
        GPIO.output(BUZZER_PIN, GPIO.LOW)    # ブザーOFF
        time.sleep(silence)

# --- 状態更新処理 ---
def update_status(beacons, target_ids):
    """
    BLEビーコンの検知結果に応じてLEDとブザーを制御する
    - 個別青LED → 持ち物ごとの状態
    - 赤LED+ブザー → 不足がある間警告
    """
    found_ids = [b["id"] for b in beacons]

    # 個別ランプ（青）
    GPIO.output(LED1_PIN, GPIO.HIGH if target_ids[0] in found_ids else GPIO.LOW)
    GPIO.output(LED2_PIN, GPIO.HIGH if target_ids[1] in found_ids else GPIO.LOW)

    # 全体判定
    if all(t in found_ids for t in target_ids):
        # 全部揃った → ブザー停止、赤LED消灯
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        GPIO.output(RED_LED_PIN, GPIO.LOW)
    else:
        # 不足あり → 赤LED点滅＋ブザー鳴動
        blink_red_led(times=3, interval=0.5)
        buzzer_warning(times=3)
