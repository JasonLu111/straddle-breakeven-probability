import pandas as pd
import pytest

from src.backtest.entry_rules import (strategy_a_unconditional, strategy_b_compression_rule,
                                        strategy_c_probability_filtered)
from src.backtest.engine import compute_strategy_stats


def make_trades():
    return pd.DataFrame({
        "trade_date": pd.date_range("2020-01-03", periods=6, freq="7D"),
        "compression_regime_20": [True, False, True, False, False, True],
        "y_prob": [0.6, 0.3, 0.55, 0.2, 0.7, 0.1],
        "fold_train_median_prob": [0.5, 0.5, 0.5, 0.4, 0.4, 0.4],
        "net_pnl": [100, -50, 200, -30, 150, -400],
        "return_on_premium": [0.5, -0.2, 0.8, -0.1, 0.6, -1.0],
        "premium_mid": [5, 5, 5, 5, 5, 5],
    })


def test_strategy_a_selects_all_trades():
    trades = make_trades()
    mask = strategy_a_unconditional(trades)
    assert mask.all()
    assert mask.sum() == len(trades)


def test_strategy_b_selects_only_compression_weeks():
    trades = make_trades()
    mask = strategy_b_compression_rule(trades)
    assert mask.tolist() == [True, False, True, False, False, True]


def test_strategy_c_selects_only_prob_above_fold_threshold():
    trades = make_trades()
    mask = strategy_c_probability_filtered(trades)
    # row 0: 0.6>0.5 True; row1: 0.3>0.5 False; row2: 0.55>0.5 True;
    # row3: 0.2>0.4 False; row4: 0.7>0.4 True; row5: 0.1>0.4 False
    assert mask.tolist() == [True, False, True, False, True, False]


def test_strategy_c_threshold_is_per_fold_not_global():
    # same y_prob value (0.45) is selected in one fold-threshold context but not another
    trades = pd.DataFrame({
        "y_prob": [0.45, 0.45],
        "fold_train_median_prob": [0.4, 0.5],  # fold A threshold lower, fold B threshold higher
    })
    mask = strategy_c_probability_filtered(trades)
    assert mask.tolist() == [True, False]


def test_engine_computes_stats_only_over_selected_trades():
    trades = make_trades()
    mask = strategy_b_compression_rule(trades)
    stats = compute_strategy_stats(trades, mask)
    assert stats["n_trades"] == 3  # rows 0, 2, 5
    assert stats["avg_net_pnl"] == pytest.approx((100 + 200 - 400) / 3)


def test_engine_handles_empty_selection():
    trades = make_trades()
    empty_mask = pd.Series(False, index=trades.index)
    stats = compute_strategy_stats(trades, empty_mask)
    assert stats["n_trades"] == 0
