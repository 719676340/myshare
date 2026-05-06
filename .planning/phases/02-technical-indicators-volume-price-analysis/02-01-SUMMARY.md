---
phase: 02-technical-indicators-volume-price-analysis
plan: 01
subsystem: api, database
tags: [ta, pandas, macd, rsi, kdj, bollinger, vpa, kline-patterns, sqlalchemy, fastapi]

# Dependency graph
requires:
  - phase: 01-data-foundation-k-line-charting
    provides: "Stock/DailyBar models, database setup, API patterns (daily.py)"
provides:
  - "IndicatorValue model with params_hash multi-parameter caching"
  - "IndicatorService: MACD/RSI/KDJ/BOLL computation with ta library + custom KDJ"
  - "VPAService: volume-price signal detection and K-line pattern recognition"
  - "GET /api/indicators/{ts_code} endpoint with configurable params"
  - "GET /api/vpa/{ts_code} endpoint returning signals and patterns"
affects: [02-technical-indicators-volume-price-analysis, 03-strategy-analysis-module]

# Tech tracking
tech-stack:
  added: [ta==0.11.0]
  patterns: [indicator-caching-via-params-hash, custom-kdj-stochastic-oscillator, vpa-signal-detection, kline-pattern-recognition]

key-files:
  created:
    - backend/app/services/indicator_service.py
    - backend/app/services/vpa_service.py
    - backend/app/api/indicators.py
    - backend/app/api/vpa.py
    - backend/tests/test_indicators.py
    - backend/tests/test_vpa.py
  modified:
    - backend/app/models.py
    - backend/app/database.py
    - backend/app/main.py
    - backend/requirements.txt
    - backend/tests/conftest.py

key-decisions:
  - "KDJ custom implementation using Stochastic Oscillator formula (ta library lacks direct KDJ)"
  - "params_hash uses MD5 of JSON-serialized sorted params dict (first 16 hex chars)"
  - "VPA signals use 5-day rolling volume average as baseline for comparison"
  - "Hanging man distinguished from hammer by uptrend context (close > open AND close > MA5)"
  - "Doji detection uses body/range < 0.1 threshold and takes priority over hammer/shooting_star"

patterns-established:
  - "Indicator caching: compute -> store in indicator_values with params_hash -> cache hit returns stored data"
  - "Signal detection: load OHLCV DataFrame -> add derived columns -> iterate with threshold checks"
  - "API endpoint pattern: validate ts_code -> parse params -> call service -> return result or HTTPException"

requirements-completed: [DATA-03, DATA-04, INDIC-01, INDIC-02, INDIC-03, INDIC-04, INDIC-06]

# Metrics
duration: 14min
completed: 2026-05-06
---

# Phase 2 Plan 1: Backend Indicator Engine and VPA Service Summary

**MACD/RSI/KDJ/BOLL indicator computation with ta library + custom KDJ, VPA signal detection, K-line pattern recognition, and two API endpoints with params_hash caching**

## Performance

- **Duration:** 14 min
- **Started:** 2026-05-06T02:03:51Z
- **Completed:** 2026-05-06T02:17:53Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- IndicatorService computes MACD, RSI, BOLL via ta library and KDJ via custom Stochastic Oscillator
- Computed indicator values cached in indicator_values table with params_hash for multi-parameter coexistence
- VPAService detects 5 volume-price signal types (2 confirmation + 3 anomaly) and 4 K-line patterns
- Two new API endpoints registered: /api/indicators/{ts_code} and /api/vpa/{ts_code}

## Task Commits

Each task was committed atomically (TDD: RED then GREEN):

1. **Task 1: IndicatorValue model and indicator service** - RED: `2159883` (test), GREEN: `0ed6533` (feat)
2. **Task 2: VPA service and API endpoints** - RED: `8987d0f` (test), GREEN: `2253edc` (feat)

## Files Created/Modified
- `backend/app/models.py` - Added IndicatorValue model with params_hash unique constraint
- `backend/app/database.py` - Updated init_db to import IndicatorValue
- `backend/app/services/indicator_service.py` - IndicatorService: MACD/RSI/KDJ/BOLL computation with caching
- `backend/app/services/vpa_service.py` - VPAService: volume-price signals and K-line pattern detection
- `backend/app/api/indicators.py` - GET /api/indicators/{ts_code} with indicator and params query params
- `backend/app/api/vpa.py` - GET /api/vpa/{ts_code} returning combined signals + patterns
- `backend/app/main.py` - Registered indicators_router and vpa_router under /api prefix
- `backend/requirements.txt` - Added ta==0.11.0
- `backend/tests/conftest.py` - Added IndicatorValue import for test table creation
- `backend/tests/test_indicators.py` - 7 tests for indicator computation and model
- `backend/tests/test_vpa.py` - 10 tests for VPA signals, patterns, and API endpoints

## Decisions Made
- KDJ uses custom Stochastic Oscillator formula (2/3 prev_K + 1/3 RSV for K, same smoothing for D, J=3K-2D clamped to [0,100]) because ta library lacks direct KDJ implementation
- params_hash is first 16 chars of MD5(JSON dumps with sorted keys), sufficient for deduplication
- VPA signal thresholds: volume_up_rise requires vol > avg_vol_5 * 1.2, volume_down_fall requires vol < avg_vol_5 * 0.8
- Anomaly thresholds: long_candle_low_volume body_ratio > 0.6 and vol < avg_vol_5 * 0.7; short_candle_high_volume body_ratio < 0.3 and vol > avg_vol_5 * 1.5
- Doji detection (body/range < 0.1) takes priority over hammer/shooting star to avoid misclassification

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test date generation producing duplicate trade_dates**
- **Found during:** Task 1 (indicator tests)
- **Issue:** _make_ohlcv_df helper generated duplicate dates when n_rows > 28
- **Fix:** Used datetime.timedelta for sequential unique date generation
- **Files modified:** backend/tests/test_indicators.py
- **Verification:** All tests pass without IntegrityError
- **Committed in:** 0ed6533 (Task 1 commit)

**2. [Rule 1 - Bug] Fixed test data for K-line patterns to produce correct pattern classification**
- **Found during:** Task 2 (VPA tests)
- **Issue:** Hammer test bar had open==close (zero body) classified as doji; shooting star had body_ratio < 0.1 classified as doji; hanging man close==MA5 failing uptrend check
- **Fix:** Adjusted OHLCV values to ensure proper body sizes and trend context for each pattern
- **Files modified:** backend/tests/test_vpa.py
- **Verification:** All 10 VPA tests pass
- **Committed in:** 2253edc (Task 2 commit)

---
**Total deviations:** 2 auto-fixed (2 bug fixes in test data)
**Impact on plan:** Test data adjustments only. Production code follows plan exactly.

## Issues Encountered
None - all functionality implemented as planned.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend indicator computation engine complete, ready for frontend chart integration (Plan 02-02)
- API endpoints return MACD/RSI/KDJ/BOLL data in format ready for ECharts series configuration
- VPA signals and K-line patterns ready for frontend visual markers (triangles, dots)
- IndicatorValue table supports multiple parameter sets via params_hash for user-configurable indicators

---
*Phase: 02-technical-indicators-volume-price-analysis*
*Completed: 2026-05-06*

## Self-Check: PASSED

All 10 created/modified files verified present on disk. All 4 plan commits (2159883, 0ed6533, 8987d0f, 2253edc) confirmed in git log.
