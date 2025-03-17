from flask import Flask, request, jsonify, render_template
from chat import generate_response

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    user_query = request.json.get("query", "")
    answer = generate_response(user_query)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
