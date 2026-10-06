# AI-Based Job Application Prioritization System

## Project Objective
This is a final-year engineering project to build an AI decision-support system that helps job seekers decide which jobs are worth applying to by providing:
- Overall fit score
- Skill gap analysis
- Evidence-based matching
- Application priority ranking
- Preparation recommendations
- Outcome tracking and feedback learning

## Current Phase: BASELINE (Phase 0)
This is the **baseline implementation** that focuses ONLY on:
1. Text extraction from resume files (PDF/DOCX)
2. SBERT embedding generation
3. Cosine similarity calculation
4. Job ranking by semantic similarity

This baseline does NOT yet implement:
- Structured skill extraction
- Skill-gap analysis
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
- No skill-based matching
- No experience or project relevance considered
- No explainability or evidence for scores
- Scores should not be interpreted as probabilities or percentages of success
- Intended only as a starting point for comparison with enhanced approaches

## Next Planned Components
1. Structured skill extraction (LLM-based)
2. Skill ontology and normalization
3. Skill-gap analysis
4. Experience and project relevance scoring
5. Hybrid fit scoring formula
6. Application priority ranking
7. Preparation recommendations
8. Application tracking database
9. Outcome feedback and personalization