"""Market-state features: momentum, distance from moving average, volume, downside risk."""
from __future__ import annotations

import numpy as np
import pandas as pd


def momentum(close: pd.Series, window: int) -> pd.Series:
    return close / close.shift(window) - 1.0


def distance_from_ma(close: pd.Series, window: int) -> pd.Series:
    ma = close.rolling(window).mean()
    return close / ma - 1.0


def volume_change(volume: pd.Series, window: int = 20) -> pd.Series:
    return volume / volume.rolling(window).mean() - 1.0


def downside_semivolatility(returns: pd.Series, window: int, annualization_factor: int = 252) -> pd.Series:
    downside = returns.where(returns < 0, 0.0)
    return downside.rolling(window).std() * np.sqrt(annualization_factor)


def upside_downside_vol_ratio(returns: pd.Series, window: int, annualization_factor: int = 252) -> pd.Series:
    upside = returns.where(returns > 0, 0.0)
    downside = returns.where(returns < 0, 0.0)
    up_vol = upside.rolling(window).std() * np.sqrt(annualization_factor)
    down_vol = downside.rolling(window).std() * np.sqrt(annualization_factor)
    return up_vol / down_vol


def build_momentum_features(df: pd.DataFrame, momentum_windows: list[int], ma_window: int,
                              price_col: str = "adj_close") -> pd.DataFrame:
    from src.features.volatility import log_returns

    out = pd.DataFrame(index=df.index)
    close = df[price_col]
    ret = log_returns(close)

    for w in momentum_windows:
        out[f"momentum_{w}"] = momentum(close, w)

    out["distance_from_ma20"] = distance_from_ma(close, ma_window)
    out["volume_change"] = volume_change(df["volume"], ma_window)
    out["downside_semivolatility"] = downside_semivolatility(ret, max(momentum_windows[-1], ma_window))
    out["upside_downside_vol_ratio"] = upside_downside_vol_ratio(ret, max(momentum_windows[-1], ma_window))

    return out
