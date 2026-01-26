from flask import Flask, render_template
import requests

app = Flask(__name__)

def get_weather():
    try:
        # 気象庁のAPI（例として東京都: 130000）から取得
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/130000.json"
        response = requests.get(url)
        data = response.json()
        
        # 最初の予報エリアの情報を抽出
        weather_text = data[0]['timeSeries'][0]['areas'][0]['weathers'][0]
        # 簡略化（長すぎる場合があるため）
        weather_simple = weather_text.split('　')[0] 
        return weather_simple
    except:
        return "取得エラー"

@app.route("/")
def home():
    weather = get_weather()
    # 天気情報を index.html に渡す
    return render_template("index.html", weather=weather)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)