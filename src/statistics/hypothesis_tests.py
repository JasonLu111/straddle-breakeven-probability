"""Two-sample tests for comparing a continuous outcome across regimes."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from src.statistics.bootstrap import bootstrap_diff_ci


def compare_groups(outcome: pd.Series, condition: pd.Series, n_boot: int = 10000,
                    alpha: float = 0.05) -> dict:
    """Compare `outcome` between condition=True (treatment) and condition=False
    (control) groups: descriptive stats, Welch's t-test, Mann-Whitney U, and a
    bootstrap CI on the difference in means. Rows with NA in either series are
    dropped.
    """
    df = pd.DataFrame({"outcome": outcome, "condition": condition}).dropna()
    df["condition"] = df["condition"].astype(bool)

    treatment = df.loc[df["condition"], "outcome"].to_numpy(dtype=float)
    control = df.loc[~df["condition"], "outcome"].to_numpy(dtype=float)

    t_stat, t_pvalue = stats.ttest_ind(treatment, control, equal_var=False)
    u_stat, u_pvalue = stats.mannwhitneyu(treatment, control, alternative="two-sided")

    diff_point, diff_lo, diff_hi = bootstrap_diff_ci(treatment, control, np.mean, n_boot, alpha)

    return {
        "n_treatment": len(treatment),
        "n_control": len(control),
        "mean_treatment": float(np.mean(treatment)),
        "mean_control": float(np.mean(control)),
        "median_treatment": float(np.median(treatment)),
        "median_control": float(np.median(control)),
        "mean_difference": diff_point,
        "mean_difference_ci": (diff_lo, diff_hi),
        "welch_t_stat": float(t_stat),
        "welch_p_value": float(t_pvalue),
        "mannwhitney_u_stat": float(u_stat),
        "mannwhitney_p_value": float(u_pvalue),
    }


def benjamini_hochberg(p_values: list[float], fdr: float = 0.05) -> list[bool]:
    """Benjamini-Hochberg FDR control. Returns a boolean list (same order as input)
    indicating which hypotheses are rejected (significant) at the given FDR."""
    p_values = np.asarray(p_values)
    n = len(p_values)
    order = np.argsort(p_values)
    ranked = p_values[order]
    thresholds = (np.arange(1, n + 1) / n) * fdr

    below = ranked <= thresholds
    if not below.any():
        reject_sorted = np.zeros(n, dtype=bool)
    else:
        max_idx = np.max(np.where(below)[0])
        reject_sorted = np.zeros(n, dtype=bool)
        reject_sorted[: max_idx + 1] = True

    reject = np.zeros(n, dtype=bool)
    reject[order] = reject_sorted
    return reject.tolist()
