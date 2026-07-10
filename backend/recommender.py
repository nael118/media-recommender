from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_similarity(movie1, movie2):
    texts = [
        movie1.get_profile(),
        movie2.get_profile()
    ]

    vectorizer = TfidfVectorizer()

    vectors = vectorizer.fit_transform(texts)

    similarity = cosine_similarity(
        vectors[0],
        vectors[1]
    )

    return similarity[0][0]