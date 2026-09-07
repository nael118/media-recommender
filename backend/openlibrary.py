import time
import requests

BASE_URL = "https://openlibrary.org"

MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 2


def _get_with_retry(url, params=None):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, params=params, timeout=6)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt == MAX_RETRIES:
                raise
            print(f"  (Open Library request failed, retrying {attempt}/{MAX_RETRIES}: {e})")
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)


def search_book(title):
    url = f"{BASE_URL}/search.json"
    params = {"q": title, "limit": 1}
    return _get_with_retry(url, params)


def get_work_details(work_key):
    url = f"{BASE_URL}{work_key}.json"
    return _get_with_retry(url)


def get_subject_works(subject, limit=30, offset=0):
    url = f"{BASE_URL}/subjects/{subject}.json"
    params = {"limit": limit, "offset": offset}
    return _get_with_retry(url, params)