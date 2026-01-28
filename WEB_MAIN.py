import asyncio
import datetime
import json
import os
from BLE_New_beacon import scan_beacon  
import LED_New_Buzzer as gpio       
import time  
import os   

# ----------------- 設定 --------------------

START_TIME = "9:15"   # チェック開始時刻（この時間になるまで待機）
END_TIME   = "15:00"  # チェック終了時刻（この時間を過ぎたら終了）

RSSI_THRESHOLD = -84  # タグの検知とみなすRSSIのしきい値
LOG_FILE = "beacon_log.txt"        # スキャン結果のログ保存先
STATS_FILE = "forget_stats.json"   # 忘れ物統計データの保存先
STATUS_FILE = "tag_status.json"    # Webアプリ連携用ファイル
CONFIG_FILE = "config.json"        # webアプリ側で設定したSTART_TIMEとEND_TIMEの読み込み

# MACアドレスと表示名の対応表（ログや表示用）
ID_MAP = {"DC:0D:30:16:88:8B": "タグ 1",
          "DC:0D:30:16:87:F1": "タグ 2"}

# 最新のスキャン結果を保持するための変数
latest_beacons = None

# ---------------------------------------------------------
# Webアプリ用に現在の状態を保存する関数
# ---------------------------------------------------------
def save_status_for_web(beacons, target_ids, is_finished=False):
    """Webアプリが読み取れるように現在の状態をJSONで保存する"""
    status_data = []
    
    # しきい値以上で検知できているタグのIDリスト（大文字統一）
    found_ids_near = [
        b["id"].upper() for b in beacons
        if b.get("rssi") is not None and b["rssi"] >= RSSI_THRESHOLD
    ]

    for t_id in target_ids:
        t_id_upper = t_id.upper()
        name = ID_MAP.get(t_id_upper, t_id_upper)
        
        # 検知状態の判定
        is_near = t_id_upper in found_ids_near
        status_data.append({
            "name": name,
            "status": "検知" if is_near else "未検知",
            "class": "in" if is_near else "out"
        })

    # status_dataに時刻を追加
    # 終了フラグを追加
    status_payload = {
        "last_update": time.time(), # 現在時刻を記録
        "is_finished": is_finished,  # 終了フラグ
        "tags": status_data  #タグのリスト
    }

    # ファイルに書き出し（Flask側が読み取れるように）
    # 安全にファイルに書き出す（一時ファイル経由）
    temp_file = STATUS_FILE + ".tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            # status_data 単体ではなく、時刻入りの status_payload を保存する
            json.dump(status_payload, f, indent=4, ensure_ascii=False)
        
        # 書き込みが終わったら一瞬で本番ファイルに置き換える
        os.replace(temp_file, STATUS_FILE)
    except Exception as e:
        print(f"ステータス保存エラー: {e}")

# ---------------------------------------------------------
# 忘れ物統計データを記録する関数
# ---------------------------------------------------------
def record_stats(missing_names):
    """不足していたタグの名前を統計ファイルに記録する"""

    stats = {}

    # 既存の統計ファイルがあれば読み込む
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                stats = json.load(f)
        except:
            stats = {}

    # 不足していたタグのカウントを増やす
    for name in missing_names:
        stats[name] = stats.get(name, 0) + 1

    # 上書き保存
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)

# ---------------------------------------------------------
# 現在時刻が指定した時間帯に入っているか判定
# ---------------------------------------------------------
def in_time_range(start_str, end_str):
    """現在時刻が START_TIME〜END_TIME の間かどうかを返す"""

    now = datetime.datetime.now().time()  # 現在時刻（時刻のみ）
    start = datetime.datetime.strptime(start_str, "%H:%M").time()
    end = datetime.datetime.strptime(end_str, "%H:%M").time()

    return start <= now <= end

