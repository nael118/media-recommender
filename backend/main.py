from tmdb import search_movie, get_movie_keywords
from utils import get_genres
from movie import Movie


movie_name = input("Enter a movie: ")

results = search_movie(movie_name)

if not results["results"]:
    print("Movie not found.")
    exit()

movie = results["results"][0]


keywords_data = get_movie_keywords(movie["id"])

keywords = [
    keyword["name"]
    for keyword in keywords_data["keywords"]
]

genres = get_genres(movie["genre_ids"])


movie_profile = Movie(
    title=movie["title"],
    release_date=movie["release_date"],
    rating=movie["vote_average"],
    genres=genres,
    keywords=keywords,
    overview=movie["overview"]
)


movie_profile.display()