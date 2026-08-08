import numpy as np
import pandas as pd
import pytest

from src.features.volatility import log_returns, realized_volatility, rolling_percentile


def test_log_returns_matches_manual_calc():
    close = pd.Series([100.0, 110.0, 99.0, 108.9])
    result = log_returns(close)
    expected = pd.Series([np.nan, np.log(1.1), np.log(99 / 110), np.log(108.9 / 99)])
    pd.testing.assert_series_equal(result, expected, check_names=False)


def test_realized_volatility_constant_returns_gives_zero_vol():
    # constant daily return -> zero rolling std -> zero realized vol
    returns = pd.Series([0.001] * 30)
    rv = realized_volatility(returns, window=10, annualization_factor=252)
    assert rv.iloc[15:].abs().max() < 1e-10


def test_realized_volatility_known_value():
    rng = np.random.default_rng(0)
    daily_std = 0.01
    returns = pd.Series(rng.normal(0, daily_std, size=5000))
    rv = realized_volatility(returns, window=250, annualization_factor=252)
    expected = daily_std * np.sqrt(252)
    # sample estimate should be within ~15% of the true annualized vol
    assert abs(rv.iloc[-1] - expected) / expected < 0.15


def test_rolling_percentile_current_max_is_one():
    series = pd.Series(range(1, 21), dtype=float)  # strictly increasing
    pct = rolling_percentile(series, lookback=10)
    # for a strictly increasing series, the current value is always the max of
    # its trailing window -> percentile rank should be 1.0
    assert (pct.dropna() == 1.0).all()


def test_rolling_percentile_bounds():
    rng = np.random.default_rng(1)
    series = pd.Series(rng.normal(size=500))
    pct = rolling_percentile(series, lookback=100)
    valid = pct.dropna()
    assert (valid >= 0).all() and (valid <= 1).all()
