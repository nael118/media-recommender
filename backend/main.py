from tmdb import search_movie

movie_name = input("Enter a movie: ")

results = search_movie(movie_name)

if not results["results"]:
    print("Movie not found.")
    exit()

movie = results["results"][0]

print("\n=== Movie Information ===")
print(f"Title: {movie['title']}")
print(f"Release Date: {movie['release_date']}")
print(f"Rating: {movie['vote_average']:.1f}/10")
print("\nOverview:")
print(movie["overview"])