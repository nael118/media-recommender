import time

from tmdb import get_popular_movies, get_movie_keywords
from movie import Movie


REQUEST_DELAY_SECONDS = 0.25


def get_popular_movie_objects(num_pages=1):
    movies = []

    for page in range(1, num_pages + 1):
        data = get_popular_movies(page)

        for movie_data in data["results"]:
            keywords_data = get_movie_keywords(movie_data["id"])
            time.sleep(REQUEST_DELAY_SECONDS)

            movie = Movie.from_tmdb_result(movie_data, keywords_data)

            if movie is not None:
                movies.append(movie)

        print(f"Page {page}/{num_pages} done — {len(movies)} valid movies so far.")

    return movies


if __name__ == "__main__":
    movies = get_popular_movie_objects(num_pages=25)

    print(f"\nBuilt {len(movies)} valid Movie objects out of {25 * 20} TMDb results.\n")

    for movie in movies[:3]:
        movie.display()