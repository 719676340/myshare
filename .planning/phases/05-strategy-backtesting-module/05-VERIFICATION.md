---
phase: 05-strategy-backtesting-module
verified: 2026-05-07T13:15:00Z
status: passed
score: 9/9 must-haves verified
re_verification:
  previous_status: gaps_found
  previous_score: 4/9
  gaps_closed:
    - "Backend _calc_statistics now returns trade_pairs in statistics dict (line 749)"
    - "Backend get_session returns flat format {session_id, trades, equity_curve, baseline_curve, statistics} matching run_backtest (lines 923-929)"
    - "Frontend BacktestResults.vue reads baseline_curve as separate array from currentResult (line 140)"
    - "Frontend BacktestView.vue history table uses row.total_return_pct as top-level field (line 33-34)"
  gaps_remaining: []
  regressions: []
---

# Phase 5: Strategy Backtesting Module Verification Report

**Phase Goal:** Users can run automated backtests with preset strategy templates and custom indicator expressions, configure buy/sell conditions with nested AND/OR groups, and see comprehensive performance metrics with equity curves and K-line trade markers
**Verified:** 2026-05-07T13:15:00Z
**Status:** passed
**Re-verification:** Yes -- after gap closure via plan 05-03

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Expression parser safely evaluates formulas like VOL/MA(VOL,20) against OHLCV DataFrames | VERIFIED | expression_parser.py: 179 lines, AST whitelist with SAFE_FIELDS/FUNCTIONS/NODES, parse_and_validate + evaluate_expression + evaluate_expression_with_custom all present |
| 2 | Backtest engine iterates daily through data, evaluates buy/sell conditions, executes trades with A-share rules (T+1, fees, board lots) | VERIFIED | backtest_service.py: 964 lines, _run_simulation with T+1 check (line 393), fee calculation (lines 400-401), board lot rounding (line 425), _evaluate_condition_tree with 11 operators |
| 3 | Backend API accepts backtest configuration and returns trades, equity curve, baseline curve, and all 8 metrics | VERIFIED | backtest.py: 249 lines, 6 endpoints. run_backtest returns {session_id, trades, equity_curve, baseline_curve, statistics}. _calc_statistics computes all 8 metrics plus trade_pairs (line 749) |
| 4 | Preset strategy templates (MA crossover, volume breakout, MACD divergence) are pre-filled configs served from backend | VERIFIED | backtest_service.py: PRESET_STRATEGIES with 3 complete templates, GET /presets endpoint |
| 5 | User can select from 3 preset strategy templates and see them auto-fill the configuration | VERIFIED | PresetSelector.vue: 107 lines, card click calls applyPreset, store.applyPreset fills indicators/conditions and triggers validation |
| 6 | User can type custom indicator expressions and see real-time validation feedback | VERIFIED | IndicatorBuilder.vue: 162 lines, @blur triggers validateIndicator, green check/red X with error text feedback, calls POST /validate-expression |
| 7 | User can build nested AND/OR buy/sell condition groups with indicator + operator + threshold | VERIFIED | ConditionGroup.vue: 159 lines, recursive component rendering, AND/OR radio toggle, addRule/addSubgroup actions, ConditionRule with 11 operators |
| 8 | User can run backtest and see 8 metric cards, equity curve with dual lines, K-line with buy/sell markers, and trade table | VERIFIED | BacktestResults.vue: 328 lines. baseline_curve read separately (line 140), trade_pairs from statistics (line 136), all 8 metrics rendered (lines 29-59), equity curve dual-line chart (lines 138-203), buySellMarkers for K-line (lines 206-213) |
| 9 | Backtest results persist and user can browse history | VERIFIED | BacktestView.vue: 127 lines. History table reads row.total_return_pct at top level (line 33-34). get_session returns flat format matching run_backtest (lines 923-929) with reconstructed equity_curve and baseline_curve. loadSession stores as currentResult (store line 142). |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/services/expression_parser.py` | AST-based expression parser | VERIFIED | 179 lines, all 4 exports present |
| `backend/app/services/backtest_service.py` | Backtest engine | VERIFIED | 964 lines, BacktestService with run_backtest, list/get/delete_session, get_presets, 3 PRESET_STRATEGIES. get_session returns flat format with reconstructed curves (lines 923-929). _calc_statistics includes trade_pairs (line 749). |
| `backend/app/api/backtest.py` | REST endpoints | VERIFIED | 249 lines, 6 endpoints with Pydantic recursive models |
| `backend/app/models.py` | BacktestSession and BacktestTrade | VERIFIED | Both models with correct columns, relationships, foreign keys |
| `frontend/src/stores/backtest.js` | Pinia store | VERIFIED | 175 lines, all actions wired (executeBacktest, loadSession, loadHistory, deleteSession) |
| `frontend/src/views/BacktestView.vue` | Main backtest page | VERIFIED | 127 lines, history table reads top-level row.total_return_pct |
| `frontend/src/components/backtest/BacktestConfig.vue` | Configuration area | VERIFIED | 291 lines, 3-step layout |
| `frontend/src/components/backtest/IndicatorBuilder.vue` | Expression input with validation | VERIFIED | 162 lines, blur validation with visual feedback |
| `frontend/src/components/backtest/ConditionGroup.vue` | Recursive AND/OR groups | VERIFIED | 159 lines, recursive self-render |
| `frontend/src/components/backtest/ConditionRule.vue` | Condition row | VERIFIED | 216 lines, 11 operators |
| `frontend/src/components/backtest/PresetSelector.vue` | Preset picker | VERIFIED | 107 lines, card layout with apply |
| `frontend/src/components/backtest/BacktestResults.vue` | Results display | VERIFIED | 328 lines. Reads baseline_curve separately (line 140), trade_pairs from statistics (line 136), all data flows correct |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/app/api/backtest.py` | `backend/app/services/backtest_service.py` | BacktestService instantiation per request | WIRED | Line 104: service = BacktestService(db) |
| `backend/app/services/backtest_service.py` | `backend/app/services/expression_parser.py` | parse_and_validate + evaluate_expression_with_custom | WIRED | Lines 19-25: imports, Line 212: parse_and_validate, Line 229: evaluate_expression_with_custom |
| `backend/app/services/backtest_service.py` | `backend/app/models.py` | BacktestSession/BacktestTrade persistence | WIRED | Lines 253-283: creates and saves session + trade records |
| `frontend/src/views/BacktestView.vue` | `frontend/src/stores/backtest.js` | useBacktestStore() | WIRED | Line 55: import, Line 65: useBacktestStore() |
| `frontend/src/stores/backtest.js` | `frontend/src/api/index.js` | runBacktest, getBacktestPresets, etc. | WIRED | Lines 2-9: imports all 6 API functions |
| `frontend/src/components/backtest/BacktestResults.vue` | `frontend/src/components/KLineChart.vue` | buySellMarkers and fixedData props | WIRED | Lines 71-73: KLineChart with :buySellMarkers and :fixedData |
| `frontend/src/components/backtest/ConditionGroup.vue` | `frontend/src/components/backtest/ConditionRule.vue` | Recursive rendering of condition tree | WIRED | Line 52: import ConditionRule, Lines 28-32: conditional rendering |
| `backend/app/main.py` | `backend/app/api/backtest.py` | Router registration | WIRED | Line 93: include_router with /api prefix |
| `backend/app/database.py` | `backend/app/models.py` | Model import for table creation | WIRED | Line 40: imports BacktestSession, BacktestTrade |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| BacktestResults equity curve (strategy line) | `strategyData` | `backtestStore.currentResult.equity_curve[].net_worth` | Yes -- _build_equity_curve iterates all dates computing cash + market_value | FLOWING |
| BacktestResults equity curve (baseline line) | `baselineValues` | `backtestStore.currentResult.baseline_curve[].net_worth` | Yes -- _build_baseline_curve computes buy-and-hold proportional worth | FLOWING |
| BacktestResults trade table | `tradePairs` | `statistics.value.trade_pairs` | Yes -- _calc_statistics includes trade_pairs via _pair_trades (line 749). Backward-compat check in get_session (lines 918-921) for older sessions. | FLOWING |
| BacktestResults K-line markers | `buySellMarkers` | `backtestStore.currentResult.trades` | Yes -- trades array from run_backtest or get_session, mapped to {date, type, price} | FLOWING |
| BacktestResults metrics cards | `statistics` | `backtestStore.currentResult.statistics` | Yes -- all 8 metrics computed in _calc_statistics, stored in session, returned by both run_backtest and get_session | FLOWING |
| BacktestView history table return rate | `row.total_return_pct` | `backtestStore.historyList[]` items | Yes -- list_sessions extracts stats.get("total_return_pct") as top-level field (line 838) | FLOWING |
| BacktestView history reload | `loadSession` -> `currentResult` | `getBacktestSession` API -> `get_session` flat response | Yes -- get_session returns {session_id, trades, equity_curve, baseline_curve, statistics} matching run_backtest format | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Frontend route to /backtest | Verified in router/index.js: lines 19-21 | path: '/backtest', component: BacktestView | PASS |
| get_session and run_backtest return identical key sets | Compared return blocks at lines 285-291 and 923-929 | Both return {session_id, trades, equity_curve, baseline_curve, statistics} | PASS |
| Expression parser import | Requires running Python | Could not verify without server | SKIP |
| All API routes registered | Requires running Python | Could not verify without server | SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| BACK-01 | 05-01, 05-02 | Preset strategy templates (MA crossover, volume breakout, MACD divergence) | SATISFIED | 3 presets in PRESET_STRATEGIES, GET /presets endpoint, PresetSelector.vue |
| BACK-02 | 05-01, 05-02 | User can adjust strategy parameters via condition builder | SATISFIED | ConditionGroup + ConditionRule with 11 operators, dynamic thresholds |
| BACK-03 | 05-01, 05-02, 05-03 | 8 metrics: total/annualized return, max drawdown, trade count, win rate, profit factor, Sharpe, avg holding days | SATISFIED | _calc_statistics computes all 8 metrics + trade_pairs, frontend renders all 8 metric cards and trade detail table |
| BACK-04 | 05-01, 05-02, 05-03 | Equity curve: strategy NAV vs buy-and-hold baseline (dual-line) | SATISFIED | equity_curve and baseline_curve built separately, frontend reads baseline_curve as separate array, dual-line ECharts chart |
| BACK-05 | 05-01, 05-02 | Buy/sell points marked on K-line chart | SATISFIED | buySellMarkers computed from trades, KLineChart receives them via props |
| DATA-05 | 05-01, 05-02 | Custom indicator expression builder with four arithmetic operations | SATISFIED | AST expression parser supports MA, EMA, STD, MAX, MIN, REF, CROSS with field arithmetic. Note: REQUIREMENTS.md traceability table says "Deferred to v2" but implementation is complete and functional. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| BacktestResults.vue | 141 | `return {}` on empty curve | Info | Valid early-return guard for empty chart data, not a stub |

