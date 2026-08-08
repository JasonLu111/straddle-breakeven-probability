# Research Report — Phase 1: Market Event Research

**Straddle Breakeven Probability Lab**
**Status: Phase 1 complete (MVP tier — underlying price data only). Phases 2–4 not yet started.**

---

## 1. 資料範圍與方法（Data & Methodology）

| 項目 | 內容 |
|---|---|
| 標的 | SPY, QQQ |
| 資料來源 | Yahoo Finance (`yfinance`)，日線 OHLCV + Adjusted Close |
| 資料期間 | 2005-01-03 至 2026-08-07（5,433 個交易日） |
| 資料層級 | **MVP tier — 僅使用標的價格資料，未使用任何選擇權資料** |
| 驗證方式 | walk-forward 原則已預先落實在特徵工程層級（見第 5 節 no-look-ahead 測試），本階段統計檢定為 in-sample 描述性/推論統計，非樣本外預測評估 |

**重要聲明**：本階段完全不涉及選擇權權利金、隱含波動率或任何跨式策略損益。因此本
報告**不能**、也**沒有**宣稱驗證了 Long Straddle 策略的獲利能力。本階段唯一的目的是
檢驗 H1 ——「波動率壓縮是否預測未來較大的絕對報酬」。這一點在 README 與本報告中
重複聲明，是為了避免結果被誤讀為完整的選擇權回測。

## 2. 研究問題與假說（H1）

> H1：當過去 20 日 realized volatility 位於歷史低分位，且 Bollinger Band width 較低時，
> 未來 10 日或 20 日的絕對報酬較高。

操作型定義：

- **Realized volatility**：10/20/60 日年化已實現波動率（`sqrt(252) x std(log returns)`）。
- **Volatility percentile**：`rv_20` 在過去 252 個交易日的分位排名。
- **Bollinger Band width**：`(upper - lower) / MA`，20 日窗口、2 倍標準差；同樣取過去 252
  日分位排名。
- **Compression regime**：`rv_20_percentile <= threshold AND bb_width_percentile <= threshold`。
  主要設定（pre-registered primary spec）使用 20th percentile；10th / 30th percentile
  作為穩健性檢查（robustness check），避免只挑選事後表現最好的門檻（data snooping）。
- **Outcome**：`fwd_abs_return_{10,20}d = |ln(P_{t+h}) - ln(P_t)|`。
- **輔助二元事件（large-move proxy）**：由於本階段尚無選擇權權利金，無法定義真正的
  breakeven 事件（那是 Phase 2 的工作），因此用「未來絕對報酬超過該標的、該期間、
  無條件分布的第 75 百分位數」作為 large-move 的代理事件，僅用於估計條件機率，
  **不代表任何真實的損益兩平機率**。

## 3. 主要結果（Primary specification：SPY, 20th percentile threshold, 20D horizon）

| 統計量 | Compression regime | Normal regime |
|---|---|---|
| 觀察數 | 606 | 4,536 |
| 平均未來 20 日絕對報酬 | 2.90% | 3.52% |
| 平均差異（compression − normal） | **-0.63%**（95% bootstrap CI：[-0.81%, -0.44%]） |
| Welch's t-test | t = -6.64, p = 4.85e-11 |
| Mann-Whitney U | p = 0.018 |
| Benjamini-Hochberg（12 個規格聯合檢定） | 拒絕虛無假設（reject） |
| P(large move top-quartile \| compression) | 17.3% |
| P(large move top-quartile) 無條件 | 26.1% |
| Probability ratio | 0.66 |

**結論：H1 在本樣本中被拒絕，且方向與假說相反。** 波動壓縮狀態下，未來 20 日絕對報酬
不僅沒有變大，反而顯著更小；壓縮狀態下出現「大幅波動」（top-quartile 絕對報酬）的機率
只有無條件機率的 66%，而非更高。

## 4. 穩健性分析（Robustness across 12 specifications）

對 2 個標的（SPY, QQQ）× 2 個預測期間（10D, 20D）× 3 個 compression 門檻（10th/20th/30th
percentile）共 12 個規格全部執行相同檢定，並用 Benjamini-Hochberg 控制 false discovery
rate。完整結果見 [`reports/tables/h1_summary_table.md`](tables/h1_summary_table.md) 與
[`results/statistical_tests/phase1_h1_results.csv`](../results/statistical_tests/phase1_h1_results.csv)。

**方向完全一致**：全部 12 個規格中，compression regime 的平均未來絕對報酬皆低於 normal
regime（差異介於 -0.30% 至 -0.89% 之間），且在 BH 校正後全部達統計顯著。這不是單一
門檻或單一標的的偶然結果。

