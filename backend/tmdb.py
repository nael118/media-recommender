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