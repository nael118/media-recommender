import requests

BASE_URL = "https://openlibrary.org"


def search_book(title):
    url = f"{BASE_URL}/search.json"

    params = {
        "q": title,
        "limit": 1
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()


def get_work_details(work_key):
    url = f"{BASE_URL}{work_key}.json"

    response = requests.get(url)
    response.raise_for_status()

    return response.json()