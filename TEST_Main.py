import asyncio
import datetime
from BLE_beacon_v2 import scan_beacon
import LED_Buzzer_v3 as gpio

# --- RSSIしきい値設定 ---
# 1.5m程度を目安にするなら -55〜-60dBm が目安
RSSI_THRESHOLD = -60
LOG_FILE = "beacon_log.txt"

def update_and_log(beacons, target_ids):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | 検知: {beacons}\n")

    # RSSIしきい値を考慮して「近いビーコン」だけを有効にする
    found_ids = []
    for b in beacons:
        rssi = b.get("rssi")
        if rssi is not None and rssi > RSSI_THRESHOLD:
            found_ids.append(b["id"])

    gpio.update_status(beacons, target_ids)

    if all(t in found_ids for t in target_ids):
        print(f"{timestamp} ✅ 全部揃いました（近距離）")
    else:
        print(f"{timestamp} ⚠️ 不足があります（遠いか未検知）")

async def main_loop(target_ids):
    gpio.setup_gpio()
    try:
        while True:
            try:
                # スキャン時間を短縮（ほぼ常時）
                beacons = await scan_beacon(timeout=1, target_ids=target_ids)
            except Exception as e:
                now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"{now_str} ⚠️ スキャンで例外発生: {e}")
                beacons = []

            if not beacons:
                print("⚠️ ビーコンが見つかりませんでした")
                gpio.update_status([], target_ids)
            else:
                update_and_log(beacons, target_ids)

            # ほぼ常時スキャン（待機時間を極小に）
            await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        print("終了します")
    finally:
        gpio.cleanup_gpio()
        print("GPIOクリーンアップ完了")

if __name__ == "__main__":
    target_ids = ["DC:0D:30:16:88:8B", "DC:0D:30:16:87:F1"]  # 実際のビーコンMACアドレス
    asyncio.run(main_loop(target_ids))
