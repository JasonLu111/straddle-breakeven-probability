"""Generic bootstrap confidence intervals for arbitrary statistics."""
from __future__ import annotations

import numpy as np


def bootstrap_ci(data: np.ndarray, stat_fn=np.mean, n_boot: int = 10000,
                  alpha: float = 0.05, seed: int = 42) -> tuple[float, float, float]:
    """Percentile bootstrap CI. Returns (point_estimate, lower, upper)."""
    rng = np.random.default_rng(seed)
    data = np.asarray(data)
    data = data[~np.isnan(data)]
    n = len(data)
    if n == 0:
        return (np.nan, np.nan, np.nan)

    boot_stats = np.empty(n_boot)
    for i in range(n_boot):
        sample = data[rng.integers(0, n, n)]
        boot_stats[i] = stat_fn(sample)

    lower = np.nanpercentile(boot_stats, 100 * alpha / 2)
    upper = np.nanpercentile(boot_stats, 100 * (1 - alpha / 2))
    return (float(stat_fn(data)), float(lower), float(upper))


def bootstrap_diff_ci(group_a: np.ndarray, group_b: np.ndarray, stat_fn=np.mean,
                       n_boot: int = 10000, alpha: float = 0.05,
                       seed: int = 42) -> tuple[float, float, float]:
    """Bootstrap CI for stat_fn(group_a) - stat_fn(group_b), resampling each group
    independently with replacement."""
    rng = np.random.default_rng(seed)
    a = np.asarray(group_a)
    a = a[~np.isnan(a)]
    b = np.asarray(group_b)
    b = b[~np.isnan(b)]
    n_a, n_b = len(a), len(b)
    if n_a == 0 or n_b == 0:
        return (np.nan, np.nan, np.nan)

    diffs = np.empty(n_boot)
    for i in range(n_boot):
        sample_a = a[rng.integers(0, n_a, n_a)]
        sample_b = b[rng.integers(0, n_b, n_b)]
        diffs[i] = stat_fn(sample_a) - stat_fn(sample_b)

    point = float(stat_fn(a) - stat_fn(b))
    lower = float(np.nanpercentile(diffs, 100 * alpha / 2))
    upper = float(np.nanpercentile(diffs, 100 * (1 - alpha / 2)))
    return (point, lower, upper)
