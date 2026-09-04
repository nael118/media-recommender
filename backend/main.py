from tmdb import search_movie, get_movie_keywords
from movie import Movie
from semantic_recommender import calculate_semantic_similarity


def create_movie_profile(movie_name):
    results = search_movie(movie_name)

    if not results["results"]:
        print(f"{movie_name} not found.")
        return None

    movie_data = results["results"][0]

    keywords_data = get_movie_keywords(movie_data["id"])

    movie = Movie.from_tmdb_result(movie_data, keywords_data)

    if movie is None:
        print(f"{movie_name} found, but doesn't have enough data yet (unreleased or too few ratings).")
        return None

    return movie


movie_name1 = input("First movie: ")
movie_name2 = input("Second movie: ")


movie1 = create_movie_profile(movie_name1)
movie2 = create_movie_profile(movie_name2)


if movie1 and movie2:
    print("\n=== Movie 1 ===")
    movie1.display()

    print("\n=== Movie 2 ===")
    movie2.display()

    similarity = calculate_semantic_similarity(movie1, movie2)

    print(f"\nSimilarity score: {similarity:.2f}")