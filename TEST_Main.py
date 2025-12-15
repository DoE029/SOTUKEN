import asyncio
import datetime
from BLE_beacon_v2 import scan_beacon
import LED_Buzzer_v3 as gpio

LOG_FILE = "beacon_log.txt"

# --- 近距離しきい値（玄関0.5〜1m目安） ---
NEAR_RSSI_THRESHOLD = -70   # 環境に応じて -68〜-72 に調整

# 最新の検知状態を保持
latest_beacons = []
latest_found_ids = []

def update_and_log(beacons, target_ids):
    global latest_beacons, latest_found_ids
    latest_beacons = beacons
    latest_found_ids = [b["id"].lower() for b in beacons]

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | 検知: {beacons}\n")

    # RSSIしきい値で近距離のみ抽出
    near_beacons = []
    targets_lower = [t.lower() for t in target_ids]
    for b in beacons:
        rssi = b.get("rssi")
        if rssi is not None and rssi > NEAR_RSSI_THRESHOLD and b["id"].lower() in targets_lower:
            near_beacons.append(b)

    # GPIO制御
    gpio.update_status(near_beacons, target_ids)

    near_ids = [b["id"].lower() for b in near_beacons]
    if all(t.lower() in near_ids for t in target_ids):
        print(f"{timestamp} ✅ 近距離で全部揃いました")
    else:
        print(f"{timestamp} ⚠️ 不足があります")

async def buzzer_task(target_ids):
    """不足がある間は一定間隔で鳴らす常駐タスク"""
    while True:
        if not all(t.lower() in latest_found_ids for t in target_ids):
            gpio.buzzer_warning()
        await asyncio.sleep(2)  # 2秒ごとに鳴らす（安定）

async def main_loop(target_ids):
    gpio.setup_gpio()
    try:
        asyncio.create_task(buzzer_task(target_ids))

        while True:
            try:
                beacons = await scan_beacon(timeout=2, target_ids=target_ids)
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

            await asyncio.sleep(6)  # 合計8秒周期

    except KeyboardInterrupt:
        print("終了します")
    finally:
        gpio.cleanup_gpio()
        print("GPIOクリーンアップ完了")

if __name__ == "__main__":
    target_ids = ["DC:0D:30:16:88:8B", "DC:0D:30:16:87:F1"]
    asyncio.run(main_loop(target_ids))
