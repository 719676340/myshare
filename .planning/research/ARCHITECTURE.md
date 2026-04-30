# Architecture Research

**Domain:** Volume-Price Trading Learning Platform (A-share, local desktop)
**Researched:** 2026-04-30
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Browser (localhost:5173)                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Vue 3 + ECharts Frontend                    │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │ │
│  │  │ StockChart│  │ Practice │  │Backtest  │  │ StockSearch  │  │ │
│  │  │ Component│  │ Module   │  │ Module   │  │ Component    │  │ │
│  │  └─────┬────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │ │
│  │        │             │             │                │          │ │
│  │  ┌─────┴─────────────┴─────────────┴────────────────┴───────┐ │ │
│  │  │              API Client Layer (axios / fetch)             │ │ │
│  │  └─────┬─────────────┬─────────────┬────────────────┬───────┘ │ │
│  └────────┼─────────────┼─────────────┼────────────────┼─────────┘ │
└───────────┼─────────────┼─────────────┼────────────────┼───────────┘
            │ HTTP REST   │             │                │
┌───────────┼─────────────┼─────────────┼────────────────┼───────────┐
│           ▼             ▼             ▼                ▼           │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                 FastAPI Backend (localhost:8000)              │ │
│  │  ┌────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │ │
│  │  │ Routers│  │ Services │  │Indicator │  │  Tushare      │  │ │
│  │  │ (API)  │→ │ (Logic)  │→ │ Engine   │  │  Client       │  │ │
│  │  └────────┘  └──────────┘  └──────────┘  └───────────────┘  │ │
│  │        │            │                                         │ │
│  │  ┌─────┴────────────┴──────────────────────────────────────┐ │ │
│  │  │              Repository Layer (SQLAlchemy)               │ │ │
│  │  └─────────────────────┬────────────────────────────────────┘ │ │
│  └────────────────────────┼───────────────────────────────────────┘ │
│                           ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    SQLite Database                            │ │
│  │  stocks | daily_quotes | indicators | practice_trades | ...  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                          Local Filesystem                          │
└────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Implementation |
|-----------|----------------|----------------|
| **StockChart** | Renders K-line candlestick + volume + indicators in linked ECharts grids | Vue 3 SFC, `vue-echarts` wrapper, ECharts multi-grid option |
| **Practice Module** | Day-by-day stock simulation, buy/sell UI, position management | Vue 3 views + Pinia store for trade state |
| **Backtest Module** | Strategy template selection, parameter tuning, results display | Vue 3 views + ECharts equity curve chart |
| **StockSearch** | Fuzzy search by code/name, stock list with autocomplete | Vue 3 component, debounced API calls |
| **API Client** | Centralized HTTP requests, error handling, response typing | axios instance with interceptors |
| **Routers** | HTTP endpoint definitions, request validation (Pydantic) | FastAPI `APIRouter` per module |
| **Services** | Business logic: indicator calculation, backtesting engine, trade simulation | Plain Python functions/classes |
| **Indicator Engine** | MACD, RSI, KDJ, BOLL computation, K-line pattern recognition | `pandas-ta` + custom logic |
| **Tushare Client** | Fetch A-share daily OHLCV data, handle rate limits and caching | `tushare` SDK wrapper with retry logic |
| **Repository Layer** | Database queries, CRUD operations, session management | SQLAlchemy ORM + `aiosqlite` async driver |
| **SQLite Database** | Persistent local storage for all application data | Single `.db` file with WAL mode |

## Recommended Project Structure

### Frontend (`/frontend`)

