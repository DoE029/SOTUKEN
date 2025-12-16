import RPi.GPIO as GPIO
import time

# --- ⚙️ GPIOピン設定（BCM） ---
LED1_BLUE = 11
LED1_RED = 25
LED2_BLUE = 8
LED2_RED = 7
BUZZER_PIN = 9

# --- ⚙️ 動作パラメータ ---
BUZZER_DURATION = 0.2
BUZZER_INTERVAL = 0.5

# --- ⚙️ GPIOセットアップフラグ ---
_gpio_is_setup = False


def setup_gpio():
    """GPIOの初期設定を行う"""
    global _gpio_is_setup
    if not _gpio_is_setup:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in [LED1_BLUE, LED1_RED, LED2_BLUE, LED2_RED, BUZZER_PIN]:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        _gpio_is_setup = True
        print("GPIO初期設定完了")

def cleanup_gpio():
    """GPIO設定を解放する"""
    global _gpio_is_setup
    if _gpio_is_setup:
        GPIO.cleanup()
        _gpio_is_setup = False
        # print("GPIOクリーンアップ完了") # main_loopで出力されるためここでは省略

# -------------------------------------------------------------
# 🔽🔽🔽 新規追加関数 🔽🔽🔽

def set_blue_led(pin: int, state: bool):
    """
    指定されたピンの青色LEDの状態を設定します。

    :param pin: 制御する青色LEDのピン番号 (LED1_BLUE または LED2_BLUE)
    :param state: True で点灯 (HIGH)、False で消灯 (LOW)
    """
    if not _gpio_is_setup:
        print("Warning: GPIOが設定されていません。LED制御をスキップします。")
        return
    
    # ピンが青色LEDであることを確認する（安全のため）
    if pin not in [LED1_BLUE, LED2_BLUE]:
        print(f"Error: ピン {pin} は青色LEDピンとして登録されていません。")
        return

    output_state = GPIO.HIGH if state else GPIO.LOW
    GPIO.output(pin, output_state)

def set_all_blue_leds(state: bool):
    """
    すべての青色LEDを同時に指定された状態に設定します。
    （main_loopからの点滅処理に使用することを想定）

    :param state: True で点灯 (HIGH)、False で消灯 (LOW)
    """
    if not _gpio_is_setup:
        print("Warning: GPIOが設定されていません。LED制御をスキップします。")
        return

    output_state = GPIO.HIGH if state else GPIO.LOW
    GPIO.output(LED1_BLUE, output_state)
    GPIO.output(LED2_BLUE, output_state)

# -------------------------------------------------------------
# 既存関数

def buzzer_warning():
    """不足がある間はぴぴぴを鳴らす"""
    # ... (既存のコード) ...
    for _ in range(3):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(BUZZER_DURATION)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(BUZZER_INTERVAL)

def update_status(beacons, target_ids):
    """検知したら青点灯・赤消灯。未検知なら赤点灯"""
    found_ids = [b["id"].lower() for b in beacons]
    t0, t1 = target_ids[0].lower(), target_ids[1].lower()

    # 持ち物A
    if t0 in found_ids:
        GPIO.output(LED1_BLUE, GPIO.HIGH)
        GPIO.output(LED1_RED, GPIO.LOW)
    else:
        GPIO.output(LED1_BLUE, GPIO.LOW)
        GPIO.output(LED1_RED, GPIO.HIGH)

    # 持ち物B
    if t1 in found_ids:
        GPIO.output(LED2_BLUE, GPIO.HIGH)
        GPIO.output(LED2_RED, GPIO.LOW)
    else:
        GPIO.output(LED2_BLUE, GPIO.LOW)
        GPIO.output(LED2_RED, GPIO.HIGH)

    # 両方揃っているか
    if t0 in found_ids and t1 in found_ids:
        GPIO.output(BUZZER_PIN, GPIO.LOW)
    else:
        # Note: buzzer_warningはメインループ（buzzer_task）から呼び出されるため、
        # ここではブザー制御は行わない方がメインロジックと衝突しない安全な設計ですが、
        # 既存のコードに従い残しています。
        # 修正後の main_loop のロジックでは buzzer_task がブザーを制御するため、
        # この else 節の buzzer_warning() はコメントアウトすることが推奨されます。
        pass # buzzer_warning()