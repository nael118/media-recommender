import requests
from config import TMDB_API_KEY

BASE_URL = "https://api.themoviedb.org/3"


def search_movie(title):
    url = f"{BASE_URL}/search/movie"

    params = {
        "api_key": TMDB_API_KEY,
        "query": title
    }

    response = requests.get(url, params=params)

    return response.json()

def get_movie_keywords(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}/keywords"

    params = {
        "api_key": TMDB_API_KEY
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()

def get_popular_movies(page=1):
    url = f"{BASE_URL}/movie/popular"

    params = {
        "api_key": TMDB_API_KEY,
        "page": page
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()