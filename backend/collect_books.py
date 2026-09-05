import time

from openlibrary import search_book, get_work_details
from book import Book
from embeddings import generate_embedding
from database import get_connection, create_books_table, save_book, get_movie_count

REQUEST_DELAY_SECONDS = 0.3

# Small seed list — Open Library has no simple "popular books" endpoint like TMDb,
# so for now this is a manually curated starting list rather than an automated crawl.
SEED_TITLES = [
    "Norwegian Wood", "Kafka on the Shore", "The Great Gatsby",
    "Never Let Me Go", "The Bell Jar", "1984",
    "Slaughterhouse-Five", "The Catcher in the Rye", "Sputnik Sweetheart",
    "A Little Life", "The Remains of the Day", "Convenience Store Woman",
    "Klara and the Sun", "The Virgin Suicides", "White Noise",
    "Breakfast at Tiffany's", "On the Road", "The Perks of Being a Wallflower",
    "Eleanor Oliphant Is Completely Fine", "The Unbearable Lightness of Being"
]


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
    print(f"\nFinished. {saved_count} books saved out of {len(titles)} attempted.")


if __name__ == "__main__":
    collect_books()