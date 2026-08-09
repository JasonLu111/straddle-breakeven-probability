"""Module 5 entry rules: which weeks does each strategy actually trade?

Strategy D (expected-value filter) is intentionally not implemented -- the
research proposal itself flags it as a v2 extension ("第一版先完成 probability
threshold 即可"), and there is no reason to build it here given Phase 3 found
no reliable discrimination to filter on in the first place.
"""
from __future__ import annotations

import pandas as pd


def strategy_a_unconditional(trades: pd.DataFrame) -> pd.Series:
    """Every available week."""
    return pd.Series(True, index=trades.index)


def strategy_b_compression_rule(trades: pd.DataFrame, regime_col: str = "compression_regime_20") -> pd.Series:
    """Only weeks flagged as a compression regime at entry."""
    return trades[regime_col].astype(bool)


def strategy_c_probability_filtered(trades: pd.DataFrame, prob_col: str = "y_prob",
                                      threshold_col: str = "fold_train_median_prob") -> pd.Series:
    """Only weeks where the model's predicted probability exceeds that fold's
    own training-set median predicted probability. The threshold is per-fold
    and computed strictly from that fold's training data (see
    scripts/compute_fold_thresholds.py) -- never from the test period or the
    full-sample prediction distribution, which would leak future information
    into the entry decision.
    """
    return trades[prob_col] > trades[threshold_col]
