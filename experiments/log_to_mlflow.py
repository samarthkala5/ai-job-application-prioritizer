"""Log the Phase 1 validation results to MLflow.

Run the experiment first, then this script, from the project root:
  python experiments/run_phase1_validation.py
  python experiments/log_to_mlflow.py
  mlflow ui          # open http://127.0.0.1:5000 and compare runs

Each invocation creates one MLflow run holding the dataset size, the model
name, every headline metric for both ranking signals, and the output files.
"""

from __future__ import annotations

import json
from pathlib import Path

import mlflow

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "experiments" / "results"

metrics = json.loads((RESULTS / "phase1_metrics.json").read_text())

mlflow.set_experiment("job-ranker-phase1-validation")

with mlflow.start_run():
    mlflow.log_params(
        {
            "embedding_model": "all-MiniLM-L6-v2",
            "n_resumes": metrics["n_resumes"],
            "n_jobs": metrics["n_jobs"],
            "n_pairs": metrics["n_pairs"],
            "coverage_high": metrics["thresholds"]["coverage_high"],
            "coverage_low": metrics["thresholds"]["coverage_low"],
        }
    )

    for signal in ("semantic", "coverage"):
        ranking = metrics["ranking_mean"][signal]
        mlflow.log_metrics(
            {
                f"{signal}_ndcg_at_3": ranking["ndcg@3"],
                f"{signal}_ndcg_at_10": ranking["ndcg@10"],
                f"{signal}_top1_best_label": ranking["top1_best_label"],
                f"{signal}_spearman_vs_label": metrics[f"spearman_{signal}_vs_label"]["rho"],
                f"{signal}_roc_auc": metrics["roc_auc_relevant_label_ge2"][signal],
            }
        )
    mlflow.log_metric("random_ndcg_at_3", metrics["ranking_mean"]["random_expected"]["ndcg@3"])

    for name in (
        "phase1_metrics.json",
        "phase1_validation.csv",
        "phase1_validation_analysis.md",
    ):
        mlflow.log_artifact(str(RESULTS / name))
    plots = RESULTS / "plots"
    if plots.exists():
        mlflow.log_artifacts(str(plots), artifact_path="plots")

print("Logged to MLflow. View with: mlflow ui")
