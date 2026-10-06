"""Phase 1 validation experiment: semantic similarity vs. required skill coverage.

Compares two INDEPENDENT signals against manual reference relevance labels:
  1. Semantic similarity (Phase 0: all-MiniLM-L6-v2 + cosine similarity)
  2. Required skill coverage (Phase 1: ontology extraction + skill matching)

The signals are deliberately NOT combined into a single score.

Inputs (experiments/data/):
  resumes/*.txt, jobs/*.txt, job_requirements.json, ground_truth.csv
Outputs (experiments/results/):
  phase1_validation.csv, phase1_metrics.json, phase1_resume_skills.json, plots/*.png

Run from the project root:
  venv/Scripts/python.exe experiments/run_phase1_validation.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Union

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import ndcg_score, roc_auc_score

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from matching.embeddings import embed_texts  # noqa: E402  (Phase 0)
from matching.similarity import compute_cosine_similarity  # noqa: E402  (Phase 0)
from matching.skill_extractor import get_default_extractor  # noqa: E402  (Phase 1)
from matching.skill_matcher import match_skills  # noqa: E402  (Phase 1)

DATA = ROOT / "experiments" / "data"
RESULTS = ROOT / "experiments" / "results"
PLOTS = RESULTS / "plots"

# Disagreement category thresholds.
# Cosine similarity has no absolute scale, so semantic bands are dataset terciles.
# Coverage is a proportion, so fixed bands are used.
COV_HIGH = 0.60
COV_LOW = 0.30

# Resumes used for the example figures (chosen for illustration only;
# all metrics use every pair).
RANKING_EXAMPLE_RESUME = "resume_E_general"
DISAGREEMENT_EXAMPLE_RESUME = "resume_B_ml"

# Pre-existing pairs where the resume's current employer is the job's company
# (designed one-to-one matches). Reported separately as a robustness check.
DESIGNED_PAIRS = {
    ("resume_A_backend", "job_01_backend"), ("resume_B_ml", "job_02_ml"),
    ("resume_C_frontend", "job_05_frontend"), ("resume_D_embedded", "job_06_embedded"),
}

BOOTSTRAP_SAMPLES = 2000
RANDOM_SEED = 42

LABEL_NAMES = {0: "0 Not relevant", 1: "1 Weak", 2: "2 Partial", 3: "3 Strong"}
LABEL_COLORS = {0: "#b0b0b0", 1: "#f2a65a", 2: "#5b9bd5", 3: "#2e7d32"}

RequiredEntry = Union[str, List[str]]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_texts(folder: Path, pattern: str) -> Dict[str, str]:
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted(folder.glob(pattern))}


def job_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.lower().startswith("title:"):
            return line.split(":", 1)[1].strip()
    return fallback


def load_requirements() -> Dict[str, dict]:
    data = json.loads((DATA / "job_requirements.json").read_text(encoding="utf-8"))
    ontology = get_default_extractor().ontology
    for job_id, req in data["jobs"].items():
        for entry in req["required_skills"] + req["preferred_skills"]:
            for name in (entry if isinstance(entry, list) else [entry]):
                if ontology.normalize(name) is None:
                    raise ValueError(f"{job_id}: {name!r} is not in the skill ontology")
    return data["jobs"]


def load_ground_truth() -> Dict[tuple, dict]:
    with open(DATA / "ground_truth.csv", encoding="utf-8", newline="") as f:
        return {
            (r["resume_id"], r["job_id"]): {"label": int(r["relevance_label"]), "reason": r["reason"]}
            for r in csv.DictReader(f)
        }


def resolve_required(required: Sequence[RequiredEntry], resume_skills: List[str]) -> List[str]:
    """Collapse any-of groups to one skill name each, without changing the matcher.

    A group resolves to the first member the resume has; if none, it resolves to
    a label like "PyTorch or TensorFlow" that is not in the ontology and is
    therefore reported as missing by match_skills.
    """
    ontology = get_default_extractor().ontology
    have = {s.casefold() for s in resume_skills}
    resolved: List[str] = []
    for entry in required:
        if isinstance(entry, str):
            resolved.append(entry)
            continue
        canonical = [ontology.normalize(s) or s for s in entry]
        hit = next((s for s in canonical if s.casefold() in have), None)
        resolved.append(hit if hit is not None else " or ".join(canonical))
    return resolved


# ---------------------------------------------------------------------------
# Experiment
# ---------------------------------------------------------------------------
def run() -> List[dict]:
    resumes = load_texts(DATA / "resumes", "resume_*.txt")
    jobs = load_texts(DATA / "jobs", "job_*.txt")
    requirements = load_requirements()
    truth = load_ground_truth()

    missing_req = set(jobs) - set(requirements)
    if missing_req:
        raise ValueError(f"No structured requirements for: {sorted(missing_req)}")

    extractor = get_default_extractor()
    resume_skills = {rid: extractor.extract(text) for rid, text in resumes.items()}

    resume_ids, job_ids = list(resumes), list(jobs)
    resume_emb = dict(zip(resume_ids, embed_texts([resumes[r] for r in resume_ids])))
    job_emb = dict(zip(job_ids, embed_texts([jobs[j] for j in job_ids])))

    rows: List[dict] = []
    for rid in resume_ids:
        for jid in job_ids:
            if (rid, jid) not in truth:
                raise ValueError(f"No ground-truth label for ({rid}, {jid})")
            required = resolve_required(requirements[jid]["required_skills"], resume_skills[rid])
            result = match_skills(resume_skills[rid], required)
            rows.append({
                "resume_id": rid,
                "job_id": jid,
                "job_title": job_title(jobs[jid], jid),
                "semantic_similarity": compute_cosine_similarity(resume_emb[rid], job_emb[jid]),
                "skill_coverage": result.required_skill_coverage,
                "matched_skills": result.matched_skills,
                "missing_skills": result.missing_skills,
                "ground_truth_label": truth[(rid, jid)]["label"],
                "reason": truth[(rid, jid)]["reason"],
            })

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "phase1_resume_skills.json").write_text(
        json.dumps(resume_skills, indent=2), encoding="utf-8"
    )
    return rows


def save_results_csv(rows: List[dict]) -> None:
    cols = ["resume_id", "job_id", "job_title", "semantic_similarity", "skill_coverage",
            "matched_skills", "missing_skills", "ground_truth_label"]
    with open(RESULTS / "phase1_validation.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({
                **{c: r[c] for c in cols},
                "semantic_similarity": f"{r['semantic_similarity']:.4f}",
                "skill_coverage": f"{r['skill_coverage']:.4f}",
                "matched_skills": "; ".join(r["matched_skills"]),
                "missing_skills": "; ".join(r["missing_skills"]),
            })


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def bootstrap_spearman_ci(x: np.ndarray, y: np.ndarray, rng: np.random.Generator) -> List[float]:
    stats = []
    n = len(x)
    for _ in range(BOOTSTRAP_SAMPLES):
        idx = rng.integers(0, n, n)
        if np.ptp(x[idx]) == 0 or np.ptp(y[idx]) == 0:
            continue
        stats.append(spearmanr(x[idx], y[idx]).statistic)
    return [float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))]


def tie_aware_top1(scores: np.ndarray, labels: np.ndarray) -> float:
    """Expected probability that the top-scored job has the resume's best label."""
    top = np.flatnonzero(scores == scores.max())
    return float(np.mean(labels[top] == labels.max()))


