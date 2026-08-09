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

## Phase 2 (options data)

- **Data source**: ORATS Data API, History (EOD) plan, `datav2/hist/strikes` endpoint.
  Verified live against the actual subscription on 2026-08-09.
- **Backtest window starts 2013-01-01, not earlier**, despite ORATS returning data
  back to ~2007. Empirically checked (12 sample dates spanning 2009-2014): SPY
  expirations landing in the 20-40 DTE entry window are essentially absent before
  2013 (2009-2012 chains are dominated by monthly-cycle expirations whose DTEs
  cluster around 8/16/44/72/... days, skipping the 20-40 window entirely). From
  2013 onward, 2-3 expirations reliably fall in that window every week. Using
  data before 2013 would silently exclude most or all weeks, so the window was
  set empirically rather than assumed from memory of when SPY weeklies launched.
- **Weeks with no expiration in the DTE window are excluded, not imputed.** SPY:
  9/690 weeks excluded (no matching expiration), QQQ: 0/690. A further 4 weeks per
  ticker are excluded because the entry hadn't reached expiration yet as of the
  underlying price data's last available date (most recent open positions, not a
  data defect). This is disclosed rather than backfilled or imputed.
- **Expiration date convention**: ORATS lists standard monthly expirations by their
  OCC settlement date (the Saturday after the third Friday), not the actual last
  trading day. `build_breakeven_dataset.py::_last_trading_day_on_or_before` resolves
  this to the most recent trading day within a 3-day tolerance -- this was caught
  and fixed during development (see git history) after an initial version silently
  dropped ~4% of trades whose listed expiration fell on a non-trading day.
- **Raw vs. dividend-adjusted price**: the expiry price used to settle each straddle
  is the underlying's raw `close`, not `adj_close`. `adj_close` is dividend-adjusted
  for the Phase 1 return calculations and would introduce a multi-decade adjustment
  gap (tens of dollars for SPY, compounding since the trade's era) if used to price
  option payoffs against a strike quoted in real terms. This was also caught during
  development -- an initial version using `adj_close` produced implausible ~20%
  "moves" that were actually just the dividend adjustment. See the code comment in
  `build_breakeven_dataset.py`.
- **Entry price convention**: primary analysis uses `(bid+ask)/2` on both legs;
  a parallel ask-only ("pay full ask") variant is computed for every trade
  (`*_ask` columns) as the conservative transaction-cost sensitivity check the
  proposal calls for.
- **PnL is quoted per-contract (100x multiplier)**, commission is a fixed
  per-contract dollar amount from `configs/backtest.yaml` (2 legs: one call +
  one put), and slippage is 0% by default (configurable). No bid-ask-spread
  cost beyond the ask-vs-mid entry price comparison, and no separate exit-side
  transaction cost is modeled (positions are held to expiration, not closed
  early).
- **Single ATM strike, single expiration per week** (closest available DTE to
  30 within the 20-40 window; closest strike to the underlying price at entry).
  No search across strikes/DTEs for a "better" straddle -- that would be a
  second layer of data snooping on top of the regime-threshold sensitivity
  already controlled for in Phase 1.

## Phase 3 (probability models)

- **Small pooled evaluation set.** 378 out-of-sample predictions per ticker (8 folds x
  ~47 test rows/fold on average) is not enough to distinguish a ROC-AUC of 0.55 from
  0.50 with any confidence -- no formal test for "is this AUC significantly above chance"
  is run in this phase. Read the Phase 3 results as "no evidence of a reliable signal
  found," not as a precise estimate of how close to zero the true signal is.
- **Sigmoid over isotonic calibration**, chosen because isotonic regression is
  nonparametric and needs several hundred+ calibration samples to be stable, and each
  fold's training window is only 300-656 observations before the internal calibration
  CV split shrinks it further. Isotonic results are still reported as a secondary
  comparison (`*_isotonic` model rows) rather than omitted.
- **No per-fold hyperparameter tuning.** Logistic Regression's `C` and Random Forest's
  tree depth/leaf size are fixed once in `configs/model.yaml`, not selected via
  cross-validation inside each fold. Given the already-small per-fold sample, an inner
  tuning loop would add a second layer of data-snooping risk on top of the walk-forward
  split itself, likely inflating apparent performance without a real improvement in the
  underlying signal.
- **Calibration slope/intercept are unreliable for `dummy_prior` and
  `compression_rule`**, since those baselines only emit 1-2 distinct probability values
  per fold -- see `reports/model_card.md`.
- **Feature importances/coefficients are reported for transparency, not as validated
  findings.** Given near-chance discrimination overall, treating any single feature's
  rank as an economic result would be over-interpreting an underpowered model.

## Phase 4 (strategy comparison)

- **All three strategies are restricted to the 2019-2026 common window**, not the full
  2013-2026 history, because Strategy C only has honest out-of-sample probabilities
  there (2013-2018 was Phase 3's initial training window, never held out). A
  full-2013-2026 view of Strategies A/B is reported separately
  (`results/backtests/phase4_full_sample_descriptive.csv`) but is explicitly labeled
  "descriptive only, not comparable to Strategy C" -- comparing A/B on 13 years against
  C on 7.5 years would make C look better or worse than it is for reasons having
  nothing to do with the strategy itself.
- **Strategy C's threshold (tau) is set per walk-forward fold from that fold's own
  training-set predicted-probability median**, applied causally to the next test
  window -- never chosen from test-period outcomes or the pooled test-period
  prediction distribution. See `scripts/compute_fold_thresholds.py` and
  `tests/test_entry_rules.py::test_strategy_c_threshold_is_per_fold_not_global`.
- **CVaR(5%) is undefined (reported as NaN) for Strategy B**, whose compression-regime
  trade counts (46-52 over the common window) put fewer than 5 observations in a 5%
  tail -- reported as missing rather than computed from too few points to mean
  anything.
- **Trade-sequence drawdown, not calendar-time drawdown.** Since at most one position
  is held at a time (`concurrent_positions: 1` in `configs/backtest.yaml`), cumulative
  PnL in the order trades were entered is a reasonable and standard convention, but it
  is not the same as a mark-to-market equity curve with daily granularity.
- **Large trade-level variance relative to strategy differences.** QQQ Strategy C's
  equity curve visually separates from Strategy A, but per-trade net PnL standard
  deviation (~$1,600) dwarfs the ~$127 mean difference between the two strategies --
  the visual gap is not statistically significant (Welch p=0.37, Mann-Whitney p=0.44).
  This is flagged explicitly in the report as a caution against over-reading equity
  curves without checking the underlying variance.
- **No multiple-testing correction across the 3 pairwise comparisons x 2 tickers** shown
  in the Phase 4 comparison table -- consistent with earlier phases, treat this as an
  exploratory comparison, not 6 independent confirmed hypothesis tests.
