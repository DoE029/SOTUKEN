import asyncio
import datetime
from BLE_beacon_v2 import scan_beacon
import LED_Buzzer_v4 as gpio

LOG_FILE = "beacon_log.txt"

# 🔽 距離感のしきい値（環境に合わせて調整してください）
# -60 だとかなり近く、-70〜-80 だと少し離れても反応します。
RSSI_THRESHOLD = -70 

# 最新の検知状態を保持
latest_beacons = None  

def update_and_log(beacons, target_ids):
    global latest_beacons
    latest_beacons = beacons  

    # ✅ 「指定のID」かつ「RSSIがしきい値より大きい（近い）」ものだけを抽出
    found_beacons_near = [
        b["id"].lower() for b in beacons 
        if b["rssi"] >= RSSI_THRESHOLD
    ]

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ログには詳細（RSSI値など）を残すと調整しやすくなります
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | 全検知: {beacons}\n")

    # GPIO制御（近くにあるタグのみを判定対象に渡す）
    # ※LED_Buzzer側のupdate_statusがIDリストを受け取る前提
    gpio.update_status(beacons, target_ids, RSSI_THRESHOLD)

    # すべてのターゲットIDが「近くに」あるかチェック
    all_found = all(t.lower() in found_beacons_near for t in target_ids)

    if all_found:
        print(f"{timestamp} ✨ 全て近くにあります！忘れ物なし！")
    else:
        print(f"{timestamp} ⚠️ 離れているか、見つからない物があります！")
    
    return all_found 


async def buzzer_task(target_ids):
    """不足がある間は一定間隔で鳴らす常駐タスク"""
    while True:
        current_beacons = latest_beacons if latest_beacons is not None else []
        
        # ✅ ここでも距離の判定を入れる
        found_ids_near = [
            b["id"].lower() for b in current_beacons 
            if b["rssi"] >= RSSI_THRESHOLD
        ]
        
        if not all(t.lower() in found_ids_near for t in target_ids):
            gpio.buzzer_warning()
            
        try:
            await asyncio.sleep(1) 
        except asyncio.CancelledError:
            print("ブザー警告停止。")
            break

# main_loop 以下の変更は不要ですが、RSSI_THRESHOLDを意識した動きになります。
# (以下略)