import asyncio
from bleak import BleakScanner

async def scan_beacon(timeout=5, target_ids=None):
    """
    BLEビーコンをスキャンする処理
    """
    print(f"{timeout}秒スキャンを開始")
    devices = await BleakScanner.discover(timeout=timeout)
    beacon = []

    for d in devices:
        # RSSIは metadata に含まれる（新しい bleak 仕様）
        rssi = d.metadata.get("rssi", None)
        if target_ids is None or d.address.lower() in [addr.lower() for addr in target_ids]:
            beacon_info = {
                "id": d.address,
                "name": d.name if d.name else "Unknown",
                "rssi": rssi
            }
            beacon.append(beacon_info)

    return beacon

def judge_range(beacon, threshold=-50):
    """
    RSSI値から近距離/遠距離を判定
    """
    rssi = beacon.get("rssi")
    if rssi is not None and rssi > threshold:
        return "near"
    else:
        return "far"

if __name__ == "__main__":
    TARGET_IDS = ["DC:0D:30:16:88:8B", "DC:0D:30:16:87:F1"]
    beacon = asyncio.run(scan_beacon(timeout=5, target_ids=TARGET_IDS))

    if not beacon:
        print("ターゲットビーコンが見つかりませんでした")
    else:
        for b in beacon:
            status = judge_range(b, threshold=-50)
            print(f"検知: {b['id']} (RSSI = {b['rssi']}dBm) → {status}")
