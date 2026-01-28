import subprocess
import time
import sys
import os
import json
from datetime import datetime

def start_system():
    # --- 設定：終了したい時間を指定（例：22時00分） ---
    END_HOUR = 22
    END_MINUTE = 0

    STATUS_FILE = "tag_status.json"
    # -----------------------------------------------------

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 起動時に終了フラグを False に戻す
    status_path = os.path.join(base_dir, STATUS_FILE)
    if os.path.exists(status_path):
        try:
            with open(status_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["is_finished"] = False
            with open(status_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("前回の終了フラグをリセットしました（スキャン開始準備完了）")
        except Exception as e:
            print(f"リセットに失敗しました: {e}")

    print("忘れ物探知システムを起動しています...")

    # 1. Webアプリ (app.py) を起動
    flask_dir = os.path.join(base_dir, "webapp")  # ← webapp2 ではなく webapp
    flask_process = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=flask_dir
    )
    print("Webアプリを起動しました (http://ラズパイIP:5000)")

    time.sleep(3)

    # 2. メインのスキャンプログラム (WEB_MAIN.py) を起動
    print("ビーコンスキャンを開始します...")
    try:
        subprocess.run([sys.executable, "WEB_MAIN.py"], cwd=base_dir, check=True)

        print(f"\nスキャン完了！ {END_HOUR:02d}:{END_MINUTE:02d} までWebアプリを維持します。")

        # 3. 指定時刻まで待機
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

        print("ラズパイをシャットダウンします...")
        os.system("sudo shutdown -h now")

if __name__ == "__main__":
    start_system()
