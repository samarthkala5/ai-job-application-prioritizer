# AI-Based Job Application Prioritization System

## Project Objective
This is a final-year engineering project to build an AI decision-support system that helps job seekers decide which jobs are worth applying to by providing:
- Overall fit score
- Skill gap analysis
- Evidence-based matching
- Application priority ranking
- Preparation recommendations
- Outcome tracking and feedback learning

## Current Status
**Phase 0 (baseline, in the Streamlit app):**
1. Text extraction from resume files (PDF/DOCX)
2. SBERT embedding generation
3. Cosine similarity calculation
4. Job ranking by semantic similarity

**Phase 1 (backend modules, validated offline, not yet wired into the Streamlit UI):**
1. Ontology-based skill extraction (100-skill ontology, `backend/matching/skill_extractor.py`)
2. Matched and missing required skills per resume-job pair (`backend/matching/skill_matcher.py`)
3. A validation experiment comparing both signals against reference relevance labels (see below)

**Not implemented yet:**
- Evidence analysis
- Fit scoring
- Application prioritization
- Preparation recommendations
- Application tracking
- Feedback learning

## Architecture
```
Resume Upload
    ↓
Text Extraction (PyMuPDF/python-docx)
    ↓
SBERT Embedding (all-MiniLM-L6-v2)
    ↓
Cosine Similarity (scikit-learn)
    ↓
Ranked Results Display (Streamlit)
```

## Installation
1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
4. Install dependencies: `pip install -r requirements.txt`
5. Download sample data: Place 3 resumes in `data/resumes/` and 5 job descriptions in `data/jobs/`
6. Run the application: `streamlit run frontend/app.py`

## How the Baseline Works
1. User uploads a resume (PDF/DOCX) or pastes text
2. System extracts text using appropriate parser
3. Text is encoded into a 384-dimensional vector using all-MiniLM-L6-v2
4. Job descriptions are similarly encoded
5. Cosine similarity is computed between resume and each job description
6. Results are displayed ranked by similarity score (labeled as "Semantic Match Score")

## Technical Details
- **Embedding Model**: all-MiniLM-L6-v2 (Sentence Transformers)
- **Embedding Dimension**: 384
- **Similarity Metric**: Cosine similarity (range: -1 to 1, displayed as 0-1)
- **Text Extraction**: PyMuPDF for PDF, python-docx for DOCX
- **UI Framework**: Streamlit

## Limitations of Baseline
- Semantic similarity alone does not indicate job fit quality
- The app itself does not use skill matching yet (Phase 1 lives in the backend modules)
- No experience or project relevance considered
- No explainability or evidence for scores
- Scores should not be interpreted as probabilities or percentages of success
- Intended only as a starting point for comparison with enhanced approaches

## Validation Results
`experiments/run_phase1_validation.py` ranks 10 jobs for each of 5 resumes (50 pairs) with two independent signals and compares them to reference relevance labels (0 to 3). Full write-up: [`experiments/results/phase1_validation_analysis.md`](experiments/results/phase1_validation_analysis.md).

| Metric | Semantic similarity | Skill coverage | Random |
|---|---|---|---|
| NDCG@3 | 0.87 | 0.97 | 0.40 |
| Top-1 job has the best label | 4 / 5 | 5 / 5 | - |
| ROC AUC (label >= 2) | 0.82 | 0.97 | - |

**Caveat:** the same annotator wrote the required-skill lists and the labels, so coverage's advantage is partly circular. Independent human labels are needed before drawing strong conclusions. This is a small, controlled dataset, not a statistically definitive study.

## Testing, CI, Docker and experiment tracking
- **Tests:** `python -m pytest tests -q`
- **CI:** GitHub Actions runs the tests and builds the Docker image on every push (`.github/workflows/ci.yml`).
- **Docker:** `docker build -t job-prioritizer .` then `docker run -p 8501:8501 job-prioritizer`
- **MLflow:** `pip install -r experiments/requirements.txt`, then `python experiments/log_to_mlflow.py` and `mlflow ui` to browse the logged metrics and result files.

## Next Planned Components
1. Wire skill matching into the Streamlit app
2. Skill-gap analysis in the UI
3. Experience and project relevance scoring
4. Hybrid fit scoring formula
5. Application priority ranking
6. Preparation recommendations
7. Application tracking database
8. Outcome feedback and personalization
