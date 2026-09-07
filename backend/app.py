from flask import Flask, request, jsonify

from flask import Flask, request, jsonify, send_from_directory

from recommend import recommend

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/recommend", methods=["POST"])
def recommend_endpoint():
    data = request.get_json()

    if not data or "titles" not in data:
        return jsonify({"error": "Request body must include a 'titles' list."}), 400

    titles = data["titles"]

    if not isinstance(titles, list):
        return jsonify({"error": "'titles' must be a list of {title, media_type} objects."}), 400

    try:
        inputs = [(item["title"], item["media_type"]) for item in titles]
    except (KeyError, TypeError):
        return jsonify({"error": "Each item in 'titles' must have 'title' and 'media_type' fields."}), 400

    top_n = data.get("top_n", 10)

    results = recommend(inputs, top_n=top_n)

    if not results:
        return jsonify({
            "error": "None of the provided titles could be found or used.",
            "input_titles": titles
        }), 404

    return jsonify({
        "input_titles": titles,
        "recommendations": [
            {"title": title, "score": round(float(score), 3), "media_type": media_type}
            for title, score, media_type in results
        ]
    })


if __name__ == "__main__":
    app.run(debug=True)