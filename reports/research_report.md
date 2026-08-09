# Research Report — Phase 1 & 2

**Straddle Breakeven Probability Lab**
**Status: Phase 1 & 2 complete (Full-research tier for H1/H2, real ORATS option chain data). Phases 3–4 not yet started.**

## Part A: Phase 1 — Market Event Research

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

## Part B: Phase 2 — Breakeven Dataset（真實選擇權資料）

### 1. 資料與方法

| 項目 | 內容 |
|---|---|
| 資料來源 | ORATS Data API，History (EOD) 方案，`datav2/hist/strikes` endpoint |
| 資料層級 | **Full-research tier** — 真實歷史 bid/ask、IV、delta、open interest |
| 回測期間 | **2013-01-01 至 2026-08-07**（非 2007 年起，見下方「資料涵蓋範圍」） |
| 進場規則 | 每週五進場，最接近 ATM 的 strike，20–40 DTE 中最接近 30 DTE 的到期日，持有至到期 |
| 進場價格 | 主要：`(bid+ask)/2`；穩健性版本：買方全額支付 ask（`*_ask` 欄位） |
| 交易成本 | 每口合約 commission（見 `configs/backtest.yaml`），選擇權乘數 100 |

**資料涵蓋範圍**：實際測試發現，ORATS 雖然有 2007 年起的資料，但 SPY 在 2013 年之前
的到期日高度集中在月選（DTE 約 8/16/44/72...），20–40 DTE 區間經常完全沒有對應合約
可交易。抽樣 2009–2014 共 12 個交易日驗證後，確認從 2013 年起才穩定每週都有落在
20–40 DTE 區間的到期日。因此本階段回測期間設為 2013–2026，而非假設「SPY 週選很早
就存在」。

**排除的週數**：SPY 690 週中排除 9 週（無 20–40 DTE 合約）與 4 週（尚未到期，屬最新
未平倉部位，非資料缺陷）；QQQ 690 週排除 0 週（無合約）與 4 週（尚未到期）。排除週
數不做任何插補，直接排除。

**開發過程中發現並修正的兩個資料正確性問題**（詳見 `reports/limitations.md`）：

1. ORATS 的 `expirDate` 對月選採用 OCC 慣例，標示為第三個星期五之後的星期六（結算
   日），而非實際最後交易日（星期五）。已修正為自動回溯至到期日（含）之前最近的
   實際交易日（3 天容忍度）。
2. 到期損益計算原本誤用了 `adj_close`（股息調整後收盘價，用於 Phase 1 報酬率計算是
   正確的），但選擇權履約結算應該對照**未經股息調整的實際成交價**。混用兩者會產生
   長達十幾年股息調整累積造成的假性「20% 跳空」，已修正為使用 `close`。

### 2. 主要結果：H2（Compression 是否提高真實 breakeven 機率）

**Primary spec：SPY, 20th percentile threshold**

| 統計量 | 數值 |
|---|---|
| 有效交易週數 | 681 |
| Compression 週數 | 74 |
| P(breakeven \| compression) | 41.9%（95% bootstrap CI: [31.1%, 52.7%]） |
| P(breakeven) 無條件 | 41.6%（95% bootstrap CI: [37.7%, 45.4%]） |
| Probability ratio | 1.008 |
| 平均 net PnL (compression) | -$195.56 / 口 |
| 平均 net PnL (normal) | -$38.89 / 口 |
| Welch's t-test (PnL 差異) | p = 0.088 |

**結論：H2 沒有被支持，但也沒有被拒絕——是一個乾淨的虛無結果（null result）。**
Compression 狀態下的條件 breakeven 機率（41.9%）與無條件機率（41.6%）幾乎相同，
兩者的 95% bootstrap 信賴區間高度重疊。這與 H1 的結果形成有意思的對比：

- Phase 1（H1）：compression 下**未來絕對報酬顯著更小**（12 個規格全部同向顯著）。
- Phase 2（H2）：compression 下**真實 breakeven 機率沒有顯著差異**。

