import pandas as pd
import pytest

from src.targets.breakeven import select_straddle_entry
from src.targets.build_breakeven_dataset import _last_trading_day_on_or_before


def make_chain_row(strike, dte, stock_price=100.0, expir_date="2020-02-01"):
    return {
        "ticker": "TEST", "tradeDate": "2020-01-01", "expirDate": expir_date, "dte": dte,
        "strike": strike, "stockPrice": stock_price,
        "callBidPrice": 3.0, "callAskPrice": 3.2, "putBidPrice": 2.8, "putAskPrice": 3.0,
        "callMidIv": 0.2, "putMidIv": 0.21,
        "callOpenInterest": 50, "putOpenInterest": 60, "callVolume": 5, "putVolume": 6,
    }


def test_selects_closest_dte_to_preferred_within_window():
    rows = [make_chain_row(100, dte=d) for d in [10, 22, 29, 45]]
    chain = pd.DataFrame(rows)
    entry = select_straddle_entry(chain, min_dte=20, max_dte=40, preferred_dte=30)
    assert entry is not None
    assert entry.dte == 29  # closer to 30 than 22, and 10/45 are out of window


def test_selects_closest_atm_strike_within_chosen_expiration():
    rows = [make_chain_row(strike, dte=30, stock_price=100.0) for strike in [90, 98, 101, 110]]
    chain = pd.DataFrame(rows)
    entry = select_straddle_entry(chain, min_dte=20, max_dte=40, preferred_dte=30)
    assert entry.strike == 101  # closer to 100 than 98 (dist 1 vs 2)


def test_returns_none_when_no_expiration_in_window():
    rows = [make_chain_row(100, dte=d) for d in [8, 16, 44, 72]]
    chain = pd.DataFrame(rows)
    entry = select_straddle_entry(chain, min_dte=20, max_dte=40, preferred_dte=30)
    assert entry is None


def test_returns_none_on_empty_chain():
    chain = pd.DataFrame(columns=["dte", "strike", "stockPrice"])
    assert select_straddle_entry(chain) is None


def test_does_not_mix_strikes_across_different_expirations():
    # closest-to-preferred expiration is dte=30 (strike 101 available there);
    # a much closer ATM strike (100) exists only at dte=45, which must be ignored
    rows = [
        make_chain_row(100, dte=45, expir_date="2020-02-15"),
        make_chain_row(105, dte=30, expir_date="2020-02-01"),
    ]
    chain = pd.DataFrame(rows)
    entry = select_straddle_entry(chain, min_dte=20, max_dte=40, preferred_dte=30)
    assert entry.dte == 30
    assert entry.strike == 105


def test_last_trading_day_resolves_occ_saturday_convention():
    # OCC lists standard monthly expirations as the Saturday after the third
    # Friday; the actual last trading day is that Friday.
    trading_days = pd.DatetimeIndex(["2013-02-13", "2013-02-14", "2013-02-15"])  # Wed/Thu/Fri
    result = _last_trading_day_on_or_before(trading_days, pd.Timestamp("2013-02-16"), max_lag_days=3)  # Saturday
    assert result == pd.Timestamp("2013-02-15")


def test_last_trading_day_returns_none_beyond_lag_tolerance():
    trading_days = pd.DatetimeIndex(["2013-01-01"])
    result = _last_trading_day_on_or_before(trading_days, pd.Timestamp("2013-01-10"), max_lag_days=3)
    assert result is None


def test_last_trading_day_returns_none_when_target_before_all_data():
    trading_days = pd.DatetimeIndex(["2013-05-01", "2013-05-02"])
    result = _last_trading_day_on_or_before(trading_days, pd.Timestamp("2013-01-01"), max_lag_days=3)
    assert result is None
