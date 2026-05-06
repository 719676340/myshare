---
phase: 04-trading-practice-module
plan: 01
subsystem: api, database
tags: [fastapi, sqlalchemy, pydantic, sqlite, trading-rules]

# Dependency graph
requires:
  - phase: 01-data-foundation-k-line-charting
    provides: Stock/DailyBar ORM models, database.py Base class, async session pattern
  - phase: 02-technical-indicators-volume-price-analysis
    provides: Service class pattern (AsyncSession injection), API router pattern
provides:
  - PracticeSession/Trade/Position ORM models with FIFO position tracking
  - PracticeService with 7 async methods for session lifecycle management
  - 7 REST API endpoints for trading practice
  - A-share rule enforcement (T+1, price limits 10%/5%/20%, commission/stamp tax)
  - FIFO trade pairing for statistics with equity curve builder
affects: [04-trading-practice-module]

# Tech tracking
tech-stack:
  added: [pydantic BaseModel for request validation]
  patterns: [practice service pattern, FIFO trade matching, equity curve replay]

key-files:
  created:
    - backend/app/services/practice_service.py
    - backend/app/api/practice.py
  modified:
    - backend/app/models.py
    - backend/app/database.py
    - backend/app/main.py

key-decisions:
  - "Position model uses remaining_shares for FIFO tracking; sell reduces per-lot shares"
  - "current_date initialized to last bar before start_date so user sees context on session creation"
  - "Equity curve built by replaying trades chronologically against daily close prices"

patterns-established:
  - "PracticeService pattern: constructor takes AsyncSession, 7 public async methods, private helpers prefixed with _"
  - "Pydantic request models for POST endpoints: CreateSessionRequest, OrderRequest, SellOrderRequest"
  - "FIFO trade pairing: buy_queue consumed by sell trades, partial matching across multiple buys"

requirements-completed: [PRACT-01, PRACT-02, PRACT-03, PRACT-04, PRACT-05, PRACT-06, PRACT-07, PRACT-08]

# Metrics
duration: 5min
completed: 2026-05-06
---

# Phase 04 Plan 01: Backend Practice Infrastructure Summary

**PracticeSession/Trade/Position ORM models with PracticeService enforcing A-share rules (T+1, price limits, fees) and 7 REST endpoints for full practice lifecycle**

## Performance

- **Duration:** 5 min
- **Started:** 2026-05-06T12:19:26Z
- **Completed:** 2026-05-06T12:25:02Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Three new ORM models (PracticeSession, Trade, Position) with relationships and FIFO position tracking
- PracticeService with complete trade lifecycle: session creation, daily advancement, buy/sell with rule enforcement, statistics
- A-share trading rules correctly enforced: T+1 sell restriction, price limits by stock type (10% normal, 5% ST, 20% ChiNext/STAR), commission 0.025% both sides, stamp tax 0.1% on sells only
- FIFO trade pairing for statistics with per-pair profit, holding days, and aggregate metrics
- Equity curve builder that replays trades day-by-day to compute net worth over time
- 7 REST API endpoints with Pydantic request validation and consistent error handling

## Task Commits

Each task was committed atomically:

1. **Task 1: Add PracticeSession, Trade, Position models** - `c0279e4` (feat)
2. **Task 2: Create PracticeService** - `2ba5044` (feat)
3. **Task 3: Create practice API endpoints and register router** - `2e5c79c` (feat)

## Files Created/Modified
- `backend/app/models.py` - Added PracticeSession, Trade, Position ORM models with relationships
- `backend/app/database.py` - Updated init_db import to include new models
- `backend/app/services/practice_service.py` - PracticeService with 7 public methods, FIFO pairing, equity curve
- `backend/app/api/practice.py` - 7 REST endpoints with Pydantic request models
- `backend/app/main.py` - Registered practice_router in app

## Decisions Made
- Position model tracks remaining_shares per lot for FIFO sell matching (each buy creates a separate Position record)
- Session current_date initialized to last bar before start_date so frontend shows context K-lines on session creation
- Equity curve built by replaying all trades chronologically against daily close prices rather than storing snapshots
- Price limit detection uses stock name for ST check and ts_code prefix for ChiNext (30xxx) / STAR (688xxx)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend practice infrastructure complete, ready for frontend integration (Plan 04-02)
- All 7 endpoints return correct JSON and are accessible via FastAPI
- Frontend can create sessions, advance days, place orders, and retrieve statistics
- Plan 04-02 will build the practice UI (config page, K-line with advance, trade panel, results)

## Self-Check: PASSED

All 5 files verified present. All 3 task commits (c0279e4, 2ba5044, 2e5c79c) confirmed in git log.

---
*Phase: 04-trading-practice-module*
*Completed: 2026-05-06*
