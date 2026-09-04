from sentence_transformers import SentenceTransformer


model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_embedding(movie):
    profile = movie.get_profile()

    embedding = model.encode(profile)

    return embedding