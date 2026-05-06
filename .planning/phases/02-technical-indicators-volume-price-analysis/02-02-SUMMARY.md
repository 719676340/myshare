---
phase: 02-technical-indicators-volume-price-analysis
plan: 02
subsystem: ui, api
tags: [echarts, vue, pinia, macd, rsi, kdj, bollinger, multi-grid, popover, toolbar]

# Dependency graph
requires:
  - phase: 02-technical-indicators-volume-price-analysis
    provides: "Indicator/VPA API endpoints (GET /api/indicators/{ts_code}, GET /api/vpa/{ts_code})"
  - phase: 01-data-foundation-k-line-charting
    provides: "KLineChart.vue, chart/stock stores, StrategyView.vue, ECharts dark theme"
provides:
  - "Dynamic multi-grid chart layout with MACD/RSI/KDJ sub-charts and BOLL overlay"
  - "Indicator toggle buttons with el-popover parameter panels in toolbar"
  - "API client functions getIndicatorData and getVPAData"
  - "Extended chart store with indicator toggles, params, signal toggles"
  - "Extended stock store with indicator/VPA data fetching actions"
affects: [02-technical-indicators-volume-price-analysis, 03-strategy-analysis-module]

# Tech tracking
tech-stack:
  added: []
  patterns: [dynamic-multi-grid-layout, indicator-data-alignment-via-lookup-map, popover-param-panel]

key-files:
  created: []
  modified:
    - frontend/src/api/index.js
    - frontend/src/stores/stock.js
    - frontend/src/stores/chart.js
    - frontend/src/components/KLineChart.vue
    - frontend/src/views/StrategyView.vue

key-decisions:
  - "Grid heights scaled proportionally when multiple indicators shown (K-line=35%, volume=12%, each indicator=15%)"
  - "BOLL bands as 3 line series on main K-line grid (not sub-chart), purple dashed/solid lines"
  - "MACD histogram bars colored red (positive) / green (negative) matching A-share convention"
  - "RSI markLines at 30/70 with dashed gray lines for overbought/oversold reference"
  - "Indicator data aligned via Map lookup on trade_date, null for missing dates"
  - "Popover param panels use local reactive copies, Apply button syncs to store and refetches"

patterns-established:
  - "Dynamic grid builder: build grids/xAxes/yAxes arrays conditionally based on chartStore toggles"
  - "Indicator data alignment: Map from trade_date to values, map dates array to aligned values"
  - "Popover param panel pattern: local reactive copy + Apply button to sync store + refetch"
  - "fetchAllEnabledData: batch-fetch all active indicators after stock data loads via watcher"

requirements-completed: [INDIC-01, INDIC-02, INDIC-03, INDIC-04, INDIC-06, DATA-04]

# Metrics
duration: 6min
completed: 2026-05-06
---

# Phase 2 Plan 2: Frontend Indicator Sub-charts and Toolbar Controls Summary

**Dynamic multi-grid K-line chart with toggleable MACD/RSI/KDJ sub-charts, BOLL overlay, and toolbar popover parameter panels integrated with backend indicator API**

## Performance

- **Duration:** 6 min
- **Started:** 2026-05-06T02:22:21Z
- **Completed:** 2026-05-06T02:29:06Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- KLineChart.vue dynamically builds multi-grid layout based on chartStore toggle states
- MACD sub-chart renders macd line (blue), signal line (orange), and histogram bars (red/green)
- RSI sub-chart renders rsi line (purple) with 30/70 reference markLines
- KDJ sub-chart renders K (white), D (yellow), J (red) lines
- BOLL bands overlay on K-line main chart with upper/middle/lower lines
- Toolbar has indicator toggle buttons with el-popover parameter panels and Apply button
- Signal and pattern toggle buttons added to toolbar
- All sub-charts synchronize via shared dataZoom and axisPointer linking

## Task Commits

Each task was committed atomically:

1. **Task 1: API client functions and Pinia store extensions** - `41da50e` (feat)
2. **Task 2: KLineChart multi-grid extension and StrategyView toolbar** - `1969807` (feat)

## Files Created/Modified
- `frontend/src/api/index.js` - Added getIndicatorData and getVPAData API functions
- `frontend/src/stores/stock.js` - Added indicatorData/vpaData state, fetchIndicatorData/fetchVPAData/fetchAllEnabledData actions
- `frontend/src/stores/chart.js` - Added indicator toggles (showMACD/showRSI/showKDJ/showBOLL), signal toggles (showSignals/showPatterns), indicatorParams, toggleIndicator/updateIndicatorParams actions
- `frontend/src/components/KLineChart.vue` - Rewrote chartOption as dynamic multi-grid builder with BOLL overlay and indicator sub-charts
- `frontend/src/views/StrategyView.vue` - Added indicator toggle buttons with el-popover parameter panels, signal/pattern toggles, data fetching watcher

## Decisions Made
- Grid heights are proportionally scaled when multiple indicators shown: K-line=35%, volume=12%, each indicator=15%, with a scaling factor if total exceeds 100%
- BOLL bands rendered as 3 line series on grid 0 (K-line main chart) with purple dashed upper/lower and solid middle
- MACD histogram bars use red for positive and green for negative values (matching A-share up/down convention)
- RSI has static y-axis range 0-100 with markLine references at 30/70 for overbought/oversold
- Indicator data aligned via Map lookup on trade_date; null values fill gaps where no indicator data exists for a date
- Popover parameter panels use local reactive copies of store params; Apply button syncs to store and triggers refetch

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None - all functionality implemented as planned.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Frontend indicator chart rendering complete, ready for VPA signal markers and K-line pattern annotations (Plan 02-03)
- Chart store has showSignals/showPatterns toggles ready for marker rendering
- Stock store has vpaData (signals + patterns) ready to be consumed by chart components
- Dynamic multi-grid architecture supports adding more sub-charts in future phases

---
*Phase: 02-technical-indicators-volume-price-analysis*
*Completed: 2026-05-06*

## Self-Check: PASSED

All 5 modified files and 1 SUMMARY file verified present on disk. Both plan commits (41da50e, 1969807) confirmed in git log.