# ---------------------------------------------------------
# スキャン結果を表示・ログ保存・LED更新する関数
# ---------------------------------------------------------
def update_and_log(beacons, target_ids):

    global latest_beacons
    latest_beacons = beacons  # 最新のスキャン結果を保存

    print(f"--- 現在の状況 (しきい値: {RSSI_THRESHOLD}dBm) ---")

    # Webアプリ用のデータを更新（スキャン中なので is_finished=False）
    save_status_for_web(beacons, target_ids, is_finished=False)

    # 取得したタグごとに状態を表示
    for b in beacons:
        raw_id = b['id'].upper()
        display_name = ID_MAP.get(raw_id, raw_id)

        rssi_val = b.get("rssi")
        rssi_display = f"{rssi_val}dBm" if rssi_val is not None else "取得不可"

        status = "OK" if rssi_val is not None and rssi_val >= RSSI_THRESHOLD else "遠い/未検知"

        print(f"番号: {display_name} | RSSI: {rssi_display} | 状態: {status}")

    # しきい値以上で検知できているタグ一覧
    found_ids_near = [
        b["id"].upper() for b in beacons
        if b.get("rssi") is not None and b["rssi"] >= RSSI_THRESHOLD
    ]

    # ログに保存
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | 全検知: {beacons}\n")

    # LEDの状態を更新
    gpio.update_status(beacons, target_ids, RSSI_THRESHOLD)

    # 全て揃っているか判定
    all_found = all(t.upper() in found_ids_near for t in target_ids)

    if all_found:
        print("全て近くにあります。忘れ物なし")
    else:
        # 不足しているタグ名を抽出
        missing_names = [
            ID_MAP.get(t.upper(), t)
            for t in target_ids
            if t.upper() not in found_ids_near
        ]
        print(f"不足中: {missing_names}")

        # 統計データに記録
        record_stats(missing_names)

    return all_found


# ---------------------------------------------------------
# 不足がある間、1秒ごとにブザーを鳴らすタスク
# ---------------------------------------------------------
async def buzzer_task(target_ids):

    while True:
        current_beacons = latest_beacons if latest_beacons is not None else []

        # しきい値以上で検知できているタグ一覧
        found_ids_near = [
            b["id"].upper() for b in current_beacons
            if b.get("rssi") is not None and b["rssi"] >= RSSI_THRESHOLD
        ]

        # 不足があればブザーを鳴らす
        if not all(t.upper() in found_ids_near for t in target_ids):
            gpio.buzzer_warning()

        try:
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            break


# ---------------------------------------------------------
# メインループ（時間帯まで待機 → チェック開始 → 終了）
# ---------------------------------------------------------
async def main_loop(target_ids):

    print(f"{START_TIME} 〜 {END_TIME} の間だけチェックを行います")

    save_status_for_web([], target_ids, is_finished=False) # 終了フラグをfalseにする
    print("終了フラグをリセットしました。")

    # 時間帯に入るまで待機（ここが「朝起動して時間まで待つ」部分）
    while not in_time_range(START_TIME, END_TIME):
        await asyncio.sleep(10)

    print("チェック時間帯に入りました。スキャンを開始します")

    gpio.setup_gpio()  # LED・ブザーのGPIO初期化
    
    # 不足がある間ブザーを鳴らすタスクを開始
    buzzer_handle = asyncio.create_task(buzzer_task(target_ids))

    try:
        # 時間帯の間だけスキャンを繰り返す
        while in_time_range(START_TIME, END_TIME):

            try:
                # BLEタグをスキャン
                beacons = await scan_beacon(timeout=3, target_ids=target_ids)
            except Exception as e:
                print(f"スキャンエラー: {e}")
                beacons = []

            # スキャン結果があれば処理
            if beacons:
                all_found = update_and_log(beacons, target_ids)
            else:
                # 何も見つからなかった場合
                now_str = datetime.datetime.now().strftime('%H:%M:%S')
                print(f"{now_str} 持ち物が見つかりません (範囲外)")

                latest_beacons = []
                # ここでも False を送って「プログラムは生きてるよ」と伝える
                # !!!! save_status_for_web([], target_ids, is_finished=False)
                gpio.update_status([], target_ids, RSSI_THRESHOLD)
                all_found = False

            # 全部揃ったら終了
            if all_found:
                print("全部揃いました")
                #終了フラグを保存
                save_status_for_web(beacons, target_ids, is_finished=True)

                if buzzer_handle:
                    buzzer_handle.cancel()

                try:
                    gpio.set_all_blue_leds(True)  # 青LEDを点灯
                    await asyncio.sleep(10)
                except AttributeError:
                    pass

                break

            await asyncio.sleep(3)  # 次のスキャンまで待機

    except KeyboardInterrupt:
        print("手動終了")

    finally:
        # ブザータスクが残っていたら停止
        if buzzer_handle and not buzzer_handle.done():
            buzzer_handle.cancel()

        gpio.cleanup_gpio()
        print("チェック時間帯を終了しました")


