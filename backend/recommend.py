import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from database import get_connection
from embeddings import generate_embedding
from movie import Movie
from tmdb import search_movie, get_movie_keywords


def build_movie_from_title(title):
    results = search_movie(title)

    if not results["results"]:
        print(f"{title} not found.")
        return None

    movie_data = results["results"][0]
    keywords_data = get_movie_keywords(movie_data["id"])

    movie = Movie.from_tmdb_result(movie_data, keywords_data)

    if movie is None:
        print(f"{title} found, but doesn't have enough data yet (unreleased or too few ratings).")

    return movie


def recommend(title, top_n=10):
    input_movie = build_movie_from_title(title)

    if input_movie is None:
        return []

    input_embedding = generate_embedding(input_movie)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, embedding FROM movies")
    rows = cursor.fetchall()
    conn.close()

    results = []

    for movie_id, movie_title, embedding_json in rows:
        if movie_id == input_movie.tmdb_id:
            continue

        stored_embedding = np.array(json.loads(embedding_json))

        similarity = cosine_similarity(
            [input_embedding],
            [stored_embedding]
        )[0][0]

        results.append((movie_title, similarity))

    results.sort(key=lambda x: x[1], reverse=True)

    return results[:top_n]


if __name__ == "__main__":
    title = input("Enter a movie: ")
    recommendations = recommend(title)

    print(f"\nTop {len(recommendations)} recommendations for '{title}':\n")
    for rank, (movie_title, score) in enumerate(recommendations, start=1):
        print(f"{rank}. {movie_title} ({score:.2f})")