| Ticker | Horizon | Threshold | Mean diff | Welch p | P(large move\|compression) | P(large move) unconditional |
|---|---|---|---|---|---|---|
| SPY | 10D | 10% | -0.67% | 8.1e-13 | 12.8% | 26.0% |
| SPY | 10D | 20% | -0.59% | 8.2e-18 | 16.5% | 26.0% |
| SPY | 10D | 30% | -0.57% | 2.8e-20 | 18.1% | 26.0% |
| SPY | 20D | 10% | -0.89% | 6.8e-13 | 12.8% | 26.1% |
| SPY | 20D | 20% (primary) | -0.63% | 4.8e-11 | 17.3% | 26.1% |
| SPY | 20D | 30% | -0.67% | 8.9e-16 | 17.9% | 26.1% |
| QQQ | 10D | 10% | -0.59% | 2.0e-06 | 18.9% | 25.6% |
| QQQ | 10D | 20% | -0.30% | 2.9e-03 | 23.1% | 25.6% |
| QQQ | 10D | 30% | -0.40% | 3.2e-07 | 20.9% | 25.6% |
| QQQ | 20D | 10% | -0.58% | 1.6e-03 | 23.5% | 25.6% |
| QQQ | 20D | 20% | -0.63% | 1.7e-06 | 21.4% | 25.6% |
| QQQ | 20D | 30% | -0.70% | 2.7e-11 | 19.5% | 25.6% |

## 5. 圖表

- [`reports/figures/h1_forward_return_by_regime.png`](figures/h1_forward_return_by_regime.png) —
  Compression vs normal regime 的未來 20 日絕對報酬分布比較（boxplot）。
- [`reports/figures/compression_regime_timeline.png`](figures/compression_regime_timeline.png) —
  SPY 價格走勢與 compression regime 標記時間軸。
- [`reports/figures/conditional_probability_by_threshold.png`](figures/conditional_probability_by_threshold.png) —
  三種門檻下條件機率 vs 無條件機率比較。

## 6. 解讀（Interpretation）

原始假說（H1）背後的直覺是「低波動壓縮之後容易出現突破」（俗稱 volatility contraction
precedes expansion）。但這個簡單的單變量檢定顯示，在 SPY / QQQ 2005–2026 的樣本中，
**低波動狀態在統計上具有相當的持續性（volatility clustering / persistence）**：波動率低的
時期，後續一段時間的波動率傾向於維持偏低，而不是立即反轉為大幅波動。這與 GARCH 類
波動率聚集現象一致，但與「壓縮後必噴出」的交易直覺相反。

這對整個研究鏈的意義：

- **H1 在無條件（unconditional）意義上不成立**——不能只靠「波動壓縮」本身作為進場
  訊號來預期未來絕對報酬變大。
- 但這不代表整條研究鏈失敗。真正與策略有關的問題是 H2（是否能突破選擇權隱含的
  breakeven 門檻，而非任意的「大幅波動」），因為 breakeven 門檻本身就是由目前已支付
  的權利金（隱含波動率）決定的——如果壓縮狀態下 IV 也同步偏低，即使未來絕對報酬
  的「絕對值」較小，也可能仍然「相對於便宜的權利金」更容易突破。這正是文件中特別
  強調 `iv_minus_rv`、`straddle_premium_pct` 等 option-cost features 的原因，必須留到
  Phase 2（有真實選擇權資料後）才能檢驗。
- Phase 3 的多變量模型（H3-H5）有機會捕捉到單一 compression 規則看不到的交互作用
  （例如 momentum、downside skew 等），因此不應僅憑本階段的單變量結果就放棄整個
  研究方向，而是把它當作誠實的 baseline：**任何後續模型都必須打敗「不做任何事」以及
  「單純看 compression 規則」這兩個 baseline**，而後者在本階段已經證明方向是負的。

## 7. 下一步

Phase 2（Breakeven Dataset）需要真實歷史選擇權資料（bid/ask, IV, OI, delta），用以：

1. 建立真正的 breakeven 門檻（`K ± (C0 + P0)`），而非本階段的「top-quartile 絕對報酬」代理事件；
2. 計算 `target_expiry`（到期時是否突破）與扣除交易成本後的真實 PnL；
3. 重新檢驗 H2：`P(突破 breakeven | compression)` 是否高於無條件機率——這是與 H1 不同
   的問題，因為 breakeven 門檻本身會隨 compression 狀態下降（IV 通常也偏低）。

見任務追蹤：待使用者提供歷史選擇權資料來源（API / 檔案）後啟動。
