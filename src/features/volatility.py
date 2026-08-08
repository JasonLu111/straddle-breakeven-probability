"""Realized volatility and rolling percentile features.

All rolling windows are strictly backward-looking: the value at row t uses only
rows [t-window+1, t] (or [t-lookback+1, t] for percentiles), never future data.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def log_returns(close: pd.Series) -> pd.Series:
    return np.log(close / close.shift(1))


def realized_volatility(returns: pd.Series, window: int, annualization_factor: int = 252) -> pd.Series:
    """Annualized realized volatility over a trailing window of daily log returns."""
    return returns.rolling(window).std() * np.sqrt(annualization_factor)


def rolling_percentile(series: pd.Series, lookback: int) -> pd.Series:
    """Percentile rank (0-1) of the current value within the trailing `lookback` window,
    inclusive of the current observation.
    """
    def _pct_rank(window: np.ndarray) -> float:
        current = window[-1]
        return float((window <= current).mean())

    return series.rolling(lookback, min_periods=lookback).apply(_pct_rank, raw=True)


def build_volatility_features(df: pd.DataFrame, windows: list[int], annualization_factor: int,
                                percentile_lookback: int, price_col: str = "adj_close") -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    ret = log_returns(df[price_col])
    for w in windows:
        out[f"rv_{w}"] = realized_volatility(ret, w, annualization_factor)

    out["rv_20_percentile"] = rolling_percentile(out["rv_20"], percentile_lookback)
    out["rv_term_ratio_10_60"] = out["rv_10"] / out["rv_60"]

    vol_of_vol_window = max(windows)
    out["vol_of_vol"] = out["rv_20"].rolling(vol_of_vol_window).std()

    return out
