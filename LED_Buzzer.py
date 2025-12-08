import RPi.GPIO as GPIO #ラズパイのどの線に指すか
import time
import asyncio # asyncioは、bleakと組み合わせるために必要です

# --- ⚙️ 設定定数 ---
# GPIOピン番号 (BCMモード)
# BCMモード → 汎用入出力ピンををPythonで制御する際に、ピンの番号を指定する方法
LED_PIN    = 27  # LED接続ピン (GPIO27を使用する想定)
BUZZER_PIN = 22  # ブザー接続ピン (GPIO22を使用する想定)

# 🚨 警告パターン設定 🚨
LED_BLINK_INTERVAL = 0.5  # LED点滅の間隔 (秒)
BUZZER_DURATION = 0.2     # ブザーを鳴らす時間 (秒)
BUZZER_SILENCE = 0.8      # ブザーの休止時間 (秒)

#GPIOの初期設定とクリーンアップ
def setup_gpio():
    """GPIOの初期設定を行う"""
    # BCMモードでピン番号を指定
    GPIO.setmode(GPIO.BCM) 
    # ピンを出力(OUT)に設定
    GPIO.setup(LED_PIN, GPIO.OUT) #27
    GPIO.setup(BUZZER_PIN, GPIO.OUT) #22
    
    # 初期状態はすべてOFF
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    print("GPIO初期設定完了。")

def cleanup_gpio():
    """プログラム終了時にGPIO設定をリセットする"""
    # すべてのピンの状態を解放
    GPIO.cleanup()
    print("GPIOクリーンアップ完了。")

#通知制御関数
#BLEビーコンのファイルから「スキャンとチェック」の関数から呼び出して使う

#忘れ物があった場合の１回通知してくれる
def notify_warning_once(times = 3):
    """
    警告アクションを1回実行する（LED点灯と短時間のブザー鳴動）。
    警告が継続する場合は、これを繰り返し呼び出す。
    """
    # 1. LED点灯 (点滅はループ側で制御するため、ここではONにする)
    GPIO.output(LED_PIN, GPIO.HIGH)
    
    # 2. ブザーを短く鳴らす(繰り返し)
    for _ in range(times):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)  #ブザーオン
        time.sleep(BUZZER_DURATION)         #ブザー0.2秒間なる
        GPIO.output(BUZZER_PIN, GPIO.LOW)   #ブザーオフ
        time.sleep(0.5)  # 休止時間を追加（音を不自然にしないため）
    
#忘れ物がそろったら
def notify_normal():
    """正常状態を通知する（LED、ブザーをOFFにする）"""
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.output(BUZZER_PIN, GPIO.LOW)



