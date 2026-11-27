"""Evaluation metrics and uncertainty (Module 4 - owner: Basile Chabrel).

Accuracy is NOT used: with ~6% positives, always predicting "not All-Star" already scores
~94% while finding no All-Star (Week 1 report, section 4).

- PR-AUC (average precision): main metric. Random baseline = positive rate.
- ROC-AUC: reported for completeness (optimistic under imbalance).
- Precision / recall / F1 on the positive class at a threshold chosen on VALIDATION only.
- Hits@K per season: each season, take the K players with the highest score, K = number of
  real All-Stars that season, and count how many were real All-Stars. Easy to explain:
  "the model found 19 of the 24 All-Stars".
- 95% confidence intervals by season-block bootstrap: we resample whole seasons, because
  rows of one season are not independent (same voters, same number of places).
"""
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.config import N_BOOTSTRAP, SEED, TARGET_COL


def best_f1_threshold(y_true, scores) -> float:
    """Threshold that maximises F1. Call it on VALIDATION scores only, never on test."""
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    f1 = 2 * precision * recall / np.clip(precision + recall, 1e-12, None)
    return float(thresholds[np.argmax(f1[:-1])])


def hits_at_k(frame: pd.DataFrame, score_col: str = "score") -> pd.DataFrame:
    """Per season: K = real All-Stars, hits = real All-Stars among the top-K scores."""
    rows = []
    for season, group in frame.groupby("season"):
        k = int(group[TARGET_COL].sum())
        top = group.nlargest(k, score_col)
        rows.append({"season": season, "k": k, "hits": int(top[TARGET_COL].sum())})
    out = pd.DataFrame(rows)
    out["hit_rate"] = out["hits"] / out["k"]
    return out


def point_metrics(frame: pd.DataFrame, threshold: float, score_col: str = "score") -> dict:
    """All metrics on one evaluation frame (columns: season, all_star, score)."""
    y, s = frame[TARGET_COL].to_numpy(), frame[score_col].to_numpy()
    pred = (s >= threshold).astype(int)
    hits = hits_at_k(frame, score_col)
    return {
        "pr_auc": average_precision_score(y, s),
        "roc_auc": roc_auc_score(y, s),
        "precision": precision_score(y, pred, zero_division=0),
        "recall": recall_score(y, pred, zero_division=0),
        "f1": f1_score(y, pred, zero_division=0),
        "hits_at_k": hits["hits"].sum() / hits["k"].sum(),
        "positive_rate": y.mean(),
    }


def season_bootstrap_ci(frame: pd.DataFrame, threshold: float, score_col: str = "score",
                        n_boot: int = N_BOOTSTRAP, seed: int = SEED) -> pd.DataFrame:
    """95% CI of each metric, resampling whole seasons with replacement."""
    rng = np.random.default_rng(seed)
    seasons = frame["season"].unique()
    by_season = {s: g for s, g in frame.groupby("season")}
    draws = []
    for _ in range(n_boot):
        picked = rng.choice(seasons, size=len(seasons), replace=True)
        # Re-label resampled seasons so that a season drawn twice counts as two seasons.
        sample = pd.concat([by_season[s].assign(season=i) for i, s in enumerate(picked)])
        draws.append(point_metrics(sample, threshold, score_col))
    draws = pd.DataFrame(draws)
    point = point_metrics(frame, threshold, score_col)
    return pd.DataFrame({
        "value": pd.Series(point),
        "ci_low": draws.quantile(0.025),
        "ci_high": draws.quantile(0.975),
    })


def calibration_summary(y_true, proba) -> dict:
    """Brier score (lower is better) and mean predicted vs observed rate."""
    return {
        "brier": brier_score_loss(y_true, proba),
        "mean_predicted": float(np.mean(proba)),
        "observed_rate": float(np.mean(y_true)),
    }
