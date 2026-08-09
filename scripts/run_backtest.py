"""Phase 4: Strategy Comparison (H6).

Strategy A (unconditional), B (compression rule), and C (probability-filtered)
are compared over the *same* window: the 2019-2026 walk-forward test period,
because Strategy C only has model predictions there (the first 6 years,
2013-2018, were needed as Phase 3's initial training window and were never
held out, so no honest OOS probability exists for them). Comparing A/B over
the full 2013-2026 history against C over 2019-2026 only would be an apples-
to-oranges comparison; restricting all three to the common window is what
makes the comparison fair. A full-sample descriptive view of A/B (not
comparable to C) is reported separately for context only.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

from src.backtest.engine import compute_strategy_stats
from src.backtest.entry_rules import (strategy_a_unconditional, strategy_b_compression_rule,
                                        strategy_c_probability_filtered)

TICKERS = ["SPY", "QQQ"]
STRATEGIES = {
    "A_unconditional": strategy_a_unconditional,
    "B_compression_rule": strategy_b_compression_rule,
    "C_probability_filtered": strategy_c_probability_filtered,
}

RESULTS_DIR = Path("results/backtests")
FIGURES_DIR = Path("reports/figures")
TABLES_DIR = Path("reports/tables")


def load_common_window_trades(ticker: str) -> pd.DataFrame:
    breakeven = pd.read_parquet(f"data/processed/{ticker}_phase2_breakeven.parquet")
    thresholds = pd.read_parquet(f"results/predictions/{ticker}_strategy_c_thresholds.parquet")

    common = breakeven.merge(thresholds[["trade_date", "y_prob", "fold_train_median_prob"]],
                              on="trade_date", how="inner")
    return common.reset_index(drop=True)


def run_ticker(ticker: str) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    trades = load_common_window_trades(ticker)

    stats_rows = []
    masks = {}
    for name, rule_fn in STRATEGIES.items():
        mask = rule_fn(trades)
        masks[name] = mask
        row = {"ticker": ticker, "strategy": name}
        row.update(compute_strategy_stats(trades, mask))
        stats_rows.append(row)

        # gross (no transaction cost) variant, using premium_mid vs the
        # already-net-of-cost net_pnl -- reconstruct gross from gross_pnl col
        gross_row = {"ticker": ticker, "strategy": f"{name}_gross_no_costs"}
        gross_row.update(compute_strategy_stats(trades, mask, pnl_col="gross_pnl"))
        stats_rows.append(gross_row)

    pairwise = []
    strategy_names = list(STRATEGIES.keys())
    for i in range(len(strategy_names)):
        for j in range(i + 1, len(strategy_names)):
            a_name, b_name = strategy_names[i], strategy_names[j]
            a_pnl = trades.loc[masks[a_name], "net_pnl"]
            b_pnl = trades.loc[masks[b_name], "net_pnl"]
            if len(a_pnl) < 2 or len(b_pnl) < 2:
                continue
            t_stat, t_p = stats.ttest_ind(a_pnl, b_pnl, equal_var=False)
            u_stat, u_p = stats.mannwhitneyu(a_pnl, b_pnl, alternative="two-sided")
            pairwise.append({
                "ticker": ticker, "strategy_a": a_name, "strategy_b": b_name,
                "n_a": len(a_pnl), "n_b": len(b_pnl),
                "mean_diff": float(a_pnl.mean() - b_pnl.mean()),
                "welch_p_value": float(t_p), "mannwhitney_p_value": float(u_p),
            })

    return pd.DataFrame(stats_rows), masks, pd.DataFrame(pairwise), trades


def make_figures(ticker: str, trades: pd.DataFrame, masks: dict) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    for name, mask in masks.items():
        selected = trades.loc[mask].sort_values("trade_date")
        equity = selected["net_pnl"].cumsum()
        ax.plot(selected["trade_date"], equity, label=name, linewidth=1.2)
    ax.axhline(0, color="grey", linewidth=0.6, linestyle="--")
    ax.set_ylabel("Cumulative net PnL ($, trade-sequence order)")
    ax.set_title(f"{ticker}: strategy equity curves (common window {trades['trade_date'].min().date()}"
                 f" to {trades['trade_date'].max().date()})")
    ax.legend(fontsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"phase4_{ticker.lower()}_equity_curves.png", dpi=150)
    plt.close(fig)


def make_descriptive_full_sample_view(ticker: str) -> pd.DataFrame:
    """Strategy A/B over the FULL 2013-2026 history -- descriptive context
    only, NOT comparable to Strategy C's common-window numbers above."""
    breakeven = pd.read_parquet(f"data/processed/{ticker}_phase2_breakeven.parquet")
    rows = []
    for name, rule_fn in [("A_unconditional", strategy_a_unconditional),
                           ("B_compression_rule", strategy_b_compression_rule)]:
        mask = rule_fn(breakeven)
        row = {"ticker": ticker, "strategy": name, "window": "full_2013_2026_descriptive_only"}
        row.update(compute_strategy_stats(breakeven, mask))
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    all_stats, all_pairwise, all_full_sample = [], [], []
    for ticker in TICKERS:
        stats_df, masks, pairwise_df, trades = run_ticker(ticker)
        all_stats.append(stats_df)
        all_pairwise.append(pairwise_df)
        make_figures(ticker, trades, masks)
        all_full_sample.append(make_descriptive_full_sample_view(ticker))

        print(f"\n=== {ticker} (common window, n={len(trades)}) ===")
        print(stats_df[stats_df.strategy.isin(STRATEGIES.keys())][
            ["strategy", "n_trades", "win_rate", "avg_net_pnl", "max_drawdown", "cvar_5pct", "longest_losing_streak"]
        ].to_string(index=False))

    stats_all = pd.concat(all_stats, ignore_index=True)
    pairwise_all = pd.concat(all_pairwise, ignore_index=True)
    full_sample_all = pd.concat(all_full_sample, ignore_index=True)

    stats_all.round(4).to_csv(RESULTS_DIR / "phase4_strategy_stats.csv", index=False)
    pairwise_all.round(4).to_csv(RESULTS_DIR / "phase4_pairwise_tests.csv", index=False)
    full_sample_all.round(4).to_csv(RESULTS_DIR / "phase4_full_sample_descriptive.csv", index=False)

    with open(TABLES_DIR / "phase4_strategy_comparison.md", "w", encoding="utf-8") as f:
        main_cols = ["ticker", "strategy", "n_trades", "win_rate", "avg_net_pnl", "return_on_premium_mean",
                     "max_drawdown", "cvar_5pct", "longest_losing_streak", "annualized_trade_count",
                     "total_premium_spent"]
        f.write(stats_all[stats_all.strategy.isin(STRATEGIES.keys())][main_cols].round(4).to_markdown(index=False))

    with open(TABLES_DIR / "phase4_pairwise_tests.md", "w", encoding="utf-8") as f:
        f.write(pairwise_all.round(4).to_markdown(index=False))

    print(f"\nFull results: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
