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
    #bleakライブラリの関数で、周囲のBLEデバイスをスキャンしてくれる
    #引数 timeout は「何秒間スキャンするか」を指定してくれる
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

def judge_range(beacon, threshold=-50):
    """
    RSSI値から近距離/遠距離を判定
    param beacon: ビーコン情報(dict)
    param threshold: 判定のしきい値(dBm)
    return: "near" or "far"
    near : 近い
    far  : 遠い
    threshold : しきい値、境界値や基準値のこと
    """

    if beacon["rssi"] > threshold:
        return "near"
    else:
        return "far"

if __name__ == "__main__":
    # 実行例
    target_ids = None  
    # ["AA:BB:CC:DD:EE:FF"] のように指定もできる
    beacons = asyncio.run(scan_beacons(timeout = 5, target_ids = target_ids))

    if not beacons:
        print("ビーコンが見つかりませんでした")
    else:
        for b in beacons:
            status = judge_range(b, threshold = -50)
            print(f"検知: {b['id']} (RSSI = {b['rssi']}dBm) → {status}")