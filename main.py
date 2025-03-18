from flask import Flask, request, jsonify, render_template
from chat import generate_response

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/per_game")
def per_game():
    return render_template("per_game.html")

@app.route("/general")
def general():
    return render_template("general.html")

@app.route("/comparison")
def comparison():
    return render_template("comparison.html")

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    user_query = request.json.get("query", "")
    answer = generate_response(user_query)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