```
frontend/
├── src/
│   ├── api/                    # API client layer
│   │   ├── client.js           # axios instance, base URL, interceptors
│   │   ├── stock.js            # stock-related API calls
│   │   ├── indicator.js        # indicator-related API calls
│   │   ├── practice.js         # practice module API calls
│   │   └── backtest.js         # backtest module API calls
│   ├── components/
│   │   ├── chart/              # ECharts chart components
│   │   │   ├── KlineChart.vue       # Main K-line candlestick + volume
│   │   │   ├── IndicatorPanel.vue   # Sub-chart for MACD/RSI/KDJ
│   │   │   ├── ChartOverlay.vue     # Markings: patterns, S/R levels
│   │   │   └── useChartOption.js    # Composable: build ECharts option
│   │   ├── stock/
│   │   │   └── StockSearch.vue      # Fuzzy search autocomplete
│   │   ├── practice/
│   │   │   ├── TradePanel.vue       # Buy/sell controls
│   │   │   └── PositionTable.vue    # Current positions display
│   │   └── backtest/
│   │       ├── StrategySelector.vue # Strategy template picker
│   │       ├── ParamEditor.vue      # Parameter tuning UI
│   │       └── BacktestReport.vue   # Results metrics + equity curve
│   ├── views/                  # Page-level components (router pages)
│   │   ├── StrategyView.vue         # Strategy Analysis page
│   │   ├── PracticeView.vue         # Trading Practice page
│   │   └── BacktestView.vue         # Auto Backtesting page
│   ├── stores/                 # Pinia state stores
│   │   ├── stock.js                 # Selected stock, quote data
│   │   ├── chart.js                 # Chart config, indicator toggles
│   │   ├── practice.js              # Practice session state
│   │   └── backtest.js              # Backtest parameters + results
│   ├── composables/            # Reusable composition functions
│   │   ├── useStockData.js          # Fetch + cache stock quotes
│   │   └── useIndicator.js          # Fetch + transform indicator data
│   ├── utils/
│   │   ├── echarts-theme.js         # TradingView dark theme config
│   │   └── format.js                # Number/date formatting helpers
│   ├── router/
│   │   └── index.js                 # Vue Router, 3 main routes
│   ├── App.vue
│   └── main.js
├── index.html
├── vite.config.js
└── package.json
```

### Backend (`/backend`)

```
backend/
├── app/
│   ├── main.py                 # FastAPI app, CORS, router registration
│   ├── config.py               # Settings (tushare token, DB path)
│   ├── database.py             # SQLAlchemy engine, session factory
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── stock.py                 # Stock, DailyQuote, StockList
│   │   ├── indicator.py             # IndicatorResult
│   │   └── practice.py              # PracticeSession, TradeRecord
│   ├── schemas/                # Pydantic request/response schemas
│   │   ├── stock.py
│   │   ├── indicator.py
│   │   ├── practice.py
│   │   └── backtest.py
│   ├── routers/                # API endpoint definitions
│   │   ├── stock.py                 # /api/stocks, /api/stocks/{code}/daily
│   │   ├── indicator.py             # /api/indicators/{code}
│   │   ├── practice.py              # /api/practice/sessions, trades
│   │   └── backtest.py              # /api/backtest/run, /api/backtest/results
│   ├── services/               # Business logic
│   │   ├── stock_service.py         # Stock data fetch + cache logic
│   │   ├── indicator_service.py     # Indicator calculation orchestration
│   │   ├── pattern_service.py       # K-line pattern recognition
│   │   ├── practice_service.py      # Trade simulation logic
│   │   └── backtest_service.py      # Backtesting engine
│   ├── engines/                # Computation-heavy modules
│   │   ├── indicators.py            # pandas-ta based calculations
│   │   ├── patterns.py              # K-line pattern detection
│   │   ├── support_resistance.py    # S/R level detection
│   │   └── backtest_engine.py       # Core backtesting loop
│   ├── data/                   # External data access
│   │   └── tushare_client.py        # Tushare API wrapper + rate limiter
│   └── repositories/           # Database query layer
│       ├── stock_repo.py
│       ├── indicator_repo.py
│       └── practice_repo.py
├── data/
│   └── trading.db              # SQLite database file
├── requirements.txt
└── run.py                      # uvicorn entry point
```

### Structure Rationale

