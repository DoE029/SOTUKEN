import asyncio
import datetime
from BLE_beacon_v2 import scan_beacon
import LED_Buzzer_v3 as gpio

# --- 近距離しきい値（1m目安） ---
NEAR_RSSI_THRESHOLD = -55   # 環境に応じて -55〜-60 で調整
LOG_FILE = "beacon_log.txt"

def update_and_log(beacons, target_ids):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ログ（全検知）
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | 全検知: {beacons}\n")

    # 近距離のみ抽出
    near_beacons = []
    targets_lower = [t.lower() for t in target_ids]
    for b in beacons:
        rssi = b.get("rssi")
        if (rssi is not None) and (rssi > NEAR_RSSI_THRESHOLD) and (b["id"].lower() in targets_lower):
            near_beacons.append(b)

    # GPIO制御
    gpio.update_status(near_beacons, target_ids)

    # 両方近距離で揃っているか
    near_ids = [b["id"].lower() for b in near_beacons]
    if all(t.lower() in near_ids for t in target_ids):
        print(f"{timestamp} ✅ 近距離で全部揃いました（~1m）")
    else:
        print(f"{timestamp} ⚠️ 不足があります（遠いか未検知）")

async def main_loop(target_ids):
    gpio.setup_gpio()
    try:
        while True:
            try:
                # 8秒に1回スキャン
                beacons = await scan_beacon(timeout=2, target_ids=target_ids)
            except Exception as e:
                now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"{now_str} ⚠️ スキャンで例外発生: {e}")
                with open(LOG_FILE, "a") as f:
                    f.write(f"{now_str} | スキャン失敗: {e}\n")
                beacons = []

            if not beacons:
                now_str = datetime.datetime.now().strftime('%H:%M:%S')
                print(f"{now_str} ⚠️ ターゲットが見つかりませんでした")
                with open(LOG_FILE, "a") as f:
                    f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 検知なし\n")
                gpio.update_status([], target_ids)
            else:
                update_and_log(beacons, target_ids)

            # 休止時間を長めにして「8秒に1回」へ
            await asyncio.sleep(6)  # timeout=2 + sleep=6 → 合計8秒周期

    except KeyboardInterrupt:
        print("終了します")
    finally:
        gpio.cleanup_gpio()
        print("GPIOクリーンアップ完了")

if __name__ == "__main__":
    target_ids = ["DC:0D:30:16:88:8B", "DC:0D:30:16:87:F1"]  # 実際のビーコンMACアドレス
    asyncio.run(main_loop(target_ids))
