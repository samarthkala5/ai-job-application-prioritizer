# Presentation Source Pack: AI-Based Job Application Prioritization System

Final-year engineering project review. Covers Phase 0 (baseline) and Phase 1 (skill matching and validation).

## Status key

Every claim in this pack carries one of these markers:

| Marker | Meaning |
|---|---|
| **[IMPLEMENTED]** | Code exists in the repository and is covered by passing unit tests |
| **[EVALUATED]** | Measured in the Phase 1 validation experiment; numbers are taken from `experiments/results/` |
| **[PLANNED]** | Not implemented; future work only |

## Ground rules followed in this pack

- Every number comes from a file in the repository. The source file is cited in each section.
- The Phase 1 reference relevance labels (`experiments/data/ground_truth.csv`) and the structured required/preferred skill lists (`experiments/data/job_requirements.json`) were **authored by the developer**. They are not independent annotations.
- The correlation results (skill coverage ρ = 0.88 vs semantic similarity ρ = 0.70) are **not** presented as proof that skill coverage is superior.

---

## 1. Title

**Slide title:** AI-Based Job Application Prioritization System: Baseline and Explicit Skill Matching

**Bullets:**
- Final-year engineering project: a decision-support tool for job seekers.
- Progress covered in this review:
  - **Phase 0:** semantic-similarity baseline **[IMPLEMENTED]**
  - **Phase 1:** deterministic skill extraction and matching **[IMPLEMENTED]**, with a validation experiment **[EVALUATED]**
- Covered as future work only: Phase 2 onwards (fit scoring, prioritisation, tracking, feedback) **[PLANNED]**.

**Recommended visual:**
- Title slide with the project name, student name, supervisor and date.
- A three-step strip underneath: "Phase 0 ✓ → Phase 1 ✓ → Phase 2+ (planned)".

**Numerical results:** none on this slide.

**Speaker notes:** Introduce the project as decision support, not automated hiring. State upfront that this review covers two completed phases. Everything after Phase 1 is a plan. The review will be explicit about what is built, what is measured, and what is still to come.

**Source:** `README.md` (Project Objective, Current Phase).

---

## 2. Objective

**Slide title:** Project Objective

**Bullets:**
- Help a job seeker decide **which jobs are worth applying to**, given their resume and a set of job descriptions.
- The end goal, as listed in `README.md` (all **[PLANNED]** beyond Phase 1):
  - overall fit score
  - skill-gap analysis
  - evidence-based matching
  - application priority ranking
  - preparation recommendations
  - outcome tracking and feedback learning
- Current objective for this review:
  - Build a reproducible baseline (Phase 0).
  - Add explicit, explainable skill matching (Phase 1).
  - Test whether skill matching adds information beyond the baseline.
- Design principle: scores are decision support. They are labelled as match signals, **not** probabilities of being hired.

**Recommended visual:** Two-column slide. Left: "End goal" (the six capabilities from the README, greyed out where planned). Right: "This review" (Phase 0 and Phase 1, highlighted).

**Numerical results:** none.

**Speaker notes:** The long-term objective is broad. Make clear that the review is about the foundations: can we represent resume–job relevance at all, and does an explicit skill signal tell us anything the semantic baseline does not? The design constraint in `similarity.py` says scores must not be read as probabilities or predictions of hiring success.

**Source:** `README.md`; docstring of `backend/matching/similarity.py` (design constraint); docstring of `backend/matching/skill_matcher.py`.

---

## 3. Problem & Motivation

**Slide title:** Why Job Prioritisation Is Hard

**Bullets:**
- Job seekers face many postings and limited time. Deciding *where to apply* is a ranking problem under uncertainty.
- Keyword search misses relevant jobs worded differently. Pure semantic similarity rewards *topic overlap*, not *capability*.
- Observed in our own validation:
  - An ML-engineer resume scores **0.65** semantic similarity against an embedded Edge-AI job, yet matches only **2 of 7** required skills.
  - Reference label for that pair: Weak.
- A single opaque score gives the user no reason and no gap list, so they cannot act on it.
- Motivation for Phase 1: add an **explainable** signal (which required skills are matched or missing) alongside the semantic one.

**Recommended visual:**
- Side-by-side "same score, different reality" example: the B_ml × Edge AI pair, with semantic similarity 0.65 next to its missing-skill list.
- Or use the existing plot `experiments/results/plots/5_disagreement_example.png`.

