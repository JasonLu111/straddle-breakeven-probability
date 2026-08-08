"""Price-range compression features: Bollinger Band width, ATR, rolling range."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.volatility import rolling_percentile


def bollinger_band_width(close: pd.Series, window: int, num_std: float) -> pd.Series:
    ma = close.rolling(window).mean()
    sd = close.rolling(window).std()
    upper = ma + num_std * sd
    lower = ma - num_std * sd
    return (upper - lower) / ma


def average_true_range(high: pd.Series, low: pd.Series, close: pd.Series, window: int) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window).mean()


def rolling_range(high: pd.Series, low: pd.Series, close: pd.Series, window: int) -> pd.Series:
    """(rolling max high - rolling min low) / current close."""
    roll_high = high.rolling(window).max()
    roll_low = low.rolling(window).min()
    return (roll_high - roll_low) / close


def build_compression_features(df: pd.DataFrame, bb_window: int, bb_num_std: float,
                                 atr_window: int, range_windows: list[int],
                                 percentile_lookback: int, price_col: str = "adj_close") -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)

    out["bb_width"] = bollinger_band_width(df[price_col], bb_window, bb_num_std)
    out["bb_width_percentile"] = rolling_percentile(out["bb_width"], percentile_lookback)

    atr = average_true_range(df["high"], df["low"], df[price_col], atr_window)
    out["atr"] = atr
    out["atr_percentile"] = rolling_percentile(atr, percentile_lookback)

    for w in range_windows:
        out[f"range_{w}"] = rolling_range(df["high"], df["low"], df[price_col], w)

    return out


def build_compression_regime(features: pd.DataFrame, threshold: float,
                               rv_percentile_col: str = "rv_20_percentile",
                               bb_percentile_col: str = "bb_width_percentile") -> pd.Series:
    """Boolean regime flag: True when both RV percentile and BB width percentile
    are at or below `threshold`. NaN (warmup period, before rolling windows are
    full) is preserved rather than silently coerced to False.
    """
    rv_pct = features[rv_percentile_col]
    bb_pct = features[bb_percentile_col]
    regime = (rv_pct <= threshold) & (bb_pct <= threshold)
    regime = regime.astype("boolean")  # pandas nullable boolean, supports NA
    regime[rv_pct.isna() | bb_pct.isna()] = pd.NA
    return regime.rename(f"compression_regime_{int(threshold * 100)}")
