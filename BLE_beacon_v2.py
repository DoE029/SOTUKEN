import asyncio
from bleak import BleakScanner

# ターゲットビーコンのMACアドレスリスト
TARGET_IDS = [
    "DC:0D:30:16:88:8B",
    "DC:0D:30:16:87:F1"
]

async def scan_beacon(timeout=5, target_ids=None):
    """
    BLEビーコンをスキャンする処理
    param timeout   : スキャン時間（秒数）
    param target_ids: 検知したいビーコンのアドレスリスト
    return          : 検知したビーコン情報のリスト
    """
    print(f"{timeout}秒スキャンを開始")
    devices = await BleakScanner.discover(timeout=timeout)
    beacon = []

    for d in devices:
        # フィルタリング（特定のビーコンだけ）
        if target_ids is None or d.address.lower() in [addr.lower() for addr in target_ids]:
            beacon_info = {
                "id": d.address,   # MACアドレス
                "name": d.name if d.name else "Unknown",
                "rssi": d.rssi    # RSSI値(dBm)
            }
            beacon.append(beacon_info)

    return beacon

def judge_range(beacon, threshold=-50):
    """
    RSSI値から近距離/遠距離を判定
    """
    if beacon["rssi"] > threshold:
        return "near"
    else:
        return "far"

if __name__ == "__main__":
    # 実行例
    beacon = asyncio.run(scan_beacon(timeout=5, target_ids=TARGET_IDS))

    if not beacon:
        print("ターゲットビーコンが見つかりませんでした")
    else:
        for b in beacon:
            status = judge_range(b, threshold=-50)
            print(f"検知: {b['id']} (RSSI = {b['rssi']}dBm) → {status}")
            # ここに同期させたい処理を書く
            # 例: GitHubにログをpushする、GPIOでLEDを点灯するなど
