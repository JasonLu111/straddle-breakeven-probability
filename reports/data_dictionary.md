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

## Phase 2: breakeven event dataset

Source: `data/processed/{TICKER}_phase2_breakeven.parquet`, built by
`src/targets/build_breakeven_dataset.py` from cached ORATS chains
(`data/raw/options/{TICKER}/{date}.parquet`). One row per week (Friday entry,
ATM strike, nearest-to-30-DTE expiration within 20-40 DTE).

| Column | Description |
|---|---|
| `trade_date` | Entry date (Friday) |
| `expir_date` | Listed expiration date (OCC convention -- may be a Saturday for standard monthly contracts) |
| `pricing_date` | Actual trading day used to price expiry P&L (last trading day on/before `expir_date`, within a 3-day tolerance) |
| `dte` | Days to expiration at entry |
| `strike` | ATM strike selected |
| `stock_price` | Underlying price at entry (from ORATS, matches the raw/unadjusted underlying series) |
| `expiry_price` | Underlying **raw close** (not dividend-adjusted) on `pricing_date` -- mixing this with `adj_close` would inject a spurious dividend-adjustment gap, see the code comment in `build_breakeven_dataset.py` |
| `premium_mid`, `premium_ask` | Total straddle premium: `(bid+ask)/2` per leg (primary) vs. paying full ask on both legs (conservative variant) |
| `upper_breakeven_mid`, `lower_breakeven_mid` | `strike +/- premium_mid` |
| `call_mid_iv`, `put_mid_iv` | ORATS mid IV for the selected contracts |
| `call_open_interest`, `put_open_interest` | Open interest at entry |
| `target_expiry` | 1 if `\|expiry_price - strike\| > premium_mid` (real breakeven event, mid-price basis) |
| `gross_pnl`, `net_pnl` | Per-contract (100x) dollar P&L, before/after commission + slippage (see `configs/backtest.yaml`) |
| `return_on_premium` | `net_pnl / (premium_mid * 100)` |
| `target_positive_net_pnl` | 1 if `net_pnl > 0` |
| `target_expiry_ask`, `net_pnl_ask`, `target_positive_net_pnl_ask` | Same definitions, ask-price entry variant |
| `compression_regime_10/20/30`, `compression_regime` | Phase 1 regime flags, as of `trade_date` (joined from `{TICKER}_phase1.parquet`) |

Weeks with no expiration in the [20,40] DTE window, or where the resolved
`pricing_date` couldn't be matched within 3 days (e.g. trade not yet expired),
are excluded rather than imputed -- see `reports/limitations.md` for counts.

## Phase 3: model input & outputs

Source: `data/processed/{TICKER}_phase3_model_input.parquet`, built by
`src/models/build_model_dataset.py` (Phase 1 features + Phase 2 option-cost
features, joined on `trade_date`).

New columns beyond what's listed above (see `src/features/option_features.py`):

| Column | Description |
|---|---|
| `straddle_premium_pct` | `premium_mid / stock_price` |
| `atm_implied_volatility` | `(call_mid_iv + put_mid_iv) / 2` |
| `put_call_iv_difference` | `put_mid_iv - call_mid_iv` |
| `days_to_expiry` | Alias of `dte` |
| `bid_ask_spread_pct` | `(premium_ask - premium_mid) / premium_mid` |
| `iv_minus_rv` | `atm_implied_volatility - rv_20` (as of `trade_date`) |

Model outputs:

- `results/predictions/{TICKER}_oos_predictions.parquet` — long format,
  one row per (fold, model, test observation): `ticker, fold_id, model,
  trade_date, y_true, y_prob`. Every row's `y_prob` was produced by a model
  fit only on data strictly before `trade_date`'s test fold.
- `results/model_metrics/{TICKER}_fold_diagnostics.json` — fold boundaries
  (train/test date ranges, sample sizes) and per-fold-averaged Logistic
  Regression coefficients / Random Forest feature importances.
- `results/model_metrics/phase3_pooled_metrics.csv` — one row per
  (ticker, model): classification + probability-quality metrics computed on
  the pooled out-of-sample predictions across all folds.
