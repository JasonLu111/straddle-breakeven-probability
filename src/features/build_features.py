"""Orchestrates Phase 1 feature construction: volatility + compression + momentum."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from src.features.compression import build_compression_features, build_compression_regime
from src.features.momentum import build_momentum_features
from src.features.volatility import build_volatility_features


def load_features_config(config_path: str | Path = "configs/features.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_all_features(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    rv_cfg = cfg["realized_volatility"]
    vol_feats = build_volatility_features(
        df,
        windows=rv_cfg["windows"],
        annualization_factor=rv_cfg["annualization_factor"],
        percentile_lookback=rv_cfg["percentile_lookback"],
    )

    bb_cfg, atr_cfg, range_cfg = cfg["bollinger_band"], cfg["atr"], cfg["range"]
    comp_feats = build_compression_features(
        df,
        bb_window=bb_cfg["window"],
        bb_num_std=bb_cfg["num_std"],
        atr_window=atr_cfg["window"],
        range_windows=range_cfg["windows"],
        percentile_lookback=bb_cfg["percentile_lookback"],
    )

    mom_cfg = cfg["momentum"]
    mom_feats = build_momentum_features(
        df,
        momentum_windows=mom_cfg["windows"],
        ma_window=mom_cfg["ma_window"],
    )

    features = pd.concat([vol_feats, comp_feats, mom_feats], axis=1)

    regime_cfg = cfg["compression_regime"]
    for threshold in regime_cfg["sensitivity_thresholds"]:
        regime = build_compression_regime(features, threshold)
        features[regime.name] = regime

    features["compression_regime"] = features[
        f"compression_regime_{int(regime_cfg['primary_threshold'] * 100)}"
    ]

    return features


def build_forward_targets(df: pd.DataFrame, horizons: list[int], price_col: str = "adj_close") -> pd.DataFrame:
    """Forward absolute log return over each horizon. Uses only future data by
    construction (this is the prediction target, not a feature) -- must never be
    joined back as an input feature at the same timestamp.
    """
    import numpy as np

    out = pd.DataFrame(index=df.index)
    log_price = np.log(df[price_col])
    for h in horizons:
        out[f"fwd_abs_return_{h}d"] = (log_price.shift(-h) - log_price).abs()
    return out


def run(ticker: str, data_cfg_path: str = "configs/data.yaml",
        features_cfg_path: str = "configs/features.yaml") -> pd.DataFrame:
    with open(data_cfg_path, "r", encoding="utf-8") as f:
        data_cfg = yaml.safe_load(f)

    raw_path = Path(data_cfg["underlying"]["raw_path"]) / f"{ticker}.parquet"
    df = pd.read_parquet(raw_path)

    features_cfg = load_features_config(features_cfg_path)
    features = build_all_features(df, features_cfg)
    targets = build_forward_targets(df, features_cfg["forward_horizons"]["days"])

    dataset = pd.concat([df, features, targets], axis=1)

    out_path = Path("data/processed") / f"{ticker}_phase1.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_parquet(out_path)
    print(f"{ticker}: {len(dataset)} rows -> {out_path}")
    return dataset


if __name__ == "__main__":
    import sys
    tickers = sys.argv[1:] or ["SPY", "QQQ"]
    for t in tickers:
        run(t)
