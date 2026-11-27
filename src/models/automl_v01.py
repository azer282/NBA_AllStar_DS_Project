"""Baselines and AutoML pipeline v0.1 (Module 3 - owner: Basile Chabrel).

v0.1 = data preparation + feature selection + model selection among standard algorithms
+ hyperparameter search, as asked in the course guidelines (Step 2).

Leakage guards:
- Imputation and scaling live INSIDE the sklearn Pipeline, so they are fitted on the
  training fold only (never on validation or test rows).
- Model selection uses a PredefinedSplit: fit on train seasons, score on validation
  seasons. The test seasons are used once, after every choice is frozen.
"""
from functools import partial

import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, PredefinedSplit
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from src.config import SEED, TARGET_COL
from src.models.split import feature_columns

# ---------------------------------------------------------------------------
# Baselines: what a model must beat to be useful
# ---------------------------------------------------------------------------

def baseline_scores(frame: pd.DataFrame) -> dict[str, np.ndarray]:
    """Three non-learned baselines, scored on any frame of the "prev" table."""
    rng = np.random.default_rng(SEED)
    pts = frame["prev_pts_per_game"].fillna(0).to_numpy()
    return {
        # 1. Random score: PR-AUC ~ positive rate.
        "random": rng.random(len(frame)),
        # 2. Top scorers of last season.
        "prev_points": pts,
        # 3. "Same as last year": last season's All-Stars first, then by points.
        "same_as_last_year": frame["all_star_prev_season"].to_numpy() * 100 + pts,
    }


# ---------------------------------------------------------------------------
# AutoML v0.1
# ---------------------------------------------------------------------------

def _preprocess(k_best: int | str = "all") -> list:
    return [
        # Median is robust to outliers (a few players have extreme per-minute stats).
        # add_indicator keeps the information "this value was missing" (e.g. rookies).
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
        ("scale", StandardScaler()),
        ("select", SelectKBest(partial(mutual_info_classif, random_state=SEED), k=k_best)),
    ]


def candidate_grids() -> dict[str, tuple[Pipeline, dict]]:
    """Standard algorithms from the course with a small, justified search space."""
    return {
        "logistic_regression": (
            Pipeline(_preprocess() + [("model", LogisticRegression(
                class_weight="balanced", max_iter=5000, random_state=SEED))]),
            {"model__C": [0.001, 0.01, 0.1, 1.0], "select__k": [15, 30, "all"]},
        ),
        "decision_tree": (
            Pipeline(_preprocess() + [("model", DecisionTreeClassifier(
                class_weight="balanced", random_state=SEED))]),
            {"model__max_depth": [3, 5, 8], "model__min_samples_leaf": [10, 50], "select__k": [15, "all"]},
        ),
        "svm_rbf": (
            Pipeline(_preprocess() + [("model", SVC(
                kernel="rbf", class_weight="balanced", random_state=SEED))]),
            {"model__C": [0.1, 1.0, 10.0], "model__gamma": ["scale", 0.01], "select__k": [15, "all"]},
        ),
        "knn": (
            Pipeline(_preprocess() + [("model", KNeighborsClassifier())]),
            {"model__n_neighbors": [15, 50, 150], "model__weights": ["uniform", "distance"], "select__k": [15, "all"]},
        ),
    }


def score_of(model, X) -> np.ndarray:
    """Probability of the positive class when available, else decision function."""
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    return model.decision_function(X)


def run_automl(train: pd.DataFrame, validation: pd.DataFrame, grids: dict | None = None) -> pd.DataFrame:
    """Grid-search every candidate: fit on train, score PR-AUC on validation.

    Returns one row per algorithm with its best hyperparameters and validation PR-AUC,
    plus the fitted search objects in `.attrs["searches"]`.
    """
    grids = grids or candidate_grids()
    cols = feature_columns(train)
    both = pd.concat([train, validation])
    fold = PredefinedSplit(np.r_[np.full(len(train), -1), np.zeros(len(validation))])
    rows, searches = [], {}
    for name, (pipe, grid) in grids.items():
        search = GridSearchCV(pipe, grid, scoring="average_precision", cv=fold, n_jobs=-1, refit=False)
        search.fit(both[cols], both[TARGET_COL])
        # refit=False + PredefinedSplit: refit the best setting on TRAIN only, so that the
        # validation scores used later (threshold choice) stay out-of-sample.
        best = pipe.set_params(**search.best_params_).fit(train[cols], train[TARGET_COL])
        searches[name] = best
        rows.append({"model": name, "best_params": search.best_params_,
                     "validation_pr_auc": search.best_score_})
    result = pd.DataFrame(rows).sort_values("validation_pr_auc", ascending=False).reset_index(drop=True)
    result.attrs["searches"] = searches
    return result
