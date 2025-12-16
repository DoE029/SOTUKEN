import asyncio
import datetime
from BLE_beacon_v2 import scan_beacon
import LED_Buzzer_v4 as gpio

LOG_FILE = "beacon_log.txt"

# 最新の検知状態を保持
latest_beacons = None  # ← 初期は None にして「未確定」扱い

def update_and_log(beacons, target_ids):
    """
    検知状態を更新し、ログに記録し、GPIOを制御します。
    :return: target_idsがすべて揃った場合に True を返します。
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
        print(f"{timestamp} ✅ 全部揃いました -> 終了準備へ")
    else:
        print(f"{timestamp} ⚠️ 不足があります")
    
    return all_found # 全部揃ったかどうかを返す

async def buzzer_task(target_ids):
    """不足がある間は一定間隔で鳴らす常駐タスク"""
    while True:
        # 初期状態（まだスキャン結果なし）は鳴らさない
        if latest_beacons is not None:
            found_ids = [b["id"].lower() for b in latest_beacons]
            # 不足がある場合にブザーを鳴らす
            if not all(t.lower() in found_ids for t in target_ids):
                gpio.buzzer_warning()
        try:
            # タスクがキャンセルされた場合に備えて await を try-except に入れる
            await asyncio.sleep(2)  # 2秒ごとにチェック
        except asyncio.CancelledError:
            # キャンセルされたらループを抜ける
            print("ブザー警告タスクを停止します。")
            break

async def main_loop(target_ids):
    gpio.setup_gpio()
    # ブザータスクのハンドルを保持
    buzzer_handle = asyncio.create_task(buzzer_task(target_ids))
    
    try:
        while True:
            # 🔽🔽🔽 メインループ処理 🔽🔽🔽
            try:
                # 8秒に1回スキャン（2秒スキャン＋6秒休止）
                beacons = await scan_beacon(timeout=2, target_ids=target_ids)
            except Exception as e:
                now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"{now_str} ⚠️ スキャンで例外発生: {e}")
                with open(LOG_FILE, "a") as f:
                    f.write(f"{now_str} | スキャン失敗: {e}\n")
                beacons = [] # エラー時は空リストとして扱う

            if not beacons:
                now_str = datetime.datetime.now().strftime('%H:%M:%S')
                print(f"{now_str} ⚠️ ビーコンが見つかりませんでした")
                with open(LOG_FILE, "a") as f:
                    f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 検知なし\n")
                gpio.update_status([], target_ids)
                all_found = False
            else:
                all_found = update_and_log(beacons, target_ids)
            # 🔼🔼🔼 メインループ処理 🔼🔼🔼
            
            if all_found:
                print(f"{datetime.datetime.now().strftime('%H:%M:%S')} ✨ 全部揃いました。点滅シーケンスへ移行します。")
                
                # 1. ブザー警告タスクを即座に停止
                if buzzer_handle:
                    buzzer_handle.cancel()
                    # キャンセルが完了するのを短時間待つ
                    try:
                        await asyncio.wait_for(buzzer_handle, timeout=0.1)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        pass
                
                # 2. 青ランプを点滅 (例: 3回点滅、合計3秒)
                BLINK_COUNT = 3
                BLINK_DURATION = 0.5 # ONとOFFを0.5秒ずつ

                # NOTE: gpio.set_blue_led(True/False) は仮のAPIです。
                # 実際のLED_Buzzer_v3モジュールの関数名に修正してください。
                try:
                    for i in range(BLINK_COUNT):
                        gpio.set_blue_led(True) # ON
                        await asyncio.sleep(BLINK_DURATION)
                        gpio.set_blue_led(False) # OFF
                        await asyncio.sleep(BLINK_DURATION)
                except AttributeError:
                    print("⚠️ LED_Buzzer_v3に set_blue_led 関数がないため点滅をスキップしました。")
                
                # 3. メインループを抜ける
                break # 終了へ
            
            await asyncio.sleep(6) # スキャン時間(2秒)と合わせて合計8秒周期

    except KeyboardInterrupt:
        # 手動終了のメッセージ（GPIOクリーンアップメッセージとは分ける）
        print("\n手動での終了操作を検出しました...")
    finally:
        # メインループ終了時（breakまたは例外）に必ず実行されるクリーンアップ
        
        # 1. ブザータスクがまだ実行中であれば、念のため完了を待つ（既にキャンセル済みのはず）
        if buzzer_handle:
            try:
                # すでにキャンセルされていれば即座に例外が出るため、待機処理は軽めに
                await asyncio.wait_for(buzzer_handle, timeout=0.1) 
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
                
        # 2. GPIOクリーンアップ
        gpio.cleanup_gpio()
        
        # 3. 終了メッセージを一本化
        print("GPIOクリーンアップ完了")
        print("システムを終了します")

if __name__ == "__main__":
    target_ids = ["DC:0D:30:16:88:8B", "DC:0D:30:16:87:F1"]
    # ユーザーコードには二重のimportがありましたが、ここでは一つに統合しています。
    asyncio.run(main_loop(target_ids))