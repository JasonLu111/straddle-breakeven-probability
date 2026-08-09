import pandas as pd
import pytest

from src.backtest.risk_metrics import annualized_trade_count, cvar, longest_losing_streak, max_drawdown


def test_max_drawdown_on_simple_sequence():
    # cumulative: 100, 150, 50, 100, 30  -> peak 150, trough 30 -> drawdown -120
    pnl = pd.Series([100, 50, -100, 50, -70])
    assert max_drawdown(pnl) == pytest.approx(-120)


def test_max_drawdown_all_gains_is_zero():
    pnl = pd.Series([10, 20, 30])
    assert max_drawdown(pnl) == pytest.approx(0)


def test_max_drawdown_empty_is_nan():
    assert pd.isna(max_drawdown(pd.Series([], dtype=float)))


def test_longest_losing_streak_counts_consecutive_losses():
    pnl = pd.Series([10, -5, -5, -5, 10, -5, -5, 10])
    assert longest_losing_streak(pnl) == 3


def test_longest_losing_streak_zero_when_no_losses():
    pnl = pd.Series([10, 20, 0, 30])
    assert longest_losing_streak(pnl) == 0


def test_cvar_is_mean_of_worst_tail():
    # 100 trades, worst 5 (alpha=0.05) are the five -100s
    pnl = pd.Series([-100] * 5 + [10] * 95)
    result = cvar(pnl, alpha=0.05)
    assert result == pytest.approx(-100, rel=0.1)


def test_cvar_nan_when_tail_too_small():
    pnl = pd.Series([10, 20, 30])  # far fewer than 5 in any 5% tail
    assert pd.isna(cvar(pnl, alpha=0.05))


def test_annualized_trade_count_two_years_weekly():
    dates = pd.Series(pd.date_range("2020-01-03", periods=104, freq="7D"))  # ~2 years weekly
    result = annualized_trade_count(dates)
    assert 50 < result < 54