這正好驗證了 Phase 1 報告中提出的解讀假說：compression 狀態下 IV／權利金通常也同步
偏低，breakeven 門檻本身會跟著收窄，兩個效應大致互相抵銷，使得「未來絕對報酬變小」
不會直接轉化為「突破機率變小」。換句話說，**只看「未來會不會大漲大跌」是錯誤的分析
單位；真正決定策略成敗的是「未來變動」相對「當下已支付的權利金」的比較**——這也是
原始研究提案中特別強調 breakeven 機率而非單純方向性大幅波動的原因。

### 3. 穩健性分析（Ticker × threshold）

全部 6 個規格（SPY/QQQ × 10/20/30th percentile）的條件機率信賴區間都與無條件機率的
信賴區間重疊，沒有一個規格達到統計顯著：

| Ticker | Threshold | Compression n | P(breakeven\|comp) | P(breakeven) 無條件 | Ratio | Mean PnL (comp) | Mean PnL (normal) | Welch p |
|---|---|---|---|---|---|---|---|---|
| SPY | 10% | 26 | 46.2% | 41.6% | 1.11 | -$223.28 | -$49.27 | 0.201 |
| SPY | 20% | 74 | 41.9% | 41.6% | 1.01 | -$195.56 | -$38.89 | 0.088 |
| SPY | 30% | 145 | 43.4% | 41.6% | 1.05 | -$81.98 | -$48.86 | 0.633 |
| QQQ | 10% | 33 | 42.4% | 44.1% | 0.96 | -$91.59 | -$57.15 | 0.834 |
| QQQ | 20% | 72 | 41.7% | 44.1% | 0.95 | -$148.74 | -$48.19 | 0.343 |
| QQQ | 30% | 126 | 41.3% | 44.1% | 0.94 | -$161.40 | -$35.54 | 0.137 |

有一個值得留意但未達顯著的一致方向：**6 個規格中，compression 狀態下的平均 net PnL
全部比 normal 狀態更差**（更負）。沒有任何一個單獨達到 5% 顯著水準（且未經多重檢定
校正），樣本數也偏小（compression 子樣本僅 26–145 筆交易），統計檢定力有限。這是一
個「有方向但證據不足」的觀察，不應過度解讀，但值得在 Phase 3/4 用更大樣本或更精細
的模型重新檢驗，而不是直接當作可交易的訊號。

### 4. 圖表

- [`reports/figures/h2_breakeven_probability.png`](figures/h2_breakeven_probability.png) —
  Compression vs normal regime 的真實 breakeven 機率比較。
- [`reports/figures/h2_net_pnl_by_regime.png`](figures/h2_net_pnl_by_regime.png) —
  兩種 regime 下的真實 net PnL 分布（已扣除交易成本）。

### 5. 下一步

Phase 3（Probability Model）建議方向，基於 Phase 1+2 的發現：

1. 單一 compression 規則對 breakeven 機率**沒有**單變量預測力（H2 null result），因此
   Phase 3 的多變量模型必須納入 option-cost features（`iv_minus_rv`、
   `straddle_premium_pct` 等，Phase 2 資料已包含 `call_mid_iv`/`put_mid_iv`）而不能只用
   價格壓縮特徵，否則不會比「不做任何事」的 baseline 更好。
2. Compression 下 net PnL 偏負但未達顯著的觀察，適合作為 Phase 3 模型的一個檢查點：
   如果多變量模型能夠顯著分離出「PnL 更負」的子群，就代表真的捕捉到單變量看不到
   的交互作用；如果不能，則應誠實回報「此策略在本樣本中沒有可靠的統計邊際」。
3. 樣本數限制（每週一筆觀察，13 年約 680 筆）意味著 walk-forward validation 的每個
   fold 都會更小；Phase 3 需要謹慎設計 fold 數量與 calibration 方法，避免過度配適。
