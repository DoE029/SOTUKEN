import asyncio
import datetime
import json
import os
from BLE_beacon_v3 import scan_beacon
import LED_Buzzer_v5 as gpio

# --- ⚙️ 設定項目 ---
SCHEDULED_TIME = "09:33"  # 毎日この時間になったら実行
RSSI_THRESHOLD = -70 
LOG_FILE = "beacon_log.txt"
STATS_FILE = "forget_stats.json" # アプリ表示用の統計データ

# MACアドレスと表示名の対応表（大文字で統一）
ID_MAP = {
    "DC:0D:30:16:88:8B": "1",
    "DC:0D:30:16:87:F1": "2"
}

# 最新の検知状態を保持
latest_beacons = None 

def record_stats(missing_names):
    """忘れ物（不足している物）を統計ファイルに記録する"""
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

async def wait_until_time(target_time_str):
    """指定の時間まで待機する（分単位で一致すれば開始）"""
    print(f"⏰ {target_time_str} になるまで待機します...")
    while True:
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M") # 現在の「時:分」
        
        if current_time == target_time_str:
            print(f"🔔 時間になりました！({current_time})。チェックを開始します。")
            break
            
        # 10秒ごとにチェック（精度を上げました）
        await asyncio.sleep(5)

def update_and_log(beacons, target_ids):
    global latest_beacons
    latest_beacons = beacons 

    print(f"\n--- 📡 現在の状況 (目標: {RSSI_THRESHOLD}dBm以上) ---")
    for b in beacons:
        # 取得したIDを大文字に変換して照合
        raw_id = b['id'].upper()
        display_name = ID_MAP.get(raw_id, raw_id)
        
        rssi_val = b.get("rssi")
        rssi_display = f"{rssi_val}dBm" if rssi_val is not None else "取得不可"
        status = " OK" if rssi_val is not None and rssi_val >= RSSI_THRESHOLD else "遠い/未検知"
        print(f"  番号: {display_name} | RSSI: {rssi_display} | {status}")

    found_ids_near = [
        b["id"].upper() for b in beacons 
        if b.get("rssi") is not None and b["rssi"] >= RSSI_THRESHOLD
    ]

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | 全検知: {beacons}\n")

    gpio.update_status(beacons, target_ids, RSSI_THRESHOLD)

    # 全て揃っているか判定（大文字で比較）
    all_found = all(t.upper() in found_ids_near for t in target_ids)

    if all_found:
        print("✅ 全て近くにあります！忘れ物なし！")
    else:
        # 不足している番号を表示
        missing_names = [ID_MAP.get(t.upper(), t) for t in target_ids if t.upper() not in found_ids_near]
        print(f"⚠️ 不足中: {missing_names}")
        # アプリ用に統計を記録
        record_stats(missing_names)
    
    return all_found


async def buzzer_task(target_ids):
    """不足がある間は一定間隔で鳴らす常駐タスク"""
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
    # 🌟 指定時刻まで待機する処理を追加
    await wait_until_time(SCHEDULED_TIME)

    gpio.setup_gpio()
    buzzer_handle = asyncio.create_task(buzzer_task(target_ids))
    
    print(f"🔍 スキャンを開始 (しきい値: {RSSI_THRESHOLD})")
    try:
        while True:
            try:
                beacons = await scan_beacon(timeout=3, target_ids=target_ids)
            except Exception as e:
                print(f"❌ スキャンエラー: {e}")
                beacons = [] 

            if beacons:
                all_found = update_and_log(beacons, target_ids)
            else:
                now_str = datetime.datetime.now().strftime('%H:%M:%S')
                print(f"\n{now_str} ⚠️ 持ち物が見つかりません (範囲外)")
                latest_beacons = [] # 検知なしとして更新
                gpio.update_status([], target_ids, RSSI_THRESHOLD)
                all_found = False
            
            if all_found:
                print(f"\n{datetime.datetime.now().strftime('%H:%M:%S')} 🎉 全部揃いました！")
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
        if 'buzzer_handle' in locals() and buzzer_handle and not buzzer_handle.done():
            buzzer_handle.cancel()
        gpio.cleanup_gpio()
        print("システムを終了します")

if __name__ == "__main__":
    # ターゲットも大文字で指定
    targets = ["DC:0D:30:16:88:8B", "DC:0D:30:16:87:F1"]
    asyncio.run(main_loop(targets))