def compute_metrics(rows: List[dict]) -> dict:
    sem = np.array([r["semantic_similarity"] for r in rows])
    cov = np.array([r["skill_coverage"] for r in rows])
    lab = np.array([r["ground_truth_label"] for r in rows])
    rng = np.random.default_rng(RANDOM_SEED)

    by_label = {}
    for k in sorted(set(lab.tolist())):
        m = lab == k
        by_label[str(k)] = {
            "n": int(m.sum()),
            "semantic_mean": float(sem[m].mean()), "semantic_std": float(sem[m].std(ddof=1)) if m.sum() > 1 else 0.0,
            "coverage_mean": float(cov[m].mean()), "coverage_std": float(cov[m].std(ddof=1)) if m.sum() > 1 else 0.0,
        }

    def corr(x, y):
        res = spearmanr(x, y)
        return {"rho": float(res.statistic), "p_value": float(res.pvalue),
                "bootstrap_95ci": bootstrap_spearman_ci(x, y, rng)}

    relevant = (lab >= 2).astype(int)
    keep = np.array([(r["resume_id"], r["job_id"]) not in DESIGNED_PAIRS for r in rows])

    # Per-resume ranking of the 10 jobs.
    ranking = {"semantic": {}, "coverage": {}, "random_expected": {}}
    within = {"semantic": [], "coverage": []}
    resume_ids = sorted({r["resume_id"] for r in rows})
    for rid in resume_ids:
        idx = [i for i, r in enumerate(rows) if r["resume_id"] == rid]
        y = lab[idx][None, :]
        for name, s in (("semantic", sem[idx]), ("coverage", cov[idx])):
            ranking[name][rid] = {
                "ndcg@3": float(ndcg_score(y, s[None, :], k=3)),
                "ndcg@10": float(ndcg_score(y, s[None, :])),
                "top1_best_label": tie_aware_top1(s, lab[idx]),
            }
            within[name].append(float(spearmanr(s, lab[idx]).statistic))
        rand = [ndcg_score(y, rng.random((1, len(idx))), k=3) for _ in range(1000)]
        rand10 = [ndcg_score(y, rng.random((1, len(idx)))) for _ in range(1000)]
        ranking["random_expected"][rid] = {"ndcg@3": float(np.mean(rand)), "ndcg@10": float(np.mean(rand10))}

    def mean_of(name, key):
        return float(np.mean([v[key] for v in ranking[name].values()]))

    ranking_summary = {
        name: {k: mean_of(name, k) for k in ("ndcg@3", "ndcg@10", "top1_best_label")}
        for name in ("semantic", "coverage")
    }
    ranking_summary["random_expected"] = {k: mean_of("random_expected", k) for k in ("ndcg@3", "ndcg@10")}

    q33, q67 = np.percentile(sem, [100 / 3, 200 / 3])

    return {
        "n_resumes": len(resume_ids),
        "n_jobs": len({r["job_id"] for r in rows}),
        "n_pairs": len(rows),
        "label_distribution": {str(k): int((lab == k).sum()) for k in range(4)},
        "means_by_label": by_label,
        "spearman_semantic_vs_label": corr(sem, lab),
        "spearman_coverage_vs_label": corr(cov, lab),
        "spearman_semantic_vs_coverage": corr(sem, cov),
        "spearman_excluding_designed_pairs": {
            "n_pairs": int(keep.sum()),
            "semantic_vs_label": float(spearmanr(sem[keep], lab[keep]).statistic),
            "coverage_vs_label": float(spearmanr(cov[keep], lab[keep]).statistic),
            "semantic_vs_coverage": float(spearmanr(sem[keep], cov[keep]).statistic),
        },
        "within_resume_spearman_mean": {k: float(np.mean(v)) for k, v in within.items()},
        "within_resume_spearman": {k: dict(zip(resume_ids, v)) for k, v in within.items()},
        "roc_auc_relevant_label_ge2": {
            "semantic": float(roc_auc_score(relevant, sem)),
            "coverage": float(roc_auc_score(relevant, cov)),
        },
        "ranking_per_resume": ranking,
        "ranking_mean": ranking_summary,
        "thresholds": {"semantic_q33": float(q33), "semantic_q67": float(q67),
                       "coverage_high": COV_HIGH, "coverage_low": COV_LOW},
    }