- **`api/` (frontend):** Centralized API calls prevent scattered `fetch()` logic. Each file maps to one backend router module, making the contract explicit.
- **`components/chart/` (frontend):** The K-line chart is the single most complex UI component. Isolating chart logic into its own directory with a composable (`useChartOption.js`) keeps the Vue component template clean while the composable builds the complex ECharts option object.
- **`views/` vs `components/` (frontend):** Views are route-level pages; components are reusable pieces. This is standard Vue Router convention.
- **`stores/` (frontend):** Pinia stores replace prop-drilling for shared state like selected stock or practice session. Each store maps to one module's domain state.
- **`routers/` / `services/` / `repositories/` (backend):** Three-tier layering (Router -> Service -> Repository) is the standard FastAPI pattern for non-trivial apps. Routers validate input, services hold logic, repositories own SQL.
- **`engines/` (backend):** Indicator calculation, pattern recognition, and backtesting are computation-heavy and algorithmically complex. Separating them from services keeps services as orchestrators and engines as pure computation.
- **`data/` (backend):** The tushare client is isolated because it deals with rate limits, retry logic, and caching -- concerns that should not leak into services.

## Architectural Patterns

### Pattern 1: ECharts Multi-Grid Linked Layout

**What:** A single ECharts instance renders candlestick, volume, and MACD/RSI in vertically stacked, synchronized grids. One `dataZoom` slider controls all grids. Crosshair (`axisPointer`) is linked across grids.

**When to use:** Every K-line chart display -- this is the foundational chart pattern.

**Trade-offs:** The ECharts option object becomes large and deeply nested. A composable (`useChartOption.js`) must build it programmatically rather than declaring it inline. This adds indirection but makes indicator toggling and dynamic updates tractable.

**Example (conceptual option structure):**
```javascript
// useChartOption.js composable builds this
const option = {
  grid: [
    { left: 60, right: 20, top: 30, height: '50%' },  // candlestick
    { left: 60, right: 20, top: '66%', height: '12%' }, // volume
    { left: 60, right: 20, top: '82%', height: '14%' }  // MACD/RSI
  ],
  xAxis: [
    { type: 'category', data: dates, gridIndex: 0 },
    { type: 'category', data: dates, gridIndex: 1 },
    { type: 'category', data: dates, gridIndex: 2 }
  ],
  yAxis: [
    { scale: true, gridIndex: 0 },     // price
    { scale: true, gridIndex: 1 },     // volume
    { scale: true, gridIndex: 2 }      // indicator
  ],
  dataZoom: [
    { type: 'inside', xAxisIndex: [0, 1, 2], start: 70, end: 100 },
    { type: 'slider', xAxisIndex: [0, 1, 2], bottom: 5 }
  ],
  axisPointer: { link: [{ xAxisIndex: [0, 1, 2] }] },
  series: [
    { type: 'candlestick', data: ohlc, xAxisIndex: 0, yAxisIndex: 0 },
    { type: 'bar', data: volumes, xAxisIndex: 1, yAxisIndex: 1 },
    // ... MA lines on gridIndex 0, MACD lines on gridIndex 2
  ]
}
```

### Pattern 2: On-Demand Data Fetch with SQLite Cache

**What:** When a user selects a stock, the backend checks SQLite first. If data is missing or stale, it fetches from tushare, stores to SQLite, then returns the data. Subsequent requests for the same stock + date range are served from cache.

**When to use:** All stock data fetching. This is the only pattern because tushare has API rate limits (200 calls/minute for pro users, lower for free tier) and we want fast repeated access.

**Trade-offs:** Adds complexity in the service layer (cache check -> fetch -> store -> return). But this is unavoidable given the tushare rate limit constraint. The pattern also enables offline browsing of previously loaded stocks.

**Example (service layer flow):**
```python
# stock_service.py
async def get_daily_quotes(code: str, start_date: str, end_date: str):
    # 1. Check SQLite cache
    cached = await stock_repo.get_quotes(code, start_date, end_date)
    if cached and not is_stale(cached):
        return cached

    # 2. Fetch from tushare
    quotes = await tushare_client.fetch_daily(code, start_date, end_date)

    # 3. Store to SQLite (upsert)
    await stock_repo.upsert_quotes(code, quotes)

    # 4. Return merged result
    return await stock_repo.get_quotes(code, start_date, end_date)
```

