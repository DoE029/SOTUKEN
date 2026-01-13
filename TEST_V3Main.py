import asyncio
import datetime
from BLE_beacon_v3 import scan_beacon
import LED_Buzzer_v5 as gpio

LOG_FILE = "beacon_log.txt"

# --- ⚙️ 距離設定 ---
RSSI_THRESHOLD = -70 

# 最新の検知状態を保持
latest_beacons = None 

def update_and_log(beacons, target_ids):
    global latest_beacons
    latest_beacons = beacons 

    # ✅ 検知されたすべてのタグのRSSIを表示
    print(f"\n--- 📡 現在の電波強度 (目標: {RSSI_THRESHOLD}dBm以上) ---")
    for b in beacons:
        rssi_val = b.get("rssi")
        rssi_display = f"{rssi_val}dBm" if rssi_val is not None else "取得不可"
        status = " OK" if rssi_val is not None and rssi_val >= RSSI_THRESHOLD else "遠い/未検知"
        print(f"  ID: {b['id'].upper()} | RSSI: {rssi_display} | {status}")

    # RSSIが None でないことを確認してから比較
    found_ids_near = [
        b["id"].lower() for b in beacons 
        if b.get("rssi") is not None and b["rssi"] >= RSSI_THRESHOLD
    ]

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | 全検知: {beacons}\n")

    gpio.update_status(beacons, target_ids, RSSI_THRESHOLD)

    all_found = all(t.lower() in found_ids_near for t in target_ids)

    if all_found:
        print("全て近くにあります！忘れ物なし！")
    else:
        print("不足しているか、離れている物があります。")
    
    return all_found


async def buzzer_task(target_ids):
    """不足がある間は一定間隔で鳴らす常駐タスク"""
    while True:
        if latest_beacons is not None:
            found_ids_near = [
                b["id"].lower() for b in latest_beacons 
                if b.get("rssi") is not None and b["rssi"] >= RSSI_THRESHOLD
            ]
            
            if not all(t.lower() in found_ids_near for t in target_ids):
                gpio.buzzer_warning()
        
        try:
            await asyncio.sleep(1) 
        except asyncio.CancelledError:
            break

async def main_loop(target_ids):
    gpio.setup_gpio()
    buzzer_handle = asyncio.create_task(buzzer_task(target_ids))
    
    print(f"🔍 スキャンを開始します... (しきい値: {RSSI_THRESHOLD})")
    try:
        while True:
            try:
                # 3秒間スキャン
                beacons = await scan_beacon(timeout=3, target_ids=target_ids)
            except Exception as e:
                print(f"❌ スキャンエラー: {e}")
                beacons = [] 

            if beacons:
                all_found = update_and_log(beacons, target_ids)
            else:
                now_str = datetime.datetime.now().strftime('%H:%M:%S')
                print(f"\n{now_str} ⚠️ ビーコンが見つかりません (範囲外)")
                gpio.update_status([], target_ids, RSSI_THRESHOLD)
                all_found = False
            
            if all_found:
                print(f"\n{datetime.datetime.now().strftime('%H:%M:%S')} 全部揃いました！")
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
        print("\n手動終了")
    finally:
        if buzzer_handle:
            buzzer_handle.cancel()
        gpio.cleanup_gpio()
        print("システムを終了します")

if __name__ == "__main__":
    targets = ["DC:0D:30:16:88:8B", "DC:0D:30:16:87:F1"]
    asyncio.run(main_loop(targets))