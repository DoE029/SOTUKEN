import asyncio
import datetime
from BLE_beacon_v2 import scan_beacon
import LED_Buzzer_v4 as gpio

LOG_FILE = "beacon_log.txt"

# 最新の検知状態（距離判定後の near_beacons を保存）
latest_near_beacons = None

# ★ 距離判定のしきい値（ここを調整）
NEAR_RSSI_THRESHOLD = -70   # -55〜-70 の間で調整

# ★ RSSI履歴（平均化用）
rssi_history = {}

def get_avg_rssi(beacon_id, rssi):
    """直近3回のRSSI平均を返す"""
    if beacon_id not in rssi_history:
        rssi_history[beacon_id] = []
    rssi_history[beacon_id].append(rssi)

    # 履歴は3つまで
    if len(rssi_history[beacon_id]) > 3:
        rssi_history[beacon_id].pop(0)

    return sum(rssi_history[beacon_id]) / len(rssi_history[beacon_id])


def update_and_log(beacons, target_ids):
    global latest_near_beacons

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | 検知: {beacons}\n")

    near_beacons = []

    for b in beacons:
        rssi = b.get("rssi")
        if rssi is None:
            continue

        # ★ RSSI平均化
        avg_rssi = get_avg_rssi(b["id"], rssi)

        # ★ 平均値で距離判定
        if avg_rssi > NEAR_RSSI_THRESHOLD:
            near_beacons.append(b)

    # ★ 最新状態を保存（LED/ブザー両方で使用）
