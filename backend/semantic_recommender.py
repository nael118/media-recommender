from sklearn.metrics.pairwise import cosine_similarity
from embeddings import generate_embedding


def calculate_semantic_similarity(movie1, movie2):

    embedding1 = generate_embedding(movie1)
    embedding2 = generate_embedding(movie2)

    similarity = cosine_similarity(
        [embedding1],
        [embedding2]
    )

    return similarity[0][0]