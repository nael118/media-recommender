from tmdb import search_movie
from utils import get_genres


movie_name = input("Enter a movie: ")

results = search_movie(movie_name)

if not results["results"]:
    print("Movie not found.")
    exit()

movie = results["results"][0]

genres = get_genres(movie["genre_ids"])

print("\n=== Movie Information ===")
print(f"Title: {movie['title']}")
print(f"Release Date: {movie['release_date']}")
print(f"Rating: {movie['vote_average']}/10")

print("\nGenres:")
for genre in genres:
    print(f"- {genre}")

print("\nOverview:")
print(movie["overview"])