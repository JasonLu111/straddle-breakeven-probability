"""Historical option chain loader (Phase 2 — not yet implemented).

Blocked on: (1) an active ORATS API key, and (2) confirming which ORATS
product/plan is subscribed (History EOD vs. SMV Summaries vs. tick-level
chains), since that determines the endpoint and response schema. See
.env.example and reports/limitations.md.

Once unblocked, this module must produce a DataFrame with (at minimum) the
columns listed in the "選擇權資料" section of the original research proposal:
trade_date, expiration_date, strike, right (call/put), bid, ask,
implied_volatility, volume, open_interest, delta, underlying_price.
Entry price convention: (bid + ask) / 2, with a separate conservative
transaction-cost pass using the ask price -- see configs/backtest.yaml.
"""
from __future__ import annotations

import os

import pandas as pd


class OratsNotConfiguredError(RuntimeError):
    pass


def load_option_chain(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    api_key = os.environ.get("ORATS_API_KEY")
    if not api_key:
        raise OratsNotConfiguredError(
            "ORATS_API_KEY is not set (see .env.example) and the ORATS product/plan "
            "has not been confirmed yet. This loader is a placeholder for Phase 2 -- "
            "see the module docstring."
        )
    raise NotImplementedError(
        "ORATS endpoint/schema not yet finalized against the actual subscribed plan."
    )
