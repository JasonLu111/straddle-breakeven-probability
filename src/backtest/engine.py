"""Aggregates a strategy's selected trades into the Module 5 performance table."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.backtest.risk_metrics import annualized_trade_count, cvar, longest_losing_streak, max_drawdown


def compute_strategy_stats(trades: pd.DataFrame, entry_mask: pd.Series, pnl_col: str = "net_pnl",
                            premium_col: str = "premium_mid", date_col: str = "trade_date") -> dict:
    selected = trades.loc[entry_mask].sort_values(date_col)
    pnl = selected[pnl_col]

    if len(selected) == 0:
        return {"n_trades": 0}

    return {
        "n_trades": len(selected),
        "win_rate": float((pnl > 0).mean()),
        "avg_net_pnl": float(pnl.mean()),
        "median_net_pnl": float(pnl.median()),
        "std_net_pnl": float(pnl.std()) if len(pnl) > 1 else float("nan"),
        "return_on_premium_mean": float(selected["return_on_premium"].mean()),
        "max_drawdown": max_drawdown(pnl),
        "cvar_5pct": cvar(pnl, alpha=0.05),
        "longest_losing_streak": longest_losing_streak(pnl),
        "annualized_trade_count": annualized_trade_count(selected[date_col]),
        "total_premium_spent": float((selected[premium_col] * 100).sum()),
        "total_net_pnl": float(pnl.sum()),
    }
