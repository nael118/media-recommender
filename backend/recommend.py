import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from database import get_connection, add_liked_item, remove_liked_item, get_liked_items, create_liked_items_table
from embeddings import generate_embedding
from movie import Movie
from tmdb import search_movie, get_movie_keywords
from openlibrary import search_book, get_work_details
from book import Book

GENRE_BONUS = 0.05
MMR_LAMBDA = 0.7
MMR_CANDIDATE_POOL = 50


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

def build_embedding_for_liked_item(item_id, media_type, title):
    """
    Given a saved liked item, re-fetches it fresh and generates an embedding.
    (We don't store embeddings for liked_items directly, since re-fetching stays
    consistent with how movies/books are embedded elsewhere, and liked_items is
    a small list, so the extra API calls are cheap.)
    """
    if media_type == "movie":
        movie = build_movie_from_title(title)
        return generate_embedding(movie) if movie is not None else None

    elif media_type == "book":
        book, _ = build_book_from_title(title)
        return generate_embedding(book) if book is not None else None

    return None


def recommend_from_profile(top_n=10, media_types=("movies", "books"), diversity=MMR_LAMBDA):
    """
    Builds a taste vector from every item in the saved liked_items table,
    rather than requiring the caller to pass in titles fresh each time.
    """
    conn = get_connection()
    liked_items = get_liked_items(conn)
    conn.close()

    if not liked_items:
        print("Your taste profile is empty — like some movies or books first.")
        return []

    inputs_as_ids = {(item_id, media_type) for item_id, media_type, _ in liked_items}

    input_embeddings = []
    for item_id, media_type, title in liked_items:
        embedding = build_embedding_for_liked_item(item_id, media_type, title)
        if embedding is not None:
            input_embeddings.append(embedding)

    if not input_embeddings:
        print("None of your liked items could be re-fetched right now.")
        return []

    return _score_against_database(input_embeddings, inputs_as_ids, top_n, media_types, lambda_param=1 - diversity)

def recommend(inputs, top_n=10, media_types=("movies", "books"), diversity=MMR_LAMBDA):
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

    return _score_against_database(input_embeddings, input_ids, top_n, media_types, movie_input_tags, book_input_tags, lambda_param=1 - diversity)

def mmr_rerank(candidate_embeddings, candidate_scores, top_n, lambda_param=MMR_LAMBDA):
    """
    Re-ranks candidates to balance relevance against diversity.
    Returns a list of indices into candidate_embeddings/candidate_scores,
    in the order they should be presented.
    """
    num_candidates = len(candidate_scores)
    if num_candidates == 0:
        return []

    similarity_matrix = cosine_similarity(candidate_embeddings, candidate_embeddings)

    selected = []
    remaining = list(range(num_candidates))

    first_pick = max(remaining, key=lambda i: candidate_scores[i])
    selected.append(first_pick)
    remaining.remove(first_pick)

    while len(selected) < top_n and remaining:
        best_index = None
        best_mmr_score = None

        for i in remaining:
            max_similarity_to_selected = max(similarity_matrix[i][j] for j in selected)
            mmr_score = lambda_param * candidate_scores[i] - (1 - lambda_param) * max_similarity_to_selected

            if best_mmr_score is None or mmr_score > best_mmr_score:
                best_mmr_score = mmr_score
                best_index = i

        selected.append(best_index)
        remaining.remove(best_index)

    return selected

def _score_against_database(input_embeddings, input_ids, top_n, media_types, movie_input_tags=None, book_input_tags=None, lambda_param=MMR_LAMBDA):
    movie_input_tags = movie_input_tags or []
    book_input_tags = book_input_tags or []

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

    filtered_rows = [row for row in rows if (row[0], row[3]) not in input_ids and row[0] not in input_ids]

    stored_embeddings = np.array([json.loads(row[2]) for row in filtered_rows])

    similarity_matrix = cosine_similarity(input_embeddings, stored_embeddings)
    best_similarities = similarity_matrix.max(axis=0)

    scored_candidates = []

    for i, (item_id, item_title, embedding_json, media_type, tags_json) in enumerate(filtered_rows):
        score = best_similarities[i]
        candidate_tags = normalize_tags(json.loads(tags_json))

        if media_type == "movie" and movie_input_tags:
            best_overlap = max(len(candidate_tags & input_tags) / len(input_tags) for input_tags in movie_input_tags)
            score += GENRE_BONUS * best_overlap
        elif media_type == "book" and book_input_tags:
            best_overlap = max(len(candidate_tags & input_tags) / len(input_tags) for input_tags in book_input_tags)
            score += GENRE_BONUS * best_overlap

        scored_candidates.append((i, item_id, item_title, score, media_type))

    scored_candidates.sort(key=lambda x: x[3], reverse=True)

    pool_size = min(MMR_CANDIDATE_POOL, len(scored_candidates))
    pool = scored_candidates[:pool_size]

    pool_original_indices = [entry[0] for entry in pool]
    pool_embeddings = stored_embeddings[pool_original_indices]
    pool_scores = [entry[3] for entry in pool]

    mmr_order = mmr_rerank(pool_embeddings, pool_scores, top_n, lambda_param=lambda_param)

    results = [
        (pool[j][1], pool[j][2], pool[j][3], pool[j][4])
        for j in mmr_order
    ]

    return results

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
    for rank, (item_id, item_title, score, media_type) in enumerate(recommendations, start=1):
        print(f"{rank}. [{media_type}] {item_title} ({score:.2f})")