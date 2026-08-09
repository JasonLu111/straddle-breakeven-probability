"""Orchestrates Module 3: turn cached weekly ORATS chains into a breakeven-event
dataset, joined with the Phase 1 compression regime features.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from src.backtest.straddle_pnl import compute_pnl
from src.targets.breakeven import select_straddle_entry


def _last_trading_day_on_or_before(trading_index: pd.DatetimeIndex, target_date: pd.Timestamp,
                                     max_lag_days: int = 3) -> pd.Timestamp | None:
    """ORATS lists standard monthly expirations by their OCC settlement date
    (the Saturday after the third Friday), not the last trading day (Friday).
    Falls back to the most recent trading day on/before `target_date`, within
    `max_lag_days` calendar days, so weekend/holiday listed dates resolve to
    the actual last trading day without silently reaching arbitrarily far back.
    """
    pos = trading_index.searchsorted(target_date, side="right") - 1
    if pos < 0:
        return None
    candidate = trading_index[pos]
    if (target_date - candidate).days > max_lag_days:
        return None
    return candidate


def build_breakeven_dataset(ticker: str, backtest_cfg: dict, options_cache_dir: str = "data/raw/options") -> pd.DataFrame:
    underlying = pd.read_parquet(f"data/raw/underlying/{ticker}.parquet")
    underlying.index = pd.to_datetime(underlying.index)

    entry_cfg = backtest_cfg["entry"]
    cost_cfg = backtest_cfg["costs"]

    chain_dir = Path(options_cache_dir) / ticker
    chain_files = sorted(chain_dir.glob("*.parquet"))

    rows = []
    n_no_expiration = 0
    n_no_expiry_price = 0

    for chain_file in chain_files:
        trade_date = chain_file.stem
        chain = pd.read_parquet(chain_file)

        entry = select_straddle_entry(
            chain,
            min_dte=entry_cfg["dte_range"][0],
            max_dte=entry_cfg["dte_range"][1],
            preferred_dte=sum(entry_cfg["dte_range"]) // 2,
        )
        if entry is None:
            n_no_expiration += 1
            continue

        expir_date = pd.Timestamp(entry.expir_date)
        pricing_date = _last_trading_day_on_or_before(underlying.index, expir_date, max_lag_days=3)
        if pricing_date is None:
            n_no_expiry_price += 1
            continue
        # Use the raw close, not adj_close: option strikes/prices are quoted
        # against the actual traded price, not the dividend-adjusted series
        # used for the Phase 1 return/volatility calculations. Mixing the two
        # would inject a spurious multi-decade dividend-adjustment gap here.
        expiry_price = float(underlying.loc[pricing_date, "close"])

        pnl_mid = compute_pnl(
            entry, expiry_price,
            commission_per_contract=cost_cfg["commission_per_contract"],
            slippage_pct=cost_cfg["slippage_pct"],
            use_ask_entry=False,
        )
        pnl_ask = compute_pnl(
            entry, expiry_price,
            commission_per_contract=cost_cfg["commission_per_contract"],
            slippage_pct=cost_cfg["slippage_pct"],
            use_ask_entry=True,
        )

        rows.append({
            "ticker": ticker,
            "trade_date": pd.Timestamp(trade_date),
            "expir_date": expir_date,
            "pricing_date": pricing_date,
            "dte": entry.dte,
            "strike": entry.strike,
            "stock_price": entry.stock_price,
            "expiry_price": expiry_price,
            "premium_mid": entry.premium_mid,
            "premium_ask": entry.premium_ask,
            "upper_breakeven_mid": entry.upper_breakeven_mid,
            "lower_breakeven_mid": entry.lower_breakeven_mid,
            "call_mid_iv": entry.call_mid_iv,
            "put_mid_iv": entry.put_mid_iv,
            "call_open_interest": entry.call_open_interest,
            "put_open_interest": entry.put_open_interest,
            "target_expiry": pnl_mid.target_expiry,
            "gross_pnl": pnl_mid.gross_pnl,
            "net_pnl": pnl_mid.net_pnl,
            "return_on_premium": pnl_mid.return_on_premium,
            "target_positive_net_pnl": pnl_mid.target_positive_net_pnl,
            "target_expiry_ask": pnl_ask.target_expiry,
            "net_pnl_ask": pnl_ask.net_pnl,
            "target_positive_net_pnl_ask": pnl_ask.target_positive_net_pnl,
        })

    dataset = pd.DataFrame(rows).sort_values("trade_date").reset_index(drop=True)

    print(f"{ticker}: {len(dataset)} valid weekly entries, "
          f"{n_no_expiration} weeks excluded (no expiration in DTE window), "
          f"{n_no_expiry_price} weeks excluded (no underlying price on expiry date)")

    return dataset, n_no_expiration, n_no_expiry_price


def join_with_regime(breakeven_df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    features = pd.read_parquet(f"data/processed/{ticker}_phase1.parquet")
    features.index = pd.to_datetime(features.index)
    regime_cols = [c for c in features.columns if c.startswith("compression_regime")]

    regime_at_entry = features[regime_cols].reindex(breakeven_df["trade_date"])
    regime_at_entry.index = breakeven_df.index
    return pd.concat([breakeven_df, regime_at_entry], axis=1)


def run(ticker: str, backtest_cfg_path: str = "configs/backtest.yaml") -> pd.DataFrame:
    with open(backtest_cfg_path, "r", encoding="utf-8") as f:
        backtest_cfg = yaml.safe_load(f)

    dataset, n_no_expiration, n_no_expiry_price = build_breakeven_dataset(ticker, backtest_cfg)
    dataset = join_with_regime(dataset, ticker)

    out_path = Path("data/processed") / f"{ticker}_phase2_breakeven.parquet"
    dataset.to_parquet(out_path)
    print(f"{ticker}: -> {out_path}")

    return dataset


if __name__ == "__main__":
    import sys
    tickers = sys.argv[1:] or ["SPY", "QQQ"]
    for t in tickers:
        run(t)
