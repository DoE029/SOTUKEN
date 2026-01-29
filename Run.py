import subprocess
import time
import sys
import os
import json
from datetime import datetime

def start_system():
    # --- 設定：終了したい時間を指定 ---
    END_HOUR = 22
    END_MINUTE = 0

    # --- 絶対パス設定（systemd対応） ---
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATUS_FILE = os.path.join(BASE_DIR, "tag_status.json")

    # 起動時に終了フラグを False に戻す
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["is_finished"] = False
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("前回の終了フラグをリセットしました（スキャン開始準備完了）")
        except Exception as e:
            print(f"リセットに失敗しました: {e}")

    print("忘れ物探知システムを起動しています...")

    # 1. Webアプリ (app.py) を起動
    flask_dir = os.path.join(BASE_DIR, "webapp")
    flask_process = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=flask_dir
    )
    print("Webアプリを起動しました (http://ラズパイIP:5000)")

    time.sleep(3)

    # 2. メインのスキャンプログラム (WEB_MAIN.py) を起動
    print("ビーコンスキャンを開始します...")
    try:
        subprocess.run([sys.executable, "WEB_MAIN.py"], cwd=BASE_DIR, check=True)

        print(f"\nスキャン完了！ {END_HOUR:02d}:{END_MINUTE:02d} までWebアプリを維持します。")

        # 指定時刻まで待機
        while True:
            now = datetime.now()

            if now.hour > END_HOUR or (now.hour == END_HOUR and now.minute >= END_MINUTE):
                print(f"\n{END_HOUR:02d}:{END_MINUTE:02d} になりました。自動終了します。")
                break

            time.sleep(30)

    except KeyboardInterrupt:
        print("\n手動で停止されました（Ctrl+C）")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        print("Webアプリを終了しています...")
        flask_process.terminate()
        time.sleep(2)

if __name__ == "__main__":
    start_system()