No blocker or warning anti-patterns found. The single `return {}` is a legitimate guard clause when no equity curve data is available.

### Human Verification Required

### 1. Preset Strategy Flow

**Test:** Select "MA Cross" preset, choose stock, set dates, run backtest
**Expected:** Config auto-fills, backtest executes, results display with metrics/charts/table
**Why human:** Cannot verify end-to-end API + rendering without running both servers

### 2. Visual Equity Curve Dual Lines

**Test:** After running backtest, inspect equity curve chart
**Expected:** Blue solid line (strategy NAV) and gray dashed line (buy-and-hold baseline) both visible
**Why human:** Chart visual quality and interaction need human eyes

### 3. K-line Buy/Sell Markers

**Test:** Check K-line chart in results for marker placement
**Expected:** Red up-triangle markers on buy dates, green down-triangle markers on sell dates
**Why human:** Marker visibility and positioning on the chart

### 4. Nested Condition Builder

**Test:** Add subgroup within a group, toggle AND/OR
**Expected:** Indented nested group renders correctly, operator toggle works
**Why human:** Recursive component rendering and visual layout

### 5. History Row Click Reload

**Test:** Click a history row
**Expected:** Full results re-display with metrics, charts, trades from saved session
**Why human:** Full session reload from database with reconstructed curves

