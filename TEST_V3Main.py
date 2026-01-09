import asyncio
import datetime
from BLE_beacon_v2 import scan_beacon
import LED_Buzzer_v5 as gpio

LOG_FILE = "beacon_log.txt"

# --- ⚙️ 距離設定 ---
RSSI_THRESHOLD = -70 

# 最新の検知状態を保持
latest_beacons = None 

def update_and_log(beacons, target_ids):
    global latest_beacons
    latest_beacons = beacons 

    # RSSIが None でないことを確認してから比較
    found_ids_near = [
        b["id"].lower() for b in beacons 
        if b.get("rssi") is not None and b["rssi"] >= RSSI_THRESHOLD
    ]

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ✅ 「近くにある」と判定されたIDを表示
    if found_ids_near:
        print(f"--- 近くで検知されたID ({RSSI_THRESHOLD}dBm以上) ---")
        for fid in found_ids_near:
            print(f"  [検知中]: {fid}")
    else:
        print(f"⚠️ {RSSI_THRESHOLD}dBm 以内にターゲットのビーコンはありません")

    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | 全検知: {beacons}\n")

    gpio.update_status(beacons, target_ids, RSSI_THRESHOLD)

    all_found = all(t.lower() in found_ids_near for t in target_ids)

    if all_found:
        print(f"{timestamp} ✨ 全て近くにあります！忘れ物なし！")
    else:
        print(f"{timestamp} ⚠️ 離れているか、見つからない物があります！")
    
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
    
    print("🔍 スキャンを開始します...")
    try:
        while True:
            try:
                # 3秒間スキャン
                beacons = await scan_beacon(timeout=3, target_ids=target_ids)
            except Exception as e:
                print(f"❌ スキャン中にエラーが発生しました: {e}")
                beacons = [] 

            # ✅ スキャン結果自体の表示（IDが取得できたかどうかのチェック）
            if beacons:
                found_all_ids = [b["id"].upper() for b in beacons]
                print(f"\n📡 ビーコンを検知しました: {', '.join(found_all_ids)}")
                all_found = update_and_log(beacons, target_ids)
            else:
                now_str = datetime.datetime.now().strftime('%H:%M:%S')
                # ✅ 取得できなかった場合の表示
                print(f"\n{now_str} ⚠️ ビーコンが一つも見つかりませんでした（範囲外または電源OFF）")
                gpio.update_status([], target_ids, RSSI_THRESHOLD)
                all_found = False
            
            if all_found:
                print(f"{datetime.datetime.now().strftime('%H:%M:%S')} 全部揃いました。終了します。")
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