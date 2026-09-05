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


def build_taste_embedding(titles):
    """
    Takes a list of movie titles the user likes, builds a Movie for each,
    generates an embedding for each, and averages them into a single
    "taste vector" representing the overall vibe of all of them combined.

    Returns (taste_embedding, input_ids) where input_ids is the set of
    TMDb ids that were successfully used, so recommend() can exclude
    them from its own results.
    """
    embeddings = []
    input_ids = set()

    for title in titles:
        movie = build_movie_from_title(title)

        if movie is None:
            continue

        embeddings.append(generate_embedding(movie))
        input_ids.add(movie.tmdb_id)

    if not embeddings:
        return None, input_ids

    taste_embedding = np.mean(embeddings, axis=0)

    return taste_embedding, input_ids


def recommend(titles, top_n=10):
    """
    titles: a single title (str) or a list of titles.
    """
    if isinstance(titles, str):
        titles = [titles]

    input_embeddings = []
    input_ids = set()

    for title in titles:
        movie = build_movie_from_title(title)

        if movie is None:
            continue

        input_embeddings.append(generate_embedding(movie))
        input_ids.add(movie.tmdb_id)

    if not input_embeddings:
        print("None of the input movies could be found or used.")
        return []

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, embedding FROM movies")
    rows = cursor.fetchall()
    conn.close()

    results = []

    for movie_id, movie_title, embedding_json in rows:
        if movie_id in input_ids:
            continue

        stored_embedding = np.array(json.loads(embedding_json))

        best_similarity = max(
            cosine_similarity([input_embedding], [stored_embedding])[0][0]
            for input_embedding in input_embeddings
        )

        results.append((movie_title, best_similarity))

    results.sort(key=lambda x: x[1], reverse=True)

    return results[:top_n]


if __name__ == "__main__":
    raw_input = input("Enter one or more movies, separated by commas: ")
    titles = [title.strip() for title in raw_input.split(",")]

    recommendations = recommend(titles)

    print(f"\nTop {len(recommendations)} recommendations for {titles}:\n")
    for rank, (movie_title, score) in enumerate(recommendations, start=1):
        print(f"{rank}. {movie_title} ({score:.2f})")