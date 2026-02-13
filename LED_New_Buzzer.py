import RPi.GPIO as GPIO
import time

#--- GPIOピン設定（BCM）★固定でお願いします★ ---
LED1_BLUE = 11  #持ち物A 青色LED
LED1_RED  = 25  #持ち物A 赤色LED
LED2_BLUE = 8   #持ち物B 青色LED
LED2_RED  = 7   #持ち物B 赤色LED
BUZZER_PIN = 9

#--- 動作パラメータ ---
BUZZER_DURATION = 0.2
BUZZER_INTERVAL = 0.02

#--- GPIOセットアップフラグ ---
_gpio_is_setup = False


def setup_gpio():
    """GPIOの初期設定を行う"""
    global _gpio_is_setup
    if not _gpio_is_setup:
        #BCMモード、警告表示なしを設定
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        #全部のピンを出力として設定して、LOW（消灯、オフ）にする
        for pin in [LED1_BLUE, LED1_RED, LED2_BLUE, LED2_RED, BUZZER_PIN]:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
            
        _gpio_is_setup = True
        print("GPIO初期設定完了")

def cleanup_gpio():
    """GPIO設定を解放する"""
    global _gpio_is_setup
    if _gpio_is_setup:
        # cleanup前に、全部のピンを安全のためにLOWに戻す必要があるっぽい
        for pin in [LED1_BLUE, LED1_RED, LED2_BLUE, LED2_RED, BUZZER_PIN]:
            try:
                GPIO.output(pin, GPIO.LOW)
            except RuntimeError:
                # クリーンアップ済みのピンを操作しようとした時を考慮
                pass
                
        GPIO.cleanup()
        _gpio_is_setup = False
        #メインループ側で出力

# -------------------------------------------------------------
#新しく追加したLED制御関数 

def set_all_blue_leds(state: bool):
    """
    すべての青色LED（LED1_BLUE, LED2_BLUE）を同時に指定された状態に設定します。
    （メインループの点滅処理で使用することを想定）

    :param state: True で点灯 (HIGH)、False で消灯 (LOW)
    """
    if not _gpio_is_setup:
        print("Warning: GPIOが設定されていません。LED制御をスキップします。")
        return

    output_state = GPIO.HIGH if state else GPIO.LOW
    GPIO.output(LED1_BLUE, output_state)
    GPIO.output(LED2_BLUE, output_state)

# -------------------------------------------------------------
#今までのやつ

def buzzer_warning():
    """不足がある間はぴぴぴを鳴らす"""
    if not _gpio_is_setup:
        return
        
    for _ in range(3):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        #time.sleepは非同期処理 (asyncio) とは独立しているため、
        #メインループで呼び出す際は注意が必要です。
        #今回はメインループの async def main_loop から独立した
        #buzzer_task 内で呼び出されるため問題ありません。
        time.sleep(BUZZER_DURATION) 
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(BUZZER_INTERVAL)

def update_status(beacons, target_ids, rssi_threshold):

    if not _gpio_is_setup:
        return
    #rssi(検知するときの数値) が None ではないことを確認する判定を追加
    found_ids = [
        b["id"].lower() for b in beacons 
        if b.get("rssi") is not None and b["rssi"] >= rssi_threshold
    ]
    
    # （下の判定ロジックは変更してない）
    if len(target_ids) < 2:
        return 

    t0, t1 = target_ids[0].lower(), target_ids[1].lower()

    #持ち物Aの判定
    if t0 in found_ids:
        GPIO.output(LED1_BLUE, GPIO.HIGH)
        GPIO.output(LED1_RED, GPIO.LOW)
    else:
        GPIO.output(LED1_BLUE, GPIO.LOW)
        GPIO.output(LED1_RED, GPIO.HIGH)

    #持ち物Bの判定
    if t1 in found_ids:
        GPIO.output(LED2_BLUE, GPIO.HIGH)
        GPIO.output(LED2_RED, GPIO.LOW)
    else:
        GPIO.output(LED2_BLUE, GPIO.LOW)
        GPIO.output(LED2_RED, GPIO.HIGH)