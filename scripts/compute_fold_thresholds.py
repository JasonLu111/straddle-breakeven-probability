"""Phase 4 prep: for Strategy C (probability-filtered entry), each fold needs an
entry threshold set from that fold's *training* data only, then applied to the
test period -- never chosen by looking at test-period outcomes or the pooled
test-period prediction distribution (see src/backtest/entry_rules.py docstring).

Reuses the Phase 3 Logistic Regression (sigmoid-calibrated) pipeline -- the
proposal's primary, most interpretable model -- refit per fold, adding one
number per fold: the median predicted probability on that fold's own training
set, used as tau.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import yaml

from scripts.train_models import prepare_features
from src.models.calibrate import fit_calibrated
from src.models.train import build_logistic_regression
from src.models.walk_forward import generate_folds

TICKERS = ["SPY", "QQQ"]


def compute_thresholds_for_ticker(ticker: str, cfg: dict) -> pd.DataFrame:
    df = pd.read_parquet(f"data/processed/{ticker}_phase3_model_input.parquet")
    feature_cols = cfg["features"]
    target_col = cfg["target"]
    cal_cfg = cfg["calibration"]

    folds = generate_folds(df["trade_date"], cfg["walk_forward"]["initial_train_years"],
                            cfg["walk_forward"]["test_window_years"])

    rows = []
    for fold in folds:
        X = prepare_features(df, feature_cols)
        y = df[target_col].astype(int)

        X_train, y_train = X[fold.train_mask], y[fold.train_mask]
        X_test = X[fold.test_mask]
        test_dates = df.loc[fold.test_mask, "trade_date"]

        lr_pipeline = build_logistic_regression(cfg)
        lr_calibrated = fit_calibrated(lr_pipeline, X_train, y_train, cal_cfg["method"], cal_cfg["cv_folds"])

        train_probs = lr_calibrated.predict_proba(X_train)[:, 1]
        fold_threshold = float(pd.Series(train_probs).median())

        test_probs = lr_calibrated.predict_proba(X_test)[:, 1]

        rows.append(pd.DataFrame({
            "ticker": ticker, "fold_id": fold.fold_id, "trade_date": test_dates.values,
            "y_prob": test_probs, "fold_train_median_prob": fold_threshold,
        }))

    return pd.concat(rows, ignore_index=True)


def main() -> None:
    with open("configs/model.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    out_dir = Path("results/predictions")
    out_dir.mkdir(parents=True, exist_ok=True)

    for ticker in TICKERS:
        thresholds = compute_thresholds_for_ticker(ticker, cfg)
        out_path = out_dir / f"{ticker}_strategy_c_thresholds.parquet"
        thresholds.to_parquet(out_path)
        n_folds = thresholds["fold_id"].nunique()
        fold_taus = thresholds.groupby("fold_id")["fold_train_median_prob"].first()
        print(f"{ticker}: {n_folds} folds, tau range [{fold_taus.min():.3f}, {fold_taus.max():.3f}] -> {out_path}")


if __name__ == "__main__":
    main()