### Pattern 3: Indicator Pre-Computation and Storage

**What:** Technical indicators (MACD, RSI, KDJ, BOLL) are calculated on the backend using `pandas-ta`, and results are stored in an `indicators` table keyed by (stock_code, date, indicator_name, parameters). The frontend requests pre-computed values instead of raw OHLCV + client-side calculation.

**When to use:** All technical indicator display. This is a deliberate architectural choice -- compute once, read many times.

**Trade-offs:** Increases database size and requires a computation trigger (on stock data update, or on-demand). But it avoids shipping indicator computation to the frontend (which would require a JS indicator library and duplicate logic), and makes indicator values available to the backtest engine without re-computation.

### Pattern 4: Practice Session as State Machine

**What:** A trading practice session is modeled as a state machine: `CREATED -> IN_PROGRESS -> COMPLETED`. The session tracks the current day index, which advances forward-only. Trades are recorded as immutable events.

**When to use:** Trading Practice module exclusively.

**Trade-offs:** Requires careful API design to prevent day-rewinding (the backend must validate day advancement). State machine logic belongs in the service layer, not the router.

### Pattern 5: Backtest Engine as Pure Function

**What:** The backtesting engine is a pure function: `(strategy_config, stock_data) -> backtest_result`. It takes a strategy definition (name + parameters) and historical OHLCV data, and returns performance metrics plus a trade list. No side effects, no database writes during the backtest loop itself.

**When to use:** Auto Backtesting module.

**Trade-offs:** The pure function approach means the full stock dataset must be loaded into memory. For daily K-line data (typically 10-20 years of daily bars per stock), this is trivially small (a few thousand rows per stock). Results are persisted only after the backtest completes.

## Data Flow

### Primary Data Flow: tushare -> SQLite -> API -> ECharts

```
User selects stock "600519"
    |
    v
[StockSearch component] -- GET /api/stocks?q=600519 --> [Stock Router]
    |                                                      |
    |                                              [Stock Service]
    |                                                      |
    |                                              [Stock Repo] -- check cache
    |                                                      |
    |                                              [Tushare Client] (if cache miss)
    |                                                      |
    |                                              [SQLite] <-- upsert quotes
    |
    v                                                   |
User sees chart area                            (return cached quotes)
    |                                                      |
    v                                                      v
[KlineChart component] -- GET /api/stocks/600519/daily --> [Stock Router]
    |                                                      |
    | (returns: dates[], ohlc[][], volumes[], ...)    [Stock Service]
    |                                                      |
    v                                                 [Stock Repo]
[ECharts renders candlestick + volume bars]         (reads from SQLite)
    |
    v
User toggles MACD indicator
    |
    v
[IndicatorPanel] -- GET /api/indicators/600519?name=MACD&p=12,26,9 --> [Indicator Router]
    |                                                                      |
    | (returns: dif[], dea[], histogram[])                         [Indicator Service]
    |                                                                      |
    v                                                              [Indicator Engine] (pandas-ta)
[ECharts adds MACD grid below volume]                                      |
                                                                    [Indicator Repo] -- cache result
                                                                    [Stock Repo] -- read OHLCV
```

### State Management

```
[Pinia Store: stock]
  - selectedCode: "600519"
  - stockInfo: { name, industry, ... }
  - dailyQuotes: [...]
      |
      +-- (watch) --> KlineChart.vue re-renders via chart.setOption()
      |
      +-- (watch) --> IndicatorPanel.vue fetches & displays active indicators

[Pinia Store: practice]
  - sessionId: null | "uuid"
  - currentDayIndex: 42
  - positions: [...]
  - cash: 100000.00
      |
      +-- (action) advanceDay() --> POST /api/practice/sessions/{id}/advance
      +-- (action) buy/sell()  --> POST /api/practice/sessions/{id}/trades

[Pinia Store: backtest]
  - strategyName: "macd_cross"
  - params: { fast: 12, slow: 26, signal: 9 }
  - results: null | { metrics, trades, equity_curve }
      |
      +-- (action) runBacktest() --> POST /api/backtest/run
```

