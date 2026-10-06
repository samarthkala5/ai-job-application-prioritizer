"""Tests for the ontology-based skill extractor."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# Import from backend
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from matching.skill_extractor import (
    DEFAULT_ONTOLOGY_PATH,
    SkillExtractor,
    SkillOntology,
    extract_skills,
)


@pytest.fixture(scope="module")
def extractor() -> SkillExtractor:
    return SkillExtractor()


# ---------------------------------------------------------------------------
# Test ontology loading
# ---------------------------------------------------------------------------
class TestSkillOntology:
    """Tests for loading and validating the skill ontology."""

    def test_default_ontology_file_exists(self) -> None:
        assert DEFAULT_ONTOLOGY_PATH.is_file()

    def test_default_ontology_size(self) -> None:
        ontology = SkillOntology.load()
        assert 75 <= len(ontology) <= 100

    def test_every_skill_has_category(self) -> None:
        ontology = SkillOntology.load()
        assert all(skill.category for skill in ontology.skills.values())

    def test_normalize_alias_to_canonical(self) -> None:
        ontology = SkillOntology.load()
        assert ontology.normalize("sklearn") == "scikit-learn"
        assert ontology.normalize("Golang") == "Go"
        assert ontology.normalize("  k8s ") == "Kubernetes"
        assert ontology.normalize("POSTGRES") == "PostgreSQL"

    def test_normalize_unknown_returns_none(self) -> None:
        ontology = SkillOntology.load()
        assert ontology.normalize("Basket Weaving") is None
        assert ontology.normalize("") is None

    def test_category_of(self) -> None:
        ontology = SkillOntology.load()
        assert ontology.category_of("pytorch") == "ml_ai"
        assert ontology.category_of("nonexistent") is None

    def test_duplicate_alias_across_skills_raises(self) -> None:
        data = {"skills": [
            {"name": "A", "category": "x", "aliases": ["shared"]},
            {"name": "B", "category": "x", "aliases": ["Shared"]},
        ]}
        with pytest.raises(ValueError):
            SkillOntology.from_dict(data)

    def test_duplicate_name_raises(self) -> None:
        data = {"skills": [
            {"name": "A", "category": "x"},
            {"name": "A", "category": "y"},
        ]}
        with pytest.raises(ValueError):
            SkillOntology.from_dict(data)

    def test_invalid_structure_raises(self) -> None:
        with pytest.raises(ValueError):
            SkillOntology.from_dict({"not_skills": []})

    def test_load_custom_path(self, tmp_path: Path) -> None:
        path = tmp_path / "onto.json"
        path.write_text(json.dumps({"skills": [
            {"name": "Foo", "category": "x", "aliases": ["foolang"]}
        ]}), encoding="utf-8")
        ontology = SkillOntology.load(path)
        assert SkillExtractor(ontology).extract("I write foolang daily") == ["Foo"]


# ---------------------------------------------------------------------------
# Test skill extraction
# ---------------------------------------------------------------------------
class TestSkillExtraction:
    """Tests for extracting skills from free text."""

    def test_case_insensitive(self, extractor: SkillExtractor) -> None:
        assert extractor.extract("PYTHON, docker and KuBeRnEtEs") == [
            "Python", "Docker", "Kubernetes"
        ]

    def test_aliases_map_to_canonical(self, extractor: SkillExtractor) -> None:
        skills = extractor.extract("Used sklearn, Golang, k8s and Postgres")
        assert skills == ["scikit-learn", "Go", "Kubernetes", "PostgreSQL"]

    def test_multi_word_skills(self, extractor: SkillExtractor) -> None:
        skills = extractor.extract("Experience in machine learning and computer vision")
        assert "Machine Learning" in skills
        assert "Computer Vision" in skills

    def test_multi_word_across_hyphen_and_newline(self, extractor: SkillExtractor) -> None:
        skills = extractor.extract("deep-learning and natural\nlanguage   processing")
        assert skills == ["Deep Learning", "Natural Language Processing"]

    def test_word_boundaries_java_vs_javascript(self, extractor: SkillExtractor) -> None:
        assert extractor.extract("JavaScript developer") == ["JavaScript"]
        assert set(extractor.extract("Java and JavaScript")) == {"Java", "JavaScript"}

    def test_word_boundaries_no_substring_match(self, extractor: SkillExtractor) -> None:
        # "Git" in "digital", "SQL" in "PostgreSQL", "Go" in "Google", "ARM" in "ARMY"
        assert extractor.extract("digital marketing") == []
        assert extractor.extract("PostgreSQL") == ["PostgreSQL"]
        assert extractor.extract("Google ARMY") == []

    def test_symbol_skills(self, extractor: SkillExtractor) -> None:
        skills = extractor.extract("C/C++, C#, Node.js and CI/CD pipelines")
        assert skills == ["C", "C++", "C#", "Node.js", "CI/CD"]

    def test_c_not_matched_inside_cpp(self, extractor: SkillExtractor) -> None:
        assert extractor.extract("Expert in C++") == ["C++"]
        assert extractor.extract("Wrote C# services") == ["C#"]

    def test_duplicates_removed(self, extractor: SkillExtractor) -> None:
        skills = extractor.extract("Python, python, PYTHON and python3")
        assert skills == ["Python"]

    def test_order_of_first_appearance(self, extractor: SkillExtractor) -> None:
        assert extractor.extract("Docker then AWS then Docker") == ["Docker", "AWS"]

    def test_longest_match_wins(self, extractor: SkillExtractor) -> None:
        assert extractor.extract("Built apps with React Native") == ["React Native"]
        assert extractor.extract("Spring Boot microservices") == [
            "Spring Boot", "Microservices"
        ]

    def test_case_sensitive_aliases_avoid_false_positives(self, extractor: SkillExtractor) -> None:
        # Common English words should not be treated as skills.
        text = "I go to work, react to feedback, excel at teamwork and rest."
        assert extractor.extract(text) == []

    def test_case_sensitive_aliases_still_match(self, extractor: SkillExtractor) -> None:
        skills = extractor.extract("Go, React, Excel and REST")
        assert skills == ["Go", "React", "Excel", "REST APIs"]

    def test_punctuation_adjacent(self, extractor: SkillExtractor) -> None:
        skills = extractor.extract("(Python), [Docker]; AWS. Git!")
        assert skills == ["Python", "Docker", "AWS", "Git"]

    def test_empty_and_whitespace(self, extractor: SkillExtractor) -> None:
        assert extractor.extract("") == []
        assert extractor.extract("   \n\t ") == []

    def test_no_skills(self, extractor: SkillExtractor) -> None:
        assert extractor.extract("Friendly, punctual and hard working.") == []

    def test_deterministic(self, extractor: SkillExtractor) -> None:
        text = "Python, PyTorch, Docker, AWS, SQL, Tableau, React"
        assert extractor.extract(text) == extractor.extract(text)

    def test_find_matches_spans(self, extractor: SkillExtractor) -> None:
        text = "Python and python"
        matches = extractor.find_matches(text)
        assert [(text[s:e], n) for s, e, n in matches] == [
            ("Python", "Python"), ("python", "Python")
        ]

    def test_module_level_extract_skills(self) -> None:
        assert extract_skills("Django and Flask") == ["Django", "Flask"]

    def test_sample_job_description(self, extractor: SkillExtractor) -> None:
        jd = ("Software Engineer - 3+ years Python and Django. Strong REST APIs, "
              "PostgreSQL, Git. AWS cloud services a plus.")
        assert extractor.extract(jd) == [
            "Python", "Django", "REST APIs", "PostgreSQL", "Git", "AWS"
        ]


# ---------------------------------------------------------------------------
# Regression tests: ambiguous "Go" and "C"
# ---------------------------------------------------------------------------
class TestAmbiguousShortSkills:
    """Regression tests for false positives on capitalised "Go" and "C"."""

    @pytest.mark.parametrize("text", [
        "Go-to person for production incidents",
        "Go-live support for the ERP rollout",
        "Owned the Go - ahead decision",
    ])
    def test_go_hyphen_compound_not_detected(self, extractor: SkillExtractor, text: str) -> None:
        assert "Go" not in extractor.extract(text)

    @pytest.mark.parametrize("text", [
        "Go programming",
        "Go language",
        "Services written in Go",
        "Python or Go, plus Golang tooling",
        "Go.",
    ])
    def test_go_legitimate_detection(self, extractor: SkillExtractor, text: str) -> None:
        assert "Go" in extractor.extract(text)

    @pytest.mark.parametrize("text", [
        "Achieved Grade C in physics",
        "Final grade: C",
        "Class C network addressing",
        "USB Type C connector",
        "Vitamin C research",
    ])
    def test_c_letter_label_not_detected(self, extractor: SkillExtractor, text: str) -> None:
        assert "C" not in extractor.extract(text)

    @pytest.mark.parametrize("text", [
        "C programming",
        "C language",
        "Firmware implemented in C",
        "Python and C",
    ])
    def test_c_legitimate_detection(self, extractor: SkillExtractor, text: str) -> None:
        assert "C" in extractor.extract(text)

    def test_c_slash_cpp_still_detects_both(self, extractor: SkillExtractor) -> None:
        assert extractor.extract("C/C++ developer") == ["C", "C++"]

    def test_grade_c_does_not_suppress_real_c(self, extractor: SkillExtractor) -> None:
        skills = extractor.extract("Grade C in art, but wrote drivers in C")
        assert skills == ["C"]
        assert len(extractor.find_matches("Grade C in art, but wrote drivers in C")) == 1
