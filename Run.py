import subprocess
import time
import sys
import os
import json
from datetime import datetime

def start_system():
    # --- 設定：終了したい時間を指定（23時00分） ---
    END_HOUR = 9
    END_MINUTE = 34

    STATUS_FILE = "tag_status.json"
    # ------------------------------------------

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 起動時に終了フラグを False に戻す
    status_path = os.path.join(base_dir, STATUS_FILE)
    if os.path.exists(status_path):
        try:
            with open(status_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # フラグをリセットして上書き保存
            data["is_finished"] = False
            with open(status_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("前回の終了フラグをリセットしました（スキャン開始準備完了）")
        except Exception as e:
            print(f"リセットに失敗しました（初回起動などの場合）: {e}")

    print("忘れ物探知システムを起動しています...")

    # 1. Webアプリ (app.py) を起動
    flask_process = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=os.path.join(base_dir, "webapp2")
    )
    print(f"Webアプリを起動しました (http://localhost:5000)")

    time.sleep(3)

    # 2. メインのスキャンプログラム (WEB_MAIN.py) を起動
    print("ビーコンスキャンを開始します...")
    try:
        # スキャン実行
        subprocess.run([sys.executable, "WEB_MAIN.py"], cwd=base_dir, check=True)
        
        print(f"\nスキャン完了！{END_HOUR:02d}:{END_MINUTE:02d} までWebアプリを維持します。")
        print("（途中で終了したい場合は Ctrl+C を押してください）")

        # 3. 指定時刻になるまで待機するループ
        while True:
            now = datetime.now()
            # 現在時刻が指定時間を過ぎたか判定
            if now.hour == END_HOUR and now.minute >= END_MINUTE:
                print(f"\n{END_HOUR:02d}:{END_MINUTE:02d} になりました。自動終了します。")
                break
            
            # 日を跨いでいた場合などのための予備判定（現在時刻が設定時より大きければ終了）
            if now.hour > END_HOUR:
                print(f"\n指定時間を過ぎているため、自動終了します。")
                break

            time.sleep(30)  # 30秒ごとに時刻をチェック

    except KeyboardInterrupt:
        print("\n手動で停止されました（Ctrl+C）")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        print("Webアプリを終了しています...")
        flask_process.terminate()
        print("今日も行ってらっしゃい！！")

if __name__ == "__main__":
    start_system()