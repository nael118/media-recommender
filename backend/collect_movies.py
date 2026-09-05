import time

from tmdb import get_popular_movies, get_top_rated_movies, get_movie_keywords
from movie import Movie
from embeddings import generate_embedding
from database import get_connection, create_table, save_movie, get_movie_count


REQUEST_DELAY_SECONDS = 0.1

SOURCES = {
    "popular": get_popular_movies,
    "top_rated": get_top_rated_movies
}


def collect_movies(source="popular", num_pages=1):
    fetch_page = SOURCES[source]

    conn = get_connection()
    create_table(conn)

    saved_count = 0

    for page in range(1, num_pages + 1):
        data = fetch_page(page)

        for movie_data in data["results"]:
            keywords_data = get_movie_keywords(movie_data["id"])
            time.sleep(REQUEST_DELAY_SECONDS)

            movie = Movie.from_tmdb_result(movie_data, keywords_data)

            if movie is not None:
                embedding = generate_embedding(movie)
                save_movie(conn, movie, embedding)
                saved_count += 1

        print(f"[{source}] page {page}/{num_pages} done — {saved_count} valid movies saved so far.")

    total_in_db = get_movie_count(conn)
    conn.close()

    print(f"\nFinished collecting from '{source}'. {saved_count} movies saved this run. Database now has {total_in_db} total movies.")


if __name__ == "__main__":
    collect_movies(source="popular", num_pages=15)
    collect_movies(source="top_rated", num_pages=15)