# ---------------------------------------------------------
# webアプリ側で入力した時間帯を確認するコード
# ---------------------------------------------------------
def get_current_config():
    """Webアプリが保存したconfig.jsonから時刻を読み込む"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    # ファイルがない、または読み込めない場合のデフォルト値
    return {"start_time": "09:15", "end_time": "15:00"}

async def main_loop(target_ids):
    print("システムを開始しました。")
    
    while True:
        # 1. ループのたびに最新の設定を読み込む
        config = get_current_config()
        st = config["start_time"]
        et = config["end_time"]

        # 2. 時間外の場合は待機
        if not in_time_range(st, et):
            # まだ時間前、または終了後の場合は、終了フラグをFalseにして待機
            save_status_for_web([], target_ids, is_finished=False)
            print(f"現在、待機時間中です。次の開始予定: {st}")
            await asyncio.sleep(60)  # 1分待機して再度時刻をチェック
            continue

        # 3. 【ここから時間内の処理】
        print(f"チェック時間帯 ({st}〜{et}) に入りました。スキャンを開始します。")
        gpio.setup_gpio()
        
        # 終了フラグをリセット
        save_status_for_web([], target_ids, is_finished=False)
        
        # ブザータスク開始
        buzzer_handle = asyncio.create_task(buzzer_task(target_ids))

        try:
            # 時間内である限りスキャンを続ける
            while in_time_range(st, et):
                # 念のため、スキャン中も設定が更新されたか確認
                config = get_current_config()
                st = config["start_time"]
                et = config["end_time"]

                try:
                    beacons = await scan_beacon(timeout=3, target_ids=target_ids)
                except Exception as e:
                    print(f"スキャンエラー: {e}")
                    beacons = []

                if beacons:
                    all_found = update_and_log(beacons, target_ids)
                else:
                    print(f"{datetime.datetime.now().strftime('%H:%M:%S')} 範囲外")
                    save_status_for_web([], target_ids, is_finished=False)
                    gpio.update_status([], target_ids, RSSI_THRESHOLD)
                    all_found = False

                if all_found:
                    print("全部揃いました。正常終了します。")
                    save_status_for_web(beacons, target_ids, is_finished=True)
                    # ブザー停止とLED点灯
                    if buzzer_handle: buzzer_handle.cancel()
                    gpio.set_all_blue_leds(True)
                    
                    # 全部揃った後は、次の開始時刻まで待機モードへ
                    # ここで「内側のwhile」を抜けて「外側のwhile」の待機に戻る
                    await asyncio.sleep(10) # 青LEDを見せる時間
                    break # while in_time_range を抜ける

                await asyncio.sleep(3) # スキャン間隔

        except KeyboardInterrupt:
            print("手動終了")
            break
        finally:
            if buzzer_handle and not buzzer_handle.done():
                buzzer_handle.cancel()
            gpio.cleanup_gpio()
            print("スキャンセッションを終了しました。次の開始時刻まで待機します。")
            
            # 全部揃って抜けた場合は、次の時間まで長めに待機
            # そうしないと、まだ時間内の場合すぐにまたスキャンが始まってしまうため
            await asyncio.sleep(60)



# ---------------------------------------------------------
# プログラムのエントリーポイント
# ---------------------------------------------------------
if __name__ == "__main__":
    # チェック対象のタグ（MACアドレス）
    targets = ["DC:0D:30:16:88:8B", "DC:0D:30:16:87:F1"]

    # メインループ開始
    asyncio.run(main_loop(targets))