**Numerical results:** B_ml × job_10_edge_ai: semantic similarity 0.6517, required skill coverage 2/7 = 0.2857, reference label 1. Missing: C, C++, Embedded Systems, Linux, ARM.

**Speaker notes:** Use the concrete example rather than abstract claims. The embedding sees "vision", "models", "edge", "latency" in both documents and judges them similar. A recruiter would immediately see that the candidate cannot write embedded C/C++. That gap motivates explicit skill matching.

**Source:** `experiments/results/phase1_validation.csv` (row resume_B_ml, job_10_edge_ai); `experiments/results/phase1_validation_analysis.md` (Case A).

---

## 4. Proposed System

**Slide title:** Proposed System: Layered Decision Support

**Bullets:**
- **Layer 1, Input [IMPLEMENTED]:** resume upload (PDF/DOCX) or pasted text; job descriptions as text.
- **Layer 2, Semantic signal [IMPLEMENTED]:** SBERT (all-MiniLM-L6-v2) embeddings and cosine similarity.
- **Layer 3, Skill signal [IMPLEMENTED as backend module]:** ontology-based skill extraction and required-skill coverage with matched and missing lists.
- **Layer 4, Fit and priority [PLANNED]:** experience/project relevance, hybrid fit score, application priority ranking, preparation recommendations.
- **Layer 5, Learning loop [PLANNED]:** application tracking database and outcome-feedback personalisation.
- The signals are currently kept **separate**. No combined fit score exists yet.

**Recommended visual:** Layered stack diagram, with layers 1–3 solid and layers 4–5 dashed or greyed. Can be derived from `presentation/architecture_future.mmd`.

**Numerical results:** none.

**Speaker notes:** Present the full vision but be precise about status. Layer 3 exists as tested backend code but is **not yet wired into the Streamlit UI**; the UI still shows only Phase 0 semantic matching. Layers 4–5 come from the README's "Next Planned Components" list and are not started.

**Source:** `README.md` (Next Planned Components); `frontend/app.py` (docstring: shows only semantic similarity); `backend/matching/skill_extractor.py`; `backend/matching/skill_matcher.py`.

---

## 5. System Architecture

**Slide title:** Current Implemented Architecture

**Bullets:**
- **Parsing [IMPLEMENTED]:** PyMuPDF for PDF and python-docx for DOCX, both producing plain text (`backend/parsers/`).
- **Phase 0 path [IMPLEMENTED]:** text → all-MiniLM-L6-v2 → 384-dimensional embedding → cosine similarity → ranked jobs → Streamlit UI.
- **Phase 1 path [IMPLEMENTED, backend only]:**
  - Extraction: text → regex extractor with the skill ontology (`data/skill_ontology.json`) → canonical skills.
  - Matching: skill matcher → matched, missing and additional skills plus required skill coverage.
- **Validation harness [EVALUATED]:** `experiments/run_phase1_validation.py` runs both paths over 50 pairs and writes CSV, JSON and plots.
- **Not present [PLANNED]:** API layer, database, fit scoring, prioritisation, feedback.

**Recommended visual:**
- Render `presentation/architecture_current.mmd` (current state).
- On a later slide or as a backup, render `presentation/architecture_future.mmd` (planned).

**Numerical results:** Embedding dimension 384. Ontology: 100 skills, 180 aliases, 15 categories.

**Speaker notes:** Walk left to right through the current diagram and point out that the two scoring paths share the parsing step but are otherwise independent. The validation harness is experiment code, not application code; it calls the Phase 0 and Phase 1 functions unmodified.

**Source:** `backend/parsers/pdf_parser.py`, `backend/parsers/docx_parser.py`, `backend/matching/embeddings.py`, `backend/matching/similarity.py`, `backend/matching/skill_extractor.py`, `backend/matching/skill_matcher.py`, `frontend/app.py`, `data/skill_ontology.json`, `presentation/architecture_current.mmd`.

---

## 6. Baseline Design & Logic

**Slide title:** Phase 0 Baseline: Semantic Similarity Ranking

**Bullets:**
- **[IMPLEMENTED]** Resume text and each job description are encoded into **384-dimensional** vectors with all-MiniLM-L6-v2.
- Cosine similarity, clamped to [−1, 1], is computed per pair. Jobs are sorted in descending order and labelled "Semantic Match Score".
- Input validation: empty or whitespace-only text raises `ValueError`; embedding dimension mismatch raises `ValueError`; zero vectors return 0.0.
- Streamlit UI:
  - Inputs: paste text, upload PDF/DOCX, or pick one of 3 built-in sample resumes; compare against 5 sample jobs.
  - Output: a ranked list.
