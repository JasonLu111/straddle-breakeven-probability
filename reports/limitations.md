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

## Carried forward to later phases

- Phase 2 will need to document the real option data source, its coverage period, and
  any survivorship/liquidity filtering applied to the option chain.
- Phase 3's walk-forward validation must refit scaling/imputation/calibration within
  each training window only (see `configs/model.yaml`), not on the full sample.
- Statistical significance (Phase 1) must not be conflated with economic significance
  net of the bid-ask spread, commissions, and slippage — that is only established (if at
  all) in Phase 4.
