import asyncio
import datetime
from BLE_New_beacon import scan_beacon
import LED_New_Buzzer as gpio

LOG_FILE = "beacon_log.txt"

# MACアドレスと表示名の対応表
ID_MAP = {
    "dc:0d:30:16:88:8b": "1",
    "dc:0d:30:16:87:f1": "2"
}

# --- 距離設定 ---
RSSI_THRESHOLD = -70 

# 最新の検知状態を保持
latest_beacons = None 


def update_and_log(beacons, target_ids):
    global latest_beacons
    latest_beacons = beacons 

    print(f"現在の状況 (目標: {RSSI_THRESHOLD}dBm以上)")
    for b in beacons:
        raw_id = b['id'].lower()
        # 辞書から「1」や「2」を取得。なければIDを表示
        display_name = ID_MAP.get(raw_id, raw_id.upper())
        
        rssi_val = b.get("rssi")
        rssi_display = f"{rssi_val}dBm" if rssi_val is not None else "取得不可"
        status = " OK" if rssi_val is not None and rssi_val >= RSSI_THRESHOLD else "遠い/未検知"
        
        # ここを display_name に変更
        print(f"  番号: {display_name} | RSSI: {rssi_display} | {status}")

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
        print(" 全て近くにあります。忘れ物はありません！")
    else:
        # 不足している番号を具体的に表示
        missing = [ID_MAP.get(t.lower(), t) for t in target_ids if t.lower() not in found_ids_near]
        print(f" 不足中: {missing}")
    
    return all_found


async def buzzer_task(target_ids):
    """不足がある間は一定間隔で鳴らす常駐タスク"""
    while True:
        # latest_beacons が None（まだ一度もスキャンできていない）か、
        # 中身が空（範囲内に何もない）の場合を考慮する
        current_beacons = latest_beacons if latest_beacons is not None else []
        
        # 近くにあるタグのIDリストを作成
        found_ids_near = [
            b["id"].lower() for b in current_beacons 
            if b.get("rssi") is not None and b["rssi"] >= RSSI_THRESHOLD
        ]
        
        # ターゲットが一つでも見つかっていない、またはRSSIが低い場合は警告
        if not all(t.lower() in found_ids_near for t in target_ids):
            gpio.buzzer_warning()
        
        try:
            await asyncio.sleep(1) 
        except asyncio.CancelledError:
            break

async def main_loop(target_ids):
    gpio.setup_gpio()
    buzzer_handle = asyncio.create_task(buzzer_task(target_ids))
    
    print(" スキャンを開始")
    try:
        while True:
            try:
                # 3秒間スキャン
                beacons = await scan_beacon(timeout=3, target_ids=target_ids)
            except Exception as e:
                print(f" スキャンエラー: {e}")
                beacons = [] 

            if beacons:
                all_found = update_and_log(beacons, target_ids)
            else:
                now_str = datetime.datetime.now().strftime('%H:%M:%S')
                print(f"\n{now_str} 持ち物が見つかりません (範囲外)")
                gpio.update_status([], target_ids, RSSI_THRESHOLD)
                all_found = False
            
            if all_found:
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