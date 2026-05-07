---
phase: 05-strategy-backtesting-module
plan: 01
subsystem: api, database
tags: [fastapi, sqlalchemy, expression-parser, ast, pandas, backtest]

# Dependency graph
requires:
  - phase: 04-trading-practice-module
    provides: "Fee calculation patterns, trade pairing, equity curve building"
  - phase: 02-indicators-module
    provides: "Technical indicator computation (MA, EMA, etc.)"
provides:
  - "AST-based expression parser for safe user-defined indicator formulas"
  - "Backtest engine with day-by-day simulation and A-share rule enforcement"
  - "6 REST API endpoints for backtest configuration, execution, and history"
  - "BacktestSession and BacktestTrade database models"
  - "3 preset strategy templates (MA crossover, volume breakout, MACD divergence)"
affects: [05-02-frontend-backtest]

# Tech tracking
tech-stack:
  added: [ast-stdlib, numpy]
  patterns: [ast-expression-parsing, topological-sort-for-dependencies, condition-tree-evaluation]

key-files:
  created:
    - backend/app/services/expression_parser.py
    - backend/app/services/backtest_service.py
    - backend/app/api/backtest.py
  modified:
    - backend/app/models.py
    - backend/app/database.py
    - backend/app/main.py

key-decisions:
  - "Expression parser uses Python ast module with whitelist validation (SAFE_FIELDS, SAFE_FUNCTIONS, SAFE_NODE_TYPES) for security"
  - "Topological sort resolves cross-indicator dependencies (e.g., EMA(MACD_DIF, 9) depends on MACD_DIF)"
  - "Full position model: buy only when no position, sell all shares at once"
  - "T+1 enforced by checking buy_date != current_date before allowing sell"
  - "Buy-and-hold baseline computed alongside strategy equity curve for comparison"

patterns-established:
  - "AST-based safe expression evaluation: parse -> validate whitelist -> eval with restricted namespace"
  - "Condition tree pattern: recursive evaluation with group (AND/OR) and rule nodes"
  - "Indicator dependency resolution via topological sort before sequential evaluation"

requirements-completed: [BACK-01, BACK-02, BACK-03, BACK-04, BACK-05, DATA-05]

# Metrics
duration: 7min
completed: 2026-05-07
---

# Phase 5 Plan 01: Backtest Backend Summary

**AST-based expression parser with safe whitelist, backtest engine with A-share T+1/fees, 8 performance metrics, and 6 REST API endpoints**

## Performance

- **Duration:** 7 min
- **Started:** 2026-05-07T03:36:38Z
- **Completed:** 2026-05-07T03:43:38Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Expression parser safely evaluates formulas like VOL/MA(VOL,20) using Python ast module with strict whitelist, rejecting malicious code like __import__("os")
- Backtest engine iterates daily through data, evaluates buy/sell condition trees, enforces T+1, computes fees (commission 0.025% + stamp tax 0.1%), and calculates all 8 metrics (total return, annualized return, max drawdown, trade count, win rate, profit factor, Sharpe ratio, avg holding days)
- 6 REST API endpoints with Pydantic recursive models for condition tree validation, expression pre-validation before backtest execution
- Topological sort for cross-indicator dependency resolution (e.g., MACD_DEA depends on MACD_DIF)
- 3 preset strategy templates as data configs, not hardcoded logic

## Task Commits

Each task was committed atomically:

1. **Task 1: Expression parser + Backtest engine + Models** - `2cb6e1e` (feat)
2. **Task 2: REST API endpoints + Router registration** - `e60f946` (feat)

## Files Created/Modified
- `backend/app/services/expression_parser.py` - AST-based expression parser with SAFE_FIELDS, SAFE_FUNCTIONS, SAFE_NODE_TYPES whitelist
- `backend/app/services/backtest_service.py` - BacktestService with day-by-day simulation, condition evaluation, statistics, presets
- `backend/app/api/backtest.py` - 6 REST API endpoints (run, presets, sessions CRUD, validate-expression)
- `backend/app/models.py` - Added BacktestSession and BacktestTrade models with JSON columns for config storage
- `backend/app/database.py` - Added new model imports for auto table creation
- `backend/app/main.py` - Registered backtest router alongside existing routers

## Decisions Made
- Expression parser uses Python stdlib ast module with whitelist approach (safer than regex-based parsing, more expressive than simple string evaluation)
- Topological sort (Kahn's algorithm) for indicator dependency ordering detects circular dependencies
- Full position model (all-in buy, full sell) simplified from practice module's multi-lot FIFO approach
- Condition tree uses recursive evaluation supporting nested AND/OR groups with 11 operators

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed duplicate /backtest prefix in route paths**
- **Found during:** Task 2 (REST API endpoints)
- **Issue:** Route decorators included /backtest/ prefix while APIRouter already had prefix="/backtest", creating paths like /backtest/backtest/run
- **Fix:** Removed /backtest/ prefix from all route decorator paths, keeping only the router-level prefix
- **Files modified:** backend/app/api/backtest.py
- **Verification:** All 6 routes verified at correct paths (/backtest/run, /backtest/presets, etc.)
- **Committed in:** e60f946 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor path fix. No scope creep.

## Issues Encountered
None - all verification tests passed on first run after the route prefix fix.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend fully ready for frontend consumption in Plan 02
- All 6 API endpoints tested and working
- Expression parser validates safety correctly (rejects __import__, unknown functions)
- 3 preset strategies available as starting templates for the UI

---
*Phase: 05-strategy-backtesting-module*
*Completed: 2026-05-07*

## Self-Check: PASSED

All created/modified files verified:
- FOUND: backend/app/services/expression_parser.py
- FOUND: backend/app/services/backtest_service.py
- FOUND: backend/app/api/backtest.py
- FOUND: backend/app/models.py
- FOUND: backend/app/database.py
- FOUND: backend/app/main.py
- FOUND: .planning/phases/05-strategy-backtesting-module/05-01-SUMMARY.md

All commits verified:
- FOUND: 2cb6e1e (Task 1)
- FOUND: e60f946 (Task 2)
