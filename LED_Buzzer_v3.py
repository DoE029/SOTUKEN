import RPi.GPIO as GPIO
import time

# --- ⚙️ GPIOピン設定 ⚙️ ---
LED1_BLUE = 17       # 持ち物A用 青LED
LED1_RED  = 22       # 持ち物A用 赤LED
LED2_BLUE = 27       # 持ち物B用 青LED
LED2_RED  = 5        # 持ち物B用 赤LED（例としてGPIO5を使用）
BUZZER_PIN = 23      # ブザー

# --- ⚙️ 動作パラメータ ⚙️ ---
BUZZER_DURATION = 0.2
BUZZER_SILENCE = 0.5
LED_BLINK_INTERVAL = 0.5

# --- GPIO初期化 ---
def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    for pin in [LED1_BLUE, LED1_RED, LED2_BLUE, LED2_RED, BUZZER_PIN]:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
    print("GPIO初期設定完了")

def cleanup_gpio():
    GPIO.cleanup()
    print("GPIOクリーンアップ完了")

# --- 赤LED点滅処理 ---
def blink_led(pin, times=3, interval=LED_BLINK_INTERVAL):
    for _ in range(times):
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(interval)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(interval)

# --- ブザー警告処理 ---
def buzzer_warning(times=3, duration=BUZZER_DURATION, silence=BUZZER_SILENCE):
    for _ in range(times):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(silence)

# --- 状態更新処理 ---
def update_status(beacons, target_ids):
    found_ids = [b["id"] for b in beacons]

    # 持ち物A
    if target_ids[0] in found_ids:
        GPIO.output(LED1_BLUE, GPIO.HIGH)
        GPIO.output(LED1_RED, GPIO.LOW)
    else:
        GPIO.output(LED1_BLUE, GPIO.LOW)
        blink_led(LED1_RED, times=3)

    # 持ち物B
    if target_ids[1] in found_ids:
        GPIO.output(LED2_BLUE, GPIO.HIGH)
        GPIO.output(LED2_RED, GPIO.LOW)
    else:
        GPIO.output(LED2_BLUE, GPIO.LOW)
        blink_led(LED2_RED, times=3)

    # 全体判定
    if all(t in found_ids for t in target_ids):
        GPIO.output(BUZZER_PIN, GPIO.LOW)
    else:
        buzzer_warning(times=3)
