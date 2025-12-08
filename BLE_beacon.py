import asyncio
from bleak import BleakScanner

async def scan_beacon(timeout = 5, target_ids = None):
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
    beacon = []

    for d in devices:
        #フィルタリング（特定のビーコンだけ）
        if target_ids is None or d.address in target_ids:
            beacon_info = {
                "id" : d.address,  #MACアドレス入力
                "name" : d.name if d.name else "Unknown",
                "rssi" : d.rssi    #RSSI（受信信号強度指標）をdBm単位で取得
            }
            beacon.append(beacon_info)

    return beacon

def judge_range(beacon, threshold=-50):
    """
    RSSI値から近距離/遠距離を判定
    param beacon: ビーコン情報(dict)
    param threshold: 判定のしきい値(dBm)
    return: "near" or "far"
    near : 近い
    far  : 遠い
    threshold : しきい値、境界値や基準値のこと 
                こいつを50とかにすると-50とか100で範囲を設定できる
    """

    if beacon["rssi"] > threshold:
        return "near"
    else:
        return "far"

if __name__ == "__main__":
    # 実行例
    target_ids = None  
    # ["AA:BB:CC:DD:EE:FF"] のように指定もできる
    beacon = asyncio.run(scan_beacon(timeout = 5, target_ids = target_ids))

    if not beacon:
        print("ビーコンが見つかりませんでした")
    else:
        for b in beacon:
            status = judge_range(b, threshold = -50)
            print(f"検知: {b['id']} (RSSI = {b['rssi']}dBm) → {status}")