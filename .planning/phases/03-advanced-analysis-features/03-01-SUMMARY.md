---
phase: 03-advanced-analysis-features
plan: 01
subsystem: api, database
tags: [pandas, numpy, fastapi, sqlalchemy, pivot-detection, trend-lines, vap, market-cycle, divergence]

# Dependency graph
requires:
  - phase: 01-data-foundation-k-line-charting
    provides: "DailyBar model, database session, _load_daily_data pattern"
  - phase: 02-technical-indicators-volume-price-analysis
    provides: "VPAService pattern, API validation pattern, IndicatorValue model"
provides:
  - "AdvancedAnalysisService with 6 computation methods"
  - "6 API endpoints for advanced analysis features"
  - "Pivot detection algorithm (isolated high/low per Chapter 07)"
  - "Support/resistance level grouping with 2% tolerance"
  - "Trend line detection connecting consecutive pivots"
  - "Market cycle phase detection (accumulation/markup/distribution/markdown)"
  - "VAP volume-at-price 30-bin distribution"
  - "Weekly/monthly K-line aggregation from daily data"
  - "Price-volume bearish divergence detection"
affects: [03-advanced-analysis-features-frontend, chart-rendering, store-extensions]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "AdvancedAnalysisService(session) follows VPAService constructor pattern"
    - "All public methods are async, return dict with top-level key"
    - "Empty data returns predictable empty dict shapes"

key-files:
  created:
    - backend/app/services/advanced_analysis_service.py
    - backend/app/api/advanced.py
  modified:
    - backend/app/main.py

key-decisions:
  - "Pivot detection uses strict isolated pivot definition from Chapter 07 (both high and low must exceed neighbors)"
  - "Support/resistance groups use 2% price tolerance, classify relative to latest close"
  - "Trend lines connect consecutive same-type pivots within 60 bars"
  - "Market cycle uses 20-bar sliding window with volume/ATR/MA comparisons"
  - "VAP distributes volume across 30 bins with linear interpolation for bar-bin overlap"
  - "Weekly aggregation uses ISO week (Monday start), monthly uses YYYYMM"
  - "Divergence uses 20-day rolling high with 80% volume threshold"

patterns-established:
  - "Advanced analysis service pattern: async methods, DataFrame-based computation, dict response"
  - "API endpoint pattern: validate ts_code, instantiate service, call method, wrap result"

requirements-completed: [VPA-04, ADVAN-01, ADVAN-02, ADVAN-03, ADVAN-04, ADVAN-05]

# Metrics
duration: 5min
completed: 2026-05-06
---

# Phase 3 Plan 1: Advanced Analysis Backend Summary

**AdvancedAnalysisService implementing pivot detection, support/resistance grouping, trend lines, market cycle phases, VAP distribution, K-line aggregation, and divergence detection with 6 FastAPI endpoints**

## Performance

- **Duration:** 5 min
- **Started:** 2026-05-06T06:37:35Z
- **Completed:** 2026-05-06T06:42:39Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- AdvancedAnalysisService with 9 test-backed computation methods covering all advanced analysis algorithms from user study notes
- 6 REST API endpoints registered under /api/advanced/{ts_code}/ prefix for frontend consumption
- All 37 backend tests pass with zero regressions from Phase 1/2

## Task Commits

Each task was committed atomically:

1. **Task 1: AdvancedAnalysisService implementation (TDD GREEN)** - `12f8deb` (feat)
2. **Task 2: API endpoints + router registration** - `8817a37` (feat)

**TDD RED commit (pre-existing):** `cc77882` (test)

## Files Created/Modified
- `backend/app/services/advanced_analysis_service.py` - Core service with 6 public methods (detect_pivots, detect_support_resistance, detect_trend_lines, detect_market_cycle, compute_vap, aggregate_kline, detect_divergence)
- `backend/app/api/advanced.py` - 6 GET endpoints for advanced analysis features
- `backend/app/main.py` - Added advanced_router registration
- `backend/tests/test_advanced_analysis.py` - 11 test cases covering all algorithms (pre-existing from TDD RED)

## Decisions Made
- Used strict isolated pivot definition from Chapter 07: both high AND low must exceed/fall below both neighbors (not just high or low alone)
- Support/resistance uses 2% tolerance for price grouping and 0.5% threshold for "both" classification
- Trend lines limited to consecutive pivots within 60 bars to avoid meaningless long-range connections
- Market cycle detection uses 20-bar window with volume/ATR/MA metrics; defaults to previous phase when no clear pattern
- VAP uses 30 price bins with linear interpolation for volume distribution across bar-bin overlap
- Weekly aggregation uses ISO calendar week (Monday-Sunday), monthly uses YYYYMM string grouping
- Divergence threshold: volume < 80% of 20-day average when price makes 20-day high

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tests passed on first implementation run.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Backend computation service and API endpoints are complete and tested
- Ready for Plan 03-02: Frontend KLineChart rendering with support/resistance lines, trend lines, market cycle bands, VAP overlay, multi-timeframe controls, and store extensions
- All 6 endpoints return data in formats suitable for direct ECharts series mapping

## Self-Check: PASSED

- FOUND: backend/app/services/advanced_analysis_service.py
- FOUND: backend/app/api/advanced.py
- FOUND: 03-01-SUMMARY.md
- FOUND: 12f8deb (Task 1 commit)
- FOUND: 8817a37 (Task 2 commit)

---
*Phase: 03-advanced-analysis-features*
*Completed: 2026-05-06*
