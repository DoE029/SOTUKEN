
print('sasdwsd')

'''
import asyncio
from bleak import BleakScanner

async def scan_beacons(timeout = 5, target_ids = None):
    """
    BLEビーコンをスキャンする処理
    param timeout   : スキャン時間（秒数）
    param target_id : 検知したいビーコンのアドレスリスト（Noneだとすべてになる）
    return          : 検知したビーコン情報のリスト
    """
    print(f":{timeout}秒数スキャンを開始")
    devices = await BleakScanner.discover(timeout = timeout)
    beacons = []

    for d in devices:
        #フィルタリング（特定のビーコンだけ）
        if target_ids is None or d.address in target_ids:
            beacons_info = {
                "id" : d.address,  #MACアドレス入力
                "name" : d.name if d.name else "Unknown",
                "rssi" : d.rssi    #電波強度のこと(dBm)
            }
            beacons.append(beacons_info)

        return beacons
  
'''