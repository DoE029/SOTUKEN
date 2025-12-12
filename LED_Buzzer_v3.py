import RPi.GPIO as GPIO
import time

# --- ⚙️ GPIOピン設定（BCM） ---
LED1_BLUE = 11
LED1_RED  = 25
LED2_BLUE = 8
LED2_RED  = 7
BUZZER_PIN = 9

# --- ⚙️ 動作パラメータ ---
BUZZER_DURATION = 0.2  # ピッの長さ（必要なら 0.3〜0.4 に調整）
BUZZER_INTERVAL = 0.3  # ピッの間隔

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in [LED1_BLUE, LED1_RED, LED2_BLUE, LED2_RED, BUZZER_PIN]:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
    print("GPIO初期設定完了")

def cleanup_gpio():
    GPIO.cleanup()
    print("GPIOクリーンアップ完了")

def buzzer_warning():
    """
    不足がある間は毎ループで ぴぴぴ を鳴らす。
    ループ側の休止で自然に間隔が空く（8秒周期）。
    """
    for _ in range(3):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(BUZZER_DURATION)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(BUZZER_INTERVAL)

def update_status(near_beacons, target_ids):
    """
    near_beacons: 近距離と判定されたビーコンのみのリスト
    target_ids: 監視対象のMACアドレス（大小無視）
    """
    found_ids = [b["id"].lower() for b in near_beacons]
    t0, t1 = target_ids[0].lower(), target_ids[1].lower()

    # 持ち物A（近距離なら青オン・赤オフ）
    if t0 in found_ids:
        GPIO.output(LED1_BLUE, GPIO.HIGH)
        GPIO.output(LED1_RED, GPIO.LOW)
    else:
        GPIO.output(LED1_BLUE, GPIO.LOW)
        GPIO.output(LED1_RED, GPIO.HIGH)

    # 持ち物B（近距離なら青オン・赤オフ）
    if t1 in found_ids:
        GPIO.output(LED2_BLUE, GPIO.HIGH)
        GPIO.output(LED2_RED, GPIO.LOW)
    else:
        GPIO.output(LED2_BLUE, GPIO.LOW)
        GPIO.output(LED2_RED, GPIO.HIGH)

    # 両方近距離で揃っているか
    if t0 in found_ids and t1 in found_ids:
        GPIO.output(BUZZER_PIN, GPIO.LOW)
    else:
        buzzer_warning()
