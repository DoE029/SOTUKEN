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
        rssi = d.metadata.get("rssi", None)  # 修正済み
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
