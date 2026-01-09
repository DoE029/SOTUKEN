import asyncio
import datetime
from BLE_beacon_v2 import scan_beacon
import LED_Buzzer_v4 as gpio

LOG_FILE = "beacon_log.txt"

# 最新の検知状態を保持
latest_beacons = None  # ← 初期は None にして「未確定」扱い

def update_and_log(beacons, target_ids):
    """
    検知状態を更新し、ログに記録し、GPIOを制御。
    :return: target_idsがすべて揃った場合に True を返す。
    """
    global latest_beacons
    latest_beacons = beacons  # 状態を保存

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | 検知: {beacons}\n")

    # GPIO制御（検知したら青点灯・赤消灯）
    gpio.update_status(beacons, target_ids)

    found_ids = [b["id"].lower() for b in beacons]
    # すべてのターゲットIDが検知されたかチェック
    all_found = all(t.lower() in found_ids for t in target_ids)

    if all_found:
        print(f"{timestamp}  忘れ物なし！ ")
    else:
        print(f"{timestamp} ⚠️ 忘れ物があります！ ")
    
    return all_found # 全部揃ったかどうかを返す


async def buzzer_task(target_ids):
    """不足がある間は一定間隔で鳴らす常駐タスク"""
    while True:
        # ✅ 修正点: latest_beacons が None であれば、空リスト [] として扱う。
        # これにより、システム起動直後の initial scan の結果を待たずに、
        # 最初から「不足状態」と判定され、ブザーが鳴り始める。
        current_beacons = latest_beacons if latest_beacons is not None else []
        
        found_ids = [b["id"].lower() for b in current_beacons]
        
        # 不足がある場合にブザーを鳴らす
        if not all(t.lower() in found_ids for t in target_ids):
            gpio.buzzer_warning()
            
        try:
            # タスクがキャンセルされた場合に備えて await を try-except に入れる
            await asyncio.sleep(1) # ここいじるとブザーの感覚が狭まる。たぶんスキャン感覚。
        except asyncio.CancelledError:
            # キャンセルされたらループを抜ける
            print("ブザー警告停止。")
            break
        

async def main_loop(target_ids):
    gpio.setup_gpio()
    # ブザータスクのハンドルを保持
    buzzer_handle = asyncio.create_task(buzzer_task(target_ids))
    
    try:
        while True:
            # 🔽🔽🔽 メインループ処理（スキャン、判定など） 🔽🔽🔽
            try:
                # 8秒に1回スキャン（2秒スキャン＋6秒休止）
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
                all_found = False
            else:
                all_found = update_and_log(beacons, target_ids)
            # 🔼🔼🔼 メインループ処理（スキャン、判定など） 🔼🔼🔼
            
            if all_found:
                print(f"{datetime.datetime.now().strftime('%H:%M:%S')}全部揃いました。行ってらっしゃい！。")
                
                # 1. ブザー警告タスクを即座に停止
                if buzzer_handle:
                    buzzer_handle.cancel()
                    try:
                        await asyncio.wait_for(buzzer_handle, timeout=0.1)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        pass
                
                # 2. 青ランプを点滅 (例: 3回点滅、合計3秒)
                try:
                    # update_and_logで既に点灯しているはずですが、確実にHIGHにします
                    gpio.set_all_blue_leds(True) 
                    
                    # 10秒間待機
                    await asyncio.sleep(10)
                    
                    # Note: 青ランプをOFFにする処理は、
                    # finallyブロック内の gpio.cleanup_gpio() が実行時に自動で行います。
                except AttributeError:
                    print("⚠️ LED_Buzzer_v3に set_all_blue_leds 関数がないため点滅をスキップしました。")
                
                # 3. メインループを抜ける
                break # 終了へ
            
            await asyncio.sleep(3) # スキャン時間(2秒)と合わせて合計8秒周期

    except KeyboardInterrupt:
        # 手動終了のメッセージ
        print("\n手動での終了操作を検出しました...")
    finally:
        # ... (クリーンアップ処理は変更なし) ...
        if buzzer_handle:
            try:
                await asyncio.wait_for(buzzer_handle, timeout=0.1) 
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
                
        gpio.cleanup_gpio()
        
        print("システムを終了します")

if __name__ == "__main__":
    target_ids = ["DC:0D:30:16:88:8B", "DC:0D:30:16:87:F1"]
    # ユーザーコードには二重のimportがありましたが、ここでは一つに統合しています。
    asyncio.run(main_loop(target_ids))