- Test coverage: **38 unit tests** (16 parser, 22 similarity), all passing.
- Known limitation:
  - Measures *textual/topic similarity only*; no skills, experience or explanation.
  - Input is truncated at 256 tokens (see Section 7).

**Recommended visual:** Simple pipeline (Resume → Embed → Cosine → Rank), plus a screenshot of the Streamlit ranked-results view. Taking the screenshot means running `streamlit run frontend/app.py`; none is stored in the repo.

**Numerical results:** 384-dimensional embeddings. 38/38 Phase 0 tests passing (16 in `tests/test_parsers.py`, 22 in `tests/test_similarity.py`).

**Speaker notes:** Explain why a baseline matters. It gives a reference point for every later phase. The output is deliberately labelled "Semantic Match Score" so users do not read it as a percentage chance of success. The README itself lists the baseline's limitations.

**Source:** `backend/matching/embeddings.py`; `backend/matching/similarity.py`; `frontend/app.py`; `tests/test_parsers.py`; `tests/test_similarity.py`; `README.md` (Limitations of Baseline).

---

## 7. Model Selection & Optimisation

**Slide title:** Model Choice and Engineering Optimisations

**Bullets:**
- **Model [IMPLEMENTED]:** `all-MiniLM-L6-v2` (Sentence-Transformers).
  - Produces a 384-dimensional sentence embedding.
  - A small model that runs on CPU (the installed PyTorch build is CPU-only).
- **Selection basis:** chosen as a lightweight, general-purpose sentence-embedding baseline. **No comparative benchmark against other embedding models has been run yet [PLANNED]**.
- **Optimisations [IMPLEMENTED]:**
  - The model is lazy-loaded once and cached at module level; a unit test checks it loads only once.
  - Texts are batch-encoded with `embed_texts`.
  - The Phase 1 extractor compiles each alias regex once and caches a default extractor.
- **Current limitation, 256-token truncation [EVALUATED]:**
  - The model's `max_seq_length` is **256** word-pieces.
  - Validation resumes are **447–750** word-pieces, so only about **34–57%** of each resume is embedded.
  - **7 of the 10** validation job descriptions also exceed 256.
- Mitigation is **not implemented**. Candidates for later (chunking and pooling, or section-wise embedding) are **[PLANNED]**.

**Recommended visual:** A single bar showing one resume's length against the 256-token window, with the embedded part shaded and the rest hatched as "never seen by Phase 0". Use the range figures below rather than per-document counts.

**Numerical results:**
- Embedding dimension 384; `max_seq_length` 256.
- Validation resumes are 447–750 word-pieces, so about 34–57% of each is embedded.
- 7 of 10 validation job descriptions exceed 256 word-pieces.

**Speaker notes:**
- Be candid that model selection was a pragmatic baseline choice, not the outcome of a model-comparison study.
- The most important finding here is truncation. For long resumes, Phase 0 never sees most of the experience section.
- The skill extractor reads the full text, which is one reason the two signals behave differently.
- Fixing truncation would change Phase 0, which is frozen for this review.

**Source:**
- `backend/matching/embeddings.py` (lazy load, batch encode).
- `tests/test_similarity.py` (`test_model_loads_only_once`).
- `experiments/results/phase1_validation_analysis.md` ("What Phase 1 Adds", point 5: truncation).
- Truncation figures (447–750 word-pieces, 34–57% embedded, 7 of 10 JDs over the limit) come from the analysis document. Per-document token counts are not stored in the repository; to show them, generate them by re-running the model tokenizer over `experiments/data/`.

---

## 8. Phase 1 — Skill Matching

**Slide title:** Phase 1: Deterministic, Explainable Skill Matching

**Bullets:**
- **Skill ontology [IMPLEMENTED]:** `data/skill_ontology.json`, with **100 skills**, **180 aliases** and **15 categories** (e.g. `sklearn` → scikit-learn, `k8s` → Kubernetes).
- **Extractor [IMPLEMENTED]:**
  - Case-insensitive matching; multi-word skills tolerate spaces, hyphens and line breaks.
  - Custom word boundaries, so "Java" ≠ "JavaScript" and "C" ≠ "C++".
  - Where matches overlap, the longest wins; duplicates are removed.
