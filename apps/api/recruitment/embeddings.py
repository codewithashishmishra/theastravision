"""Shared sentence-transformers model (lazy-loaded)."""

from __future__ import annotations

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def encode_texts(texts: list[str]):
    model = get_embedding_model()
    return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
