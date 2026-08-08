"""Conditional vs. unconditional event probability comparison."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.statistics.bootstrap import bootstrap_ci


def conditional_probability_table(event: pd.Series, condition: pd.Series,
                                    n_boot: int = 10000, alpha: float = 0.05) -> dict:
    """Compare P(event=1 | condition=True) vs P(event=1) (unconditional, over the
    full valid sample). Both `event` and `condition` may contain NA; rows with NA
    in either are dropped.
    """
    df = pd.DataFrame({"event": event, "condition": condition}).dropna()
    df["event"] = df["event"].astype(int)
    df["condition"] = df["condition"].astype(bool)

    unconditional = df["event"].to_numpy(dtype=float)
    conditional = df.loc[df["condition"], "event"].to_numpy(dtype=float)

    p_unconditional, p_unc_lo, p_unc_hi = bootstrap_ci(unconditional, np.mean, n_boot, alpha)
    p_conditional, p_cond_lo, p_cond_hi = bootstrap_ci(conditional, np.mean, n_boot, alpha)

    return {
        "n_total": len(df),
        "n_condition_true": int(df["condition"].sum()),
        "p_unconditional": p_unconditional,
        "p_unconditional_ci": (p_unc_lo, p_unc_hi),
        "p_conditional": p_conditional,
        "p_conditional_ci": (p_cond_lo, p_cond_hi),
        "probability_difference": p_conditional - p_unconditional,
        "probability_ratio": (p_conditional / p_unconditional) if p_unconditional > 0 else np.nan,
    }
