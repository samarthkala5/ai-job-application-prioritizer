"""Deterministic skill extraction for the AI Job Application Prioritization System.

Extracts canonical technical skills from free text (resumes or job descriptions)
using a curated skill ontology (data/skill_ontology.json) and regular expressions.

Matching rules:
- Case-insensitive by default; aliases listed under ``case_sensitive_aliases``
  in the ontology (e.g. "Go", "React", "Excel") only match with exact casing,
  to avoid false positives on ordinary English words.
- Aliases map to a single canonical skill name.
- Multi-word skills tolerate any whitespace or hyphens between words
  ("machine learning", "machine-learning", "machine\\nlearning").
- Word boundaries are enforced with custom lookarounds so that skills containing
  symbols ("C++", "C#", "Node.js", "CI/CD") work, and "Java" does not match
  inside "JavaScript".
- When matches overlap, the longest match wins ("React Native" is not also
  reported as "React").
- Each canonical skill is reported at most once.

No machine learning or LLM is used: the same input always yields the same output.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


DEFAULT_ONTOLOGY_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "skill_ontology.json"
)

# A skill must not be directly preceded or followed by these characters.
# '+' and '#' on the right stop "C" matching inside "C++" / "C#";
# '&' stops "R&D"-style tokens from producing single-letter matches.
_LEFT_BOUNDARY = r"(?<![A-Za-z0-9_&])"
_RIGHT_BOUNDARY = r"(?![A-Za-z0-9_+#&])"

# Context exclusions for ambiguous case-sensitive aliases that are also common
# English tokens. Each entry maps the exact alias to (before, after) regexes;
# a match is rejected if `before` matches the text ending at the match start,
# or `after` matches the text starting at the match end.
_CONTEXT_EXCLUSIONS: Dict[str, Tuple[Optional[re.Pattern[str]], Optional[re.Pattern[str]]]] = {
    # "Go-to person", "Go-live", "Go-ahead": hyphenated compounds of the verb.
    "Go": (None, re.compile(r"\s*-")),
    # "Grade C", "Class C network", "Type: C", "Vitamin C": a letter label.
    "C": (
        re.compile(
            r"\b(?:grade|class|type|vitamin|section|level|tier|category|"
            r"option|appendix|figure|plan|part|group|phase|row|block|room)"
            r"\s*[:\-]?\s*$",
            re.IGNORECASE,
        ),
        None,
    ),
}
_CONTEXT_WINDOW = 20


def _normalize_key(text: str) -> str:
    """Normalize a skill string for dictionary lookup (casefold, collapse spaces)."""
    return " ".join(text.replace("-", " ").split()).casefold()


def _alias_to_pattern(alias: str) -> str:
    """Convert an alias into a regex body (without boundaries or flags).

    Spaces and hyphens between words match any run of whitespace/hyphens, so
    "machine learning" also matches "machine-learning" and line-wrapped text.
    """
    words = re.split(r"[\s\-]+", alias.strip())
    return r"[\s\-]+".join(re.escape(w) for w in words if w)


@dataclass(frozen=True)
class Skill:
    """A canonical skill entry from the ontology."""

    name: str
    category: str
    aliases: Tuple[str, ...] = ()
    case_sensitive_aliases: Tuple[str, ...] = ()


@dataclass
class SkillOntology:
    """Loaded skill ontology with alias lookup.

    Attributes:
        skills: Mapping of canonical name -> Skill.
    """

    skills: Dict[str, Skill] = field(default_factory=dict)
    _lookup: Dict[str, str] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> "SkillOntology":
        """Build an ontology from a parsed JSON dictionary.

        Raises:
            ValueError: If the structure is invalid, a canonical name is
                duplicated, or an alias maps to more than one skill.
        """
        if not isinstance(data, dict) or not isinstance(data.get("skills"), list):
            raise ValueError("Ontology must be an object with a 'skills' list")

        ontology = cls()
        for entry in data["skills"]:
            name = (entry.get("name") or "").strip()
            if not name:
                raise ValueError(f"Skill entry missing a name: {entry!r}")
            if name in ontology.skills:
                raise ValueError(f"Duplicate skill name in ontology: {name!r}")

            skill = Skill(
                name=name,
                category=entry.get("category", "uncategorized"),
                aliases=tuple(a.strip() for a in entry.get("aliases", []) if a.strip()),
                case_sensitive_aliases=tuple(
                    a.strip() for a in entry.get("case_sensitive_aliases", []) if a.strip()
                ),
            )
            ontology.skills[name] = skill

            for surface in (name, *skill.aliases, *skill.case_sensitive_aliases):
                key = _normalize_key(surface)
                existing = ontology._lookup.get(key)
                if existing is not None and existing != name:
                    raise ValueError(
                        f"Alias {surface!r} maps to both {existing!r} and {name!r}"
                    )
                ontology._lookup[key] = name

        return ontology

    @classmethod
    def load(cls, path: Optional[Path | str] = None) -> "SkillOntology":
        """Load an ontology JSON file (defaults to data/skill_ontology.json)."""
        path = Path(path) if path is not None else DEFAULT_ONTOLOGY_PATH
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def normalize(self, skill: str) -> Optional[str]:
        """Map a skill name or alias to its canonical name.

        This is an exact whole-string lookup (case-insensitive), intended for
        structured skill lists rather than free text.

        Returns:
            The canonical skill name, or None if the skill is not in the ontology.
        """
        if not skill or not skill.strip():
            return None
        return self._lookup.get(_normalize_key(skill))

    def category_of(self, skill: str) -> Optional[str]:
        """Return the category of a skill (name or alias), or None if unknown."""
        canonical = self.normalize(skill)
        return self.skills[canonical].category if canonical else None

    def __len__(self) -> int:
        return len(self.skills)


class SkillExtractor:
    """Extracts canonical skills from text using an ontology and regex matching."""

    def __init__(self, ontology: Optional[SkillOntology] = None) -> None:
        self.ontology = ontology if ontology is not None else SkillOntology.load()
        self._patterns: List[Tuple[re.Pattern[str], str, Optional[str]]] = (
            self._compile_patterns()
        )

    def _compile_patterns(self) -> List[Tuple[re.Pattern[str], str, Optional[str]]]:
        """Compile one regex per (alias, case-sensitivity) pair.

        Each entry is (regex, canonical_name, exclusion_key), where exclusion_key
        names a _CONTEXT_EXCLUSIONS entry for ambiguous case-sensitive aliases.
        """
        patterns: List[Tuple[re.Pattern[str], str, Optional[str]]] = []
        for skill in self.ontology.skills.values():
            case_sensitive = set(skill.case_sensitive_aliases)
            surfaces = [(a, True) for a in skill.case_sensitive_aliases]
            if skill.name not in case_sensitive:
                surfaces.append((skill.name, False))
            surfaces.extend((a, False) for a in skill.aliases)

            for surface, is_case_sensitive in surfaces:
                body = _alias_to_pattern(surface)
                if not body:
                    continue
                flags = 0 if is_case_sensitive else re.IGNORECASE
                regex = re.compile(_LEFT_BOUNDARY + body + _RIGHT_BOUNDARY, flags)
                exclusion = (
                    surface
                    if is_case_sensitive and surface in _CONTEXT_EXCLUSIONS
                    else None
                )
                patterns.append((regex, skill.name, exclusion))
        return patterns

    @staticmethod
    def _is_excluded(text: str, start: int, end: int, exclusion: Optional[str]) -> bool:
        """Return True if the surrounding context marks this match as non-skill."""
        if exclusion is None:
            return False
        before, after = _CONTEXT_EXCLUSIONS[exclusion]
        if before is not None and before.search(text[max(0, start - _CONTEXT_WINDOW):start]):
            return True
        if after is not None and after.match(text, end):
            return True
        return False

    def find_matches(self, text: str) -> List[Tuple[int, int, str]]:
        """Find non-overlapping skill mentions in text.

        Overlaps are resolved by preferring the longest span, then the earliest.

        Returns:
            List of (start, end, canonical_skill) sorted by start position.
            The same skill may appear more than once (one entry per mention).
        """
        if not text or not text.strip():
            return []

        candidates: List[Tuple[int, int, str]] = []
        for regex, skill_name, exclusion in self._patterns:
            for m in regex.finditer(text):
                if self._is_excluded(text, m.start(), m.end(), exclusion):
                    continue
                candidates.append((m.start(), m.end(), skill_name))

        # Longest first, then earliest, then by name for full determinism.
        candidates.sort(key=lambda c: (-(c[1] - c[0]), c[0], c[2]))

        accepted: List[Tuple[int, int, str]] = []
        for start, end, name in candidates:
            if all(end <= a_start or start >= a_end for a_start, a_end, _ in accepted):
                accepted.append((start, end, name))

        accepted.sort(key=lambda c: (c[0], c[1]))
        return accepted

    def extract(self, text: str) -> List[str]:
        """Extract unique canonical skills, in order of first appearance.

        Args:
            text: Resume or job description text.

        Returns:
            List of canonical skill names with duplicates removed.
        """
        seen: Dict[str, None] = {}
        for _, _, name in self.find_matches(text):
            seen.setdefault(name, None)
        return list(seen)


_default_extractor: Optional[SkillExtractor] = None


def get_default_extractor() -> SkillExtractor:
    """Return a cached extractor built from the default ontology file."""
    global _default_extractor
    if _default_extractor is None:
        _default_extractor = SkillExtractor()
    return _default_extractor


def extract_skills(text: str) -> List[str]:
    """Extract unique canonical skills from text using the default ontology."""
    return get_default_extractor().extract(text)
