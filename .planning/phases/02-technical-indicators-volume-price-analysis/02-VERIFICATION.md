---
phase: 02-technical-indicators-volume-price-analysis
verified: 2026-05-06T03:00:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 2: Technical Indicators + Volume-Price Analysis Verification Report

**Phase Goal:** Users can view technical indicator sub-charts and see automatic volume-price signal markers and K-line pattern annotations on the chart
**Verified:** 2026-05-06T03:00:00Z
**Status:** passed
**Re-verification:** No -- initial verification

## Goal Achievement

The phase goal is fully achieved. All backend computation services, API endpoints, frontend chart rendering, toolbar controls, and signal/pattern markers are implemented, wired, and verified.

### Observable Truths

Derived from ROADMAP.md Success Criteria and PLAN must_haves:

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can view MACD, RSI, KDJ indicators in sub-charts below the K-line chart, with BOLL bands overlaid on the main chart | VERIFIED | KLineChart.vue lines 143-644: dynamic multi-grid layout builds separate grids for each active indicator. BOLL bands as 3 line series on grid 0 (line 284-324). MACD sub-chart with macd/signal lines + histogram bars (lines 489-549). RSI sub-chart with markLine at 30/70 (lines 550-588). KDJ sub-chart with K/D/J lines (lines 589-641). |
| 2 | User can adjust indicator parameters (periods, thresholds) and see recalculated results | VERIFIED | StrategyView.vue lines 13-101: el-popover panels with el-input-number for each indicator's params. Apply button (line 202-207) calls chartStore.updateIndicatorParams + stockStore.fetchIndicatorData which hits GET /api/indicators/{ts_code} with custom params. Backend IndicatorService.compute_indicators merges custom params with defaults (line 79). |
| 3 | Volume-price confirmation signals (volume-up on rise, volume-down on fall) are automatically marked on the chart | VERIFIED | VPAService.detect_volume_price_signals (vpa_service.py lines 30-114) detects volume_up_rise (line 65-71) and volume_down_fall (line 73-79). Frontend KLineChart.vue lines 338-385 builds confirmUpData (green triangle) and confirmDownData (red inverted triangle) scatter series from signalMap. |
| 4 | Volume-price anomaly signals (long candle + low volume trap, short candle + high volume weakness) are automatically marked | VERIFIED | VPAService detects long_candle_low_volume (line 82-88), short_candle_high_volume (line 90-96), rising_volume_decline (line 99-112). Frontend KLineChart.vue lines 387-410 builds anomalyData scatter series with yellow diamond symbol. |
| 5 | K-line patterns (hammer, shooting star, doji, hanging man) are automatically identified and annotated | VERIFIED | VPAService.detect_kline_patterns (vpa_service.py lines 116-197) detects doji (line 151), hammer (line 165), hanging_man (line 168-179), shooting_star (line 189). Frontend KLineChart.vue lines 421-456 builds patternDotData scatter series with light gray circle dots. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/models.py` | IndicatorValue model with params_hash | VERIFIED | Lines 66-112: class IndicatorValue with ts_code, trade_date, indicator_name, params_hash, value_json. UniqueConstraint on (ts_code, trade_date, indicator_name, params_hash). |
| `backend/app/services/indicator_service.py` | MACD/RSI/KDJ/BOLL computation with ta + custom KDJ | VERIFIED | 399 lines. IndicatorService class. _compute_macd uses ta.trend.MACD, _compute_rsi uses ta.momentum.RSIIndicator, _compute_boll uses ta.volatility.BollingerBands, _compute_kdj is custom Stochastic Oscillator (lines 206-250). Caching via params_hash (lines 313-398). |
| `backend/app/services/vpa_service.py` | VPA signal detection + K-line pattern recognition | VERIFIED | 251 lines. VPAService with detect_volume_price_signals (5 signal types) and detect_kline_patterns (4 pattern types). Uses rolling avg_vol_5 for signal thresholds. |
| `backend/app/api/indicators.py` | GET /api/indicators/{ts_code} endpoint | VERIFIED | 96 lines. @router.get("/indicators/{ts_code}") with indicator and params query params. Validates ts_code, validates indicator name, parses params JSON, calls IndicatorService. |
| `backend/app/api/vpa.py` | GET /api/vpa/{ts_code} endpoint | VERIFIED | 72 lines. @router.get("/vpa/{ts_code}") calling both detect_volume_price_signals and detect_kline_patterns, returns combined result. |
| `frontend/src/components/KLineChart.vue` | Dynamic multi-grid chart with indicators, BOLL overlay, signal/pattern markers | VERIFIED | 822 lines. Dynamic grid/xAxis/yAxis/series builder based on chartStore toggles. BOLL overlay (3 line series on grid 0). MACD/RSI/KDJ sub-charts. Signal scatter series (triangles + diamonds). Pattern scatter series (dots). Tooltip includes signal/pattern info. |
| `frontend/src/stores/chart.js` | Indicator toggle state, params, signal toggles | VERIFIED | 61 lines. State: showMACD/RSI/KDJ/BOLL (default false), showSignals/showPatterns (default true), indicatorParams with defaults. Actions: toggleIndicator, updateIndicatorParams. |
| `frontend/src/stores/stock.js` | Indicator/VPA data fetching actions | VERIFIED | 157 lines. State: indicatorData, vpaData. Actions: fetchIndicatorData, fetchVPAData, fetchAllEnabledData. Imports getIndicatorData and getVPAData from API. |
| `frontend/src/api/index.js` | getIndicatorData and getVPAData API functions | VERIFIED | 89 lines. getIndicatorData (line 70) calls /indicators/{tsCode} with params. getVPAData (line 84) calls /vpa/{tsCode}. |
| `frontend/src/views/StrategyView.vue` | Toolbar with indicator toggles, Popover params, signal toggles | VERIFIED | 361 lines. 4 el-popover panels for MACD/RSI/KDJ/BOLL params. Apply button triggers recalculation. Signal/pattern toggle buttons. Watcher fetches all enabled data when stock loads. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| backend/app/api/indicators.py | backend/app/services/indicator_service.py | IndicatorService(db).compute_indicators() | WIRED | Line 12 imports, line 81 instantiates, line 83 calls compute_indicators |
| backend/app/api/vpa.py | backend/app/services/vpa_service.py | VPAService(db).detect_*() | WIRED | Line 10 imports, line 53 instantiates, lines 55-56 call both detect methods |
| backend/app/main.py | backend/app/api/indicators.py | include_router | WIRED | Lines 81-86: imports indicators_router, app.include_router with /api prefix |
| backend/app/main.py | backend/app/api/vpa.py | include_router | WIRED | Lines 82-87: imports vpa_router, app.include_router with /api prefix |
| frontend/src/stores/stock.js | /api/indicators/{ts_code} | getIndicatorData API call | WIRED | Line 2 imports, line 113 calls getIndicatorData in fetchIndicatorData action |
| frontend/src/stores/stock.js | /api/vpa/{ts_code} | getVPAData API call | WIRED | Line 2 imports, line 127 calls getVPAData in fetchVPAData action |
| frontend/src/components/KLineChart.vue | frontend/src/stores/chart.js | chartStore.showMACD etc. for visibility | WIRED | Lines 144-146 (activeIndicators), line 284 (BOLL), line 338 (signals), line 421 (patterns) |
| frontend/src/views/StrategyView.vue | frontend/src/stores/chart.js | toggleIndicator actions on buttons | WIRED | Line 189 chartStore.toggleIndicator(name), line 205 chartStore.updateIndicatorParams |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| KLineChart.vue (MACD sub-chart) | stockStore.indicatorData.macd | fetchIndicatorData -> GET /api/indicators -> IndicatorService._compute_macd -> ta.trend.MACD on DailyBar data | Yes: queries DailyBar from DB, computes via ta library, returns real values | FLOWING |
| KLineChart.vue (RSI sub-chart) | stockStore.indicatorData.rsi | fetchIndicatorData -> GET /api/indicators -> IndicatorService._compute_rsi -> ta.momentum.RSIIndicator on DailyBar data | Yes: real DB data + ta computation | FLOWING |
| KLineChart.vue (KDJ sub-chart) | stockStore.indicatorData.kdj | fetchIndicatorData -> GET /api/indicators -> IndicatorService._compute_kdj -> custom Stochastic Oscillator on DailyBar data | Yes: real DB data + custom computation | FLOWING |
| KLineChart.vue (BOLL overlay) | stockStore.indicatorData.boll | fetchIndicatorData -> GET /api/indicators -> IndicatorService._compute_boll -> ta.volatility.BollingerBands on DailyBar data | Yes: real DB data + ta computation | FLOWING |
| KLineChart.vue (signal markers) | stockStore.vpaData.signals | fetchVPAData -> GET /api/vpa -> VPAService.detect_volume_price_signals on DailyBar data | Yes: queries DailyBar from DB, computes derived columns, applies threshold checks | FLOWING |
| KLineChart.vue (pattern markers) | stockStore.vpaData.patterns | fetchVPAData -> GET /api/vpa -> VPAService.detect_kline_patterns on DailyBar data | Yes: queries DailyBar, computes body/shadow/range, applies pattern rules | FLOWING |
| StrategyView.vue (param adjustment) | chartStore.indicatorParams | Local reactive copies in Popover -> applyParams() -> chartStore.updateIndicatorParams + stockStore.fetchIndicatorData | Yes: updates store params and refetches from backend with new params | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Backend indicator tests pass | `cd backend && python -m pytest tests/test_indicators.py tests/test_vpa.py -x -v` | 17 passed in 0.21s | PASS |
| Frontend build succeeds | `cd frontend && npx vite build` | Built in 2.70s, no errors | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DATA-03 | 02-01 | Technical indicator results persisted in database | SATISFIED | IndicatorValue model in models.py, _cache_results in indicator_service.py writes to indicator_values table with params_hash |
| DATA-04 | 02-01, 02-02 | Support indicator parameter adjustment | SATISFIED | Backend: IndicatorService.compute_indicators accepts params dict, merges with defaults. Frontend: Popover panels with el-input-number, Apply button triggers refetch |
| VPA-01 | 02-01, 02-03 | Auto-mark volume-price confirmation signals | SATISFIED | VPAService detects volume_up_rise and volume_down_fall. Frontend renders green/red triangle scatter markers |
| VPA-02 | 02-01, 02-03 | Auto-mark volume-price anomaly signals | SATISFIED | VPAService detects long_candle_low_volume, short_candle_high_volume, rising_volume_decline. Frontend renders yellow diamond scatter markers |
| VPA-03 | 02-01, 02-03 | K-line pattern auto-recognition | SATISFIED | VPAService detects hammer, shooting_star, doji, hanging_man. Frontend renders light gray circle dot markers with tooltip |
| INDIC-01 | 02-01, 02-02 | MACD indicator in sub-chart | SATISFIED | Backend _compute_macd via ta.trend.MACD. Frontend MACD sub-chart with macd line + signal line + histogram bars |
| INDIC-02 | 02-01, 02-02 | RSI indicator in sub-chart with param adjustment | SATISFIED | Backend _compute_rsi via ta.momentum.RSIIndicator. Frontend RSI sub-chart with 30/70 markLine references |
| INDIC-03 | 02-01, 02-02 | KDJ indicator in sub-chart | SATISFIED | Backend _compute_kdj custom Stochastic Oscillator. Frontend KDJ sub-chart with K/D/J lines |
| INDIC-04 | 02-01, 02-02 | BOLL bands overlay on K-line chart | SATISFIED | Backend _compute_boll via ta.volatility.BollingerBands. Frontend 3 line series (upper dashed, middle solid, lower dashed) on grid 0 |
| INDIC-06 | 02-01, 02-02 | User can adjust indicator parameters and recalculate | SATISFIED | Backend params_hash supports multiple parameter sets. Frontend Popover panels + Apply button triggers recalculation |

No orphaned requirements found. All 10 requirements from REQUIREMENTS.md Phase 2 are covered by plans and verified in the codebase.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| frontend/src/stores/stock.js | 117 | console.error in fetchIndicatorData catch | Info | Proper error logging, not a stub |
| frontend/src/stores/stock.js | 130 | console.error in fetchVPAData catch | Info | Proper error logging, not a stub |

No blockers or warnings found. All TODO/FIXME/placeholder/stub patterns came back clean across all 9 key files.

### Human Verification Required

### 1. Visual verification of indicator sub-chart rendering

**Test:** Start both backend and frontend servers, search for a stock, click MACD/RSI/KDJ/BOLL buttons
**Expected:** Each indicator sub-chart appears correctly below the volume chart. BOLL bands overlay on K-line. Sub-charts scroll together. Crosshair is synchronized.
**Why human:** Visual appearance of chart rendering, proper scaling, color rendering, and grid proportions require visual inspection.

### 2. Signal marker visual verification

**Test:** With a stock loaded, observe the K-line chart for triangle/diamond/dot markers
**Expected:** Green triangles above bars for volume-up-rise signals, red inverted triangles below bars for volume-down-fall, yellow diamonds for anomalies, gray dots for K-line patterns. Hover tooltip shows signal/pattern info.
**Why human:** Marker positioning accuracy, visual distinction between marker types, and tooltip interaction quality need human eyes.

### 3. Parameter adjustment end-to-end

**Test:** Click MACD button, open popover, change fast period from 12 to 8, click Apply
**Expected:** Chart updates with recalculated MACD values using new parameter. Visual difference in MACD line should be observable.
**Why human:** Need to observe the actual chart recalculation and verify the visual change is meaningful.

### Gaps Summary

No gaps found. All observable truths are verified at all four levels (exists, substantive, wired, data flowing). All 10 requirements are satisfied. Backend tests (17/17) and frontend build pass cleanly. Anti-pattern scan returned zero blockers or warnings.

---

_Verified: 2026-05-06T03:00:00Z_
_Verifier: Claude (gsd-verifier)_
