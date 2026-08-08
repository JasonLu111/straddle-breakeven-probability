# Data Dictionary — Phase 1

Source: `data/processed/{TICKER}_phase1.parquet`, built by
`src/features/build_features.py`.

## Raw price columns (from `yfinance`)

| Column | Description |
|---|---|
| `open`, `high`, `low`, `close` | Daily OHLC |
| `adj_close` | Dividend/split-adjusted close, used for all return/volatility calculations |
| `volume` | Daily share volume |

## Volatility features (`src/features/volatility.py`)

| Column | Description |
|---|---|
| `rv_10`, `rv_20`, `rv_60` | Annualized realized volatility over trailing N days: `sqrt(252) * std(log returns)` |
| `rv_20_percentile` | Percentile rank of `rv_20` within its trailing 252-day window |
| `rv_term_ratio_10_60` | `rv_10 / rv_60` — short/long vol term structure ratio |
| `vol_of_vol` | Rolling std of `rv_20` over the longest RV window |

## Compression features (`src/features/compression.py`)

| Column | Description |
|---|---|
| `bb_width` | Bollinger Band width: `(upper - lower) / MA`, 20-day window, 2 std |
| `bb_width_percentile` | Trailing 252-day percentile rank of `bb_width` |
| `atr` | 14-day Average True Range |
| `atr_percentile` | Trailing 252-day percentile rank of `atr` |
| `range_10`, `range_20` | `(rolling max high - rolling min low) / close` over N days |
| `compression_regime_10/20/30` | Boolean (nullable): `rv_20_percentile <= p AND bb_width_percentile <= p` for p in {10,20,30}. `NA` during the 252-day warmup period. |
| `compression_regime` | Alias for the primary specification (`compression_regime_20`) |

## Momentum / market-state features (`src/features/momentum.py`)

| Column | Description |
|---|---|
| `momentum_5`, `momentum_20` | `close / close.shift(N) - 1` |
| `distance_from_ma20` | `close / MA20 - 1` |
| `volume_change` | `volume / rolling_mean(volume, 20) - 1` |
| `downside_semivolatility` | Annualized std of negative log returns only |
| `upside_downside_vol_ratio` | Ratio of annualized upside-only vol to downside-only vol |

## Targets (`src/features/build_features.py::build_forward_targets`)

| Column | Description |
|---|---|
| `fwd_abs_return_10d`, `fwd_abs_return_20d` | `\|ln(P_{t+h}) - ln(P_t)\|` — forward absolute log return. **Uses future data by construction; must never be used as a model input feature at time t.** |

## Not yet populated (Phase 2+)

Option-cost features (`straddle_premium_pct`, `atm_implied_volatility`, `iv_minus_rv`,
`days_to_expiry`, `bid_ask_spread_pct`, `put_call_iv_difference`) and breakeven targets
(`target_expiry`, `target_path`, `target_positive_net_pnl`) require real historical
option chain data and are not present in the current Phase 1 dataset.
