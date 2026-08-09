"""Module 4 option-cost features: the variables that separate 'volatility looks
compressed' from 'the straddle is actually cheap relative to what it costs'.
"""
from __future__ import annotations

import pandas as pd


def build_option_cost_features(breakeven_df: pd.DataFrame, rv_20: pd.Series) -> pd.DataFrame:
    """breakeven_df: one row per weekly trade (from build_breakeven_dataset), must
    contain trade_date, stock_price, premium_mid, call_mid_iv, put_mid_iv, dte and
    the raw bid/ask fields are NOT retained in that table -- bid_ask_spread_pct is
    therefore approximated from premium_mid vs premium_ask (the two entry-cost
    variants already computed), which is the spread cost actually paid, rather
    than re-deriving it from individual leg bid/ask (equivalent under the
    (bid+ask)/2 vs ask-only convention already used elsewhere in this project).
    rv_20: Phase 1 realized-vol series indexed by date (from {ticker}_phase1.parquet).
    """
    out = pd.DataFrame(index=breakeven_df.index)

    out["straddle_premium_pct"] = breakeven_df["premium_mid"] / breakeven_df["stock_price"]
    out["atm_implied_volatility"] = (breakeven_df["call_mid_iv"] + breakeven_df["put_mid_iv"]) / 2
    out["put_call_iv_difference"] = breakeven_df["put_mid_iv"] - breakeven_df["call_mid_iv"]
    out["days_to_expiry"] = breakeven_df["dte"]
    out["bid_ask_spread_pct"] = (breakeven_df["premium_ask"] - breakeven_df["premium_mid"]) / breakeven_df["premium_mid"]

    rv_20_at_entry = rv_20.reindex(breakeven_df["trade_date"])
    rv_20_at_entry.index = breakeven_df.index
    out["iv_minus_rv"] = out["atm_implied_volatility"] - rv_20_at_entry

    return out
