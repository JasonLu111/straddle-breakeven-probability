# Straddle Breakeven Probability Lab

*A Volatility-Regime and Probability-Based Research Framework for Long Straddle Strategies*

跨式策略損益兩平機率研究：以波動率壓縮與機率校準模型為核心

## Summary

This project investigates whether volatility compression predicts price movements large
enough for an at-the-money long straddle to exceed its option-implied breakeven
threshold. It combines hypothesis-driven regime analysis, breakeven-event
construction, calibrated probability modelling, walk-forward validation, and
transaction-cost-aware strategy evaluation.

The project does not merely predict market direction or volatility. It evaluates whether
observable market conditions contain enough information to identify occasions when
future realized movement is likely to exceed the cost embedded in option premiums.

本專案研究低波動與價格壓縮狀態，是否能預測足以突破平值買進跨式策略損益兩平門
檻的未來價格變動。研究整合市場狀態假說、損益兩平事件建構、機率校準模型、
walk-forward 樣本外驗證，以及納入交易成本的策略比較。

## Research questions

1. 波動壓縮是否具有預測力？(Does volatility compression have predictive power?)
2. 預測力是否足以覆蓋選擇權權利金？(Is that predictive power large enough to cover option premium?)
3. 機率模型是否校準良好？(Is the probability model well calibrated?)
4. 使用模型篩選交易後，是否真的改善策略績效？(Does model-filtered entry actually improve strategy performance?)

## Hypotheses

| ID | Hypothesis |
|----|------------|
| H1 | Volatility compression (low realized vol percentile, low BB width) predicts larger future 10D/20D absolute returns. |
| H2 | Conditional breakeven-event probability under compression exceeds the unconditional probability. |
| H3 | A multivariate feature model outperforms a single compression rule out-of-sample. |
| H4 | Non-linear models (RF/GBM) may capture regime interactions, but Logistic Regression is the primary interpretable baseline. |
| H5 | Walk-forward calibrated probabilities are reliable (Brier score, calibration curve). |
| H6 | Probability-filtered entry improves risk-adjusted strategy performance vs. unconditional/rule-based entry. |

## Data honesty disclaimer

This repository distinguishes explicitly between two data tiers, per module (see
`data/README.md` once populated):

- **MVP tier**: underlying price data only (SPY/QQQ via `yfinance`), option premiums
  estimated via Black–Scholes / implied-move proxy. Results at this tier are
  **"breakeven-event research under estimated option costs"**, not a real options
  backtest.
- **Full-research tier**: real historical option chain data (bid/ask, IV, OI, delta).
  Only results built on this tier are described as an actual Long Straddle backtest.

**Current status: Phase 1-3 complete.** Phase 2 uses real historical option chain data
(ORATS History/EOD plan) for SPY/QQQ, 2013-2026. Phase 3's walk-forward-validated
probability models (Logistic Regression, Random Forest) show near-chance discrimination
(pooled OOS ROC-AUC 0.44-0.55) -- consistent with, not contradicting, Phase 2's H2 null
result. Phase 4 (strategy comparison) is not yet started. See
[`reports/research_report.md`](reports/research_report.md) for current findings,
[`reports/model_card.md`](reports/model_card.md) for the Phase 3 models, and
[`reports/limitations.md`](reports/limitations.md) for what is and isn't validated so far.

## Project structure

```
straddle-breakeven-probability-lab/
├── configs/          # data / feature / model / backtest configuration
├── data/              # raw (gitignored), interim, processed
├── notebooks/         # exploration and presentation only — logic lives in src/
├── src/
│   ├── data/           # loaders + validation
│   ├── features/       # volatility, compression, momentum, option-cost features
│   ├── targets/        # breakeven / path / pnl target construction
│   ├── statistics/      # conditional probability, hypothesis tests, bootstrap
│   ├── models/          # baselines, training, calibration, walk-forward, evaluation
│   ├── backtest/        # entry rules, straddle PnL, transaction costs, risk metrics
│   └── visualization/
├── scripts/           # CLI entry points (download_data, build_dataset, ...)
├── tests/             # incl. no-lookahead / leakage checks
├── reports/           # research_report.md, data_dictionary.md, model_card.md, limitations.md
└── results/           # statistical_tests, model_metrics, predictions, backtests
```

## Implementation phases

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Market event research (H1, price data only) | Done |
| 2 | Breakeven dataset (real option chain, H2) | Done |
| 3 | Probability model + walk-forward + calibration (H3-H5) | Done |
| 4 | Strategy comparison (H6) | Not started |

## Setup

```bash
pip install -r requirements.txt
make data      # download underlying price data
make phase1    # build Phase 1 dataset + run statistical tests
make test

# Phase 2 (real option chain data) requires an ORATS API key:
cp .env.example .env   # fill in ORATS_API_KEY
make phase2    # downloads weekly chains (cached), builds breakeven dataset, runs H2 tests
```

## License

MIT — see [LICENSE](LICENSE).