def categorize(rows: List[dict], thresholds: dict) -> Dict[str, List[dict]]:
    q33, q67 = thresholds["semantic_q33"], thresholds["semantic_q67"]

    def band(s):
        return "high" if s >= q67 else ("low" if s < q33 else "moderate")

    cats = {"A_high_sem_low_cov": [], "B_moderate_sem_high_cov": [], "B2_low_sem_high_cov": [],
            "C_high_sem_high_cov": [], "D_low_sem_low_cov": []}
    for r in rows:
        b, c = band(r["semantic_similarity"]), r["skill_coverage"]
        if b == "high" and c <= COV_LOW:
            cats["A_high_sem_low_cov"].append(r)
        elif b == "moderate" and c >= COV_HIGH:
            cats["B_moderate_sem_high_cov"].append(r)
        elif b == "low" and c >= COV_HIGH:
            cats["B2_low_sem_high_cov"].append(r)
        elif b == "high" and c >= COV_HIGH:
            cats["C_high_sem_high_cov"].append(r)
        elif b == "low" and c <= COV_LOW:
            cats["D_low_sem_low_cov"].append(r)
    for v in cats.values():
        v.sort(key=lambda r: -r["semantic_similarity"])
    return cats


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------
def _style() -> None:
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 200, "font.size": 11,
        "axes.titlesize": 13, "axes.titleweight": "bold", "axes.labelsize": 11,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.25, "legend.frameon": False,
    })


