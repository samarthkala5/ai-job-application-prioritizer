"""Tests for the skill matcher (matched / missing skills and coverage)."""

from __future__ import annotations

from pathlib import Path

import pytest

# Import from backend
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from matching.skill_matcher import SkillMatchResult, match_resume_to_job, match_skills


# ---------------------------------------------------------------------------
# Test matching of skill lists
# ---------------------------------------------------------------------------
class TestMatchSkills:
    """Tests for comparing skill lists."""

    def test_full_match(self) -> None:
        result = match_skills(["Python", "Docker"], ["Python", "Docker"])
        assert result.matched_skills == ["Python", "Docker"]
        assert result.missing_skills == []
        assert result.required_skill_coverage == 1.0

    def test_partial_match(self) -> None:
        result = match_skills(
            ["Python", "Docker", "Git"],
            ["Python", "Kubernetes", "Docker", "AWS"],
        )
        assert result.matched_skills == ["Python", "Docker"]
        assert result.missing_skills == ["Kubernetes", "AWS"]
        assert result.additional_skills == ["Git"]
        assert result.required_skill_coverage == pytest.approx(0.5)

    def test_no_match(self) -> None:
        result = match_skills(["Excel"], ["PyTorch", "TensorFlow"])
        assert result.matched_skills == []
        assert result.missing_skills == ["PyTorch", "TensorFlow"]
        assert result.required_skill_coverage == 0.0

    def test_aliases_are_normalized(self) -> None:
        result = match_skills(["sklearn", "golang", "k8s"],
                              ["scikit-learn", "Go", "Kubernetes"])
        assert result.matched_skills == ["scikit-learn", "Go", "Kubernetes"]
        assert result.required_skill_coverage == 1.0

    def test_case_insensitive(self) -> None:
        result = match_skills(["PYTHON"], ["python"])
        assert result.matched_skills == ["Python"]

    def test_duplicates_removed(self) -> None:
        result = match_skills(["Python", "python", "python3"],
                              ["Python", "PYTHON", "AWS", "aws"])
        assert result.matched_skills == ["Python"]
        assert result.missing_skills == ["AWS"]
        assert result.num_required == 2
        assert result.required_skill_coverage == pytest.approx(0.5)

    def test_unknown_skills_compared_case_insensitively(self) -> None:
        result = match_skills(["Basket Weaving"], ["basket weaving", "Origami"])
        assert result.matched_skills == ["basket weaving"]
        assert result.missing_skills == ["Origami"]

    def test_empty_required_has_undefined_coverage(self) -> None:
        result = match_skills(["Python"], [])
        assert result.required_skill_coverage is None
        assert result.matched_skills == []
        assert result.additional_skills == ["Python"]

    def test_empty_resume(self) -> None:
        result = match_skills([], ["Python", "SQL"])
        assert result.missing_skills == ["Python", "SQL"]
        assert result.required_skill_coverage == 0.0

    def test_blank_entries_ignored(self) -> None:
        result = match_skills(["", "  ", "Python"], ["Python", ""])
        assert result.matched_skills == ["Python"]
        assert result.num_required == 1

    def test_coverage_in_unit_range(self) -> None:
        result = match_skills(["Python"], ["Python", "SQL", "AWS"])
        assert 0.0 <= result.required_skill_coverage <= 1.0
        assert result.required_skill_coverage == pytest.approx(1 / 3)

    def test_to_dict(self) -> None:
        d = match_skills(["Python"], ["Python", "SQL"]).to_dict()
        assert set(d) == {"matched_skills", "missing_skills",
                          "additional_skills", "required_skill_coverage"}


# ---------------------------------------------------------------------------
# Test text-to-text matching
# ---------------------------------------------------------------------------
class TestMatchResumeToJob:
    """Tests for extracting and matching skills directly from text."""

    def test_resume_to_job(self) -> None:
        resume = "Python developer: Django, Flask, PostgreSQL, Docker, Git."
        job = "Need Python, Django, PostgreSQL, Kubernetes and AWS."
        result = match_resume_to_job(resume, job)
        assert isinstance(result, SkillMatchResult)
        assert result.matched_skills == ["Python", "Django", "PostgreSQL"]
        assert result.missing_skills == ["Kubernetes", "AWS"]
        assert result.additional_skills == ["Flask", "Docker", "Git"]
        assert result.required_skill_coverage == pytest.approx(3 / 5)

    def test_alias_in_resume_matches_canonical_in_job(self) -> None:
        result = match_resume_to_job("Built models with sklearn and k8s",
                                     "Requires scikit-learn and Kubernetes")
        assert result.matched_skills == ["scikit-learn", "Kubernetes"]
        assert result.required_skill_coverage == 1.0

    def test_job_without_recognised_skills(self) -> None:
        result = match_resume_to_job("Python developer", "Friendly team player wanted")
        assert result.required_skill_coverage is None

    def test_sample_data_files(self) -> None:
        root = Path(__file__).parent.parent / "data"
        resume = (root / "resumes" / "resume3_data_analyst.txt").read_text(encoding="utf-8")
        job = (root / "jobs" / "job3_data_analyst.txt").read_text(encoding="utf-8")
        result = match_resume_to_job(resume, job)
        assert result.missing_skills == []
        assert result.required_skill_coverage == 1.0
