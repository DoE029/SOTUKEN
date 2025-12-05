a = 12

print(a)

'''
import RPi.GPIO as GPIO
import time

# --- GPIOピン番号の設定 ---
SENSOR_PIN = 17  # センサーの入力ピン (例としてGPIO17)
LED_PIN    = 27  # LEDの出力ピン (例としてGPIO27)
BUZZER_PIN = 22  # ブザーの出力ピン (例としてGPIO22)

# GPIO設定
GPIO.setmode(GPIO.BCM)  # BCMモード (GPIO番号で指定)
GPIO.setup(SENSOR_PIN, GPIO.IN)  # センサーは入力
GPIO.setup(LED_PIN, GPIO.OUT)    # LEDは出力
GPIO.setup(BUZZER_PIN, GPIO.OUT) # ブザーは出力

def check_for_forgotten_item():
    """センサーの状態をチェックし、忘れ物があれば通知する関数"""
    
    # センサーの状態を読み取る (センサーの種類により読み取りロジックは変わります)
    # 例: 赤外線センサーで、HIGHが「モノがない＝忘れ物」とする場合
    sensor_state = GPIO.input(SENSOR_PIN)
    
    if sensor_state == GPIO.HIGH:
        print("🚨 忘れ物を感知しました！")
        # 忘れ物を知らせるアクション
        GPIO.output(LED_PIN, GPIO.HIGH)  # LED点灯
        # アクティブブザーの場合
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(1) # ブザーを1秒間鳴らす
        GPIO.output(BUZZER_PIN, GPIO.LOW)
    else:
        print("✅ モノがあります。異常なし。")
        GPIO.output(LED_PIN, GPIO.LOW) # LED消灯
        
try:
    while True:
        check_for_forgotten_item()
        time.sleep(5)  # 5秒ごとにチェック
        
except KeyboardInterrupt:
    print("システムを終了します")
    
finally:
    GPIO.cleanup() # GPIO設定をリセット
'''

'''
# PCでの動作確認用ダミー関数
def simulate_gpio_output(pin, state):
    state_str = "HIGH (点灯/鳴動)" if state == 1 else "LOW (消灯)"
    print(f"  [GPIOシミュレーション] ピン{pin}を {state_str} に設定")

def check_for_forgotten_item():
    # ... (ビーコン検出ロジックはPCで実行可能) ...
    
    found_beacon = False # 仮に検出できなかったと仮定
    
    if not found_beacon:
        print("忘れ物を感知しました！")
        # 実際のGPIO制御関数をダミー関数に置き換える
        simulate_gpio_output(27, 1) # LED ON
        simulate_gpio_output(22, 1) # BUZZER ON
    else:
        print("異常なし。")
        simulate_gpio_output(27, 0) # LED OFF
'''