- **False-positive mitigation [IMPLEMENTED]:**
  - **13 case-sensitive aliases** for words that are also ordinary English (Go, C, React, Excel, REST, Spring, Express, Spark, ML, RAG, YOLO, ARM, Jest).
  - Context rules for the two most ambiguous: "Go-to" is not Go; "Grade C" is not C.
- **Matcher [IMPLEMENTED]:**
  - Outputs: matched skills, missing skills, additional skills, and **required skill coverage** = matched / required.
  - Coverage is `None` when a job has no recognised skills.
- **Tests:** 65 Phase 1 tests (49 extractor, 16 matcher), including 19 regression tests for the Go/C false positives. The full suite stands at **103/103** passing.
- **Known limitations:**
  - Fixed vocabulary.
  - Detects presence, not proficiency.
  - All skills weighted equally.
  - The deployed pipeline treats every skill in a job description as required; there is no required/preferred section parsing yet **[PLANNED]**.

**Recommended visual:**
- Worked example: one sentence of resume text with highlighted spans mapped to canonical skills, then a matched/missing table for one job.
- Suggested pair: B_ml × job_10_edge_ai, with matched Python and Computer Vision and missing C, C++, Embedded Systems, Linux, ARM.

**Numerical results:** 100 skills; 180 aliases; 15 categories; 13 case-sensitive aliases; 49 + 16 = 65 Phase 1 tests; 103 total tests passing.

**Speaker notes:**
- Stress *deterministic*: no LLM and no model, so the same input always gives the same output and every decision is auditable.
- The false-positive work came from review: "I go to work" or "react to feedback" must not become skills. Ambiguous short tokens therefore need exact casing, plus context rules for "Go-to" and "Grade C".

**Source:** `data/skill_ontology.json`; `backend/matching/skill_extractor.py` (`_CONTEXT_EXCLUSIONS`, boundary rules); `backend/matching/skill_matcher.py`; `tests/test_skill_extractor.py`; `tests/test_skill_matcher.py`.

---

## 9. Validation Methodology

**Slide title:** How Phase 1 Was Validated

**Bullets:**
- **Dataset [EVALUATED]:** **5 resumes × 10 jobs = 50 pairs**.
  - Resumes: backend, ML, frontend/full-stack, embedded, junior generalist.
  - Jobs: 7 pre-existing plus 3 added for this experiment (Full-Stack, AI Engineer, Edge-AI Embedded).
- **Two independent signals, never combined:**
  - Semantic similarity (Phase 0).
  - Required skill coverage (Phase 1), computed only over manually labelled `required_skills`. Preferred skills do not count; "X or Y" requirements are any-of groups.
- **Reference labels:** 0 = not relevant, 1 = weak, 2 = partial, 3 = strong, each with a written reason.
  - Distribution: 23 / 11 / 8 / 8.
  - **Both the labels and the required-skill lists were authored by the developer.** They are not independent annotations.
- **Metrics:**
  - Mean score per label.
  - Spearman ρ against the label.
  - Within-resume Spearman.
  - ROC AUC for label ≥ 2.
  - Per-resume NDCG@3 and NDCG@10, plus a top-1 check.
  - Comparison against expected random ranking.
- **Robustness check:** the analysis is repeated without the 4 "designed" pairs, where the resume's current employer is the job's company.

**Recommended visual:** Flow diagram: resumes and jobs → (a) Phase 0 similarity, (b) Phase 1 coverage, with manual labels as a third input → metrics and plots. Annotate the label box "developer-authored".

**Numerical results:**
- 50 pairs; label distribution {0: 23, 1: 11, 2: 8, 3: 8}; 4 designed pairs excluded in the robustness check (n = 46).
- Disagreement-category thresholds:
  - semantic terciles at 0.414 and 0.553
  - coverage low ≤ 0.30, high ≥ 0.60

**Speaker notes:**
- The labels were written before running either system on the new data and were not revised afterwards.
- Because one person wrote both the labels and the required-skill lists, coverage is expected to agree with the labels to some degree by construction. This is the most important caveat of the experiment and is stated again with the results.
- Pairs are not independent, since each resume appears 10 times, so p-values are not used as significance claims.

