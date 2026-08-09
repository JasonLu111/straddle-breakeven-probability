"""Phase 2 statistical test runner: H2 (does volatility compression predict a
higher probability of the straddle actually breaking even by expiration,
using real option premiums -- not the Phase 1 proxy event)?
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.statistics.conditional_probability import conditional_probability_table
from src.statistics.hypothesis_tests import benjamini_hochberg, compare_groups

TICKERS = ["SPY", "QQQ"]
THRESHOLDS = [10, 20, 30]
PRIMARY_SPEC = {"ticker": "SPY", "threshold": 20}

RESULTS_DIR = Path("results/statistical_tests")
FIGURES_DIR = Path("reports/figures")
TABLES_DIR = Path("reports/tables")


def run_all_specs() -> pd.DataFrame:
    rows = []
    for ticker in TICKERS:
        df = pd.read_parquet(f"data/processed/{ticker}_phase2_breakeven.parquet")
        for threshold in THRESHOLDS:
            regime_col = f"compression_regime_{threshold}"
            prob_stats = conditional_probability_table(df["target_expiry"], df[regime_col])
            pnl_stats = compare_groups(df["net_pnl"], df[regime_col])

            is_primary = ticker == PRIMARY_SPEC["ticker"] and threshold == PRIMARY_SPEC["threshold"]
            rows.append({
                "ticker": ticker,
                "compression_threshold_pct": threshold,
                "is_primary_spec": is_primary,
                "n_trades_total": len(df),
                **{f"prob_{k}": v for k, v in prob_stats.items()},
                **{f"pnl_{k}": v for k, v in pnl_stats.items()},
            })

    results = pd.DataFrame(rows)
    results["pnl_welch_reject_bh"] = benjamini_hochberg(results["pnl_welch_p_value"].tolist())
    return results


def make_figures(results: pd.DataFrame) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(f"data/processed/{PRIMARY_SPEC['ticker']}_phase2_breakeven.parquet")
    regime_col = f"compression_regime_{PRIMARY_SPEC['threshold']}"
    valid = df.dropna(subset=["net_pnl", regime_col])

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(["Normal regime", "Compression regime"], [
        results.loc[(results.ticker == PRIMARY_SPEC["ticker"]) & (results.compression_threshold_pct == PRIMARY_SPEC["threshold"]), "prob_p_unconditional"].iloc[0],
        results.loc[(results.ticker == PRIMARY_SPEC["ticker"]) & (results.compression_threshold_pct == PRIMARY_SPEC["threshold"]), "prob_p_conditional"].iloc[0],
    ])
    ax.set_ylabel("P(breakeven by expiry)")
    ax.set_title(f"{PRIMARY_SPEC['ticker']}: real breakeven probability\n(primary spec: {PRIMARY_SPEC['threshold']}th pct threshold)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "h2_breakeven_probability.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    data_to_plot = [
        valid.loc[~valid[regime_col].astype(bool), "net_pnl"],
        valid.loc[valid[regime_col].astype(bool), "net_pnl"],
    ]
    ax.boxplot(data_to_plot, tick_labels=["Normal regime", "Compression regime"], showfliers=False)
    ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ax.set_ylabel("Net PnL per straddle contract ($)")
    ax.set_title(f"{PRIMARY_SPEC['ticker']}: net straddle PnL by regime")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "h2_net_pnl_by_regime.png", dpi=150)
    plt.close(fig)


def make_summary_table(results: pd.DataFrame) -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    cols = [
        "ticker", "compression_threshold_pct", "is_primary_spec", "n_trades_total",
        "prob_n_total", "prob_n_condition_true",
        "prob_p_conditional", "prob_p_unconditional", "prob_probability_difference", "prob_probability_ratio",
        "pnl_mean_treatment", "pnl_mean_control", "pnl_mean_difference", "pnl_welch_p_value", "pnl_welch_reject_bh",
    ]
    summary = results[cols].copy()
    round_cols = [c for c in summary.columns if "p_value" not in c]
    summary[round_cols] = summary[round_cols].round(4)
    summary.to_csv(TABLES_DIR / "h2_summary_table.csv", index=False)
    with open(TABLES_DIR / "h2_summary_table.md", "w", encoding="utf-8") as f:
        f.write(summary.to_markdown(index=False))


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results = run_all_specs()
    results.to_csv(RESULTS_DIR / "phase2_h2_results.csv", index=False)
    with open(RESULTS_DIR / "phase2_h2_results.json", "w", encoding="utf-8") as f:
        json.dump(json.loads(results.to_json(orient="records")), f, indent=2)

    make_figures(results)
    make_summary_table(results)

    primary = results[results["is_primary_spec"]].iloc[0]
    print("=== Primary specification result (SPY, 20th pct threshold) ===")
    print(f"n_trades={primary['n_trades_total']}, n_compression={primary['prob_n_condition_true']}")
    print(f"P(breakeven | compression)={primary['prob_p_conditional']:.3f}, "
          f"P(breakeven) unconditional={primary['prob_p_unconditional']:.3f}, "
          f"ratio={primary['prob_probability_ratio']:.3f}")
    print(f"mean net PnL: compression=${primary['pnl_mean_treatment']:.2f}, normal=${primary['pnl_mean_control']:.2f}, "
          f"Welch p={primary['pnl_welch_p_value']:.4f}")
    print(f"\nFull results: {RESULTS_DIR / 'phase2_h2_results.csv'}")


if __name__ == "__main__":
    main()
