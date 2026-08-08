"""Phase 1 statistical test runner: H1 (does volatility compression predict larger
future absolute returns?).

Runs the primary pre-registered specification (SPY, 20th percentile compression
threshold, 20-day horizon) plus robustness checks (QQQ, 10th/30th percentile
thresholds, 10-day horizon), with Benjamini-Hochberg FDR control applied across
all p-values to guard against data-snooping from testing multiple specifications.
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
HORIZONS = [10, 20]
THRESHOLDS = [10, 20, 30]  # percentile thresholds (compression_regime_{p} columns)
PRIMARY_SPEC = {"ticker": "SPY", "horizon": 20, "threshold": 20}
LARGE_MOVE_QUANTILE = 0.75  # proxy "large move" event: top quartile of unconditional fwd abs return

RESULTS_DIR = Path("results/statistical_tests")
FIGURES_DIR = Path("reports/figures")
TABLES_DIR = Path("reports/tables")


def large_move_event(fwd_abs_return: pd.Series, quantile: float = LARGE_MOVE_QUANTILE) -> pd.Series:
    threshold = fwd_abs_return.quantile(quantile)
    event = (fwd_abs_return > threshold).astype("boolean")
    event[fwd_abs_return.isna()] = pd.NA
    return event, threshold


def run_all_specs() -> pd.DataFrame:
    rows = []
    for ticker in TICKERS:
        df = pd.read_parquet(f"data/processed/{ticker}_phase1.parquet")
        for horizon in HORIZONS:
            outcome_col = f"fwd_abs_return_{horizon}d"
            event, event_threshold = large_move_event(df[outcome_col])
            for threshold in THRESHOLDS:
                regime_col = f"compression_regime_{threshold}"
                group_stats = compare_groups(df[outcome_col], df[regime_col])
                prob_stats = conditional_probability_table(event, df[regime_col])

                is_primary = (
                    ticker == PRIMARY_SPEC["ticker"]
                    and horizon == PRIMARY_SPEC["horizon"]
                    and threshold == PRIMARY_SPEC["threshold"]
                )

                row = {
                    "ticker": ticker,
                    "horizon_days": horizon,
                    "compression_threshold_pct": threshold,
                    "is_primary_spec": is_primary,
                    "large_move_event_threshold": event_threshold,
                    **{f"group_{k}": v for k, v in group_stats.items()},
                    **{f"prob_{k}": v for k, v in prob_stats.items()},
                }
                rows.append(row)

    results = pd.DataFrame(rows)
    results["welch_reject_bh"] = benjamini_hochberg(results["group_welch_p_value"].tolist())
    results["mannwhitney_reject_bh"] = benjamini_hochberg(results["group_mannwhitney_p_value"].tolist())
    return results


def make_figures(results: pd.DataFrame) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    primary = results[results["is_primary_spec"]].iloc[0]

    df = pd.read_parquet(f"data/processed/{PRIMARY_SPEC['ticker']}_phase1.parquet")
    outcome_col = f"fwd_abs_return_{PRIMARY_SPEC['horizon']}d"
    regime_col = f"compression_regime_{PRIMARY_SPEC['threshold']}"
    valid = df.dropna(subset=[outcome_col, regime_col])

    fig, ax = plt.subplots(figsize=(6, 4))
    data_to_plot = [
        valid.loc[~valid[regime_col].astype(bool), outcome_col],
        valid.loc[valid[regime_col].astype(bool), outcome_col],
    ]
    ax.boxplot(data_to_plot, tick_labels=["Normal regime", "Compression regime"], showfliers=False)
    ax.set_ylabel(f"Forward {PRIMARY_SPEC['horizon']}D absolute return")
    ax.set_title(f"{PRIMARY_SPEC['ticker']}: forward return by volatility regime\n"
                 f"(primary spec: {PRIMARY_SPEC['threshold']}th pct threshold)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "h1_forward_return_by_regime.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df.index, df["adj_close"], color="black", linewidth=0.8, label=f"{PRIMARY_SPEC['ticker']} adj close")
    regime_mask = df[regime_col].astype("boolean").fillna(False).astype(bool)
    ax.fill_between(df.index, df["adj_close"].min(), df["adj_close"].max(),
                     where=regime_mask, color="orange", alpha=0.3, label="Compression regime")
    ax.set_yscale("log")
    ax.set_title(f"{PRIMARY_SPEC['ticker']} price with compression regime overlay "
                 f"({PRIMARY_SPEC['threshold']}th pct threshold)")
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "compression_regime_timeline.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    sub = results[(results["ticker"] == PRIMARY_SPEC["ticker"]) & (results["horizon_days"] == PRIMARY_SPEC["horizon"])]
    x = sub["compression_threshold_pct"].astype(str)
    ax.bar(x, sub["prob_p_conditional"], width=0.35, label="P(large move | compression)", align="edge")
    ax.bar(x, sub["prob_p_unconditional"], width=-0.35, label="P(large move) unconditional", align="edge")
    ax.set_xlabel("Compression percentile threshold")
    ax.set_ylabel("Probability")
    ax.set_title(f"{PRIMARY_SPEC['ticker']}: conditional vs unconditional\n"
                 f"P(top-quartile {PRIMARY_SPEC['horizon']}D move)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "conditional_probability_by_threshold.png", dpi=150)
    plt.close(fig)


def make_summary_table(results: pd.DataFrame) -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    cols = [
        "ticker", "horizon_days", "compression_threshold_pct", "is_primary_spec",
        "group_n_treatment", "group_n_control",
        "group_mean_treatment", "group_mean_control", "group_mean_difference",
        "group_welch_p_value", "welch_reject_bh",
        "group_mannwhitney_p_value", "mannwhitney_reject_bh",
        "prob_p_conditional", "prob_p_unconditional", "prob_probability_difference", "prob_probability_ratio",
    ]
    summary = results[cols].copy()
    round6_cols = [c for c in summary.columns if "p_value" not in c]
    summary[round6_cols] = summary[round6_cols].round(6)
    summary.to_csv(TABLES_DIR / "h1_summary_table.csv", index=False)

    with open(TABLES_DIR / "h1_summary_table.md", "w", encoding="utf-8") as f:
        f.write(summary.to_markdown(index=False))


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results = run_all_specs()

    results.to_csv(RESULTS_DIR / "phase1_h1_results.csv", index=False)
    with open(RESULTS_DIR / "phase1_h1_results.json", "w", encoding="utf-8") as f:
        json.dump(json.loads(results.to_json(orient="records")), f, indent=2)

    make_figures(results)
    make_summary_table(results)

    primary = results[results["is_primary_spec"]].iloc[0]
    print("=== Primary specification result (SPY, 20th pct threshold, 20D horizon) ===")
    print(f"n_compression={primary['group_n_treatment']}, n_normal={primary['group_n_control']}")
    print(f"mean fwd abs return: compression={primary['group_mean_treatment']:.4f}, "
          f"normal={primary['group_mean_control']:.4f}, diff={primary['group_mean_difference']:.4f}")
    print(f"Welch p={primary['group_welch_p_value']:.2e} (BH reject={primary['welch_reject_bh']}), "
          f"Mann-Whitney p={primary['group_mannwhitney_p_value']:.2e} (BH reject={primary['mannwhitney_reject_bh']})")
    print(f"P(large move | compression)={primary['prob_p_conditional']:.3f}, "
          f"P(large move) unconditional={primary['prob_p_unconditional']:.3f}, "
          f"ratio={primary['prob_probability_ratio']:.3f}")
    print(f"\nFull results: {RESULTS_DIR / 'phase1_h1_results.csv'}")
    print(f"Figures: {FIGURES_DIR}")
    print(f"Summary table: {TABLES_DIR / 'h1_summary_table.md'}")


if __name__ == "__main__":
    main()
