import asyncio
from bleak import BleakScanner

async def scan_beacon(timeout=3, target_ids=None):
    """BLEビーコンをスキャンする処理"""
    print("持ち物を探してます...")
    
    #discover() はdevice, advertisement_dataのタプルを返すモードで実行
    devices_dict = await BleakScanner.discover(timeout=timeout, return_adv=True)
    beacons = []

    targets_lower = [addr.lower() for addr in target_ids] if target_ids else None

    #devices_dict.values() には BLEDeviceとAdvertisementDataが入ってる
    for d, adv in devices_dict.values():
        #advertisement_data から直接 RSSI を取得
        rssi = adv.rssi if adv else None

        #もし上で取れなかった時用のバックアップ
        if rssi is None:
            rssi = getattr(d, "rssi", None)

        if targets_lower is None or d.address.lower() in targets_lower:
            beacon_info = {
                "id": d.address,
                "name": d.name if d.name else "Unknown",
                "rssi": rssi  # メイン側で期待してるrssi
            }
            beacons.append(beacon_info)

    return beacons