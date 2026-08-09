"""Trade-level risk metrics for a sequence of realized straddle trades.

All metrics operate on trade-sequence order (the order trades were actually
entered), not calendar time -- appropriate here since the backtest.yaml entry
rule holds at most one concurrent position, so trades never overlap.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def max_drawdown(pnl_sequence: pd.Series) -> float:
    """Largest peak-to-trough decline in cumulative PnL, in dollars (negative or 0)."""
    if len(pnl_sequence) == 0:
        return float("nan")
    cumulative = pnl_sequence.cumsum()
    running_max = cumulative.cummax()
    drawdown = cumulative - running_max
    return float(drawdown.min())


def cvar(pnl_sequence: pd.Series, alpha: float = 0.05) -> float:
    """Conditional Value at Risk: mean PnL among the worst `alpha` fraction of
    trades. Returns NaN if fewer than 5 trades fall in that tail (too small a
    sample for the average to mean anything).
    """
    if len(pnl_sequence) == 0:
        return float("nan")
    threshold = pnl_sequence.quantile(alpha)
    tail = pnl_sequence[pnl_sequence <= threshold]
    if len(tail) < 5:
        return float("nan")
    return float(tail.mean())


def longest_losing_streak(pnl_sequence: pd.Series) -> int:
    """Longest run of consecutive trades with net_pnl < 0, in trade-sequence order."""
    is_loss = (pnl_sequence < 0).to_numpy()
    if len(is_loss) == 0:
        return 0
    longest = current = 0
    for loss in is_loss:
        current = current + 1 if loss else 0
        longest = max(longest, current)
    return int(longest)


def annualized_trade_count(trade_dates: pd.Series) -> float:
    if len(trade_dates) < 2:
        return float("nan")
    span_years = (trade_dates.max() - trade_dates.min()).days / 365.25
    if span_years <= 0:
        return float("nan")
    return len(trade_dates) / span_years
