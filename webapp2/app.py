from flask import Flask, render_template
import requests
import json
import os
import random
import time 

app = Flask(__name__)

STATUS_FILE = "../tag_status.json"

# ---------------------------------------------------------
# 新潟市の天気予報を取得する関数
# ---------------------------------------------------------
def get_weather():
    try:
        # 新潟県（150000）の予報を取得
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/150000.json"
        response = requests.get(url, timeout=2)
        data = response.json()
        
        # 新潟県下越地方（新潟市含む）の天気情報を抽出
        # data[0]は直近の予報、areas[0]が下越地方です
        weather_text = data[0]['timeSeries'][0]['areas'][0]['weathers'][0]
        
        # 「曇り　時々　雨」などを「曇り」にスッキリさせる
        weather_simple = weather_text.split('　')[0] 
        return weather_simple
    except Exception as e:
        print(f"天気取得エラー: {e}")
        return "取得エラー"
    
# ---------------------------------------------------------
# おみくじの結果を決める関数[重み付け]
# ---------------------------------------------------------
def get_omikuji():
    results = ["大吉", "中吉", "小吉", "吉", "末吉", "凶", "大凶"]
    # それぞれの出る確率（重み）を設定
    weights = [5, 15, 20, 20, 40, 30 ,10]   #重み付け

    # 設定した確率に基づいて1つ選ぶ
    selection = random.choices(results, weights=weights, k=1)
    return selection[0]


@app.route("/")
def home():
    current_weather = get_weather() #天気の表示
    omikuji_result = get_omikuji() #おみくじを引く
    
    tags_data = []
    refresh_interval = 2  # デフォルト（スキャン中）は2秒

    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                full_data = json.load(f) # 全体（時刻＋タグ）を読み込む
                
                # 時刻チェック（15秒以上更新がなければ「停止中」にする）
                last_update = full_data.get("last_update", 0)
                is_finished = full_data.get("is_finished", False) # 終了フラグを読み取る
                # 「15秒以上更新なし」かつ「正常終了フラグが立っていない」場合のみ通信切断
                if (time.time() - last_update > 15) and not is_finished:
                    tags_data = [
                        {"name": t["name"], "status": "通信切断", "class": "out"} 
                        for t in full_data.get("tags", [])
                    ]
                else:
                    # 正常ならタグのリストを取り出す
                    tags_data = full_data.get("tags", [])

                    # 全て揃って終了フラグがTrueなら、更新間隔を60秒にする
                    if is_finished:
                        refresh_interval = 60
                    else:
                        refresh_interval = 2 # まだ揃っていないなら2秒
                    
        except Exception as e:
            print(f"ファイル読み取りエラー: {e}")
        

    return render_template("index.html", weather=current_weather, tags=tags_data, 
                           omikuji=omikuji_result, interval=refresh_interval)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)