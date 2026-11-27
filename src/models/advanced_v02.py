"""Week 3: advanced models, ensemble, out-of-course model (Module 3 - owner: Basile Chabrel).

v0.2 adds, on top of v0.1 (same preprocessing, same split, same metric):
- Random forest and histogram gradient boosting (advanced versions of the decision tree).
- An MLP neural network: the "algorithm outside the course". Reference used to frame the
  comparison: Grinsztajn, Oyallon & Varoquaux (NeurIPS 2022), "Why do tree-based models still
  outperform deep learning on typical tabular data?" - they find tree ensembles remain
  state-of-the-art on medium-sized tabular data (~10K rows), which is our case (11K train rows).
  Our hypothesis to test: the MLP will not beat gradient boosting here.
- A rank-average ensemble of the best models (soft voting on ranks, robust to the fact that
  the models' scores are on different scales).
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from scipy.stats import rankdata

from src.config import SEED


def advanced_grids() -> dict:
    impute_scale = [
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
        ("scale", StandardScaler()),
    ]
    return {
        "random_forest": (
            Pipeline([("impute", SimpleImputer(strategy="median", add_indicator=True)),
                      ("model", RandomForestClassifier(
                          n_estimators=400, class_weight="balanced_subsample",
                          random_state=SEED, n_jobs=-1))]),
            {"model__max_depth": [6, 12, None], "model__min_samples_leaf": [5, 20]},
        ),
        # Gradient boosting handles missing values natively: no imputer needed.
        "gradient_boosting": (
            Pipeline([("model", HistGradientBoostingClassifier(
                class_weight="balanced", random_state=SEED, early_stopping=False))]),
            {"model__learning_rate": [0.03, 0.1], "model__max_depth": [3, 6],
             "model__max_iter": [200, 400], "model__l2_regularization": [0.0, 1.0]},
        ),
        # MLP: no class_weight option; PR-AUC only depends on the ranking of scores, and the
        # decision threshold is tuned on validation, so imbalance is handled there.
        "mlp": (
            Pipeline(impute_scale + [("model", MLPClassifier(
                max_iter=500, early_stopping=True, validation_fraction=0.15,
                random_state=SEED))]),
            {"model__hidden_layer_sizes": [(32,), (64, 32)], "model__alpha": [1e-4, 1e-2, 1.0]},
        ),
    }


def rank_average(score_list: list[np.ndarray]) -> np.ndarray:
    """Average of the per-model ranks, scaled to [0, 1]."""
    ranks = np.mean([rankdata(s) for s in score_list], axis=0)
    return (ranks - ranks.min()) / (ranks.max() - ranks.min())


def permutation_importance_table(model, X: pd.DataFrame, y: pd.Series, n_repeats: int = 10) -> pd.DataFrame:
    """Drop in PR-AUC when one feature is shuffled (computed on validation data)."""
    from sklearn.inspection import permutation_importance
    result = permutation_importance(model, X, y, scoring="average_precision",
                                    n_repeats=n_repeats, random_state=SEED, n_jobs=-1)
    return (pd.DataFrame({"feature": X.columns, "importance_mean": result.importances_mean,
                          "importance_std": result.importances_std})
            .sort_values("importance_mean", ascending=False).reset_index(drop=True))
