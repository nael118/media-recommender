class Movie:
    def __init__(self, title, release_date, rating, genres, keywords, overview):
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
        Title: {self.title}

        Genres:
        {", ".join(self.genres)}

        Keywords:
        {", ".join(self.keywords)}

        Overview:
        {self.overview}
        """