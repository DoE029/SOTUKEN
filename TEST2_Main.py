import asyncio
import datetime
from BLE_beacon_v2 import scan_beacon
import LED_Buzzer_v3 as gpio

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
        print(f"{timestamp} ✅ 全部揃いました -> システム終了準備")
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
            try:
                # 8秒に1回スキャン（2秒スキャン＋6秒休止）
                beacons = await scan_beacon(timeout=2, target_ids=target_ids)
            except Exception as e:
                now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"{now_str} ⚠️ スキャンで例外発生: {e}")
                with open(LOG_FILE, "a") as f:
                    f.write(f"{now_str} | スキャン失敗: {e}\n")
                beacons = []

            if not beacons:
                now_str = datetime.datetime.now().strftime('%H:%M:%S')
                print(f"{now_str} ⚠️ ビーコンが見つかりませんでした")
                with open(LOG_FILE, "a") as f:
                    f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 検知なし\n")
                gpio.update_status([], target_ids)
            else:
                # ビーコン検知時: 状態更新とログ記録、そして全部揃ったかチェック
                all_found = update_and_log(beacons, target_ids)
                
                if all_found:
                    # ✅ 全部揃ったのでメインループを抜ける
                    break

            await asyncio.sleep(6)  # 合計8秒周期

    except KeyboardInterrupt:
        print("\n手動で終了します")
    finally:
        # メインループ終了時または手動終了時
        
        # 1. ブザータスクをキャンセル
        if buzzer_handle:
            buzzer_handle.cancel()
            # キャンセルが完了するのを待つ（タイムアウトを設けて安全に）
            try:
                await asyncio.wait_for(buzzer_handle, timeout=1.0)
            except asyncio.TimeoutError:
                print("ブザー警告タスクの停止がタイムアウトしました。")
            except asyncio.CancelledError:
                pass # 既にキャンセルされたのでOK
                
        # 2. GPIOクリーンアップ
        gpio.cleanup_gpio()
        print("GPIOクリーンアップ完了")
        # 3. 終了メッセージ
        print("システムを終了します")

if __name__ == "__main__":
    target_ids = ["DC:0D:30:16:88:8B", "DC:0D:30:16:87:F1"]
    asyncio.run(main_loop(target_ids))