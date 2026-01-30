from flask import Flask, render_template
import requests
import json
import os
import random
import time 

app = Flask(__name__)

# --- 絶対パス設定（systemd対応） --- 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.join(BASE_DIR, "..", "tag_status.json")

# ---------------------------------------------------------
# グラフを表示する
# ---------------------------------------------------------

@app.route("/log_graph")
def log_graph():
    # ダミーデータ（後で本物のログに差し替え可能）
    dummy_labels = ["月", "火", "水", "木", "金"]
    dummy_values = [1, 0, 2, 1, 0]

    return render_template(
        "log_graph.html",
        labels=dummy_labels,
        values=dummy_values
    )

# ---------------------------------------------------------
# 新潟市の天気予報を取得する関数
# ---------------------------------------------------------
def get_weather():
    try:
        # 新潟県（150000）の予報を取得
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/150000.json"
        response = requests.get(url, timeout=1)
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
        
    tags_data = []
    is_finished = False  # デフォルトは False
    omikuji_result = ''  #おみくじを初期化

    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                full_data = json.load(f) # 全体（時刻＋タグ）を読み込む
                
                #フラグ類の読み込み
                is_finished = full_data.get("is_finished", False) # 終了フラグを読み取る
                
                # --- おみくじの維持ロジック ---
                # jsonの中にすでにおみくじの結果があればそれを使う
                if "omikuji" in full_data:
                    omikuji_result = full_data["omikuji"]
                else:
                    # なければ新しく引いて、変数に入れる（保存は後述）
                    omikuji_result = get_omikuji()
                # ----------------------------

                
                # 正常ならタグのリストを取り出す
                tags_data = full_data.get("tags", [])

                    
        except Exception as e:
            print(f"ファイル読み取りエラー: {e}")
        
    # もし omikuji_result が空なら（ファイルがない場合など）引く
    if not omikuji_result:
        omikuji_result = get_omikuji()        

    return render_template("index.html", weather=current_weather, tags=tags_data, 
                           omikuji=omikuji_result, is_finished=is_finished)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)