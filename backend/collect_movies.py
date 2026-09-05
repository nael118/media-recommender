import time

from tmdb import get_popular_movies, get_movie_keywords
from movie import Movie
from embeddings import generate_embedding
from database import get_connection, create_table, save_movie, get_movie_count


REQUEST_DELAY_SECONDS = 0.25


def collect_popular_movies(num_pages=1):
    conn = get_connection()
    create_table(conn)

    saved_count = 0

    for page in range(1, num_pages + 1):
        data = get_popular_movies(page)

        for movie_data in data["results"]:
            keywords_data = get_movie_keywords(movie_data["id"])
            time.sleep(REQUEST_DELAY_SECONDS)

            movie = Movie.from_tmdb_result(movie_data, keywords_data)

            if movie is not None:
                embedding = generate_embedding(movie)
                save_movie(conn, movie, embedding)
                saved_count += 1

        print(f"Page {page}/{num_pages} done — {saved_count} valid movies saved so far.")

    total_in_db = get_movie_count(conn)
    conn.close()

    print(f"\nFinished. {saved_count} movies saved this run. Database now has {total_in_db} total movies.")


if __name__ == "__main__":
    collect_popular_movies(num_pages=25)