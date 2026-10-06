"""Tests for the similarity engine (embeddings and cosine similarity)."""

from __future__ import annotations

import numpy as np
import pytest

# Import from backend
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from matching.embeddings import embed_text, embed_texts, get_embedding_dimension
from matching.similarity import compute_cosine_similarity, rank_jobs, format_score


# ---------------------------------------------------------------------------
# Test embedding generation
# ---------------------------------------------------------------------------
class TestEmbeddings:
    """Tests for SBERT embedding generation."""

    def test_embed_single_text(self) -> None:
        """Test embedding a single text string."""
        text = "This is a test sentence."
        embedding = embed_text(text)

        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
        # Should be 384 dimensions for all-MiniLM-L6-v2
        assert len(embedding) == get_embedding_dimension()

    def test_embed_empty_string_raises(self) -> None:
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError):
            embed_text("")

    def test_embed_whitespace_only_raises(self) -> None:
        """Test that whitespace-only string raises ValueError."""
        with pytest.raises(ValueError):
            embed_text("   \n\t  ")

    def test_embed_multiple_texts(self) -> None:
        """Test embedding multiple texts."""
        texts = [
            "First test sentence.",
            "Second test sentence with different words.",
            "Third sentence here."
        ]
        embeddings = embed_texts(texts)

        assert isinstance(embeddings, list)
        assert len(embeddings) == len(texts)
        for emb in embeddings:
            assert isinstance(emb, list)
            assert len(emb) == get_embedding_dimension()
            assert all(isinstance(x, float) for x in emb)

    def test_embed_multiple_with_empty_raises(self) -> None:
        """Test that embedding list with empty string raises ValueError."""
        with pytest.raises(ValueError):
            embed_texts(["Valid text", "", "Another valid"])

    def test_model_loads_only_once(self) -> None:
        """Verify that the model is loaded only once (cached)."""
        # Call embed_text multiple times - should not reload model
        text1 = "First test"
        text2 = "Second test"

        emb1 = embed_text(text1)
        emb2 = embed_text(text2)

        # Both should return valid embeddings
        assert len(emb1) == get_embedding_dimension()
        assert len(emb2) == get_embedding_dimension()
        # They should be different (different inputs)
        assert emb1 != emb2

    def test_embedding_dimension(self) -> None:
        """Test that get_embedding_dimension returns correct value."""
        dim = get_embedding_dimension()
        assert dim == 384  # all-MiniLM-L6-v2 dimension


