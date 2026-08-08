# Limitations

## Phase 1 (current)

- **No options data used.** All statements about "large moves" are about the underlying's
  own absolute return distribution, not about any option payoff. This is explicitly
  **not** a Long Straddle backtest — see `README.md` data-tier disclaimer.
- **`large_move_event` is a proxy, not a breakeven event.** It is defined post hoc from the
  unconditional top-quartile of forward absolute returns within each (ticker, horizon)
  sample. It has no relationship to any real option premium and must not be
  reused/reinterpreted as a breakeven probability once Phase 2 introduces real option
  data — Phase 2 will replace it with `target_expiry` built from actual strike/premium data.
- **In-sample statistics, not out-of-sample evaluation.** Phase 1 uses the full
  2005–2026 sample for descriptive/inferential statistics (t-test, Mann-Whitney,
  bootstrap CI). It does not yet involve any model fitting, so there is no train/test
  split to violate — but this also means Phase 1 alone says nothing about a tradeable
  edge. Walk-forward validation is deferred to Phase 3 where a fitted model exists.
- **Multiple testing.** 12 specifications (2 tickers x 2 horizons x 3 thresholds) were
  run; Benjamini-Hochberg FDR control was applied jointly across all 12 Welch p-values
  (and separately across the 12 Mann-Whitney p-values). The primary specification
  (SPY, 20th percentile threshold, 20-day horizon) was pre-registered in
  `scripts/run_statistical_tests.py::PRIMARY_SPEC` before results were inspected, to
  avoid post hoc threshold selection.
- **Survivorship / index composition.** SPY and QQQ are live, continuously-rebalanced
  ETFs; there is no delisting or survivorship bias concern here (unlike single-stock
  studies), but results are specific to broad-market/tech-heavy index behavior and may
  not generalize to single names or other asset classes.
- **No transaction costs, no options liquidity constraints.** Not applicable yet since no
  strategy is being backtested in Phase 1.

## Carried forward to later phases

- Phase 2 will need to document the real option data source, its coverage period, and
  any survivorship/liquidity filtering applied to the option chain.
- Phase 3's walk-forward validation must refit scaling/imputation/calibration within
  each training window only (see `configs/model.yaml`), not on the full sample.
- Statistical significance (Phase 1) must not be conflated with economic significance
  net of the bid-ask spread, commissions, and slippage — that is only established (if at
  all) in Phase 4.
