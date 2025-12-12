import asyncio
import datetime
from BLE_beacon_v2 import scan_beacon
import LED_Buzzer_v3 as gpio

RSSI_THRESHOLD = -60
LOG_FILE = "beacon_log.txt"

def update_and_log(beacons, target_ids):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | 検知: {beacons}\n")

    gpio.update_status(beacons, target_ids)

    found_ids = []
    for b in beacons:
        rssi = b.get("rssi")
        if rssi is not None and rssi > RSSI_THRESHOLD:
            found_ids.append(b["id"])

    if all(t in found_ids for t in target_ids):
        print(f"{timestamp} ✅ 全部揃いました")
    else:
        print(f"{timestamp} ⚠️ 不足があります")

async def main_loop(target_ids):
    gpio.setup_gpio()
    try:
        while True:
            try:
                beacons = await scan_beacon(timeout=5, target_ids=target_ids)
            except Exception as e:
                now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"{now_str} ⚠️ スキャンで例外発生: {e}")
                with open(LOG_FILE, "a") as f:
                    f.write(f"{now_str} | スキャン失敗: {e}\n")
                beacons = []

            if not beacons:
                now_str = datetime.datetime.now().strftime('%H:%M:%S')
                print(f"{now_str} ⚠️ ビーコンが見つかりませんでした")
                with open(LOG_FILE, "a") as f:
                    f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 検知なし\n")
                gpio.update_status([], target_ids)
            else:
                update_and_log(beacons, target_ids)

            await asyncio.sleep(2)

    except KeyboardInterrupt:
        print("終了します")
    finally:
        gpio.cleanup_gpio()
        print("GPIOクリーンアップ完了")

if __name__ == "__main__":
    target_ids = ["DC:0D:30:16:88:8B", "DC:0D:30:16:87:F1"]
    asyncio.run(main_loop(target_ids))
