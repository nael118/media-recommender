import numpy as np
from recommend import normalize_tags, mmr_rerank


def test_normalize_tags_lowercases():
    result = normalize_tags(["Science Fiction", "DRAMA"])
    assert result == {"science fiction", "drama"}


def test_mmr_rerank_returns_top_scoring_first():
    embeddings = np.array([[1, 0], [0, 1], [1, 0]])
    scores = [0.9, 0.5, 0.8]
    order = mmr_rerank(embeddings, scores, top_n=3, lambda_param=1.0)
    assert order[0] == 0


def test_mmr_rerank_penalizes_near_duplicates():
    # Item 0 and 2 are near-identical vectors; item 1 is orthogonal (unrelated).
    embeddings = np.array([[1, 0], [0, 1], [0.99, 0.01]])
    scores = [0.9, 0.85, 0.89]
    # With heavy diversity weighting (low lambda), the near-duplicate (item 2)
    # should be pushed later, letting the distinct item (1) rank higher than
    # its raw score alone would suggest.
    order = mmr_rerank(embeddings, scores, top_n=3, lambda_param=0.3)
    assert order[0] == 0
    assert order[1] == 1


def test_mmr_rerank_with_no_candidates_returns_empty():
    assert mmr_rerank(np.array([]).reshape(0, 2), [], top_n=5) == []