### Key Data Flows

1. **Stock Data Fetch:** User selects stock -> frontend calls `/api/stocks/{code}/daily` -> backend checks SQLite cache -> if miss, fetches from tushare -> stores to SQLite -> returns OHLCV array -> frontend passes to ECharts.

2. **Indicator Display:** User toggles indicator -> frontend calls `/api/indicators/{code}?name=MACD&params=12,26,9` -> backend checks if pre-computed in SQLite -> if not, computes with pandas-ta -> stores result -> returns arrays -> frontend adds ECharts series to indicator grid.

3. **Practice Day Advance:** User clicks "next day" -> frontend calls `POST /api/practice/sessions/{id}/advance` -> backend validates (no rewind, session is IN_PROGRESS) -> increments day index -> returns next day's OHLCV -> frontend updates chart to show one more candle.

4. **Practice Trade:** User clicks "buy" with position ratio -> frontend calls `POST /api/practice/sessions/{id}/trades` with `{action: "buy", ratio: 0.5}` -> backend calculates shares, commission (0.025%), stamp tax (0.1% on sell only) -> records trade -> returns updated position + cash -> frontend updates UI.

5. **Backtest Execution:** User selects strategy + params -> frontend calls `POST /api/backtest/run` -> backend loads OHLCV from SQLite -> computes indicators -> runs backtest engine loop -> returns metrics (total return, max drawdown, win rate) + trade list + equity curve data -> frontend renders BacktestReport.

6. **Pattern/Annotation Display:** User views strategy analysis -> frontend calls `/api/stocks/{code}/patterns` -> backend runs pattern recognition on cached OHLCV -> returns array of `{date, pattern_type, marking_data}` -> frontend renders ChartOverlay with marks on the K-line chart.

## SQLite Schema Design

### Core Tables

```sql
-- Stock list (pre-loaded from tushare stock_basic)
CREATE TABLE stocks (
    ts_code    TEXT PRIMARY KEY,    -- e.g. "600519.SH"
    symbol     TEXT NOT NULL,       -- e.g. "600519"
    name       TEXT NOT NULL,       -- e.g. "贵州茅台"
    industry   TEXT,
    list_date  TEXT,
    market     TEXT                 -- "主板"/"创业板"/"科创板"
);

-- Daily OHLCV quotes
CREATE TABLE daily_quotes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_code    TEXT NOT NULL,
    trade_date TEXT NOT NULL,       -- "2025-01-15"
    open       REAL,
    high       REAL,
    low        REAL,
    close      REAL,
    vol        REAL,                -- volume in shares
    amount     REAL,                -- turnover in yuan
    UNIQUE(ts_code, trade_date)
);
CREATE INDEX idx_quotes_code_date ON daily_quotes(ts_code, trade_date);

-- Technical indicator results
CREATE TABLE indicators (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_code         TEXT NOT NULL,
    trade_date      TEXT NOT NULL,
    indicator_name  TEXT NOT NULL,  -- "MACD", "RSI", "KDJ", "BOLL"
    params          TEXT NOT NULL,  -- JSON: "12,26,9"
    values          TEXT NOT NULL,  -- JSON: {"dif": 0.5, "dea": 0.3, "histogram": 0.2}
    UNIQUE(ts_code, trade_date, indicator_name, params)
);
CREATE INDEX idx_indicators_lookup ON indicators(ts_code, indicator_name, params, trade_date);

-- Practice sessions
CREATE TABLE practice_sessions (
    id          TEXT PRIMARY KEY,   -- UUID
    ts_code     TEXT NOT NULL,
    start_date  TEXT NOT NULL,
    end_date    TEXT NOT NULL,
    initial_cap REAL NOT NULL DEFAULT 100000,
    current_day INTEGER NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'IN_PROGRESS',  -- IN_PROGRESS, COMPLETED
    created_at  TEXT NOT NULL,
    completed_at TEXT
);

-- Practice trade records
CREATE TABLE practice_trades (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES practice_sessions(id),
    trade_date  TEXT NOT NULL,
    action      TEXT NOT NULL,      -- "buy" or "sell"
    price       REAL NOT NULL,
    shares      INTEGER NOT NULL,
    amount      REAL NOT NULL,
    commission  REAL NOT NULL DEFAULT 0,
    stamp_tax   REAL NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL
);

-- Backtest results
CREATE TABLE backtest_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_code         TEXT NOT NULL,
    strategy_name   TEXT NOT NULL,
    params          TEXT NOT NULL,      -- JSON
    start_date      TEXT NOT NULL,
    end_date        TEXT NOT NULL,
    initial_cap     REAL NOT NULL,
    total_return    REAL,
    annual_return   REAL,
    max_drawdown    REAL,
    win_rate        REAL,
    trade_count     INTEGER,
    equity_curve    TEXT,               -- JSON array of {date, value}
    trades          TEXT,               -- JSON array of trade records
    created_at      TEXT NOT NULL
);
```