def _short(job_id: str) -> str:
    return job_id.replace("job_", "")


def _resume_short(rid: str) -> str:
    return rid.replace("resume_", "")


def plot_by_label(rows, key, ylabel, title, fname, rho) -> None:
    rng = np.random.default_rng(0)
    labels = [0, 1, 2, 3]
    data = [[r[key] for r in rows if r["ground_truth_label"] == k] for k in labels]
    fig, ax = plt.subplots(figsize=(7, 4.8))
    bp = ax.boxplot(data, positions=labels, widths=0.5, patch_artist=True, showfliers=False,
                    medianprops={"color": "black"})
    for patch, k in zip(bp["boxes"], labels):
        patch.set_facecolor(LABEL_COLORS[k]); patch.set_alpha(0.35)
    for k, d in zip(labels, data):
        ax.scatter(k + rng.uniform(-0.12, 0.12, len(d)), d, color=LABEL_COLORS[k],
                   edgecolor="black", linewidth=0.5, s=36, zorder=3)
        ax.scatter([k], [np.mean(d)], marker="D", color="white", edgecolor="black", s=50, zorder=4)
    ax.set_xticks(labels, [f"{LABEL_NAMES[k]}\n(n={len(d)})" for k, d in zip(labels, data)])
    ax.set_xlabel("Reference relevance label")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.text(0.02, 0.97, f"Spearman ρ = {rho:.2f}   (◇ = mean)", transform=ax.transAxes,
            va="top", fontsize=10)
    fig.tight_layout()
    fig.savefig(PLOTS / fname)
    plt.close(fig)


