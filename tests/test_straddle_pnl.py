import pytest

from src.backtest.straddle_pnl import CONTRACT_MULTIPLIER, compute_pnl
from src.targets.breakeven import StraddleEntry


def make_entry(strike=100.0, call_bid=2.9, call_ask=3.1, put_bid=2.9, put_ask=3.1):
    return StraddleEntry(
        ticker="TEST", trade_date="2020-01-01", expir_date="2020-01-31", dte=30,
        strike=strike, stock_price=strike,
        call_bid=call_bid, call_ask=call_ask, put_bid=put_bid, put_ask=put_ask,
        call_mid_iv=0.2, put_mid_iv=0.2,
        call_open_interest=100, put_open_interest=100, call_volume=10, put_volume=10,
    )


def test_premium_and_breakeven():
    entry = make_entry()
    assert entry.premium_mid == pytest.approx(6.0)
    assert entry.upper_breakeven_mid == pytest.approx(106.0)
    assert entry.lower_breakeven_mid == pytest.approx(94.0)


def test_pnl_matches_abs_value_identity():
    # PnL_T = |S_T - K| - premium, exactly, before transaction costs
    entry = make_entry(strike=100.0)
    expiry_price = 115.0
    pnl = compute_pnl(entry, expiry_price, commission_per_contract=0.0, slippage_pct=0.0)
    expected_gross_per_share = abs(expiry_price - entry.strike) - entry.premium_mid
    assert pnl.gross_pnl == pytest.approx(expected_gross_per_share * CONTRACT_MULTIPLIER)
    assert pnl.net_pnl == pytest.approx(pnl.gross_pnl)  # zero costs


def test_target_expiry_exactly_at_breakeven_is_zero():
    entry = make_entry(strike=100.0)  # premium_mid = 6.0
    pnl_at_breakeven = compute_pnl(entry, expiry_price=106.0, commission_per_contract=0.0)
    assert pnl_at_breakeven.target_expiry == 0  # strictly greater than, not >=

    pnl_past_breakeven = compute_pnl(entry, expiry_price=106.01, commission_per_contract=0.0)
    assert pnl_past_breakeven.target_expiry == 1


def test_commission_reduces_net_pnl_not_gross():
    entry = make_entry()
    pnl = compute_pnl(entry, expiry_price=115.0, commission_per_contract=0.65)
    assert pnl.net_pnl == pytest.approx(pnl.gross_pnl - 2 * 0.65)


def test_ask_entry_is_more_conservative_than_mid_entry():
    entry = make_entry()
    pnl_mid = compute_pnl(entry, expiry_price=104.0, commission_per_contract=0.0, use_ask_entry=False)
    pnl_ask = compute_pnl(entry, expiry_price=104.0, commission_per_contract=0.0, use_ask_entry=True)
    assert pnl_ask.net_pnl < pnl_mid.net_pnl  # ask price >= mid price -> worse entry cost


def test_pinned_at_strike_is_max_loss():
    entry = make_entry(strike=100.0)
    pnl = compute_pnl(entry, expiry_price=100.0, commission_per_contract=0.0)
    assert pnl.gross_pnl == pytest.approx(-entry.premium_mid * CONTRACT_MULTIPLIER)
    assert pnl.target_positive_net_pnl == 0
