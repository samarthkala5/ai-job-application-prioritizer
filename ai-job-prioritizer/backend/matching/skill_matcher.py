"""Skill matching for the AI Job Application Prioritization System.

Compares the skills found in a resume against the skills required by a job and
reports matched skills, missing skills, additional (resume-only) skills and
required skill coverage.

DESIGN CONSTRAINT: Required skill coverage is the fraction of the job's
recognised skills that also appear in the resume. It is NOT a fit score and is
not combined with semantic similarity here.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Optional

from .skill_extractor import SkillExtractor, SkillOntology, get_default_extractor


@dataclass(frozen=True)
class SkillMatchResult:
    """Result of comparing resume skills to job skills.

    Attributes:
        matched_skills: Job skills also present in the resume (job order).
        missing_skills: Job skills absent from the resume (job order).
        additional_skills: Resume skills the job does not mention (resume order).
        required_skill_coverage: len(matched) / len(required), in [0, 1].
            None when the job has no recognised skills (coverage is undefined).
    """

    matched_skills: List[str]
    missing_skills: List[str]
    additional_skills: List[str]
    required_skill_coverage: Optional[float]

    @property
    def num_required(self) -> int:
        return len(self.matched_skills) + len(self.missing_skills)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _canonicalize(skills: Iterable[str], ontology: Optional[SkillOntology]) -> List[str]:
    """Normalize skill names to canonical form and remove duplicates (order kept).

    Skills not found in the ontology are kept as given (stripped), and are
    de-duplicated case-insensitively.
    """
    result: List[str] = []
    seen_keys: set[str] = set()
    for skill in skills:
        if not skill or not skill.strip():
            continue
        canonical = ontology.normalize(skill) if ontology is not None else None
        name = canonical if canonical is not None else skill.strip()
        key = name.casefold()
        if key not in seen_keys:
            seen_keys.add(key)
            result.append(name)
    return result


def match_skills(
    resume_skills: Iterable[str],
    required_skills: Iterable[str],
    ontology: Optional[SkillOntology] = None,
) -> SkillMatchResult:
    """Compare a resume's skills with a job's required skills.

    Args:
        resume_skills: Skills held by the candidate (names or aliases).
        required_skills: Skills required by the job (names or aliases).
        ontology: Ontology used to map aliases to canonical names. Defaults to
            the ontology of the default extractor.

    Returns:
        SkillMatchResult with matched, missing and additional skills and coverage.
    """
    if ontology is None:
        ontology = get_default_extractor().ontology

    resume = _canonicalize(resume_skills, ontology)
    required = _canonicalize(required_skills, ontology)

    resume_keys = {s.casefold() for s in resume}
    required_keys = {s.casefold() for s in required}

    matched = [s for s in required if s.casefold() in resume_keys]
    missing = [s for s in required if s.casefold() not in resume_keys]
    additional = [s for s in resume if s.casefold() not in required_keys]

    coverage = len(matched) / len(required) if required else None

    return SkillMatchResult(
        matched_skills=matched,
        missing_skills=missing,
        additional_skills=additional,
        required_skill_coverage=coverage,
    )


def match_resume_to_job(
    resume_text: str,
    job_text: str,
    extractor: Optional[SkillExtractor] = None,
) -> SkillMatchResult:
    """Extract skills from resume and job text, then match them.

    Every skill recognised in the job text is treated as required; the
    extractor does not distinguish "required" from "nice to have" sections.

    Args:
        resume_text: Resume text.
        job_text: Job description text.
        extractor: Skill extractor to use (defaults to the cached default).

    Returns:
        SkillMatchResult for the pair.
    """
    extractor = extractor if extractor is not None else get_default_extractor()
    return match_skills(
        extractor.extract(resume_text),
        extractor.extract(job_text),
        ontology=extractor.ontology,
    )
