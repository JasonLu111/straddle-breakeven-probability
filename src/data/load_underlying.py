"""Download and cache daily OHLCV data for underlying tickers."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml


def load_config(config_path: str | Path = "configs/data.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def download_ticker(ticker: str, start_date: str, end_date: str | None) -> pd.DataFrame:
    import yfinance as yf

    df = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        auto_adjust=False,
        progress=False,
    )
    if df.empty:
        raise RuntimeError(f"No data returned for {ticker}")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume",
    })
    df.index.name = "date"
    return df[["open", "high", "low", "close", "adj_close", "volume"]]


def validate_underlying(df: pd.DataFrame, ticker: str) -> None:
    if df.isnull().any().any():
        bad = df[df.isnull().any(axis=1)]
        raise ValueError(f"{ticker}: {len(bad)} rows contain nulls, e.g.\n{bad.head()}")
    if not df.index.is_monotonic_increasing:
        raise ValueError(f"{ticker}: index is not sorted ascending")
    if df.index.duplicated().any():
        raise ValueError(f"{ticker}: duplicate dates found")
    if (df["high"] < df["low"]).any():
        raise ValueError(f"{ticker}: found rows where high < low")


def run(config_path: str | Path = "configs/data.yaml") -> None:
    config = load_config(config_path)
    underlying_cfg = config["underlying"]
    raw_path = Path(underlying_cfg["raw_path"])
    raw_path.mkdir(parents=True, exist_ok=True)

    for ticker in underlying_cfg["tickers"]:
        df = download_ticker(ticker, underlying_cfg["start_date"], underlying_cfg["end_date"])
        validate_underlying(df, ticker)
        out_file = raw_path / f"{ticker}.parquet"
        df.to_parquet(out_file)
        print(f"{ticker}: {len(df)} rows, {df.index.min().date()} -> {df.index.max().date()} -> {out_file}")


if __name__ == "__main__":
    run()
