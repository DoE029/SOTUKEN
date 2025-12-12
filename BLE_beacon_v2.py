import asyncio
from bleak import BleakScanner

async def scan_beacon(timeout=1, target_ids=None):
    """
    BLEビーコンをスキャンする処理（ほぼ常時用）
    timeout: スキャン時間（秒）
    target_ids: 検知したいビーコンのアドレスリスト（大文字小文字無視）
    return: 検知したビーコン情報のリスト [{id, name, rssi}]
    """
    print(f"{timeout}秒スキャンを開始")
    devices = await BleakScanner.discover(timeout=timeout)
    beacons = []

    # 事前に lower 化比較リストを用意
    targets_lower = None
    if target_ids:
        targets_lower = [addr.lower() for addr in target_ids]

    for d in devices:
        # bleak バージョン差分に耐える RSSI 取得
        rssi = None
        if hasattr(d, "rssi"):
            rssi = d.rssi
        else:
            md = getattr(d, "metadata", None)
            if isinstance(md, dict):
                rssi = md.get("rssi", None)

        # フィルタリング（ターゲットのみ）
        if targets_lower is None or d.address.lower() in targets_lower:
            beacon_info = {
                "id": d.address,
                "name": d.name if d.name else "Unknown",
                "rssi": rssi
            }
            beacons.append(beacon_info)

    return beacons

def judge_range(beacon, threshold=-55):
    """
    RSSI値から近距離/遠距離を判定（None安全）
    threshold: 近距離判定のRSSIしきい値
    """
    rssi = beacon.get("rssi")
    if rssi is not None and rssi > threshold:
        return "near"
    return "far"
