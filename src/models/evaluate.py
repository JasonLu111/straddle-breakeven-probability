"""Classification + probability-quality metrics for a pooled set of
out-of-sample predictions (across all walk-forward folds)."""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss, f1_score,
                              log_loss, precision_score, recall_score, roc_auc_score)


def classification_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> dict:
    y_pred = (y_prob >= threshold).astype(int)
    n_pos = int(y_true.sum())
    metrics = {
        "n": len(y_true),
        "n_positive": n_pos,
        "base_rate": float(y_true.mean()),
        "roc_auc": float(roc_auc_score(y_true, y_prob)) if 0 < n_pos < len(y_true) else float("nan"),
        "pr_auc": float(average_precision_score(y_true, y_prob)) if 0 < n_pos < len(y_true) else float("nan"),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    return metrics


def probability_quality_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict:
    y_prob_clipped = np.clip(y_prob, 1e-6, 1 - 1e-6)
    return {
        "brier_score": float(brier_score_loss(y_true, y_prob)),
        "log_loss": float(log_loss(y_true, y_prob_clipped, labels=[0, 1])),
        **calibration_intercept_slope(y_true, y_prob_clipped),
        "expected_calibration_error": expected_calibration_error(y_true, y_prob),
    }


def calibration_intercept_slope(y_true: np.ndarray, y_prob_clipped: np.ndarray) -> dict:
    """Cox calibration: logistic regression of the outcome on the logit of the
    predicted probability. Slope=1, intercept=0 is perfect calibration;
    slope<1 means predictions are too extreme, intercept != 0 means a
    systematic over/under-prediction bias.
    """
    logit_p = np.log(y_prob_clipped / (1 - y_prob_clipped)).reshape(-1, 1)
    try:
        lr = LogisticRegression()
        lr.fit(logit_p, y_true)
        return {"calibration_intercept": float(lr.intercept_[0]), "calibration_slope": float(lr.coef_[0][0])}
    except ValueError:
        return {"calibration_intercept": float("nan"), "calibration_slope": float("nan")}


def expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_idx = np.clip(np.digitize(y_prob, bin_edges) - 1, 0, n_bins - 1)
    ece = 0.0
    n = len(y_true)
    for b in range(n_bins):
        mask = bin_idx == b
        if mask.sum() == 0:
            continue
        bin_conf = y_prob[mask].mean()
        bin_acc = y_true[mask].mean()
        ece += (mask.sum() / n) * abs(bin_acc - bin_conf)
    return float(ece)


def calibration_curve_points(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> list[dict]:
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_idx = np.clip(np.digitize(y_prob, bin_edges) - 1, 0, n_bins - 1)
    points = []
    for b in range(n_bins):
        mask = bin_idx == b
        if mask.sum() == 0:
            continue
        points.append({
            "bin_lower": float(bin_edges[b]),
            "bin_upper": float(bin_edges[b + 1]),
            "mean_predicted": float(y_prob[mask].mean()),
            "observed_rate": float(y_true[mask].mean()),
            "n": int(mask.sum()),
        })
    return points
