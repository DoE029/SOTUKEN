import asyncio
import datetime
import json
import os
from BLE_New_beacon import scan_beacon
import LED_New_Buzzer as gpio

# ----------------- 設定 --------------------
START_TIME = "14:43"   # チェック開始時刻
END_TIME   = "14:46"   # チェック終了時刻

RSSI_THRESHOLD = -70   #タグの検知範囲設定数値
LOG_FILE = "beacon_log.txt"
STATS_FILE = "forget_stats.json"

# MACアドレスと表示名の対応表
ID_MAP = {"DC:0D:30:16:88:8B": "タグ 1",
          "DC:0D:30:16:87:F1": "タグ 2"}

latest_beacons = None

def record_stats(missing_names):

    """忘れ物（不足している物）を統計ファイルに記録"""
    stats = {}
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                stats = json.load(f)
        except:
            stats = {}

    for name in missing_names:
        stats[name] = stats.get(name, 0) + 1

    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)


def in_time_range(start_str, end_str):

    """現在時刻が指定時間内か判定"""
    now = datetime.datetime.now().time()
    start = datetime.datetime.strptime(start_str, "%H:%M").time()
    end = datetime.datetime.strptime(end_str, "%H:%M").time()
    return start <= now <= end


def update_and_log(beacons, target_ids):

    global latest_beacons
    latest_beacons = beacons

    print(f"--- 現在の状況 (しきい値: {RSSI_THRESHOLD}dBm) ---")

    for b in beacons:
        raw_id = b['id'].upper()
        display_name = ID_MAP.get(raw_id, raw_id)

        rssi_val = b.get("rssi")
        rssi_display = f"{rssi_val}dBm" if rssi_val is not None else "取得不可"
        status = "OK" if rssi_val is not None and rssi_val >= RSSI_THRESHOLD else "遠い/未検知"

        print(f"  番号: {display_name} | RSSI: {rssi_display} | 状態: {status}")

    found_ids_near = [
        b["id"].upper() for b in beacons
        if b.get("rssi") is not None and b["rssi"] >= RSSI_THRESHOLD]

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | 全検知: {beacons}\n")

    gpio.update_status(beacons, target_ids, RSSI_THRESHOLD)

    all_found = all(t.upper() in found_ids_near for t in target_ids)

    if all_found:
        print("全て近くにあります。忘れ物なし")
    else:
        missing_names = [
            ID_MAP.get(t.upper(), t)
            for t in target_ids
            if t.upper() not in found_ids_near
        ]
        print(f"不足中: {missing_names}")
        record_stats(missing_names)

    return all_found


async def buzzer_task(target_ids):

    """不足がある間は一定間隔で鳴らすタスク"""
    while True:
        current_beacons = latest_beacons if latest_beacons is not None else []

        found_ids_near = [
            b["id"].upper() for b in current_beacons
            if b.get("rssi") is not None and b["rssi"] >= RSSI_THRESHOLD
        ]

        if not all(t.upper() in found_ids_near for t in target_ids):
            gpio.buzzer_warning()

        try:
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            break


async def main_loop(target_ids):
    print(f"{START_TIME} 〜 {END_TIME} の間だけチェックを行います")

    # 時間帯に入るまで待機
    while not in_time_range(START_TIME, END_TIME):
        await asyncio.sleep(10)

    print("チェック時間帯に入りました。スキャンを開始します")

    gpio.setup_gpio()
    buzzer_handle = asyncio.create_task(buzzer_task(target_ids))

    try:
        while in_time_range(START_TIME, END_TIME):

            try:
                beacons = await scan_beacon(timeout=3, target_ids=target_ids)
            except Exception as e:
                print(f"スキャンエラー: {e}")
                beacons = []

            if beacons:
                all_found = update_and_log(beacons, target_ids)
            else:
                now_str = datetime.datetime.now().strftime('%H:%M:%S')
                print(f"{now_str} 持ち物が見つかりません (範囲外)")
                latest_beacons = []
                gpio.update_status([], target_ids, RSSI_THRESHOLD)
                all_found = False

            if all_found:
                print("全部揃いました")
                if buzzer_handle:
                    buzzer_handle.cancel()

                try:
                    gpio.set_all_blue_leds(True)
                    await asyncio.sleep(10)
                except AttributeError:
                    pass

                break

            await asyncio.sleep(3)

    except KeyboardInterrupt:
        print("手動終了")

    finally:
        if buzzer_handle and not buzzer_handle.done():
            buzzer_handle.cancel()

        gpio.cleanup_gpio()
        print("チェック時間帯を終了しました")

if __name__ == "__main__":
    targets = ["DC:0D:30:16:88:8B", "DC:0D:30:16:87:F1"]
    asyncio.run(main_loop(targets))
