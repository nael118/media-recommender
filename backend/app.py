from flask import Flask, request, jsonify

from flask import Flask, request, jsonify, send_from_directory

from recommend import recommend
from database import get_connection, add_liked_item, remove_liked_item, get_liked_items, create_liked_items_table
from recommend import recommend_from_profile

app = Flask(__name__)

_startup_conn = get_connection()
create_liked_items_table(_startup_conn)
_startup_conn.close()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/")
def index():
    return send_from_directory("static", "index.html")
@app.route("/like", methods=["POST"])
def like_item():
    data = request.get_json()

    if not data or "id" not in data or "media_type" not in data or "title" not in data:
        return jsonify({"error": "Request must include 'id', 'media_type', and 'title'."}), 400

    conn = get_connection()
    add_liked_item(conn, data["id"], data["media_type"], data["title"])
    conn.close()

    return jsonify({"status": "added", "title": data["title"]})


@app.route("/like", methods=["DELETE"])
def unlike_item():
    data = request.get_json()

    if not data or "id" not in data or "media_type" not in data:
        return jsonify({"error": "Request must include 'id' and 'media_type'."}), 400

    conn = get_connection()
    remove_liked_item(conn, data["id"], data["media_type"])
    conn.close()

    return jsonify({"status": "removed"})


@app.route("/profile", methods=["GET"])
def get_profile():
    conn = get_connection()
    liked_items = get_liked_items(conn)
    conn.close()

    return jsonify({
        "liked_items": [
            {"id": item_id, "media_type": media_type, "title": title}
            for item_id, media_type, title in liked_items
        ]
    })


@app.route("/recommend/profile", methods=["GET"])
def recommend_from_profile_endpoint():
    top_n = request.args.get("top_n", default=10, type=int)

    results = recommend_from_profile(top_n=top_n)

    if not results:
        return jsonify({"error": "Your taste profile is empty, or none of your liked items could be re-fetched."}), 404

    return jsonify({
        "recommendations": [
            {"id": item_id, "title": title, "score": round(float(score), 3), "media_type": media_type}
            for item_id, title, score, media_type in results
        ]
    })

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
            {"id": item_id, "title": title, "score": round(float(score), 3), "media_type": media_type}
            for item_id, title, score, media_type in results
        ]
    })


if __name__ == "__main__":
    app.run(debug=True)