### Schema Rationale

- **`stocks` table:** Pre-loaded once at setup. Supports fuzzy search by code and name. This avoids calling tushare's stock_basic API on every search.
- **`daily_quotes` table:** The fact table. Composite unique constraint on (ts_code, trade_date) enables upsert for incremental updates. The covering index makes range queries fast.
- **`indicators` table:** `params` as JSON string allows flexible parameter combinations (e.g., MACD with 12,26,9 vs 5,35,5). The `values` column is also JSON because different indicators return different value structures. The index covers the typical query pattern: "get MACD(12,26,9) for stock 600519.SH ordered by date".
- **`practice_sessions` + `practice_trades`:** Separated because a session has one-to-many trades. Session tracks the current day pointer; trades are immutable event records.
- **`backtest_results`:** Stores complete results including equity curve and trade list as JSON. This allows re-displaying past backtest results without re-running.

## Three Modules: Architectural Relationships

```
                    ┌──────────────────────────────┐
                    │      Shared Data Layer        │
                    │  stocks | daily_quotes |      │
                    │  indicators                   │
                    └──────────┬───────────────────┘
                               │
              ┌────────────────┼────────────────┐
              |                |                |
              v                v                v
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │  Strategy    │  │  Practice    │  │  Backtest    │
   │  Analysis    │  │  Module      │  │  Module      │
   │              │  │              │  │              │
   │  READ-ONLY   │  │  READ +      │  │  READ +      │
   │  from shared │  │  WRITE own   │  │  COMPUTE     │
   │  data        │  │  session     │  │  then write  │
   │              │  │  data        │  │  results     │
   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
          |                 |                 |
          v                 v                 v
   ┌──────────────────────────────────────────────────┐
   │              Shared Chart Component               │
   │         (KlineChart.vue + IndicatorPanel.vue)     │
   └──────────────────────────────────────────────────┘
```

**Key insight:** All three modules share the same chart rendering components but differ in how they use shared data:

1. **Strategy Analysis** reads stocks + indicators + patterns. It is a pure visualization layer. No session state.
2. **Trading Practice** reads stock data day-by-day (frontend controls pacing). It writes practice_sessions + practice_trades. It reuses the chart component but with a restricted view (only data up to current_day).
3. **Auto Backtesting** reads stock data in bulk, runs computation, then writes results. It reuses the chart component for displaying equity curves and buy/sell markers on the K-line chart.

**Build order implication:** The chart component and data layer must be built first (Phase 1: Strategy Analysis). Practice and Backtest modules layer on top.

## Scaling Considerations

This is a single-user local application. Scaling is not a concern in the traditional sense. However:

