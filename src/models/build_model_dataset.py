"""Joins Phase 1 price/volatility features with Phase 2 option-cost features and
the real breakeven target, producing the Phase 3 model input table.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.features.option_features import build_option_cost_features

# Phase 1 columns to exclude from the Phase 3 feature set: raw OHLCV (not
# features), forward-return targets (Phase 1's own target, not ours -- using it
# here would leak information about the very future window the straddle target
# is defined over), and the compression_regime_* flags (already carried by the
# Phase 2 breakeven table, no need to duplicate).
_EXCLUDE_PHASE1_COLS = {
    "open", "high", "low", "close", "adj_close", "volume",
    "fwd_abs_return_10d", "fwd_abs_return_20d",
    "compression_regime_10", "compression_regime_20", "compression_regime_30", "compression_regime",
}


def build_model_dataset(ticker: str) -> pd.DataFrame:
    phase1 = pd.read_parquet(f"data/processed/{ticker}_phase1.parquet")
    phase1.index = pd.to_datetime(phase1.index)

    breakeven = pd.read_parquet(f"data/processed/{ticker}_phase2_breakeven.parquet")
    breakeven = breakeven.sort_values("trade_date").reset_index(drop=True)

    phase1_feature_cols = [c for c in phase1.columns if c not in _EXCLUDE_PHASE1_COLS]
    phase1_features_at_entry = phase1.loc[breakeven["trade_date"], phase1_feature_cols].reset_index(drop=True)

    option_cost_features = build_option_cost_features(breakeven, phase1["rv_20"])

    target_cols = ["target_expiry", "target_positive_net_pnl", "net_pnl", "return_on_premium"]
    regime_cols = ["compression_regime_10", "compression_regime_20", "compression_regime_30", "compression_regime"]
    id_cols = ["ticker", "trade_date", "expir_date", "pricing_date"]

    dataset = pd.concat([
        breakeven[id_cols],
        breakeven[regime_cols],
        phase1_features_at_entry,
        option_cost_features,
        breakeven[target_cols],
    ], axis=1)

    dataset = dataset.sort_values("trade_date").reset_index(drop=True)
    return dataset


def run(ticker: str) -> pd.DataFrame:
    dataset = build_model_dataset(ticker)
    out_path = Path("data/processed") / f"{ticker}_phase3_model_input.parquet"
    dataset.to_parquet(out_path)
    n_rows, n_features = dataset.shape
    print(f"{ticker}: {n_rows} rows, {n_features} columns -> {out_path}")
    return dataset


if __name__ == "__main__":
    import sys
    tickers = sys.argv[1:] or ["SPY", "QQQ"]
    for t in tickers:
        run(t)
