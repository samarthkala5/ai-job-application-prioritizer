"""Streamlit UI for the AI Job Application Prioritization System.

This is the BASELINE implementation showing ONLY semantic similarity matching.
It does NOT yet implement skill extraction, skill-gap analysis, fit scoring,
or application prioritization.
"""

from __future__ import annotations

import streamlit as st

# Import from backend modules
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from parsers.pdf_parser import PDFParser, parse_pdf
from parsers.docx_parser import DOCXParser, parse_docx
from matching.similarity import rank_jobs, format_score, get_embedding_dimension


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------
SAMPLE_JOBS = [
    {
        "id": "job1",
        "title": "Software Engineer",
        "description": "We are hiring a software engineer with 3+ years of Python and Django experience. Must have strong knowledge of REST APIs, PostgreSQL, and Git workflows. Experience with AWS cloud services is a plus.",
    },
    {
        "id": "job2",
        "title": "Machine Learning Engineer",
        "description": "Looking for an ML engineer with deep expertise in PyTorch, TensorFlow, and scikit-learn. Should have experience building and deploying neural networks for NLP and computer vision tasks.",
    },
    {
        "id": "job3",
        "title": "Data Analyst",
        "description": "Seeking a data analyst with proficiency in SQL, Excel, Tableau, and Python (Pandas, NumPy). Responsibilities include data cleaning, visualization, and dashboard creation for business stakeholders.",
    },
    {
        "id": "job4",
        "title": "Embedded Systems Engineer",
        "description": "Hiring an embedded engineer with experience in C/C++, microcontrollers (ARM, AVR), RTOS, sensor interfacing, and firmware development. Knowledge of PCB design and testing is a plus.",
    },
    {
        "id": "job5",
        "title": "Backend Engineer",
        "description": "Looking for a backend engineer with strong Node.js/Express or Go experience. Must have worked with MongoDB or PostgreSQL, message queues (RabbitMQ/Kafka), and Docker containerization.",
    },
]

SAMPLE_RESUMES = {
    "Software Developer Resume": """
John Doe
Software Developer

Summary:
Experienced Python developer with 4 years working on web applications using Django and Flask. Built REST APIs and microservices deployed on AWS. Comfortable with PostgreSQL, Redis, and Docker.

Skills:
- Languages: Python (3+ years), JavaScript (2 years), SQL
- Web: Django, Flask, FastAPI, React (basic)
- Databases: PostgreSQL, MySQL, MongoDB
- DevOps: Docker, AWS (EC2, S3, Lambda), Git
- Testing: pytest, unit tests, integration tests

Experience:
- Backend Developer at Tech Corp (2 years)
  - Built REST APIs handling 10k+ requests/day
  - Implemented CI/CD pipelines using GitHub Actions
  - Optimized database queries reducing latency by 40%

- Junior Developer at StartupX (2 years)
  - Developed internal tools using Django and React
  - Maintained PostgreSQL database with automated backups
""",
    "ML / Data Scientist Resume": """
Jane Smith
Machine Learning Engineer

Summary:
MSc in Data Science with 3 years experience building ML pipelines and deploying models. Specialized in NLP and computer vision using PyTorch and TensorFlow. Published 2 papers at NeurIPS.

Skills:
- ML/DL: PyTorch, TensorFlow, scikit-learn, transformers
- Languages: Python (expert), R (intermediate), SQL
- Data: Pandas, NumPy, Spark, Hadoop
- Tools: MLflow, Docker, Kubernetes, Airflow
- Experience: NLP (BERT, GPT), Computer Vision (CNN, YOLO)

Experience:
- ML Engineer at AI Corp (2 years)
  - Built BERT-based text classification achieving 95% accuracy
  - Deployed models on AWS SageMaker with auto-scaling
  - Collaborated with data engineers on feature pipelines

- Data Scientist at Research Lab (1 year)
  - Developed CNN models for medical image segmentation
  - Published 2 papers at NeurIPS and ICML
""",
    "Data Analyst Resume": """
Alice Johnson
Data Analyst

Summary:
3 years of experience in business intelligence and data analysis. Proficient in SQL, Excel, and Tableau with strong communication skills. Experience building dashboards for non-technical stakeholders.

Skills:
- Data: SQL (expert), Excel (advanced), Python (Pandas, NumPy)
- Visualization: Tableau, Power BI, Matplotlib, Seaborn
- Tools: Git, Jupyter, Google Analytics, Looker
- Soft skills: Communication, stakeholder management, reporting

Experience:
- Data Analyst at Analytics Corp (2 years)
  - Created 15+ Tableau dashboards for executive reporting
  - Wrote complex SQL queries for 3M+ row datasets
  - Automated weekly KPI reports using Python scripts

- Junior Analyst at StartupY (1 year)
  - Cleaned and processed survey data using Excel and R
  - Built first dashboard for sales team tracking
""",
}


