"""Module 3: breakeven event construction for a single ATM long straddle entry.

Selection rule (MVP, matches the research proposal's Module 3 spec):
  - Among expirations with DTE in [min_dte, max_dte], pick the one closest to
    `preferred_dte`.
  - Within that expiration, pick the strike closest to the underlying price
    (ATM).
  - Entry price uses (bid+ask)/2 as the primary convention, with a separate
    ask-only conservative variant for transaction-cost sensitivity.

A trade date with no expiration in [min_dte, max_dte] returns None (excluded,
not imputed) -- see reports/limitations.md for how often this happens.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class StraddleEntry:
    ticker: str
    trade_date: str
    expir_date: str
    dte: int
    strike: float
    stock_price: float
    call_bid: float
    call_ask: float
    put_bid: float
    put_ask: float
    call_mid_iv: float
    put_mid_iv: float
    call_open_interest: float
    put_open_interest: float
    call_volume: float
    put_volume: float

    @property
    def call_entry_mid(self) -> float:
        return (self.call_bid + self.call_ask) / 2

    @property
    def put_entry_mid(self) -> float:
        return (self.put_bid + self.put_ask) / 2

    @property
    def premium_mid(self) -> float:
        return self.call_entry_mid + self.put_entry_mid

    @property
    def premium_ask(self) -> float:
        """Conservative variant: pay the full ask on both legs."""
        return self.call_ask + self.put_ask

    @property
    def upper_breakeven_mid(self) -> float:
        return self.strike + self.premium_mid

    @property
    def lower_breakeven_mid(self) -> float:
        return self.strike - self.premium_mid


def select_straddle_entry(chain: pd.DataFrame, min_dte: int = 20, max_dte: int = 40,
                           preferred_dte: int = 30) -> StraddleEntry | None:
    """Select the ATM straddle entry for one day's option chain. Returns None if
    no expiration falls in [min_dte, max_dte] that day.
    """
    if chain.empty:
        return None

    in_window = chain[(chain["dte"] >= min_dte) & (chain["dte"] <= max_dte)]
    if in_window.empty:
        return None

    available_dtes = in_window["dte"].unique()
    chosen_dte = available_dtes[np.argmin(np.abs(available_dtes - preferred_dte))]
    expiry_slice = in_window[in_window["dte"] == chosen_dte].copy()

    stock_price = expiry_slice["stockPrice"].iloc[0]
    expiry_slice["strike_dist"] = (expiry_slice["strike"] - stock_price).abs()
    row = expiry_slice.sort_values("strike_dist").iloc[0]

    return StraddleEntry(
        ticker=row["ticker"],
        trade_date=row["tradeDate"],
        expir_date=row["expirDate"],
        dte=int(row["dte"]),
        strike=float(row["strike"]),
        stock_price=float(stock_price),
        call_bid=float(row["callBidPrice"]),
        call_ask=float(row["callAskPrice"]),
        put_bid=float(row["putBidPrice"]),
        put_ask=float(row["putAskPrice"]),
        call_mid_iv=float(row["callMidIv"]),
        put_mid_iv=float(row["putMidIv"]),
        call_open_interest=float(row["callOpenInterest"]),
        put_open_interest=float(row["putOpenInterest"]),
        call_volume=float(row["callVolume"]),
        put_volume=float(row["putVolume"]),
    )


def compute_target_expiry(entry: StraddleEntry, expiry_price: float, use_ask: bool = False) -> int:
    premium = entry.premium_ask if use_ask else entry.premium_mid
    return int(abs(expiry_price - entry.strike) > premium)