**Source:** `experiments/data/ground_truth.csv`; `experiments/data/job_requirements.json`; `experiments/run_phase1_validation.py`; `experiments/results/phase1_metrics.json` (`label_distribution`, `thresholds`, `spearman_excluding_designed_pairs`); `experiments/results/phase1_validation_analysis.md` (Experimental Setup, Ground Truth Methodology).

---

## 10. Results So Far

**Slide title:** Phase 1 Validation Results (Engineering Validation, n = 50)

**Bullets:**
- Both signals track the developer-authored reference labels, far above random ranking: NDCG@3 is **0.873** for semantic similarity and **0.967** for coverage, against **0.401** for random.
- Spearman ρ against the label:
  - semantic similarity **0.699** (bootstrap 95% CI 0.51–0.83)
  - skill coverage **0.882** (CI 0.80–0.93)
- Excluding the designed pairs (n = 46), ρ is **0.621** for semantic similarity and **0.855** for coverage.
- Semantic similarity **does not separate weak from partial** matches (mean 0.536 vs 0.538). Coverage does (0.356 vs 0.628).
- The signals are related but **not redundant**: ρ(semantic, coverage) = **0.752**.
- Semantic similarity ranked better for 2 of 5 resumes (NDCG@3: backend 0.978 vs 0.893; embedded 1.000 vs 0.952).
- **Interpretation:** the higher ρ for coverage is likely inflated by developer-authored labels and requirements. It is **not** proof that coverage is superior. The supported conclusion is that the two signals are **complementary**.

**Recommended visual:** Two side-by-side box plots:
- `experiments/results/plots/1_semantic_vs_label.png`
- `experiments/results/plots/2_coverage_vs_label.png`

Add a small metrics table underneath.

**Numerical results (exact values):**

| Metric | Semantic similarity | Required skill coverage |
|---|---|---|
| Spearman ρ vs label (n = 50) | 0.6989 | 0.8825 |
| Bootstrap 95% CI | 0.506 – 0.834 | 0.802 – 0.931 |
| Spearman ρ vs label, excluding designed pairs (n = 46) | 0.6206 | 0.8549 |
| Mean within-resume Spearman ρ | 0.7759 | 0.9022 |
| ROC AUC (label ≥ 2) | 0.8217 | 0.9660 |
| NDCG@3, mean over 5 resumes (random 0.4010) | 0.8727 | 0.9669 |
| NDCG@10, mean (random 0.6991) | 0.9490 | 0.9879 |
| Top-1 job has the best label | 0.8 (4/5) | 1.0 (5/5) |

Mean score by label:

| Label | n | Semantic mean | Coverage mean |
|---|---|---|---|
| 0 | 23 | 0.387 | 0.071 |
| 1 | 11 | 0.536 | 0.356 |
| 2 | 8 | 0.538 | 0.628 |
| 3 | 8 | 0.692 | 0.813 |

Correlation between the two signals: ρ(semantic, coverage) = 0.7524, or 0.6814 excluding designed pairs.

**Speaker notes:**
- Present this as engineering validation on a small controlled dataset.
- p-values exist in the metrics file, but pairs share resumes and jobs, so they overstate certainty. The bootstrap intervals are also too narrow for the same reason.
- The defensible statement is that both signals carry information and they disagree in interpretable ways, which the next slide shows.
- Do **not** say "skill coverage is 26% better".

**Source:** `experiments/results/phase1_metrics.json`; `experiments/results/phase1_validation.csv`; `experiments/results/plots/1_semantic_vs_label.png`; `experiments/results/plots/2_coverage_vs_label.png`; `experiments/results/phase1_validation_analysis.md` (Results); `presentation/phase1_results.md`.

---

## 11. Failure / Disagreement Analysis

**Slide title:** Where the Two Signals Disagree, and Why

**Bullets:**
- **Case A, high semantic + low coverage (3 pairs):** shared topic vocabulary inflates semantic similarity.
  - ML resume × Edge-AI job: **0.652** vs **2/7**, label 1.
  - Backend resume × ML job: **0.574** vs **3/11**, label 1.
  - Junior resume × Backend job: **0.564** vs **2/12**, label 1.
- **Case B, moderate semantic + high coverage (2 pairs):** coverage recovers matches worded in a different style.
  - ML resume × Data Analyst: **0.485** vs **4/6**, label 2.
  - ML resume × General SWE: **0.453** vs **2/3**, label 2.
  - Phase 0 ranks both below three label-1 jobs.
