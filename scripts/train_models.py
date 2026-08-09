"""Phase 3: walk-forward training + calibration + evaluation (H3-H5).

For every fold: fit all models on the training window only (with calibration
cross-validated inside that same training window), predict on the held-out
test window, and pool the resulting out-of-sample predictions across folds for
the final metrics. No model, scaler, or calibrator ever sees a test-period
observation before predicting on it.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from sklearn.calibration import CalibratedClassifierCV

from src.models.baselines import fit_predict_compression_rule, fit_predict_dummy
from src.models.calibrate import fit_calibrated
from src.models.evaluate import (calibration_curve_points, classification_metrics,
                                   probability_quality_metrics)
from src.models.train import build_logistic_regression, build_random_forest
from src.models.walk_forward import generate_folds

TICKERS = ["SPY", "QQQ"]
RESULTS_DIR = Path("results/model_metrics")
PRED_DIR = Path("results/predictions")
FIGURES_DIR = Path("reports/figures")
TABLES_DIR = Path("reports/tables")


def load_config() -> dict:
    with open("configs/model.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def prepare_features(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    X = df[feature_cols].copy()
    for col in X.columns:
        if X[col].dtype == "boolean" or X[col].dtype == bool:
            X[col] = X[col].astype(int)
    return X


def run_ticker(ticker: str, cfg: dict) -> tuple[pd.DataFrame, dict]:
    df = pd.read_parquet(f"data/processed/{ticker}_phase3_model_input.parquet")
    feature_cols = cfg["features"]
    target_col = cfg["target"]
    cal_cfg = cfg["calibration"]

    folds = generate_folds(df["trade_date"], cfg["walk_forward"]["initial_train_years"],
                            cfg["walk_forward"]["test_window_years"])

    all_predictions = []
    feature_importances = []  # RF, per fold
    lr_coefficients = []      # LR, per fold

    for fold in folds:
        X = prepare_features(df, feature_cols)
        y = df[target_col].astype(int)

        X_train, y_train = X[fold.train_mask], y[fold.train_mask]
        X_test, y_test = X[fold.test_mask], y[fold.test_mask]
        regime_train = df.loc[fold.train_mask, "compression_regime_20"]
        regime_test = df.loc[fold.test_mask, "compression_regime_20"]
        test_dates = df.loc[fold.test_mask, "trade_date"]

        preds = {
            "dummy_prior": fit_predict_dummy(y_train, len(X_test)),
            "compression_rule": fit_predict_compression_rule(y_train, regime_train, regime_test),
        }

        lr_pipeline = build_logistic_regression(cfg)
        lr_calibrated = fit_calibrated(lr_pipeline, X_train, y_train, cal_cfg["method"], cal_cfg["cv_folds"])
        preds["logistic_regression"] = lr_calibrated.predict_proba(X_test)[:, 1]
        lr_calibrated_iso = fit_calibrated(lr_pipeline, X_train, y_train, cal_cfg["secondary_method"], cal_cfg["cv_folds"])
        preds["logistic_regression_isotonic"] = lr_calibrated_iso.predict_proba(X_test)[:, 1]

        rf = build_random_forest(cfg)
        rf_calibrated = fit_calibrated(rf, X_train, y_train, cal_cfg["method"], cal_cfg["cv_folds"])
        preds["random_forest"] = rf_calibrated.predict_proba(X_test)[:, 1]
        rf_calibrated_iso = fit_calibrated(rf, X_train, y_train, cal_cfg["secondary_method"], cal_cfg["cv_folds"])
        preds["random_forest_isotonic"] = rf_calibrated_iso.predict_proba(X_test)[:, 1]

        # Separate uncalibrated fits purely for coefficient/importance reporting
        # (not used for any prediction/metric above).
        lr_plain = build_logistic_regression(cfg)
        lr_plain.fit(X_train, y_train)
        lr_coefficients.append(pd.Series(lr_plain.named_steps["clf"].coef_[0], index=feature_cols, name=fold.fold_id))

        rf_plain = build_random_forest(cfg)
        rf_plain.fit(X_train, y_train)
        feature_importances.append(pd.Series(rf_plain.feature_importances_, index=feature_cols, name=fold.fold_id))

        for model_name, y_prob in preds.items():
            fold_df = pd.DataFrame({
                "ticker": ticker, "fold_id": fold.fold_id, "model": model_name,
                "trade_date": test_dates.values, "y_true": y_test.values, "y_prob": y_prob,
            })
            all_predictions.append(fold_df)

    predictions = pd.concat(all_predictions, ignore_index=True)

    diagnostics = {
        "n_folds": len(folds),
        "fold_boundaries": [
            {"fold_id": f.fold_id, "train_start": str(f.train_start.date()), "train_end": str(f.train_end.date()),
             "test_start": str(f.test_start.date()), "test_end": str(f.test_end.date()),
             "n_train": int(f.train_mask.sum()), "n_test": int(f.test_mask.sum())}
            for f in folds
        ],
        "lr_coefficients_mean": pd.concat(lr_coefficients, axis=1).mean(axis=1).to_dict(),
        "rf_feature_importance_mean": pd.concat(feature_importances, axis=1).mean(axis=1).to_dict(),
    }

    return predictions, diagnostics


def compute_pooled_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (ticker, model), group in predictions.groupby(["ticker", "model"]):
        y_true = group["y_true"].to_numpy()
        y_prob = group["y_prob"].to_numpy()
        row = {"ticker": ticker, "model": model}
        row.update(classification_metrics(y_true, y_prob))
        row.update(probability_quality_metrics(y_true, y_prob))
        rows.append(row)
    return pd.DataFrame(rows)


def make_figures(predictions: pd.DataFrame) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    primary = predictions[(predictions.ticker == "SPY") & (predictions.model.isin(
        ["dummy_prior", "compression_rule", "logistic_regression", "random_forest"]))]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.8, label="perfect calibration")
    for model, group in primary.groupby("model"):
        points = calibration_curve_points(group["y_true"].to_numpy(), group["y_prob"].to_numpy(), n_bins=8)
        if not points:
            continue
        xs = [p["mean_predicted"] for p in points]
        ys = [p["observed_rate"] for p in points]
        ax.plot(xs, ys, marker="o", label=model)
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed breakeven rate")
    ax.set_title("SPY: calibration curve (pooled out-of-sample, all folds)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "phase3_calibration_curve.png", dpi=150)
    plt.close(fig)

    from sklearn.metrics import roc_curve
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.8, label="random")
    for model, group in primary.groupby("model"):
        y_true = group["y_true"].to_numpy()
        if y_true.sum() == 0 or y_true.sum() == len(y_true):
            continue
        fpr, tpr, _ = roc_curve(y_true, group["y_prob"].to_numpy())
        ax.plot(fpr, tpr, label=model)
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("SPY: ROC curve (pooled out-of-sample, all folds)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "phase3_roc_curve.png", dpi=150)
    plt.close(fig)


def main() -> None:
    cfg = load_config()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    all_predictions = []
    for ticker in TICKERS:
        predictions, diagnostics = run_ticker(ticker, cfg)
        all_predictions.append(predictions)
        predictions.to_parquet(PRED_DIR / f"{ticker}_oos_predictions.parquet")
        with open(RESULTS_DIR / f"{ticker}_fold_diagnostics.json", "w", encoding="utf-8") as f:
            json.dump(diagnostics, f, indent=2)
        print(f"{ticker}: {diagnostics['n_folds']} folds, "
              f"train sizes {[b['n_train'] for b in diagnostics['fold_boundaries']]}")

    predictions = pd.concat(all_predictions, ignore_index=True)
    metrics = compute_pooled_metrics(predictions)
    metrics.to_csv(RESULTS_DIR / "phase3_pooled_metrics.csv", index=False)
    with open(TABLES_DIR / "phase3_model_comparison.md", "w", encoding="utf-8") as f:
        cols = ["ticker", "model", "n", "base_rate", "roc_auc", "pr_auc", "precision", "recall", "f1",
                "brier_score", "log_loss", "calibration_slope", "calibration_intercept", "expected_calibration_error"]
        f.write(metrics[cols].round(4).to_markdown(index=False))
    metrics[["ticker", "model", "n", "base_rate", "roc_auc", "pr_auc", "precision", "recall", "f1",
             "brier_score", "log_loss", "calibration_slope", "calibration_intercept",
             "expected_calibration_error"]].round(4).to_csv(TABLES_DIR / "phase3_model_comparison.csv", index=False)

    make_figures(predictions)

    print("\n=== Pooled metrics (SPY) ===")
    print(metrics[metrics.ticker == "SPY"][["model", "roc_auc", "pr_auc", "brier_score", "calibration_slope"]]
          .to_string(index=False))
    print(f"\nFull results: {RESULTS_DIR / 'phase3_pooled_metrics.csv'}")


if __name__ == "__main__":
    main()
