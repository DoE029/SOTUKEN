import asyncio
import datetime
from BLE_beacon_v2 import scan_beacon
import LED_Buzzer_v5 as gpio

LOG_FILE = "beacon_log.txt"

# --- ⚙️ 距離設定 ---
# -60 (非常に近い) 〜 -80 (少し離れてもOK) の間で調整してください
RSSI_THRESHOLD = -70 

# 最新の検知状態を保持
latest_beacons = None 

def update_and_log(beacons, target_ids):
    """
    検知状態を更新し、ログに記録し、GPIOを制御。
    :return: ターゲットがすべて「近くに」揃った場合に True を返す。
    """
    global latest_beacons
    latest_beacons = beacons 

    # ✅ 指定IDのタグが「しきい値以上の強さ(＝近く)」で存在するかチェック
    # ✅ rssi が None ではないことを確認する判定を追加
    found_ids_near = [
        b["id"].lower() for b in beacons 
        if b.get("rssi") is not None and b["rssi"] >= RSSI_THRESHOLD
    ]

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | 全検知: {beacons}\n")

    # GPIO制御（LEDの点灯切り替え）
    # ※LED側の関数もRSSIを受け取れるように修正が必要です
    gpio.update_status(beacons, target_ids, RSSI_THRESHOLD)

    # すべてのターゲットIDが「近くに」あるかチェック
    all_found = all(t.lower() in found_ids_near for t in target_ids)

    if all_found:
        print(f"{timestamp} ✨ 全て近くにあります！忘れ物なし！")
    else:
        print(f"{timestamp} ⚠️ 離れているか、見つからない物があります！")
    
    return all_found


async def buzzer_task(target_ids):
    """不足がある間は一定間隔で鳴らす常駐タスク"""
    while True:
        # スキャン結果が出るまでは鳴らさない
        if latest_beacons is not None:
            # 近くにあるタグだけを抽出
            found_ids_near = [
                b["id"].lower() for b in latest_beacons 
                if b.get("rssi") is not None and b["rssi"] >= RSSI_THRESHOLD
            ]
            
            # ターゲットが近くに揃っていなければブザーを鳴らす
            if not all(t.lower() in found_ids_near for t in target_ids):
                gpio.buzzer_warning()
        
        try:
            await asyncio.sleep(1) 
        except asyncio.CancelledError:
            print("ブザー警告停止。")
            break

async def main_loop(target_ids):
    gpio.setup_gpio()
    # ブザータスク起動
    buzzer_handle = asyncio.create_task(buzzer_task(target_ids))
    
    try:
        while True:
            try:
                # 3秒間スキャン
                beacons = await scan_beacon(timeout=3, target_ids=target_ids)
            except Exception as e:
                now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"{now_str} ⚠️ スキャン失敗: {e}")
                beacons = [] 

            if not beacons:
                now_str = datetime.datetime.now().strftime('%H:%M:%S')
                print(f"{now_str} ⚠️ 持ち物が見つかりません")
                gpio.update_status([], target_ids, RSSI_THRESHOLD)
                all_found = False
            else:
                all_found = update_and_log(beacons, target_ids)
            
            # 全部近くに揃った場合
            if all_found:
                print(f"{datetime.datetime.now().strftime('%H:%M:%S')} 全部揃いました。行ってらっしゃい！")
                
                if buzzer_handle:
                    buzzer_handle.cancel()
                    try:
                        await asyncio.wait_for(buzzer_handle, timeout=0.1)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        pass
                
                # 青ランプを10秒間点灯して終了
                try:
                    gpio.set_all_blue_leds(True) 
                    await asyncio.sleep(10)
                except AttributeError:
                    print("⚠️ LED_Buzzer側に set_all_blue_leds がありません")
                
                break 
            
            # 次のスキャンまで待機（合計で約6〜7秒周期）
            await asyncio.sleep(3) 

    except KeyboardInterrupt:
        print("\n手動終了")
    finally:
        if buzzer_handle:
            buzzer_handle.cancel()
        gpio.cleanup_gpio()
        print("システムを終了します")

if __name__ == "__main__":
    # ここにあなたのビーコンIDを入れてください
    targets = ["DC:0D:30:16:88:8B", "DC:0D:30:16:87:F1"]
    asyncio.run(main_loop(targets))