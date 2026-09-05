from flask import Flask, request, jsonify

from recommend import recommend

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/recommend", methods=["POST"])
def recommend_endpoint():
    data = request.get_json()

    if not data or "titles" not in data:
        return jsonify({"error": "Request body must include a 'titles' list."}), 400

    titles = data["titles"]

    if isinstance(titles, str):
        titles = [titles]

    top_n = data.get("top_n", 10)

    results = recommend(titles, top_n=top_n)

    if not results:
        return jsonify({
            "error": "None of the provided titles could be found or used.",
            "input_titles": titles
        }), 404

    return jsonify({
        "input_titles": titles,
        "recommendations": [
            {"title": title, "score": round(float(score), 3)}
            for title, score in results
        ]
    })


if __name__ == "__main__":
    app.run(debug=True)