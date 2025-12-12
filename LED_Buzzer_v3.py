import RPi.GPIO as GPIO
import time

# --- ⚙️ GPIOピン設定 ⚙️ ---
LED1_BLUE = 11      # 持ち物A用 青LED
LED1_RED  = 25      # 持ち物A用 赤LED
LED2_BLUE = 8     # 持ち物B用 青LED
LED2_RED  = 7       # BCMで存在するピンに修正
BUZZER_PIN = 9    # ブザー

# --- ⚙️ 動作パラメータ ⚙️ ---
BUZZER_DURATION = 0.2   # ピッの長さ
BUZZER_INTERVAL = 0.3   # ピッの間隔
LED_BLINK_INTERVAL = 0.5

def setup_gpio():
    GPIO.setmode(GPIO.BCM)  # 配線がBCM番号ならこのまま
    for pin in [LED1_BLUE, LED1_RED, LED2_BLUE, LED2_RED, BUZZER_PIN]:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
    print("GPIO初期設定完了")

def cleanup_gpio():
    GPIO.cleanup()
    print("GPIOクリーンアップ完了")

def buzzer_warning():
    """
    不足がある間は「ぴぴぴ」を鳴らし続ける。
    ループごとに呼ばれるので、鳴り続ける形になる。
    """
    for _ in range(3):  # 1セットで3回鳴らす
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(BUZZER_DURATION)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(BUZZER_INTERVAL)
    # ループ側で asyncio.sleep(0.1〜2) が入るので自然に間隔が空く

def update_status(beacons, target_ids):
    found_ids = [b["id"] for b in beacons]

    # 持ち物A
    if target_ids[0] in found_ids:
        GPIO.output(LED1_BLUE, GPIO.HIGH)
        GPIO.output(LED1_RED, GPIO.LOW)
    else:
        GPIO.output(LED1_BLUE, GPIO.LOW)
        GPIO.output(LED1_RED, GPIO.HIGH)  # 不足時は赤常時オン

    # 持ち物B
