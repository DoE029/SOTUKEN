from flask import Flask, render_template
import requests
import json
import os
import random
import time
import ast
from collections import Counter

app = Flask(__name__)

# --- 絶対パス設定（systemd対応） --- 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.join(BASE_DIR, "..", "tag_status.json")
LOG_FILE = os.path.join(BASE_DIR, "..", "beacon_log.txt")   # ← ログファイルの場所を追加


# ---------------------------------------------------------
# グラフを表示する（本物のログを使用）
# ---------------------------------------------------------

@app.route("/log_graph")
def log_graph():

    # MACアドレス → 表示名（Run.py と合わせる）
    TAG_NAMES = {
        "DC:0D:30:16:87:F1": "タグ 2",
        "DC:0D:30:16:88:8B": "タグ 1"
    }

    items = []  # グラフ用に名前だけを集めるリスト

    # beacon_log.txt を読み込む
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                # 「全検知:」が含まれている行だけ処理
                if "全検知:" not in line:
                    continue

                # "全検知: [...]" の部分を取り出す
                detected_str = line.split("全検知:")[1].strip()

                try:
                    # Python のリスト形式に変換
                    detected_list = ast.literal_eval(detected_str)
                except:
                    continue

                # 各タグを処理
                for tag in detected_list:
                    mac = tag.get("id")
                    if mac in TAG_NAMES:
                        items.append(TAG_NAMES[mac])

    # 集計（Counter を使って回数を数える）
    counter = Counter(items)

    labels = list(counter.keys())     # ["タグ1", "タグ2", ...]
    values = list(counter.values())   # [12, 8, ...]

    # 上位5件のランキング
    ranking = counter.most_common(5)

    return render_template(
        "graph.html",
        labels=labels,
        values=values,
        ranking=ranking
    )


# ---------------------------------------------------------
# 新潟市の天気予報を取得する関数
# ---------------------------------------------------------
def get_weather():
    try:
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/150000.json"
        response = requests.get(url, timeout=1)
        data = response.json()

        weather_text = data[0]['timeSeries'][0]['areas'][0]['weathers'][0]
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
    weights = [5, 15, 20, 20, 40, 30, 10]
    selection = random.choices(results, weights=weights, k=1)
    return selection[0]


# ---------------------------------------------------------
# ホーム画面（天気・タグ状態・おみくじ）
# ---------------------------------------------------------
@app.route("/")
def home():
    current_weather = get_weather()

    tags_data = []
    is_finished = False
    omikuji_result = ''

    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                full_data = json.load(f)

                is_finished = full_data.get("is_finished", False)

                # おみくじの維持
                if "omikuji" in full_data:
                    omikuji_result = full_data["omikuji"]
                else:
                    omikuji_result = get_omikuji()

                tags_data = full_data.get("tags", [])

        except Exception as e:
            print(f"ファイル読み取りエラー: {e}")

    if not omikuji_result:
        omikuji_result = get_omikuji()

    return render_template(
        "index.html",
        weather=current_weather,
        tags=tags_data,
        omikuji=omikuji_result,
        is_finished=is_finished
    )


# ---------------------------------------------------------
# Flask 起動
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