def _parse_file(file_bytes: bytes, extension: str) -> str:
    """Parse uploaded file bytes based on extension.

    Args:
        file_bytes: Raw file content as bytes.
        extension: File extension (e.g., '.pdf', '.docx').

    Returns:
        Extracted text as a string.

    Raises:
        ValueError: If the extension is not supported.
    """
    if extension == ".pdf":
        return parse_pdf(file_bytes)
    elif extension == ".docx":
        return parse_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file extension: {extension}")


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------
def main() -> None:
    """Main Streamlit application."""
    st.set_page_config(
        page_title="AI Job Application Prioritizer",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🎯 AI-Based Job Application Prioritization System")
    st.markdown("### Baseline: Semantic Similarity Matching")

    # Show model info in sidebar
    with st.sidebar:
        st.header("Settings")
        st.markdown("**Model:** `all-MiniLM-L6-v2`")
        st.markdown(f"**Embedding dim:** {get_embedding_dimension()}")
        st.markdown("**Similarity:** Cosine")
        st.markdown("---")
        st.markdown("⚠️ **This is a BASELINE.** Scores are semantic similarity only, NOT fit percentages or hiring probabilities.")

    # Upload / paste resume
    st.subheader("📄 Your Resume")
    resume_text = st.text_area(
        "Paste your resume text here, or upload a PDF/DOCX file:",
        height=200,
        placeholder="Paste resume text or upload a file...",
    )

    uploaded_file = st.file_uploader(
        "Or upload a resume file (PDF/DOCX)",
        type=["pdf", "docx"],
        help="Accepted formats: PDF, DOCX",
    )

    # Handle file upload
    if uploaded_file is not None:
        try:
            file_bytes = uploaded_file.read()
            extension = Path(uploaded_file.name).suffix.lower()
            resume_text = _parse_file(file_bytes, extension)
            st.success(f"✅ Extracted text from {uploaded_file.name}")
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")
            resume_text = ""

    # Sample resume selection
    st.markdown("**Or select a sample resume:**")
    sample_resume_key = st.selectbox(
        "Sample resumes",
        options=["(none)"] + list(SAMPLE_RESUMES.keys()),
        index=0,
    )
    if sample_resume_key != "(none)":
        resume_text = SAMPLE_RESUMES[sample_resume_key]
        st.info(f"Loaded sample resume: {sample_resume_key}")

    st.divider()

    # Select job descriptions to match against
    st.subheader("💼 Job Descriptions to Compare")
    job_options = {job["title"]: job for job in SAMPLE_JOBS}
    selected_titles = st.multiselect(
        "Select job descriptions to match against:",
        options=[j["title"] for j in SAMPLE_JOBS],
        default=[j["title"] for j in SAMPLE_JOBS],
        help="Select all 5 jobs for baseline evaluation",
    )

    selected_jobs = [job_options[t] for t in selected_titles]

    # Run matching
    if st.button("🚀 Run Semantic Matching", type="primary", use_container_width=True):
        if not resume_text or not resume_text.strip():
            st.warning("⚠️ Please paste or upload a resume first.")
            return

        if not selected_jobs:
            st.warning("⚠️ Please select at least one job description.")
            return

        job_texts = [job["description"] for job in selected_jobs]

        try:
            # Run ranking
            ranked = rank_jobs(resume_text, job_texts, resume_title="Resume")

            # Display results
            st.subheader("🏆 Ranked Results")
            st.markdown(f"**Semantic Match Scores** (cosine similarity, range 0-1)")
            st.markdown("---")

            for item in ranked:
                score = item["semantic_match_score"]
                score_str = format_score(score)
                rank = item["rank"]
                title = item["job_title"]

                # Color code based on score
                if score >= 0.7:
                    color = "🟢"
                    label = "High match"
                elif score >= 0.5:
                    color = "🟡"
                    label = "Medium match"
                else:
                    color = "🔴"
                    label = "Low match"

                st.markdown(
                    f"{color} **#{rank} — {title}** "
                    f"(Semantic Match: {score_str}, {label})"
                )
                st.progress(min(score, 1.0))

            st.divider()

            # Show comparison table
            st.subheader("📊 Detailed Results")
            result_data = []
            for item in ranked:
                result_data.append({
                    "Rank": item["rank"],
                    "Job Title": item["job_title"],
                    "Semantic Match Score": format_score(item["semantic_match_score"]),
                    "Score (raw)": round(item["semantic_match_score"], 4),
                })

            st.table(result_data)

        except Exception as e:
            st.error(f"❌ Error during matching: {e}")
            st.exception(e)

    # Show job descriptions for reference
    with st.expander("📋 View Sample Job Descriptions"):
        for job in SAMPLE_JOBS:
            with st.expander(f"📌 {job['title']}"):
                st.text(job["description"])

    # Show sample resumes
    with st.expander("📄 View Sample Resumes"):
        for name in SAMPLE_RESUMES.keys():
            with st.expander(f"📄 {name}"):
                st.text(SAMPLE_RESUMES[name][:500] + "...")

    # Footer
    st.divider()
    st.caption(
        "AI-Based Job Application Prioritization System — Baseline Phase 0. "
        "Semantic similarity only. Not for hiring decisions."
    )


if __name__ == "__main__":
    main()