import asyncio
import datetime
from BLE_beacon_v2 import scan_beacon
import LED_Buzzer_v4 as gpio

LOG_FILE = "beacon_log.txt"

# 最新の検知状態（距離判定後の near_beacons を保存）
latest_near_beacons = None

# ★ 距離判定のしきい値（ここを調整）
NEAR_RSSI_THRESHOLD = -60   # -55〜-65 の間で調整すると良い

def update_and_log(beacons, target_ids):
    """
    検知状態を更新し、ログに記録し、GPIOを制御します。
    :return: target_idsがすべて揃った場合に True を返します。
    """
    global latest_near_beacons

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | 検知: {beacons}\n")

    # ★ 距離フィルタ（近距離だけ抽出）
    near_beacons = []
    for b in beacons:
        rssi = b.get("rssi")
        if rssi is not None and rssi > NEAR_RSSI_THRESHOLD:
            near_beacons.append(b)

    # ★ 最新状態として near_beacons を保存（LED/ブザー両方で使う）
    latest_near_beacons = near_beacons

    # ★ LED制御は近距離だけで行う
    gpio.update_status(near_beacons, target_ids)

    found_ids = [b["id"].lower() for b in near_beacons]
    all_found = all(t.lower() in found_ids for t in target_ids)

    if all_found:
        print(f"{timestamp}  忘れ物なし！（近距離）")
    else:
        print(f"{timestamp} ⚠️ 忘れ物があります！（遠い or 未検知）")
    
    return all_found


async def buzzer_task(target_ids):
    """不足がある間は一定間隔で鳴らす常駐タスク"""
    global latest_near_beacons

    while True:
        # ★ 距離判定後の near_beacons を使う
        current_beacons = latest_near_beacons if latest_near_beacons is not None else []

        found_ids = [b["id"].lower() for b in current_beacons]

        # ★ LED と同じ判定基準に統一
        if not all(t.lower() in found_ids for t in target_ids):
            gpio.buzzer_warning()

        try:
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            print("ブザー警告停止。")
            break
        

async def main_loop(target_ids):
    gpio.setup_gpio()
    buzzer_handle = asyncio.create_task(buzzer_task(target_ids))
    
    try:
        while True:
            try:
                beacons = await scan_beacon(timeout=3, target_ids=target_ids)
            except Exception as e:
                now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"{now_str} ⚠️ スキャンで例外発生: {e}")
                with open(LOG_FILE, "a") as f:
                    f.write(f"{now_str} | スキャン失敗: {e}\n")
                beacons = [] 

            if not beacons:
                now_str = datetime.datetime.now().strftime('%H:%M:%S')
                print(f"{now_str} ⚠️ 持ち物が見つかりませんでした")
                with open(LOG_FILE, "a") as f:
                    f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 検知なし\n")
                gpio.update_status([], target_ids)

                # ★ 距離判定後の状態も空にする
                global latest_near_beacons
                latest_near_beacons = []

                all_found = False
            else:
                all_found = update_and_log(beacons, target_ids)
            
            if all_found:
                print(f"{datetime.datetime.now().strftime('%H:%M:%S')} 全部揃いました。行ってらっしゃい！")

                if buzzer_handle:
                    buzzer_handle.cancel()
                    try:
                        await asyncio.wait_for(buzzer_handle, timeout=0.1)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        pass
                
                try:
                    gpio.set_all_blue_leds(True)
                    await asyncio.sleep(10)
                except AttributeError:
                    print("⚠️ set_all_blue_leds が無いためスキップ")
                
                break
            
            await asyncio.sleep(3)

    except KeyboardInterrupt:
        print("\n手動終了を検出しました...")
    finally:
        if buzzer_handle:
            try:
                await asyncio.wait_for(buzzer_handle, timeout=0.1)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
                
        gpio.cleanup_gpio()
        print("システムを終了します")

if __name__ == "__main__":
    target_ids = ["DC:0D:30:16:88:8B", "DC:0D:30:16:87:F1"]
    asyncio.run(main_loop(target_ids))
