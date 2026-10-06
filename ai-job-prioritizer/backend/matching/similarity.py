"""Cosine similarity engine for the AI Job Application Prioritization System.

Calculates cosine similarity between resume and job description embeddings.

DESIGN CONSTRAINT: Scores are labeled as "Semantic Match Score" and should NOT be
interpreted as probabilities, percentages, or predictions of hiring success. They
measure semantic similarity between text content only.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional

import numpy as np

from .embeddings import embed_text, embed_texts, get_embedding_dimension


def compute_cosine_similarity(
    embedding1: List[float],
    embedding2: List[float],
) -> float:
    """Compute cosine similarity between two embedding vectors.

    Args:
        embedding1: First embedding vector (length 384).
        embedding2: Second embedding vector (length 384).

    Returns:
        Cosine similarity as a float in range [-1, 1].
        We display values in [0, 1] for resume/job matching since both texts
        are typically non-negative in direction.

    Raises:
        ValueError: If embeddings have different dimensions or are empty.
    """
    if not embedding1 or not embedding2:
        raise ValueError("Embeddings cannot be empty")

    dim1 = len(embedding1)
    dim2 = len(embedding2)

    if dim1 != dim2:
        raise ValueError(
            f"Embedding dimension mismatch: expected {dim1}, got {dim2}"
        )

    # Convert to numpy arrays
    v1 = np.array(embedding1, dtype=np.float64)
    v2 = np.array(embedding2, dtype=np.float64)

    # Compute cosine similarity: dot(|v1|*|v2|)
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)

    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0

    similarity = dot_product / (norm_v1 * norm_v2)

    # Clamp to [-1, 1] for numerical safety
    return float(np.clip(similarity, -1.0, 1.0))


def rank_jobs(
    resume_text: str,
    job_texts: List[str],
    resume_title: str = "Resume",
) -> List[Dict[str, Any]]:
    """Rank job descriptions by semantic similarity to a resume.

    Creates embeddings for the resume and all job texts, then computes
    cosine similarity and ranks jobs by similarity score.

    Args:
        resume_text: The resume text to compare against.
        job_texts: List of job description texts to rank.
        resume_title: Optional title/label for the resume (for display).

    Returns:
        List of dictionaries, each containing:
            - job_title: Optional derived from job text (uses first 30 chars if not provided)
            - semantic_match_score: Cosine similarity in range [0, 1]
            - rank: Integer rank (1 = highest similarity)
            - jd_text: The original job description text (for reference)

    Example:
        >>> jobs = rank_jobs("Python developer with 3 years experience", ["ML engineer", "Data analyst"])
        >>> jobs[0]["rank"]
        1
        >>> jobs[0]["semantic_match_score"]
        0.72
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text cannot be empty or whitespace-only")

    if not job_texts:
        return []

    # Step 1: Generate embeddings
    # Model loads once (cached in embed_texts)
    resume_embedding = embed_text(resume_text)
    job_embeddings = embed_texts(job_texts)

    # Step 2: Compute similarities
    num_jobs = len(job_texts)
    results: list[tuple[float, int, str]] = []  # (score, index, jd_text)

    for idx, (job_text, job_emb) in enumerate(zip(job_texts, job_embeddings)):
        score = compute_cosine_similarity(resume_embedding, job_emb)
        results.append((score, idx, job_text))

    # Step 3: Sort by similarity descending
    results.sort(key=lambda x: x[0], reverse=True)

    # Step 4: Build ranked output
    ranked_jobs: list[Dict[str, Any]] = []
    for rank, (score, idx, jd_text) in enumerate(results, start=1):
        # Derive a short job title from the first line or first 30 chars
        first_line = jd_text.split("\n")[0].strip()
        job_title = first_line if first_line else f"Job #{idx + 1}"

        # Truncate title for display
        if len(job_title) > 50:
            job_title = job_title[:47] + "..."

        ranked_jobs.append(
            {
                "rank": rank,
                "job_title": job_title,
                "semantic_match_score": score,
                "jd_text": jd_text,
            }
        )

    return ranked_jobs


def format_score(score: float) -> str:
    """Format a cosine similarity score for display.

    Args:
        score: Cosine similarity in range [-1, 1].

    Returns:
        String formatted as "0.XX" in range [0, 1].
    """
    # Ensure in valid range
    clamped = max(0.0, min(1.0, score))
    return f"{clamped:.2f}"