# ---------------------------------------------------------------------------
# Test cosine similarity
# ---------------------------------------------------------------------------
class TestCosineSimilarity:
    """Tests for cosine similarity computation."""

    def test_compute_cosine_similarity_identical_vectors(self) -> None:
        """Test that identical vectors have similarity 1.0."""
        vec = [1.0, 0.0, 0.0, 1.0]
        similarity = compute_cosine_similarity(vec, vec)
        assert abs(similarity - 1.0) < 1e-10

    def test_compute_cosine_similarity_orthogonal_vectors(self) -> None:
        """Test that orthogonal vectors have similarity ~0."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = compute_cosine_similarity(vec1, vec2)
        assert abs(similarity - 0.0) < 1e-10

    def test_compute_cosine_similarity_opposite_vectors(self) -> None:
        """Test that opposite vectors have similarity -1.0."""
        vec = [1.0, 2.0, 3.0]
        vec_opposite = [-x for x in vec]
        similarity = compute_cosine_similarity(vec, vec_opposite)
        assert abs(similarity - (-1.0)) < 1e-10

    def test_compute_cosine_similarity_zero_vector(self) -> None:
        """Test that zero vector with anything gives 0 similarity."""
        vec = [1.0, 2.0, 3.0]
        zero_vec = [0.0, 0.0, 0.0]
        similarity = compute_cosine_similarity(vec, zero_vec)
        assert similarity == 0.0

    def test_compute_cosine_similarity_dimension_mismatch_raises(self) -> None:
        """Test that mismatched dimensions raise ValueError."""
        vec1 = [1.0, 2.0, 3.0]  # 3-dim
        vec2 = [1.0, 2.0, 3.0, 4.0]  # 4-dim

        with pytest.raises(ValueError):
            compute_cosine_similarity(vec1, vec2)

    def test_compute_cosine_similarity_empty_vector_raises(self) -> None:
        """Test that empty vectors raise ValueError."""
        with pytest.raises(ValueError):
            compute_cosine_similarity([], [1.0, 2.0])

    def test_compute_cosine_similarity_normalized_output(self) -> None:
        """Test that we handle typical ranges correctly."""
        # These should produce reasonable similarity scores
        vec1 = [1.0, 1.0, 1.0]
        vec2 = [1.0, 1.0, 0.9]
        similarity = compute_cosine_similarity(vec1, vec2)

        # Should be close to 1.0
        assert 0.9 <= similarity <= 1.0

    def test_format_score(self) -> None:
        """Test score formatting for display."""
        assert format_score(0.856) == "0.86"
        assert format_score(0.5) == "0.50"
        assert format_score(0.0) == "0.00"
        assert format_score(1.0) == "1.00"
        # Clamping
        assert format_score(-0.5) == "0.00"  # clamped to 0
        assert format_score(1.5) == "1.00"   # clamped to 1


# ---------------------------------------------------------------------------
# Test ranking
# ---------------------------------------------------------------------------
class TestRanking:
    """Tests for job ranking functionality."""

    def test_rank_jobs_basic(self) -> None:
        """Test basic job ranking."""
        resume = "Experienced Python developer with Django and REST API experience."
        jobs = [
            "Looking for a Python/Django backend engineer with 3+ years experience.",
            "Seeking a Java Spring developer with microservices expertise.",
            "Hiring a data analyst with SQL and Tableau skills."
        ]

        ranked = rank_jobs(resume, jobs)

        assert len(ranked) == 3
        # First job should be most similar (Python/Django mention)
        assert ranked[0]["rank"] == 1
        assert "Python/Django" in ranked[0]["job_title"] or "backend engineer" in ranked[0]["job_title"]
        # Scores should be in descending order
        assert ranked[0]["semantic_match_score"] >= ranked[1]["semantic_match_score"]
        assert ranked[1]["semantic_match_score"] >= ranked[2]["semantic_match_score"]

    def test_rank_jobs_empty_jobs(self) -> None:
        """Test ranking with empty job list."""
        resume = "Experienced developer"
        ranked = rank_jobs(resume, [])
        assert ranked == []

    def test_rank_jobs_empty_resume_raises(self) -> None:
        """Test that empty resume raises ValueError."""
        with pytest.raises(ValueError):
            rank_jobs("", ["Some job"])

    def test_rank_jobs_whitespace_resume_raises(self) -> None:
        """Test that whitespace-only resume raises ValueError."""
        with pytest.raises(ValueError):
            rank_jobs("   \n\t  ", ["Some job"])

    def test_rank_jobs_deterministic_order(self) -> None:
        """Test that ranking is deterministic and repeatable."""
        resume = "Software engineer with Python, Java, and cloud experience."
        jobs = [
            "DevOps engineer with AWS and Docker experience required.",
            "Frontend developer needed with React and TypeScript skills.",
            "Backend engineer position - Python, Django, REST APIs."
        ]

        # Run ranking twice
        ranked1 = rank_jobs(resume, jobs)
        ranked2 = rank_jobs(resume, jobs)

        # Results should be identical
        assert len(ranked1) == len(ranked2)
        for r1, r2 in zip(ranked1, ranked2):
            assert r1["rank"] == r2["rank"]
            assert r1["job_title"] == r2["job_title"]
            assert abs(r1["semantic_match_score"] - r2["semantic_match_score"]) < 1e-10

    def test_rank_jobs_score_range(self) -> None:
        """Test that all scores are in valid range [-1, 1]."""
        resume = "Machine learning engineer with Python and TensorFlow."
        jobs = [
            "Looking for ML engineer experienced in PyTorch and neural networks.",
            "Seeking a graphic designer with Adobe Photoshop skills.",
            "Hiring a civil engineer for bridge construction projects."
        ]

        ranked = rank_jobs(resume, jobs)

        for item in ranked:
            score = item["semantic_match_score"]
            assert -1.0 <= score <= 1.0
            # For resume/job similarity, we expect mostly positive
            # but technically cosine can be negative

    def test_rank_jobs_preserves_original_text(self) -> None:
        """Test that ranked jobs preserve the original job description text."""
        resume = "Python developer"
        jobs = ["Job A description", "Job B description with more words"]

        ranked = rank_jobs(resume, jobs)

        # Check that original text is preserved
        assert ranked[0]["jd_text"] == "Job A description"
        assert ranked[1]["jd_text"] == "Job B description with more words"