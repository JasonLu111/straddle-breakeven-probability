"""Historical option chain loader (ORATS Data API, History/EOD plan).

Verified against the live API on 2026-08-09:
- Base URL: https://api.orats.io/datav2/hist/strikes
- Auth: `token` query param
- Full-day chain for SPY is ~1,900-3,800 rows depending on era, well under the
  API's 5,000 row/request cap -- so we fetch the *whole* day unfiltered and do
  DTE/strike selection locally in pandas, rather than relying on the API's
  `dte` filter (empirically, a narrow dte filter can return an empty result on
  a day that has no expiration in that exact window, even though the ticker
  has data that day -- indistinguishable from "no data at all" unless you
  fetch unfiltered first).
- Coverage: data exists back to ~2007, but expirations are sparse before
  ~2011 (monthly-only in the earlier years, so a 20-40 DTE target frequently
  has no match). See reports/limitations.md.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.orats.io/datav2/hist/strikes"
REQUEST_INTERVAL_SEC = 0.3  # conservative rate limit (well under documented 100-1000 req/min)


class OratsNotConfiguredError(RuntimeError):
    pass


def _get_api_key() -> str:
    api_key = os.environ.get("ORATS_API_KEY")
    if not api_key:
        raise OratsNotConfiguredError(
            "ORATS_API_KEY is not set. Copy .env.example to .env and fill it in."
        )
    return api_key


_ID_COLUMNS = {"ticker", "tradeDate", "expirDate", "quoteDate", "updatedAt", "expiryTod"}


def _sanitize_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """ORATS occasionally returns a malformed/out-of-range numeric value on a
    single row (observed: a `residualRate` value too large for int64, which
    makes pyarrow's dtype inference raise on the whole column). Force every
    non-identifier column through pd.to_numeric so a single bad cell becomes
    NaN instead of crashing the parquet write.
    """
    for col in df.columns:
        if col not in _ID_COLUMNS:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
    return df


def fetch_chain_for_date(ticker: str, trade_date: str, cache_dir: str | Path = "data/raw/options",
                          force_refresh: bool = False) -> pd.DataFrame:
    """Fetch (or load from cache) the full option chain for `ticker` on `trade_date`
    (YYYY-MM-DD). Returns an empty DataFrame if ORATS has no data for that date
    (e.g. market holiday, or before the ticker's option-chain coverage begins).
    """
    cache_path = Path(cache_dir) / ticker / f"{trade_date}.parquet"

    if cache_path.exists() and not force_refresh:
        return pd.read_parquet(cache_path)

    api_key = _get_api_key()
    resp = requests.get(BASE_URL, params={"token": api_key, "tickers": ticker, "tradeDate": trade_date}, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    df = pd.DataFrame(payload.get("data", []))
    if not df.empty:
        df = _sanitize_numeric_columns(df)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache_path)
    time.sleep(REQUEST_INTERVAL_SEC)
    return df


def fetch_chains_for_dates(ticker: str, trade_dates: list[str], cache_dir: str | Path = "data/raw/options",
                            force_refresh: bool = False, verbose: bool = True) -> dict[str, pd.DataFrame]:
    """Fetch (or load from cache) chains for a list of trade dates. Only makes a
    live API call for dates not already cached, so reruns are cheap.
    """
    chains = {}
    failed_dates = []
    n_fetched = 0
    for i, d in enumerate(trade_dates):
        cache_path = Path(cache_dir) / ticker / f"{d}.parquet"
        was_cached = cache_path.exists() and not force_refresh
        try:
            df = fetch_chain_for_date(ticker, d, cache_dir, force_refresh)
        except Exception as exc:
            print(f"  {ticker} {d}: FAILED ({type(exc).__name__}: {exc}) -- skipping")
            failed_dates.append(d)
            continue
        chains[d] = df
        if not was_cached:
            n_fetched += 1
        if verbose and (i + 1) % 50 == 0:
            print(f"  {ticker}: {i + 1}/{len(trade_dates)} dates processed ({n_fetched} live-fetched)")
    if verbose:
        print(f"{ticker}: done. {len(trade_dates)} dates total, {n_fetched} fetched live, "
              f"{len(trade_dates) - n_fetched - len(failed_dates)} from cache, "
              f"{len(failed_dates)} failed: {failed_dates}")
    return chains