### Gaps Summary

All previously identified gaps have been closed:

1. **trade_pairs now in statistics.** Backend _calc_statistics (line 749) includes `trade_pairs` in its return dict. get_session has a backward-compat check (lines 918-921) that adds trade_pairs for older sessions. Frontend reads `statistics.value?.trade_pairs` (BacktestResults line 136). Data flows correctly.

2. **baseline_curve read as separate array.** Frontend BacktestResults.vue (line 140) reads `backtestStore.currentResult?.baseline_curve || []` as a separate array. Backend returns `baseline_curve` alongside `equity_curve` in both run_backtest (line 289) and get_session (line 927). Length guard at line 148 ensures ECharts doesn't break if lengths differ.

3. **get_session returns flat format matching run_backtest.** get_session (lines 923-929) returns `{session_id, trades, equity_curve, baseline_curve, statistics}` -- identical key structure to run_backtest (lines 285-291). Curves are reconstructed from stored OHLCV data using the same _build_equity_curve and _build_baseline_curve methods. Frontend loadSession stores the response directly as currentResult, so BacktestResults works for both fresh runs and history reloads.

4. **History table reads top-level total_return_pct.** BacktestView.vue (lines 33-34) reads `row.total_return_pct` as a top-level field. Backend list_sessions (line 838) extracts `stats.get("total_return_pct")` into the top-level item dict. Format is consistent.

Phase goal is achieved. All backend artifacts are substantive and correctly wired to frontend consumption.

---

_Verified: 2026-05-07T13:15:00Z_
_Verifier: Claude (gsd-verifier)_
