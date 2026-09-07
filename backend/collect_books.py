import time
import requests

from openlibrary import search_book, get_work_details, get_subject_works
from book import Book
from embeddings import generate_embedding
from database import get_connection, create_books_table, save_book


REQUEST_DELAY_SECONDS = 1.0

SEED_TITLES = [
    "Norwegian Wood", "Kafka on the Shore", "The Great Gatsby",
    "Never Let Me Go", "The Bell Jar", "1984",
    "Slaughterhouse-Five", "The Catcher in the Rye", "Sputnik Sweetheart",
    "A Little Life", "The Remains of the Day", "Convenience Store Woman",
    "Klara and the Sun", "The Virgin Suicides", "White Noise",
    "Breakfast at Tiffany's", "On the Road", "The Perks of Being a Wallflower",
    "Eleanor Oliphant Is Completely Fine", "The Unbearable Lightness of Being"
]

SUBJECTS = [
    "literary_fiction", "science_fiction", "fantasy",
    "mystery", "romance", "young_adult_fiction",
    "historical_fiction", "horror"
]


def _subject_work_to_search_result(work):
    author_names = [author["name"] for author in work.get("authors", [])] or ["Unknown"]

    return {
        "title": work.get("title", "Unknown"),
        "author_name": author_names,
        "first_publish_year": work.get("first_publish_year", "Unknown"),
        "key": work["key"]
    }


def collect_books(titles=SEED_TITLES):
    conn = get_connection()
    create_books_table(conn)

    saved_count = 0

    for title in titles:
        results = search_book(title)
        time.sleep(REQUEST_DELAY_SECONDS)

        if not results["docs"]:
            print(f"'{title}' not found, skipping.")
            continue

        search_result = results["docs"][0]
        work_key = search_result["key"]

        work_details = get_work_details(work_key)
        time.sleep(REQUEST_DELAY_SECONDS)

        book = Book.from_openlibrary_result(search_result, work_details)

        if book is None:
            print(f"'{title}' found, but data too thin, skipping.")
            continue

        embedding = generate_embedding(book)
        save_book(conn, work_key, book, embedding)
        saved_count += 1
        print(f"Saved: {book.title} ({saved_count}/{len(titles)})")

    conn.close()
    print(f"\nFinished seed collection. {saved_count} books saved out of {len(titles)} attempted.")


def collect_books_by_subject(subjects=SUBJECTS, limit_per_subject=30):
    conn = get_connection()
    create_books_table(conn)

    saved_count = 0

    for subject in subjects:
        try:
            data = get_subject_works(subject, limit=limit_per_subject)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            print(f"[{subject}] skipped entirely — Open Library would not respond.")
            continue

        works = data.get("works", [])

        for work in works:
            search_result = _subject_work_to_search_result(work)
            work_key = search_result["key"]

            try:
                work_details = get_work_details(work_key)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                print(f"  Skipping {work_key} — Open Library would not respond after retries.")
                continue

            time.sleep(REQUEST_DELAY_SECONDS)

            book = Book.from_openlibrary_result(search_result, work_details)

            if book is None:
                continue

            embedding = generate_embedding(book)
            save_book(conn, work_key, book, embedding)
            saved_count += 1

        print(f"[{subject}] done — {saved_count} total valid books saved so far.")

    conn.close()
    print(f"\nFinished subject collection. {saved_count} books saved this run.")


if __name__ == "__main__":
    collect_books_by_subject()