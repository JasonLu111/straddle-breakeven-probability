"""Guards against look-ahead bias: every feature value at time t must be
identical whether or not rows after t exist in the input. Only the forward
targets are allowed to depend on future rows (that's their entire purpose).
"""
import numpy as np
import pandas as pd
import pytest

from src.features.build_features import build_all_features, build_forward_targets, load_features_config

CFG = load_features_config()


def make_synthetic_ohlcv(n: int = 800, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2015-01-01", periods=n)
    returns = rng.normal(0, 0.01, size=n)
    close = 100 * np.exp(np.cumsum(returns))
    high = close * (1 + np.abs(rng.normal(0, 0.003, size=n)))
    low = close * (1 - np.abs(rng.normal(0, 0.003, size=n)))
    open_ = close * (1 + rng.normal(0, 0.001, size=n))
    volume = rng.integers(1_000_000, 5_000_000, size=n)

    return pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": close,
        "adj_close": close, "volume": volume,
    }, index=dates)


def test_features_unaffected_by_future_rows():
    df = make_synthetic_ohlcv()
    cutoff = 500

    full_features = build_all_features(df, CFG)
    truncated_features = build_all_features(df.iloc[: cutoff + 1], CFG)

    common_cols = full_features.columns
    full_slice = full_features.iloc[: cutoff + 1][common_cols]
    truncated_slice = truncated_features[common_cols]

    pd.testing.assert_frame_equal(full_slice, truncated_slice, check_dtype=False)


def test_forward_targets_do_depend_on_future_rows_by_design():
    df = make_synthetic_ohlcv()
    cutoff = 500

    full_targets = build_forward_targets(df, CFG["forward_horizons"]["days"])
    truncated_targets = build_forward_targets(df.iloc[: cutoff + 1], CFG["forward_horizons"]["days"])

    horizon = CFG["forward_horizons"]["days"][0]
    col = f"fwd_abs_return_{horizon}d"
    # near the truncation boundary, the truncated version can't see forward
    # enough and must be NaN where the full version has a real value
    boundary = slice(cutoff - horizon + 1, cutoff + 1)
    assert truncated_targets[col].iloc[boundary].isna().all()
    assert full_targets[col].iloc[boundary].notna().any()


def test_compression_regime_is_na_during_warmup_not_false():
    df = make_synthetic_ohlcv(n=400)  # shorter than 252-day percentile lookback + buffer
    features = build_all_features(df, CFG)
    lookback = CFG["realized_volatility"]["percentile_lookback"]
    warmup = features["compression_regime"].iloc[: lookback - 1]
    assert warmup.isna().all()
