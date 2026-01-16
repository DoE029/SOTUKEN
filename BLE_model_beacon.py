import asyncio
from bleak import BleakScanner

async def scan_beacon(timeout=3, target_ids=None):
    """BLEビーコンをスキャンする処理"""
    print("持ち物を探してます...")



    devices = await BleakScanner.discover(timeout=timeout)
    beacons = []

    targets_lower = [addr.lower() for addr in target_ids] if target_ids else None


    for d in devices:
        # bleak バージョン差分に耐える RSSI 取得
        rssi = None
        if hasattr(d, "rssi"):
            rssi = d.rssi
        else:
            md = getattr(d, "metadata", None)
            if isinstance(md, dict):
                rssi = md.get("rssi", None)

        if targets_lower is None or d.address.lower() in targets_lower:
            beacon_info = {
                "id": d.address,
                "name": d.name if d.name else "Unknown",
                "rssi": rssi
            }
            beacons.append(beacon_info)

    return beacons
