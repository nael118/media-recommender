GENRE_MAP = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    14: "Fantasy",
    27: "Horror",
    9648: "Mystery",
    10749: "Romance",
    878: "Science Fiction",
    53: "Thriller"
}


def get_genres(genre_ids):
    return [
        GENRE_MAP.get(genre_id, "Unknown")
        for genre_id in genre_ids
    ]