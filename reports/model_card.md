# Model Card — Phase 3 Breakeven Probability Models

## Overview

Four candidate predictors of `target_expiry` (did the ATM long straddle's realized
move exceed its mid-price breakeven threshold by expiration?), evaluated via
expanding-window walk-forward validation:

| Model | Description |
|---|---|
| `dummy_prior` | Predicts the training-window's historical base rate for every test row. Mathematically identical to "unconditional historical rate." |
| `compression_rule` | Predicts the training-window base rate *conditional on* the test row's own `compression_regime_20` flag. The single-rule baseline a trader eyeballing the compression indicator would use. |
| `logistic_regression` | L2-penalized logistic regression on 22 standardized features (volatility, compression, momentum, and option-cost groups — see `configs/model.yaml`), sigmoid (Platt)-calibrated. |
| `random_forest` | 300 shallow trees (`max_depth=4`, `min_samples_leaf=15`), same feature set, sigmoid-calibrated. |

Isotonic-calibrated variants of the two model-based predictors are also reported
for comparison (see `reports/limitations.md` for why sigmoid, not isotonic, is
primary at this sample size).

## Training data

`data/processed/{SPY,QQQ}_phase3_model_input.parquet` — 681 weekly observations
per ticker, 2013-01 to 2026-07 (see Phase 2 methodology in
`reports/research_report.md` for how each observation is constructed).

## Evaluation protocol

Expanding-window walk-forward: initial 6-year training window (2013-2018),
1-year test windows from 2019 through mid-2026 (8 folds per ticker, train sizes
303→656 observations, test sizes ~50/year). All scaling, calibration
(`CalibratedClassifierCV`, internal 5-fold CV), and model fitting happen strictly
inside each fold's training window — see `tests/test_walk_forward.py` and
`src/models/walk_forward.py`. No hyperparameter search per fold (hyperparameters
are pre-registered once in `configs/model.yaml`, not tuned against any test
period, to avoid a second layer of data snooping on top of the walk-forward
split itself).

Out-of-sample predictions from all folds are pooled (n=378/ticker) before
computing final metrics.

## Results summary (see `reports/tables/phase3_model_comparison.md` for full table)

**None of the four models achieve reliable discrimination.** Pooled OOS
ROC-AUC ranges 0.43-0.55 across all models and both tickers (0.50 = random).
Random Forest is nominally the best on ROC-AUC/PR-AUC but the calibration
curve (`reports/figures/phase3_calibration_curve.png`) shows no model tracking
the diagonal in any economically meaningful way, and Brier scores for every
model are within ~0.01 of the dummy baseline's ~0.25 (close to the
theoretical floor `base_rate*(1-base_rate)` for an uninformative constant
predictor).

**This is consistent with, not contradictory to, the Phase 2 finding**: H2
already showed no significant unconditional relationship between compression
and real breakeven probability. Adding more features and non-linear models does
not manufacture a signal the data doesn't contain.

## Interpretability (descriptive only — do not read as a trading signal)

Logistic Regression coefficients and Random Forest feature importances, averaged
across folds, both rank `put_call_iv_difference`, `atr_percentile`, and the
realized-vol features highest (see
`reports/figures/phase3_feature_importance.png`). Given the near-chance overall
discrimination, these rankings describe what the fitted models leaned on in
each fold, not a validated economic relationship — over-interpreting feature
importance from an underpowered model is a well-known pitfall this report is
explicitly flagging rather than repeating.

## Known limitations

- **Small sample.** 378 pooled OOS observations (weekly cadence over ~7.5 years
  of test period) is a genuinely small evaluation set for any of these metrics
  to be estimated precisely — confidence intervals around ROC-AUC ≈ 0.5 are wide.
  A ROC-AUC of 0.55 is not distinguishable from 0.50 at this sample size without
  a formal test, which this phase does not run (deferred to Phase 4 if a
  strategy-level evaluation is pursued).
- **Calibration slope/intercept are unstable for the two rule-based baselines**
  (`dummy_prior`, `compression_rule`): they output only 1-2 distinct probability
  values per fold (constant per fold, or one of two values), so the Cox
  calibration regression is effectively fit on a near-degenerate predictor.
  Treat those two models' calibration numbers as descriptive only.
- **No multiple-testing correction across the 6 models × 2 tickers × 2
  calibration methods** shown in the comparison table -- consistent with Phase
  1/2, the *primary* comparison is SPY's four non-isotonic models; the rest are
  robustness/secondary views, not independent hypothesis tests each claiming
  significance.
- **This model card reports discrimination/calibration, not trading
  profitability.** Whether a probability-filtered entry rule beats the
  Phase 2 baselines net of costs is a Phase 4 question, not answered here.
