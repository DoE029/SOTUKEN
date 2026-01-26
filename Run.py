import subprocess
import time
import sys
import os

def start_system():
    # 1. 現在のフォルダの場所を取得
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("🚀 忘れ物探知システムを起動しています...")

    # 2. Webアプリ (app.py) を起動
    # cwd を設定することで、webapp2 フォルダの中にある templates 等を正しく認識させます
    flask_process = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=os.path.join(base_dir, "webapp2")
    )
    print("✅ Webアプリを起動しました (http://localhost:5000)")

    # サーバーの立ち上がりを待つ
    time.sleep(3)

    # 3. メインのスキャンプログラム (WEB_MAIN.py) を起動
    print("✅ ビーコンスキャンを開始します...")
    try:
        # WEB_MAIN.py を実行（これは終了フラグを書き込むまで止まる）
        subprocess.run([sys.executable, "WEB_MAIN.py"], cwd=base_dir, check=True)
        
        # --- WEB_MAIN.py が正常終了した後の処理 ---
        print("\n✨ 全てのタグを検知しました！")
        print("ブラウザを確認してください。60秒後にWebアプリを終了します。")
        
        # すぐにFlaskを止めると画面が見えなくなるので、少し待つ
        time.sleep(60) 
        
    except KeyboardInterrupt:
        print("\n🛑 手動で停止されました")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
    finally:
        # Webアプリを終了
        flask_process.terminate()
        print("👋 今日も行ってらっしゃい！！")

if __name__ == "__main__":
    start_system()