def plot_scatter(rows, thresholds, rho) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    for k in (0, 1, 2, 3):
        pts = [r for r in rows if r["ground_truth_label"] == k]
        ax.scatter([r["semantic_similarity"] for r in pts], [r["skill_coverage"] for r in pts],
                   color=LABEL_COLORS[k], edgecolor="black", linewidth=0.5, s=60,
                   label=LABEL_NAMES[k], zorder=3)
    ax.axvline(thresholds["semantic_q67"], color="grey", ls="--", lw=1)
    ax.axvline(thresholds["semantic_q33"], color="grey", ls=":", lw=1)
    ax.axhline(COV_HIGH, color="grey", ls="--", lw=1)
    ax.axhline(COV_LOW, color="grey", ls=":", lw=1)
    ax.text(thresholds["semantic_q67"], 1.04, " high-sem tercile →", fontsize=9, color="grey")
    ax.text(min(r["semantic_similarity"] for r in rows), COV_HIGH + 0.01,
            f"coverage ≥ {COV_HIGH:.2f}", fontsize=9, color="grey")
    ax.text(min(r["semantic_similarity"] for r in rows), COV_LOW + 0.01,
            f"coverage ≤ {COV_LOW:.2f}", fontsize=9, color="grey")
    # Annotate the most disagreeing pairs (largest rank difference).
    sem = np.array([r["semantic_similarity"] for r in rows])
    cov = np.array([r["skill_coverage"] for r in rows])
    from scipy.stats import rankdata
    diff = np.abs(rankdata(sem) / len(sem) - rankdata(cov) / len(cov))
    for i in np.argsort(-diff)[:5]:
        r = rows[i]
        ax.annotate(f"{_resume_short(r['resume_id'])} × {_short(r['job_id'])}",
                    (r["semantic_similarity"], r["skill_coverage"]), xytext=(6, 4),
                    textcoords="offset points", fontsize=8.5)
    ax.set_xlabel("Semantic similarity (Phase 0, cosine)")
    ax.set_ylabel("Required skill coverage (Phase 1)")
    ax.set_ylim(-0.05, 1.1)
    ax.set_title(f"Two signals per resume × job pair (Spearman ρ = {rho:.2f})")
    ax.legend(title="Reference label", loc="lower right")
    fig.tight_layout()
    fig.savefig(PLOTS / "3_semantic_vs_coverage.png")
    plt.close(fig)


def plot_ranking_example(rows, rid) -> None:
    pts = sorted([r for r in rows if r["resume_id"] == rid], key=lambda r: r["semantic_similarity"])
    fig, ax = plt.subplots(figsize=(9, 6))
    y = np.arange(len(pts))
    ax.barh(y, [r["semantic_similarity"] for r in pts],
            color=[LABEL_COLORS[r["ground_truth_label"]] for r in pts], edgecolor="black", linewidth=0.5)
    for i, r in enumerate(pts):
        ax.text(r["semantic_similarity"] + 0.005, i,
                f"{r['semantic_similarity']:.2f}   coverage {r['skill_coverage']:.2f}",
                va="center", fontsize=9)
    ax.set_yticks(y, [f"#{len(pts) - i}  {r['job_title']}" for i, r in enumerate(pts)])
    ax.set_xlabel("Semantic similarity (Phase 0 ranking signal)")
    ax.set_xlim(0, max(r["semantic_similarity"] for r in pts) * 1.45)
    ax.set_title(f"Phase 0 job ranking for resume {_resume_short(rid)}")
    handles = [plt.Rectangle((0, 0), 1, 1, color=LABEL_COLORS[k]) for k in (0, 1, 2, 3)]
    ax.legend(handles, [LABEL_NAMES[k] for k in (0, 1, 2, 3)], title="Bar colour = reference label",
              loc="upper center", bbox_to_anchor=(0.4, -0.13), ncol=4, fontsize=9)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(PLOTS / "4_ranking_example.png")
    plt.close(fig)


