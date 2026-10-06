"""Sentence Transformer embedding engine for the AI Job Application Prioritization System.

Uses all-MiniLM-L6-v2 to encode resume and job description text into 384-dimensional
vectors for semantic similarity comparison.

IMPORTANT: This module loads the model once and reuses it. Do NOT reload for every comparison.
"""

from __future__ import annotations

from typing import List

from sentence_transformers import SentenceTransformer


# Load model once at module level - reusable across comparisons
# all-MiniLM-L6-v2 produces 384-dimensional embeddings
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Lazy-load the SentenceTransformer model, caching it for reuse.

    Returns:
        The loaded model instance.
    """
    global _model
    if _model is None:
        print("Loading SBERT model 'all-MiniLM-L6-v2' (first time)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print(f"Model loaded. Embedding dimension: {_model.get_sentence_embedding_dimension()}")
    return _model


def embed_text(text: str) -> List[float]:
    """Encode a single text string into an embedding vector.

    Args:
        text: Input text to encode.

    Returns:
        Embedding vector as a list of floats (length 384 for all-MiniLM-L6-v2).

    Raises:
        ValueError: If text is empty or None.
    """
    if not text or not text.strip():
        raise ValueError("Input text cannot be empty or whitespace-only")

    model = _get_model()
    # encode returns a 2D numpy array; squeeze to 1D then convert to list
    embedding = model.encode([text])[0]
    return embedding.tolist()


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Encode multiple text strings into embedding vectors.

    Args:
        texts: List of input texts to encode.

    Returns:
        List of embedding vectors, each as a list of floats (length 384).

    Raises:
        ValueError: If any text in the list is empty or None.
    """
    if not texts:
        return []

    # Validate all texts first
    for i, text in enumerate(texts):
        if not text or not text.strip():
            raise ValueError(f"Text at index {i} cannot be empty or whitespace-only")

    model = _get_model()
    embeddings = model.encode(texts)
    return embeddings.tolist()


def get_embedding_dimension() -> int:
    """Return the embedding vector dimensionality for the loaded model.

    Returns:
        Integer embedding dimension (384 for all-MiniLM-L6-v2).
    """
    model = _get_model()
    return model.get_sentence_embedding_dimension()