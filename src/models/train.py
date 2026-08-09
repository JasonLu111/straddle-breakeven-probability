"""Unfitted model factories. Hyperparameters come from configs/model.yaml and
are fixed across all folds (no per-fold tuning -- see the comment there)."""
from __future__ import annotations

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_logistic_regression(cfg: dict) -> Pipeline:
    lr_cfg = cfg["logistic_regression"]
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            C=lr_cfg["C"], max_iter=lr_cfg["max_iter"],
        )),
    ])


def build_random_forest(cfg: dict) -> RandomForestClassifier:
    rf_cfg = cfg["random_forest"]
    return RandomForestClassifier(
        n_estimators=rf_cfg["n_estimators"],
        max_depth=rf_cfg["max_depth"],
        min_samples_leaf=rf_cfg["min_samples_leaf"],
        max_features=rf_cfg["max_features"],
        random_state=rf_cfg["random_state"],
    )