def plot_disagreement_example(rows, rid) -> None:
    pts = sorted([r for r in rows if r["resume_id"] == rid],
                 key=lambda r: (r["ground_truth_label"], r["semantic_similarity"]))
    y = np.arange(len(pts))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 5.4), sharey=True)
    colors = [LABEL_COLORS[r["ground_truth_label"]] for r in pts]
    a1.barh(y, [r["semantic_similarity"] for r in pts], color=colors, edgecolor="black", linewidth=0.5)
    a2.barh(y, [r["skill_coverage"] for r in pts], color=colors, edgecolor="black", linewidth=0.5)
    for i, r in enumerate(pts):
        a1.text(r["semantic_similarity"] + 0.005, i, f"{r['semantic_similarity']:.2f}", va="center", fontsize=9)
        n_req = len(r["matched_skills"]) + len(r["missing_skills"])
        a2.text(r["skill_coverage"] + 0.01, i, f"{len(r['matched_skills'])}/{n_req}", va="center", fontsize=9)
    a1.set_yticks(y, [f"{r['job_title']}  [label {r['ground_truth_label']}]" for r in pts])
    a1.set_xlabel("Semantic similarity")
    a2.set_xlabel("Required skill coverage (matched / required)")
    a1.set_xlim(0, max(r["semantic_similarity"] for r in pts) * 1.2)
    a2.set_xlim(0, 1.15)
    a1.set_title("Phase 0: semantic similarity")
    a2.set_title("Phase 1: required skill coverage")
    for ax in (a1, a2):
        ax.grid(axis="y", visible=False)
    fig.suptitle(f"Same resume, two signals: {_resume_short(rid)} (jobs ordered by reference label)",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(PLOTS / "5_disagreement_example.png")
    plt.close(fig)


def make_plots(rows, metrics) -> None:
    PLOTS.mkdir(parents=True, exist_ok=True)
    _style()
    plot_by_label(rows, "semantic_similarity", "Semantic similarity (cosine)",
                  "Phase 0 semantic similarity vs. reference relevance",
                  "1_semantic_vs_label.png", metrics["spearman_semantic_vs_label"]["rho"])
    plot_by_label(rows, "skill_coverage", "Required skill coverage",
                  "Phase 1 required skill coverage vs. reference relevance",
                  "2_coverage_vs_label.png", metrics["spearman_coverage_vs_label"]["rho"])
    plot_scatter(rows, metrics["thresholds"], metrics["spearman_semantic_vs_coverage"]["rho"])
    plot_ranking_example(rows, RANKING_EXAMPLE_RESUME)
    plot_disagreement_example(rows, DISAGREEMENT_EXAMPLE_RESUME)


# ---------------------------------------------------------------------------
def main() -> None:
    rows = run()
    save_results_csv(rows)
    metrics = compute_metrics(rows)
    cats = categorize(rows, metrics["thresholds"])
    metrics["disagreement_categories"] = {
        k: [{"resume_id": r["resume_id"], "job_id": r["job_id"],
             "semantic_similarity": round(r["semantic_similarity"], 4),
             "skill_coverage": round(r["skill_coverage"], 4),
             "ground_truth_label": r["ground_truth_label"],
             "matched": r["matched_skills"], "missing": r["missing_skills"]} for r in v]
        for k, v in cats.items()
    }
    (RESULTS / "phase1_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    make_plots(rows, metrics)

    print(f"Pairs: {metrics['n_pairs']}  ({metrics['n_resumes']} resumes x {metrics['n_jobs']} jobs)")
    for name in ("semantic", "coverage"):
        c = metrics[f"spearman_{name}_vs_label"]
        print(f"Spearman {name:8s} vs label: rho={c['rho']:.3f}  p={c['p_value']:.2g}  "
              f"95% bootstrap CI={c['bootstrap_95ci'][0]:.2f}..{c['bootstrap_95ci'][1]:.2f}")
    print(f"Spearman semantic vs coverage: rho={metrics['spearman_semantic_vs_coverage']['rho']:.3f}")
    print("Excluding designed pairs:", metrics["spearman_excluding_designed_pairs"])
    print("Ranking mean:", json.dumps(metrics["ranking_mean"], indent=1))
    print("Within-resume Spearman mean:", metrics["within_resume_spearman_mean"])
    print("ROC AUC (label>=2):", metrics["roc_auc_relevant_label_ge2"])
    print("Means by label:", json.dumps(metrics["means_by_label"], indent=1))
    print("Thresholds:", metrics["thresholds"])
    for k, v in cats.items():
        print(f"\n{k} ({len(v)})")
        for r in v:
            print(f"  {r['resume_id']:18s} {r['job_id']:20s} sem={r['semantic_similarity']:.3f} "
                  f"cov={r['skill_coverage']:.2f} label={r['ground_truth_label']}  "
                  f"missing={r['missing_skills']}")


if __name__ == "__main__":
    main()
