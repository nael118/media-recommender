from datetime import date

from utils import get_genres


STOP_KEYWORDS = [
    "new york city",
    "los angeles, california",
    "aftercreditsstinger",
    "duringcreditsstinger",
    "based on comic",
    "based on novel",
    "semi autobiographical"
]

MIN_VOTE_COUNT = 20
MIN_KEYWORD_COUNT = 2
MIN_OVERVIEW_LENGTH = 40


class Movie:
    def __init__(self, tmdb_id, title, release_date, rating, genres, keywords, overview):
        self.tmdb_id = tmdb_id
        self.title = title
        self.release_date = release_date
        self.rating = rating
        self.genres = genres
        self.keywords = keywords
        self.overview = overview

    def display(self):
        print("\n=== Movie Information ===")
        print(f"Title: {self.title}")
        print(f"Release Date: {self.release_date}")
        print(f"Rating: {self.rating}/10")

        print("\nGenres:")
        for genre in self.genres:
            print(f"- {genre}")

        print("\nKeywords:")
        for keyword in self.keywords:
            print(f"- {keyword}")

        print("\nOverview:")
        print(self.overview)

    def get_profile(self):
        return f"""
        Genres:
        {", ".join(self.genres)}

        Important themes:
        {", ".join(self.keywords)}

        Description:
        {self.overview}
        """

    @classmethod
    def from_tmdb_result(cls, movie_data, keywords_data):
        release_date = movie_data.get("release_date", "")

        if not release_date or release_date > date.today().isoformat():
            return None

        if movie_data.get("vote_count", 0) < MIN_VOTE_COUNT:
            return None

        keywords = [
                    keyword["name"]
                    for keyword in keywords_data.get("keywords", [])
                    if keyword["name"].lower() not in STOP_KEYWORDS
                ]
        
        if len(keywords) < MIN_KEYWORD_COUNT:
            return None

        if len(movie_data.get("overview", "")) < MIN_OVERVIEW_LENGTH:
            return None

        genres = get_genres(movie_data["genre_ids"])

        return cls(
            tmdb_id=movie_data["id"],
            title=movie_data["title"],
            release_date=release_date,
            rating=movie_data["vote_average"],
            genres=genres,
            keywords=keywords,
            overview=movie_data["overview"]
        )