- **Case C, both high (11 pairs)** and **Case D, both low (14 pairs, all label 0):** the signals agree. No pair had low semantic similarity with high coverage.
- **Coverage failures:**
  - Backend × AI Engineer: **4/6** but label 1. Equal weighting lets Python/Docker/Git count as much as LLMs/RAG.
  - The ML resume lists GPT and LangChain but not "LLM", so LLMs is reported missing (ontology gap).
  - Frontend resume × General SWE: coverage **1/3**, label 3.
    - "Data Structures and Algorithms" is required, but no resume mentions it.
    - Git is missed because it only appears inside "GitHub Actions" (longest-match rule).
  - Junior resume × Frontend: "basic React tutorials" counts as React (presence, not proficiency).
- **Phase 0 failure:** for the junior resume, Phase 0 ranks Full-Stack (label 1) first and the Data Analyst job (label 2) 7th.

**Recommended visual:**
- Scatter plot `experiments/results/plots/3_semantic_vs_coverage.png`, with quadrants and coloured labels.
- Per-resume comparison `experiments/results/plots/5_disagreement_example.png` (ML resume).
- Backup: `experiments/results/plots/4_ranking_example.png` (junior resume ranking).

**Numerical results:**
- Category counts: A = 3, B = 2, low-semantic/high-coverage = 0, C = 11, D = 14.
- The remaining 20 pairs fall in intermediate bands.
- Pair values are exact from `phase1_validation.csv`:

  | Pair | Semantic | Coverage |
  |---|---|---|
  | B × 10 | 0.6517 | 0.2857 |
  | A × 02 | 0.5743 | 0.2727 |
  | E × 01 | 0.5644 | 0.1667 |
  | B × 03 | 0.4852 | 0.6667 |
  | B × 07 | 0.4528 | 0.6667 |
  | A × 09 | 0.5709 | 0.6667 (label 1) |
  | C × 07 | 0.3884 | 0.3333 (label 3) |
  | E × 08 | 0.6488 | 0.3333 (label 1; E's top semantic job) |

**Speaker notes:**
- This is the most important slide.
- Semantic similarity answers "are these documents about the same thing?"; coverage answers "are the required skills present?". Each fails in a characteristic way.
- Present the coverage failures with equal weight to the semantic ones. They define what Phase 2 must address: weighting, proficiency evidence, and vocabulary or implicit skills.

**Source:** `experiments/results/phase1_metrics.json` (`disagreement_categories`); `experiments/results/phase1_validation.csv`; `experiments/results/phase1_resume_skills.json`; `experiments/results/phase1_validation_analysis.md` (Disagreement Analysis, Failure Cases); plots 3, 4 and 5.

---

## 12. Challenges & Mitigation

**Slide title:** Engineering Challenges and How They Were Handled

**Bullets:**
- **Ambiguous skill words**, which create false positives:
  - Mitigated **[IMPLEMENTED]** with 13 case-sensitive aliases, context rules ("Go-to", "Grade C" and similar label words), custom boundaries for C/C++/C#, and longest-match overlap resolution.
  - Covered by 19 regression tests.
  - Residual risk: other label words not in the list, e.g. "Model C" and "C-suite".
- **Ontology coverage**, which causes false negatives:
  - Fixed 100-skill vocabulary; aliases such as GPT → LLMs are missing; implicit skills (Git via GitHub Actions) are not inferred.
  - Mitigation **[PLANNED]**: ontology expansion and alias review.
- **Required vs preferred skills:**
  - Handled in the experiment with manual structured labels and any-of groups.
  - The deployed matcher treats all JD skills as required. Automatic section parsing is **[PLANNED]**.
- **256-token embedding truncation:**
  - Identified **[EVALUATED]**, not mitigated.
  - Chunked or section-wise embedding is **[PLANNED]**, but needs a Phase 0 change.
- **Evaluation validity:**
  - Developer-authored labels create circularity, and the sample is small.
  - Mitigated by documenting it, a designed-pair robustness check, and making no significance claims.
  - Independent multi-annotator labels are **[PLANNED]**.
- **Maintenance:**
  - The `get_sentence_embedding_dimension` deprecation warning from sentence-transformers is noted but not yet fixed.
  - matplotlib was installed in the venv for plotting but is not listed in `requirements.txt`.

**Recommended visual:** Three-column table: Challenge | Mitigation | Status (Implemented / Documented / Planned).

**Numerical results:** 13 case-sensitive aliases; 19 regression tests for Go/C.

**Speaker notes:** Show the review cycle. After Phase 1, a review found "Go-to person" and "Grade C" false positives. They were fixed with the smallest targeted change, with legitimate cases ("written in Go", "C/C++") locked in by tests. Be equally open about the challenges that are only documented, especially truncation and label circularity.

**Source:** `backend/matching/skill_extractor.py`; `tests/test_skill_extractor.py` (`TestAmbiguousShortSkills`); `experiments/results/phase1_validation_analysis.md` (Limitations); `requirements.txt`; pytest warning output from `backend/matching/embeddings.py`.

---

## 13. Progress Status

**Slide title:** Progress Status: Implemented vs Evaluated vs Planned

**Bullets:**
- **Implemented and tested:**
  - PDF/DOCX parsing
  - SBERT embeddings and cosine ranking
  - Streamlit UI for Phase 0
  - Skill ontology, skill extractor and skill matcher
  - In total, **103 unit tests passing**
- **Experimentally evaluated:**
  - Phase 0 vs Phase 1 signals on 50 resume × job pairs
  - Disagreement analysis
  - Discovery of the 256-token truncation
- **Implemented but not yet integrated:** Phase 1 is not shown in the Streamlit UI.
- **Planned, not started:**
  - required/preferred section parsing
  - experience and project scoring
  - fit score
  - application priority
  - explainability UI
  - preparation recommendations
  - tracking database
  - feedback learning
- **Explicitly not built:** LLM-based components, API service (FastAPI), vector database, model fine-tuning.

**Recommended visual:** Status table with traffic-light colours (green = implemented, blue = evaluated, grey = planned).

**Numerical results:**

| Test file | Tests |
|---|---|
| `test_parsers.py` | 16 |
| `test_similarity.py` | 22 |
| `test_skill_extractor.py` | 49 |
| `test_skill_matcher.py` | 16 |
| **Total** | **103 passed, 0 failed** |

Phase 0 subset: 38/38.

**Speaker notes:** Be precise. Phase 1 exists as backend modules plus an offline validation experiment; a user of the current app does not see it yet. Nothing from Phase 2 onward exists in code.

**Source:** `tests/` (pytest run: 103 passed); `frontend/app.py`; `backend/`; `experiments/`; `README.md`.

| Component | Status | Evidence |
|---|---|---|
| PDF / DOCX parsing | Implemented | `backend/parsers/`, 16 tests |
| SBERT embedding + cosine ranking | Implemented | `backend/matching/embeddings.py`, `similarity.py`, 22 tests |
| Streamlit UI (semantic ranking only) | Implemented | `frontend/app.py` |
| Skill ontology (100 skills / 180 aliases) | Implemented | `data/skill_ontology.json` |
| Skill extractor + false-positive rules | Implemented | `skill_extractor.py`, 49 tests |
| Skill matcher (matched / missing / coverage) | Implemented | `skill_matcher.py`, 16 tests |
| Phase 1 in UI | Not integrated | `frontend/app.py` shows Phase 0 only |
| Phase 0 vs Phase 1 validation (50 pairs) | Evaluated | `experiments/results/` |
| 256-token truncation | Identified, not fixed | analysis document |
| Required/preferred section parsing | Planned | — |
| Experience / project relevance scoring | Planned | — |
| Hybrid fit score | Planned | — |
| Application priority ranking | Planned | — |
| Preparation recommendations | Planned | — |
| Application tracking database | Planned | — |
| Outcome feedback / personalisation | Planned | — |

---

## 14. Future Work & Development Plan

**Slide title:** Development Plan (All Items Planned)

**Bullets:**
- **Next, Phase 2 [PLANNED]:** close the gaps observed in validation:
  - Parse required vs preferred job sections.
  - Weight core skills above commodity skills.
  - Gather evidence of proficiency and recency from experience and project sections.
  - Expand the ontology and its aliases (e.g. GPT/LangChain → LLMs).
- **Address truncation [PLANNED]:** chunked or section-wise embedding of long resumes, evaluated against the current baseline on the same 50 pairs.
- **Fit and priority [PLANNED]:**
  - Combine the signals into a fit score only after independent validation.
  - Then add application priority ranking and preparation recommendations based on missing skills.
- **Product [PLANNED]:**
  - Show matched and missing skills in the Streamlit UI.
  - Add an application tracking database and an outcome-feedback loop.
- **Evaluation [PLANNED]:**
  - Larger and more realistic resume/JD set.
  - Independent multi-annotator labels with agreement measured.
  - Re-run the same validation harness.

**Recommended visual:** Roadmap timeline (Phase 0 ✓ → Phase 1 ✓ → Phase 2 → Phase 3+), rendered from `presentation/architecture_future.mmd` with planned components dashed.

**Numerical results:** none; these are plans. Do not present target numbers.

**Speaker notes:**
- Tie each future item to an observed failure:
  - equal weighting → A × AI Engineer
  - vocabulary → missing LLMs for the ML resume
  - proficiency → "basic React"
  - truncation → 34–57% of each resume embedded
  - labels → circularity
- This shows the plan is driven by evidence rather than a feature wish-list. Note that the README originally planned LLM-based extraction; the current implementation chose a deterministic ontology approach, and any LLM component remains an open design decision.

**Source:** `README.md` (Next Planned Components); `experiments/results/phase1_validation_analysis.md` (Failure Cases, Limitations); `presentation/phase1_results.md` (Why Phase 2 is necessary); `presentation/architecture_future.mmd`.

---

## 15. Conclusion

**Slide title:** Conclusion

**Bullets:**
- **Implemented:**
  - A working semantic-similarity baseline (Phase 0).
  - A deterministic, explainable skill extraction and matching layer (Phase 1): 100 skills, 180 aliases, false-positive mitigation, **103/103 tests passing**.
- **Evaluated:** on 50 resume × job pairs, both signals track the developer-authored labels:
  - semantic similarity ρ = 0.70
  - skill coverage ρ = 0.88
- That gap is **not** evidence that coverage is superior, because the labels and requirements were authored by the developer.
- The supported finding: the signals are **complementary**.
  - Semantic similarity is fooled by shared topic vocabulary.
  - Coverage is fooled by vocabulary gaps, equal weighting and presence-only matching.
- Phase 1's clearest, label-independent contribution is an **explicit list of matched and missing required skills** for every job.
- **Planned:**
  - Fix truncation, weighting, proficiency evidence and section parsing.
  - Validate with independent labels before building any combined fit score.

**Recommended visual:** Three-box summary: "Built" | "Learned" | "Next". Reuse the scatter plot thumbnail `3_semantic_vs_coverage.png`.

**Numerical results:** Spearman ρ vs label: 0.70 (semantic), 0.88 (coverage), with the stated caveats. Signal correlation 0.75. 103/103 tests passing.

**Speaker notes:** Close on the engineering lesson. A semantic score alone is not enough to prioritise applications, and neither is a skill checklist. Each covers the other's blind spots. The next phase will add evidence and weighting, and will be validated more rigorously than this phase could be.

**Source:** `experiments/results/phase1_metrics.json`; `experiments/results/phase1_validation_analysis.md` (Conclusions); `presentation/phase1_results.md`; `tests/`.

---

## Appendix: Source file index

| File | Content |
|---|---|
| `README.md` | Project objective, baseline description, planned components |
| `backend/parsers/pdf_parser.py`, `docx_parser.py` | Phase 0 parsing |
| `backend/matching/embeddings.py`, `similarity.py` | Phase 0 semantic similarity |
| `backend/matching/skill_extractor.py`, `skill_matcher.py` | Phase 1 skill extraction and matching |
| `data/skill_ontology.json` | 100-skill ontology |
| `frontend/app.py` | Streamlit UI (Phase 0 only) |
| `tests/*.py` | 103 unit tests |
| `experiments/data/job_requirements.json` | Developer-authored required/preferred skills |
| `experiments/data/ground_truth.csv` | Developer-authored reference labels (50 pairs) |
| `experiments/run_phase1_validation.py` | Validation harness |
| `experiments/results/phase1_validation.csv` | Per-pair results |
| `experiments/results/phase1_metrics.json` | All metrics |
| `experiments/results/phase1_resume_skills.json` | Extracted resume skills |
| `experiments/results/plots/1–5_*.png` | Figures |
| `experiments/results/phase1_validation_analysis.md` | Full analysis |
| `presentation/phase1_results.md` | Short results summary |
| `presentation/architecture_current.mmd` | Current architecture diagram |
| `presentation/architecture_future.mmd` | Planned architecture diagram |
