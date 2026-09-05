from openlibrary import search_book, get_work_details
from book import Book
from embeddings import generate_embedding
from database import get_connection
from sklearn.metrics.pairwise import cosine_similarity
import json
import numpy as np


def build_book_from_title(title):
    results = search_book(title)

    if not results["docs"]:
        print(f"{title} not found.")
        return None

    search_result = results["docs"][0]
    work_key = search_result["key"]

    work_details = get_work_details(work_key)

    return Book.from_openlibrary_result(search_result, work_details)


def compare_book_to_stored_movies(book_title, top_n=5):
    book = build_book_from_title(book_title)

    if book is None:
        print(f"Could not build a usable profile for '{book_title}'.")
        return

    book.display()

    book_embedding = generate_embedding(book)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT title, embedding FROM movies")
    rows = cursor.fetchall()
    conn.close()

    results = []
    for movie_title, embedding_json in rows:
        movie_embedding = np.array(json.loads(embedding_json))
        similarity = cosine_similarity([book_embedding], [movie_embedding])[0][0]
        results.append((movie_title, similarity))

    results.sort(key=lambda x: x[1], reverse=True)

    print(f"\nTop {top_n} movies closest to '{book_title}':\n")
    for rank, (movie_title, score) in enumerate(results[:top_n], start=1):
        print(f"{rank}. {movie_title} ({score:.2f})")


if __name__ == "__main__":
    title = input("Enter a book: ")
    compare_book_to_stored_movies(title)