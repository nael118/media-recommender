import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from database import get_connection
from embeddings import generate_embedding
from movie import Movie
from tmdb import search_movie, get_movie_keywords
from openlibrary import search_book, get_work_details
from book import Book


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

def build_book_from_title(title):
    results = search_book(title)

    if not results["docs"]:
        return None, None

    search_result = results["docs"][0]
    work_key = search_result["key"]

    work_details = get_work_details(work_key)

    book = Book.from_openlibrary_result(search_result, work_details)

    return book, work_key

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


def recommend(titles, top_n=10, media_types=("movies", "books")):
    """
    titles: a single title (str) or a list of titles.
    media_types: which tables to search across, e.g. ("movies",) or ("movies", "books").
    """
    if isinstance(titles, str):
        titles = [titles]

    input_embeddings = []
    input_ids = set()

    for title in titles:
        movie = build_movie_from_title(title)

        if movie is not None:
            input_embeddings.append(generate_embedding(movie))
            input_ids.add(movie.tmdb_id)
            continue

        book, work_key = build_book_from_title(title)

        if book is not None:
            input_embeddings.append(generate_embedding(book))
            input_ids.add(work_key)
            continue

        print(f"'{title}' could not be found as a movie or a book.")

    if not input_embeddings:
        print("None of the input titles could be found or used.")
        return []

    print("DEBUG input_ids:", input_ids)

    conn = get_connection()
    cursor = conn.cursor()

    rows = []

    if "movies" in media_types:
        cursor.execute("SELECT id, title, embedding FROM movies")
        rows += [(movie_id, title, embedding_json, "movie") for movie_id, title, embedding_json in cursor.fetchall()]

    if "books" in media_types:
        cursor.execute("SELECT id, title, embedding FROM books")
        rows += [(book_id, title, embedding_json, "book") for book_id, title, embedding_json in cursor.fetchall()]

    conn.close()

    results = []

    for item_id, item_title, embedding_json, media_type in rows:
        if item_id in input_ids:
            continue

        stored_embedding = np.array(json.loads(embedding_json))

        best_similarity = max(
            cosine_similarity([input_embedding], [stored_embedding])[0][0]
            for input_embedding in input_embeddings
        )

        results.append((item_title, best_similarity, media_type))

    results.sort(key=lambda x: x[1], reverse=True)

    return results[:top_n]


if __name__ == "__main__":
    raw_input = input("Enter one or more movies or books, separated by commas: ")
    titles = [title.strip() for title in raw_input.split(",")]

    recommendations = recommend(titles)

    print(f"\nTop {len(recommendations)} recommendations for {titles}:\n")
    for rank, (item_title, score, media_type) in enumerate(recommendations, start=1):
        print(f"{rank}. [{media_type}] {item_title} ({score:.2f})")