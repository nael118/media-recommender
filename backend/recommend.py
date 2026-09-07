import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from database import get_connection
from embeddings import generate_embedding
from movie import Movie
from tmdb import search_movie, get_movie_keywords
from openlibrary import search_book, get_work_details
from book import Book

GENRE_BONUS = 0.05


def normalize_tags(tags):
    return set(tag.lower() for tag in tags)


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


def recommend(inputs, top_n=10, media_types=("movies", "books")):
    """
    inputs: a single (title, media_type) tuple, or a list of them.
    media_type must be "movie" or "book".
    media_types: which tables to search across for recommendations, e.g. ("movies",) or ("movies", "books").
    """
    if isinstance(inputs, tuple):
        inputs = [inputs]

    input_embeddings = []
    input_ids = set()
    movie_input_tags = []
    book_input_tags = []

    for title, media_type in inputs:
        if media_type == "movie":
            movie = build_movie_from_title(title)

            if movie is not None:
                input_embeddings.append(generate_embedding(movie))
                input_ids.add(movie.tmdb_id)
                movie_input_tags.append(normalize_tags(movie.genres))
            else:
                print(f"'{title}' could not be found as a movie.")

        elif media_type == "book":
            book, work_key = build_book_from_title(title)

            if book is not None:
                input_embeddings.append(generate_embedding(book))
                input_ids.add(work_key)
                book_input_tags.append(normalize_tags(book.subjects))
            else:
                print(f"'{title}' could not be found as a book.")

        else:
            print(f"Unknown media type '{media_type}' for '{title}'. Use 'movie' or 'book'.")

    if not input_embeddings:
        print("None of the input titles could be found or used.")
        return []

    conn = get_connection()
    cursor = conn.cursor()

    rows = []

    if "movies" in media_types:
        cursor.execute("SELECT id, title, embedding, genres FROM movies")
        rows += [(movie_id, title, embedding_json, "movie", tags_json) for movie_id, title, embedding_json, tags_json in cursor.fetchall()]

    if "books" in media_types:
        cursor.execute("SELECT id, title, embedding, subjects FROM books")
        rows += [(book_id, title, embedding_json, "book", tags_json) for book_id, title, embedding_json, tags_json in cursor.fetchall()]

    conn.close()

    filtered_rows = [row for row in rows if row[0] not in input_ids]

    stored_embeddings = np.array([json.loads(row[2]) for row in filtered_rows])

    similarity_matrix = cosine_similarity(input_embeddings, stored_embeddings)
    best_similarities = similarity_matrix.max(axis=0)

    results = []

    for i, (item_id, item_title, embedding_json, media_type, tags_json) in enumerate(filtered_rows):
        score = best_similarities[i]
        candidate_tags = normalize_tags(json.loads(tags_json))

        if media_type == "movie" and any(candidate_tags & input_tags for input_tags in movie_input_tags):
            score += GENRE_BONUS
        elif media_type == "book" and any(candidate_tags & input_tags for input_tags in book_input_tags):
            score += GENRE_BONUS

        results.append((item_title, score, media_type))

    results.sort(key=lambda x: x[1], reverse=True)

    return results[:top_n]


if __name__ == "__main__":
    print("For each title, specify its type as 'movie' or 'book'.")
    print("Example: Her:movie, Norwegian Wood:book")

    raw_input = input("Enter one or more titles: ")

    inputs = []
    for entry in raw_input.split(","):
        entry = entry.strip()
        if ":" not in entry:
            print(f"Skipping '{entry}' — missing ':movie' or ':book' tag.")
            continue
        title, media_type = entry.rsplit(":", 1)
        inputs.append((title.strip(), media_type.strip().lower()))

    recommendations = recommend(inputs)

    print(f"\nTop {len(recommendations)} recommendations for {inputs}:\n")
    for rank, (item_title, score, media_type) in enumerate(recommendations, start=1):
        print(f"{rank}. [{media_type}] {item_title} ({score:.2f})")