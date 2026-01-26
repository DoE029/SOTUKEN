import subprocess
import time
import sys

def start_system():
    print("忘れ物探知システムを起動しています...")

    # 1. Webアプリ (app.py) をバックグラウンドで起動
    # sys.executable は現在使っているpythonのパスを指定します
    flask_process = subprocess.Popen([sys.executable, "webapp2/app.py"])
    print("Webアプリを起動しました (http://localhost:5000)")

    # Webアプリが立ち上がるまで少し待つ
    time.sleep(2)

    # 2. メインのスキャンプログラム (main.py) を起動
    print("ビーコンスキャンを開始します...")
    try:
        # main.pyを実行（これは終了するまでここで止まります）
        main_process = subprocess.run([sys.executable, "WEB_MAIN"])
    except KeyboardInterrupt:
        print("\n システムを終了します...")
    finally:
        # main.pyが終了、またはCtrl+Cが押されたらWebアプリも終了させる
        flask_process.terminate()
        print("今日も行ってらっしょい！！")

if __name__ == "__main__":
    start_system()