| Concern | Impact | Approach |
|---------|--------|----------|
| SQLite database size | After loading 5000+ stocks with 10 years of daily data, the DB could reach 500MB-1GB. | Acceptable for local use. WAL mode for concurrent read/write. |
| tushare API rate limits | Free tier: ~200 calls/minute. Loading all A-shares takes hours if done at once. | On-demand fetch + persistent cache. Pre-load a watchlist of popular stocks. |
| ECharts rendering performance | 10 years of daily bars = ~2500 data points. With indicators and overlays, ~10,000 points. | ECharts handles this easily. Use `dataZoom` to limit visible range. For extreme cases, ECharts large-scale mode. |
| Indicator computation time | Computing MACD/RSI/KDJ for one stock = milliseconds. Computing for all stocks = minutes. | Compute on-demand per stock and cache. Batch computation can be a background task. |

## Anti-Patterns

### Anti-Pattern 1: Computing Indicators on the Frontend

**What people do:** Send raw OHLCV data to the browser and compute MACD/RSI/KDJ in JavaScript.
**Why it's wrong:** Duplicates computation logic (Python backend needs indicators for backtesting anyway). JavaScript indicator libraries are less mature than Python's `pandas-ta`. Indicators computed on the frontend cannot be cached or shared with the backtest engine.
**Do this instead:** Compute all indicators on the backend with `pandas-ta`. Store results in SQLite. Send pre-computed arrays to the frontend for rendering.

### Anti-Pattern 2: One Giant ECharts Option Object in the Template

**What people do:** Write the entire ECharts option (candlestick + volume + 3 indicators + annotations) as a single inline object inside a Vue component's `data()` or `ref()`.
**Why it's wrong:** The option object for a full trading chart is 200+ lines of nested configuration. Inline it becomes unmaintainable. Adding/removing indicators requires mutating a deeply nested object.
**Do this instead:** Extract option building into a composable (`useChartOption.js`) that takes reactive inputs (quotes, active indicators, patterns) and returns a computed option object. Each indicator contributes its own series + grid config through a registry pattern.

### Anti-Pattern 3: Fetching All Stock Data Up Front

**What people do:** On app startup, fetch all A-share OHLCV data from tushare.
**Why it's wrong:** 5000+ stocks x 10 years = millions of rows. tushare API rate limits make this take hours. Wastes bandwidth for stocks the user never looks at.
**Do this instead:** Fetch on-demand when a user selects a stock. Cache to SQLite permanently. The only pre-load is the stock list (codes + names) for search, which is a single API call.

### Anti-Pattern 4: Putting Business Logic in Vue Components

**What people do:** Implement trade simulation logic (commission calculation, position tracking) in Vue component methods or Pinia actions.
**Why it's wrong:** The same trade logic is needed for backtesting. Duplicating in frontend and backend creates drift. Commission rules and tax rules must match exactly.
**Do this instead:** All trade simulation, commission calculation, and position tracking live in the backend service layer. The frontend is a thin view that sends action intents (buy/sell) and receives updated state.

### Anti-Pattern 5: Using ECharts Directly Without vue-echarts

**What people do:** Manually call `echarts.init()`, manage DOM refs, handle resize, and call `dispose()` in Vue lifecycle hooks.
**Why it's wrong:** Boilerplate-heavy, error-prone (forgetting dispose causes memory leaks), and fights Vue's reactivity system.
**Do this instead:** Use `vue-echarts` (`<v-chart>` component). It handles init/dispose/resize automatically and integrates with Vue's reactivity. Pass the option as a prop, updates happen via `setOption()` automatically.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| tushare Pro API | HTTP calls via `tushare` Python SDK, wrapped in `TushareClient` class with retry + rate limiting | Token-based auth. Free tier has 200 calls/min limit. Data is daily OHLCV only. |
| vue-echarts | npm package, registered as Vue component | Provides `<v-chart>` component. Must register ECharts modules (CandlestickChart, BarChart, LineChart, DataZoomComponent, etc.) |
| pandas-ta | pip package, imported in `engines/indicators.py` | Computes indicators on Pandas DataFrames. Returns DataFrames that are converted to JSON for API response. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Frontend <-> Backend | REST API (JSON over HTTP) | No WebSockets needed (no real-time data). CORS must allow localhost:5173 -> localhost:8000. |
| Vue Router -> Views | Vue Router navigation | 3 routes: `/strategy`, `/practice`, `/backtest`. Tab-based navigation. |
| Pinia Stores -> API Client | Store actions call API functions | Stores hold client-side state. API calls happen in store actions. |
| FastAPI Routers -> Services | Direct function calls (dependency injection) | Services are injected via FastAPI's `Depends()`. |
| Services -> Repositories | Direct function calls | Repository functions accept a SQLAlchemy session. |
| Services -> Engines | Direct function calls | Engines are stateless computation functions. |
| Services -> TushareClient | Direct method calls | Client handles HTTP, retry, rate limiting internally. |

