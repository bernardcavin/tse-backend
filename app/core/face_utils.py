"""Face embedding comparison utilities.

All face detection and embedding extraction is done client-side.
The backend only stores and compares pre-computed embedding vectors.
"""
import math


def compute_similarity(emb1: list[float], emb2: list[float]) -> float:
    """Computes cosine similarity between two face embeddings."""
    dot = sum(a * b for a, b in zip(emb1, emb2))
    norm1 = math.sqrt(sum(a * a for a in emb1))
    norm2 = math.sqrt(sum(b * b for b in emb2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def is_same_person(emb1: list[float], emb2: list[float], threshold: float = 0.6) -> bool:
    """Returns True if the cosine similarity is above the threshold."""
    return compute_similarity(emb1, emb2) >= threshold
