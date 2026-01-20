# Flask を使った Web アプリの基本コード

from flask import Flask, render_template

# Flask アプリ本体を作成
# __name__ は「このファイルが実行されている場所」を Flask に教えるためのもの
app = Flask(__name__)

# -------------------------------
# ルートURL（"/"）にアクセスしたときの処理
# -------------------------------
@app.route("/")
def home():
    # templates/index.html を表示する
    return render_template("index.html")

# -------------------------------
# Flask アプリを起動する部分
# -------------------------------
if __name__ == "__main__":
    # host="0.0.0.0" → 他の端末（スマホやPC）からもアクセス可能
    # port=5000 → Webアプリのポート番号
    # debug=True → コードを変更すると自動で再起動してくれる（開発中に便利）
    app.run(host="0.0.0.0", port=5000, debug=True)
