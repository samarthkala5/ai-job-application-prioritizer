# Phase 1 Results: Semantic Similarity vs. Explicit Skill Matching

**Setup:** 5 resumes × 10 jobs = 50 pairs, each with a manual reference label from 0 (not relevant) to 3 (strong).

The two signals are compared side by side and never combined:

- **Semantic similarity (Phase 0):** SBERT cosine similarity.
- **Required skill coverage (Phase 1):** the share of required skills present in the resume.

## Key numerical findings

| | Semantic similarity | Skill coverage |
|---|---|---|
| Spearman ρ vs reference label | 0.70 | 0.88 |
| ρ excluding 4 designed "obvious" pairs | 0.62 | 0.85 |
| NDCG@3 (random = 0.40) | 0.87 | 0.97 |
| Best job ranked #1 | 4 / 5 resumes | 5 / 5 resumes |
| Mean, weak matches (label 1) | 0.536 | 0.36 |
| Mean, partial matches (label 2) | 0.538 | 0.63 |

- The two signals correlate with each other at ρ = 0.75. They are related, but not redundant.
- Semantic similarity cannot separate weak from partial matches (0.536 vs 0.538).
- Small sample, single annotator: these figures are an **engineering validation, not a statistical proof**.

## 3 strongest examples (both signals agree)

| Resume × Job | Semantic | Coverage | Label |
|---|---|---|---|
| Backend engineer × Backend Software Engineer | 0.87 | 12/12 | Strong |
| ML engineer × AI Engineer (LLM apps) | 0.64 | 5/6 | Strong |
| Frontend/full-stack × Full-Stack Engineer | 0.63 | 4/6 | Strong |

## 3 strongest disagreement / failure examples

1. **ML engineer × Edge-AI Embedded role:** semantic 0.65 (ranked 3rd for this resume), coverage 2/7, label Weak.
   - Shared vocabulary ("vision", "models", "edge", "latency") inflates semantic similarity.
   - Phase 1 shows exactly what's missing: **C, C++, Embedded Systems, Linux, ARM**.
2. **ML engineer × Data Analyst:** semantic 0.49 (ranked *below* three Weak jobs), coverage 4/6, label Partial.
   - The resume and JD are written in different styles, but the explicit skills are present (SQL, Python, Pandas, NumPy).
   - Coverage recovers this match.
3. **Backend engineer × AI Engineer: a failure of coverage.** Coverage is 4/6, but the label is Weak.
   - The matched skills are generic (Python, FastAPI, Docker, Git); the skills that define the role (LLMs, RAG) are missing.
   - Equal skill weighting over-rates commodity skills.

## Main limitation of Phase 0

- A single opaque number that measures **topic similarity, not capability**. Shared domain vocabulary produces high scores for unqualified candidates.
- It gives no explanation of *why* a job matches or what is missing.
- The model reads only the first **256 tokens**, roughly 35–57% of each resume, so most of the experience section is never seen.

## What Phase 1 adds

- **Explainability:** an explicit list of matched and missing required skills for every resume × job pair.
- **Discrimination** between weak and partial matches, which semantic similarity cannot provide.
- **Detection** of "same topic, wrong skills" jobs, and recovery of "different wording, right skills" jobs.
- **Deterministic and auditable:** 100-skill ontology, 180 aliases, 103 unit tests.

**Conclusion:** the signals are **complementary**, not competing. Each catches errors the other makes.

## Why Phase 2 is necessary

Phase 1 coverage has clear, observed blind spots:

- **Presence ≠ proficiency:** "basic React tutorials" counts the same as "5 years expert React".
- **Equal weighting:** core skills (LLMs, RAG) count no more than commodity skills (Git, Docker).
- **Required vs preferred:** in this experiment they were labelled by hand; the current pipeline treats every JD skill as required.
- **Vocabulary and implicit skills:** GPT/LangChain were not recognised as LLMs, and "GitHub Actions" did not count as Git.
- **No experience or project evidence:** seniority, recency and depth are ignored.
- **Labelling:** independent multi-annotator labels are needed to validate any combined fit score.

Phase 2 needs to address evidence-based, weighted assessment of skills and experience. It must be validated against independent labels.
