"""Fetch (and cache) weekly Friday ORATS option chains for Phase 2.

Backtest window starts 2013-01-01: empirically verified (see
reports/limitations.md) that SPY/QQQ weekly expirations landing in the
20-40 DTE entry window are not reliably available before 2013 (monthly-only
expirations dominate 2007-2012, so a 20-40 DTE target frequently has no
match at all).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.data.load_options import fetch_chains_for_dates

BACKTEST_START_DATE = "2013-01-01"


def get_trading_fridays(ticker: str, start_date: str) -> list[str]:
    """Actual trading Fridays (not calendar Fridays) from the cached underlying
    price history, so we never request a date the market was closed.
    """
    df = pd.read_parquet(f"data/raw/underlying/{ticker}.parquet")
    df = df[df.index >= start_date]
    fridays = df.index[df.index.dayofweek == 4]
    return [d.strftime("%Y-%m-%d") for d in fridays]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", nargs="*", default=["SPY", "QQQ"])
    parser.add_argument("--start-date", default=BACKTEST_START_DATE)
    args = parser.parse_args()

    for ticker in args.tickers:
        fridays = get_trading_fridays(ticker, args.start_date)
        print(f"{ticker}: {len(fridays)} trading Fridays from {fridays[0]} to {fridays[-1]}")
        fetch_chains_for_dates(ticker, fridays)


if __name__ == "__main__":
    main()