## Build Order (Dependencies Between Components)

The architectural dependencies imply a strict build order:

```
Phase 1: Foundation + Strategy Analysis
  1.1 SQLite schema (stocks, daily_quotes)
  1.2 TushareClient (fetch + cache stock list + daily quotes)
  1.3 Backend: stock router + service + repo
  1.4 Frontend: StockSearch + API client
  1.5 Frontend: KlineChart component (candlestick + volume, no indicators yet)
  1.6 ECharts TradingView dark theme
  -- MILESTONE: User can search a stock and see K-line + volume chart --

Phase 2: Indicators + Annotations
  2.1 Backend: pandas-ta integration (indicator engine)
  2.2 SQLite: indicators table
  2.3 Backend: indicator router + service
  2.4 Frontend: IndicatorPanel component (MACD/RSI/KDJ/BOLL sub-chart)
  2.5 Backend: K-line pattern recognition engine
  2.6 Backend: support/resistance detection
  2.7 Frontend: ChartOverlay (pattern marks, S/R lines)
  -- MILESTONE: Full strategy analysis with indicators and annotations --

Phase 3: Trading Practice Module
  3.1 SQLite: practice_sessions + practice_trades tables
  3.2 Backend: practice router + service (session mgmt, trade execution)
  3.3 Frontend: PracticeView (day-by-day reveal, restricted chart)
  3.4 Frontend: TradePanel (buy/sell UI)
  3.5 Frontend: PracticeResultView (final P&L summary)
  -- MILESTONE: Complete trading practice with commission simulation --

Phase 4: Auto Backtesting Module
  4.1 Backend: backtest engine (strategy templates + execution loop)
  4.2 SQLite: backtest_results table
  4.3 Backend: backtest router + service
  4.4 Frontend: BacktestView (strategy selector + param editor)
  4.5 Frontend: BacktestReport (metrics table + equity curve + trade markers on K-line)
  -- MILESTONE: Full backtest workflow with results display --
```

## Sources

- [Apache ECharts Official Examples](https://echarts.apache.org/examples/en/index.html) -- Candlestick chart examples including multi-indicator layouts
- [Apache ECharts 6 Release Notes](https://echarts.apache.org/handbook/en/basics/release-note/v6-feature/) -- Native stock chart demos with MACD, volume, depth
- [vue-echarts (ecomfe)](https://github.com/ecomfe/vue-echarts) -- Official Vue.js wrapper for ECharts
- [FastAPI Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) -- Official docs on multi-file structure with APIRouter
- [FastAPI Architecture Best Practices (Medium)](https://medium.com/@hadiyolworld007/the-fastapi-repo-pattern-and-folder-structure-you-actually-need-c5aa06c93436) -- Repository pattern in FastAPI
- [Quant StackExchange: Stock Market Data Schema](https://quant.stackexchange.com/questions/61699/how-to-structure-a-stock-market-data-database) -- OHLCV schema design discussion
- [Vue3 + ECharts Customizable Financial Charts (Juejin)](https://juejin.cn/post/7353822048520880164) -- Vue 3 financial chart implementation
- [ECharts K-line with Indicator Linkage (51CTO)](https://blog.51cto.com/u_15668841/10367750) -- Multi-grid axisPointer link pattern
- [Wails v2 + Vue 3 + ECharts Stock Analysis Tool (Juejin)](https://juejin.cn/post/7621772907050025002) -- Production-grade reference implementation

---
*Architecture research for: Volume-Price Trading Learning Platform*
*Researched: 2026-04-30*
