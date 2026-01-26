from flask import Flask, render_template
import requests
import json
import os

app = Flask(__name__)

STATUS_FILE = "../tag_status.json"

# ---------------------------------------------------------
# 新潟市の天気予報を取得する関数
# ---------------------------------------------------------
def get_weather():
    try:
        # 新潟県（150000）の予報を取得
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/150000.json"
        response = requests.get(url, timeout=3)
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

@app.route("/")
def home():
    current_weather = get_weather()
    
    tags_data = []
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                tags_data = json.load(f)
        except Exception as e:
            print(f"ファイル読み取りエラー: {e}")
    
    if not tags_data:
        tags_data = [
            {"name": "タグ 1", "status": "スキャン中...", "class": "out"},
            {"name": "タグ 2", "status": "スキャン中...", "class": "out"}
        ]
        
    return render_template("index.html", weather=current_weather, tags=tags_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)