import asyncio
import datetime
from BLE_beacon_v2 import scan_beacon
import LED_Buzzer_v3 as gpio

# --- 近距離しきい値（1m目安） ---
# -55 で近すぎる/遠すぎる場合は -58〜-62 あたりを試してください
NEAR_RSSI_THRESHOLD = -55
HYST_ON_MARGIN = 3   # 近距離「オン」判定はしきい値より +3dB 強く
HYST_OFF_MARGIN = 3  # 「オフ」判定はしきい値より -3dB 弱く

LOG_FILE = "beacon_log.txt"

# 近距離状態を保持（ヒステリシス用）
near_state = {}  # { mac_lower: bool }

def update_and_log(beacons, target_ids):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ログ（全検知）
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | 全検知: {beacons}\n")

    # 近距離のみ抽出（ヒステリシス適用）
    near_beacons = []
    targets_lower = [t.lower() for t in target_ids]
    for b in beacons:
        mac = b["id"].lower()
        if mac not in targets_lower:
            continue

        rssi = b.get("rssi")
        prev_near = near_state.get(mac, False)

        if rssi is None:
            # RSSI不明なら前回状態を維持
            is_near = prev_near
        else:
            # ヒステリシス: ON/OFFの閾値に幅を持たせて誤判定を減らす
            on_thresh = NEAR_RSSI_THRESHOLD + HYST_ON_MARGIN
            off_thresh = NEAR_RSSI_THRESHOLD - HYST_OFF_MARGIN

            if prev_near:
                # 近距離継続にはそこまで強くなくてもOK（オフ判定まで下がらない限り維持）
                is_near = (rssi > off_thresh)
            else:
                # 新規で近距離に入るには少し強めに
                is_near = (rssi > on_thresh)

        near_state[mac] = is_near
        if is_near:
            near_beacons.append(b)

    # GPIO制御（近距離のみで青点灯・赤消灯）
    gpio.update_status(near_beacons, target_ids)

    # 両方近距離で揃っているか
    near_ids = [b["id"].lower() for b in near_beacons]
    if all(t.lower() in near_ids for t in target_ids):
        print(f"{timestamp} ✅ 近距離で全部揃いました（~1m）")
    else:
        print(f"{timestamp} ⚠️ 不足があります（遠いか未検知）")

async def main_loop(target_ids):
    gpio.setup_gpio()
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
                print(f"{now_str} ⚠️ ターゲットが見つかりませんでした")
                with open(LOG_FILE, "a") as f:
                    f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 検知なし\n")
                gpio.update_status([], target_ids)
            else:
                update_and_log(beacons, target_ids)

            await asyncio.sleep(6)  # 合計8秒周期

    except KeyboardInterrupt:
        print("終了します")
    finally:
        gpio.cleanup_gpio()
        print("GPIOクリーンアップ完了")

if __name__ == "__main__":
    target_ids = ["DC:0D:30:16:88:8B", "DC:0D:30:16:87:F1"]
    asyncio.run(main_loop(target_ids))
