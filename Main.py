# --- 必要なライブラリをインポート ---
import asyncio                # 非同期処理（BLEスキャンで使用）
import datetime               # ログに時刻を記録するために使用
from BLE_beacon_v2 import scan_beacon   # BLEビーコン検知処理（別ファイルから読み込み）
import LED_Buzzer_v3 as gpio            # GPIO制御処理（別ファイルから読み込み）

# --- RSSIしきい値設定 ---
RSSI_THRESHOLD = -60          # RSSIがこの値より強ければ「近い」と判定
LOG_FILE = "beacon_log.txt"   # ログを保存するファイル名

# --- 検知結果をログに残し、GPIO制御を呼び出す関数 ---
def update_and_log(beacons, target_ids):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 検知結果をログファイルに追記
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | 検知: {beacons}\n")

    # GPIO制御（LED・ブザー）を呼び出し
    gpio.update_status(beacons, target_ids)

    # RSSIしきい値を考慮して「近いビーコン」を抽出
    found_ids = [b["id"] for b in beacons if b["rssi"] > RSSI_THRESHOLD]

    # 全部揃っているか判定してメッセージを表示
    if all(t in found_ids for t in target_ids):
        print(f"{timestamp} ✅ 全部揃いました")
    else:
        print(f"{timestamp} ⚠️ 不足があります")

# --- 朝だけ監視するループ ---
async def main_loop(target_ids):
    """
    朝8時から45分間だけBLEビーコンを監視するループ
    """
    try:
        gpio.setup_gpio()
        while True:
            now = datetime.datetime.now()

            # 朝8:00〜8:45の間だけ監視を実行
            if now.hour == 8 and now.minute < 45:
                beacons = await scan_beacon(timeout=5, target_ids=target_ids)

                if not beacons:
                    print(f"{now.strftime('%H:%M:%S')} ⚠️ ビーコンが見つかりませんでした")
                    with open(LOG_FILE, "a") as f:
                        f.write(f"{now.strftime('%Y-%m-%d %H:%M:%S')} | 検知なし\n")
                else:
                    update_and_log(beacons, target_ids)

                # 非同期sleepに変更
                await asyncio.sleep(2)
            else:
                # 監視時間外は休止
                print(f"{now.strftime('%H:%M')} → 監視時間外です。待機中...")
                await asyncio.sleep(60)

    except KeyboardInterrupt:
        print("終了します")
    finally:
        gpio.cleanup_gpio()

# --- プログラムのエントリーポイント ---
if __name__ == "__main__":
    target_ids = ["DC:0D:30:16:88:8B", "DC:0D:30:16:87:F1"]  # 実際のビーコンMACアドレス
    asyncio.run(main_loop(target_ids))
