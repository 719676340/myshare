# Technology Stack

**Project:** 量价交易学习平台 (Volume-Price Trading Learning Platform)
**Researched:** 2026-04-30

## Recommended Stack

The stack is constrained by the project requirements: Vue + JS + ECharts frontend, Python FastAPI backend, SQLite database, tushare data source. Below are specific library choices with versions and rationale.

### Core Framework (Frontend)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Vue | 3.5.x | UI framework | Stable 3.5 line (3.5.26 latest). Vue 3.6 is still in beta. Use Options API or Composition API with JS (not TypeScript per project constraints). |
| Vite | 6.x | Build tool & dev server | Officially recommended by Vue. Blazing fast HMR. Vite 8 exists but is very new; Vite 6 is battle-tested and stable. |
| vue-echarts | 8.0.x | Vue wrapper for ECharts | Supports ECharts 6 + Vue 3 only. Clean reactive bindings. Tree-shakeable imports. |
| ECharts | 6.0.0 | Charting engine | Latest stable. Built-in `candlestick` series type. `dataZoom` for scrolling. `grid` system for K-line + volume + MACD sub-charts. Dark theme support out of the box. Progressive rendering for large datasets. |
| Vue Router | 4.6.x | Page routing | Stable for Vue 3. Three modules (strategy analysis, trading practice, auto backtest) need top-level routes. |
| Pinia | 3.0.x | State management | Official Vue 3 store. Lightweight, devtools integration. Shares stock data, chart state, user settings across components. |
| Element Plus | 2.11.x | UI component library | Most mature Vue 3 component library. Provides inputs, selects, dialogs, layouts, tooltips. Dark theme support. Essential for stock search, parameter controls, backtest result tables. |
| Axios | 1.15.x | HTTP client | Standard HTTP client for calling FastAPI backend. Version 1.15.x is the safe version after the March 2026 supply chain incident (avoid 1.4.1 and 0.30.4). |

**Confidence: HIGH** -- All versions verified via npm/PyPI as of April 2026.

### Core Framework (Backend)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | 3.12.x | Runtime | Stable, well-supported by all libraries. Not 3.13+ to avoid edge cases with scientific packages. |
| FastAPI | 0.136.x | REST API framework | Async support, automatic OpenAPI docs, Pydantic validation. Latest stable as of April 2026. |
| Uvicorn | 0.46.x | ASGI server | Standard ASGI server for FastAPI. Fast, production-ready. |
| Pydantic | 2.x | Data validation | Bundled with FastAPI. Used for request/response schemas. v2 has Rust-core performance. |
| SQLAlchemy | 2.0.x | ORM + database toolkit | Mature, battle-tested. Version 2.1 is still in beta. Use 2.0.49 (latest stable). Async-capable via aiosqlite for SQLite. |
| aiosqlite | 0.20.x | Async SQLite driver | Required for async SQLAlchemy with SQLite. Wraps sqlite3 in asyncio. |
| Alembic | 1.6.x | Database migrations | Standard migration tool for SQLAlchemy. Handles schema evolution as indicator columns are added. |

**Confidence: HIGH** -- All versions verified via PyPI as of April 2026.

### Data & Computation

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| pandas | 2.3.x | Data manipulation | Use 2.3.x (not 3.0.x which is very new and may have breaking changes). DataFrames for OHLCV data, indicator calculations, tushare output parsing. |
| numpy | 2.4.x | Numerical computation | Dependency of pandas. Used directly for indicator math (moving averages, standard deviations). |
| tushare | 1.4.29 | A-share market data | The only choice for the project (pre-decided). Pro API with token auth. Provides daily K-line data (OHLCV), stock list, trade calendar. |
| ta (Technical Analysis Library) | 0.11.x | Technical indicators calculation | Pure Python, pandas-based, ~40 indicators (MACD, RSI, Bollinger Bands, KDJ, etc.). Easy `pip install ta`. No C dependencies unlike TA-Lib. Sufficient for all indicators in the requirements. |

**Confidence: HIGH** for pandas/numpy/tushare. **MEDIUM** for `ta` -- verified on PyPI but pandas-ta is the more popular alternative (see rationale below).

### Database

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| SQLite | 3.x (built-in) | Local database | Pre-decided. Zero-config, file-based, perfect for single-user local app. Stores stock daily data, computed indicators, practice trades, backtest results. |

**Confidence: HIGH** -- SQLite is built into Python, no version decision needed.

### Dev Dependencies

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| @vitejs/plugin-vue | 5.x | Vite Vue plugin | Required for Vue SFC support in Vite. |
| sass | 1.x | CSS preprocessor | For TradingView dark theme styling. Element Plus supports SCSS customization. |
| eslint | 9.x | Linting | Standard JS linting. |
| black | 24.x+ | Python formatting | Opinionated formatter for backend code. |
| pytest | 8.x | Python testing | Backend API and indicator calculation tests. |
| httpx | 0.28.x | Async HTTP client for tests | Needed for testing FastAPI async endpoints. |

**Confidence: HIGH** -- Standard dev tooling, versions are stable.

## Key Technical Decisions

### Decision 1: ECharts 6 (not KLineChart or Lightweight Charts)

**Why ECharts 6 over alternatives:**

| Criterion | ECharts 6 | KLineChart | TradingView Lightweight Charts |
|-----------|-----------|------------|-------------------------------|
| Candlestick support | Native `candlestick` series | Native, purpose-built | Native, purpose-built |
| Technical indicators | Manual JS calculation + line/bar series | Built-in indicator system | Built-in indicator system |
| Volume sub-chart | Separate `grid` with `bar` series | Built-in | Built-in |
| DataZoom (scroll/zoom) | Native `dataZoom` component | Built-in | Built-in |
| Dark theme | Built-in, improved in v6 | Custom CSS | Built-in |
| Vue 3 integration | Official `vue-echarts` wrapper | Community, less maintained | Community wrappers |
| Bundle size | ~800KB (tree-shakeable) | ~200KB | ~200KB |
| Multi-grid sync | `axisPointer.link` + shared `dataZoom` | Automatic | Automatic |
| Ecosystem | Massive, Apache Foundation | Small team | TradingView |

**Rationale:** The project requires K-line + volume + MACD/RSI/BOLL sub-charts with linked zoom and crosshair. ECharts handles this with its `grid` + `dataZoom` + `axisPointer.link` system. While KLineChart and Lightweight Charts have built-in indicators, they lack the ecosystem maturity and Vue integration that ECharts provides. Bundle size is irrelevant for a local-only app. The project already decided on ECharts; this confirms it and specifies version 6.

### Decision 2: SQLAlchemy 2.0 (not SQLModel)

**Why SQLAlchemy over SQLModel:**

SQLModel (by the FastAPI creator) merges Pydantic and SQLAlchemy models, reducing boilerplate. However:

1. **SQLModel async support has rough edges** (per Daniel Feldroy's 2025 TIL post). For a project using async FastAPI + SQLite, this matters.
2. **SQLAlchemy 2.0 is more mature** -- 2.0.49 is battle-tested. SQLModel is still evolving its async story.
3. **Schema complexity** -- This project has stock data, indicator values, trade records, and backtest results. SQLAlchemy's explicit model definitions are clearer for complex relationships.
4. **Alembic integration** -- SQLAlchemy + Alembic is the standard migration path. SQLModel works with Alembic but adds indirection.

Use SQLAlchemy 2.0 with explicit models and Pydantic schemas separately. The slight duplication is worth the stability.

### Decision 3: `ta` library (not pandas-ta or TA-Lib)

**Why `ta` over alternatives:**

| Library | Indicators | Install | Status |
|---------|-----------|---------|--------|
| **ta** | ~40 | `pip install ta` (pure Python) | Active, maintained |
| **pandas-ta** | 130+ | `pip install pandas-ta` | Original repo went offline; forked to `pandas-ta-classic` |
| **TA-Lib** | 200+ | Requires C library compilation | Stable but hard to install |
| **talipp** | 30+ | Pure Python | Active, incremental updates |

**Rationale:** The project needs MACD, RSI, KDJ, Bollinger Bands, and moving averages -- all covered by `ta`. It installs with a simple `pip install ta` with no C dependencies. pandas-ta's original repo is gone (the `twopirllc` GitHub went offline), and while `pandas-ta-classic` exists, it adds uncertainty. TA-Lib's C compilation requirement is unnecessary friction for a learning project. `ta` is the pragmatic choice.

### Decision 4: pandas 2.3.x (not 3.0.x)

pandas 3.0.0 was released January 2026. It introduces breaking changes (PyArrow backend by default, removed deprecated APIs). For a learning platform where stability matters more than cutting-edge features, stay on 2.3.x. Migrate to 3.x later when the ecosystem has caught up.

### Decision 5: Element Plus for UI (not Vuetify, Naive UI, or Ant Design Vue)

| Library | Stars | Dark Theme | Chinese Stock UI Fit |
|---------|-------|------------|---------------------|
| **Element Plus** | 27K+ | Supported via CSS vars | Industry standard for Chinese dev teams |
| Vuetify | 19K+ | Built-in | Material Design doesn't fit trading UIs |
| Naive UI | 16K+ | Built-in | Good but smaller ecosystem |
| Ant Design Vue | 20K+ | Supported | Good but heavier |

**Rationale:** Element Plus is the de facto standard for Chinese developer teams. Its component set (tables, inputs, selects, dialogs) maps directly to what this project needs: stock search dropdowns, parameter inputs for indicators, backtest result tables, and settings dialogs. Dark theme support via CSS variables aligns with the TradingView-style requirement.

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Charting | ECharts 6 | KLineChart | Less Vue integration, smaller ecosystem, project decided on ECharts |
| Charting | ECharts 6 | TradingView Lightweight Charts | No official Vue wrapper, trading terminal features overkill |
| ORM | SQLAlchemy 2.0 | SQLModel | Async rough edges, less mature, more indirection |
| ORM | SQLAlchemy 2.0 | Raw SQL | Too much boilerplate, no migration support, harder to maintain |
| Indicators | ta | pandas-ta | Original repo gone, fork uncertainty |
| Indicators | ta | TA-Lib | C compilation required, unnecessary friction |
| pandas | 2.3.x | 3.0.x | Too new, breaking changes, ecosystem still catching up |
| UI | Element Plus | Vuetify | Material Design doesn't fit financial UIs |
| UI | Element Plus | Naive UI | Smaller ecosystem, fewer examples in Chinese |
| State | Pinia 3 | Vuex | Vuex is deprecated for Vue 3 |
| HTTP | Axios 1.15.x | fetch API | Axios has interceptors, error handling, and timeout support |
| DB Migrations | Alembic | Manual SQL | Schema will evolve as indicators are added |
| Python Runtime | 3.12 | 3.13+ | Scientific packages may lag behind newest Python |

## Project Structure (Recommended)

```
project/
  frontend/
    src/
      assets/           # SCSS theme, images
      components/
        charts/         # KLineChart.vue, VolumeChart.vue, MACDChart.vue
        common/         # StockSearch.vue, IndicatorPanel.vue
      views/
        StrategyView.vue      # Module 1: Strategy Analysis
        PracticeView.vue      # Module 2: Trading Practice
        BacktestView.vue      # Module 3: Auto Backtest
      stores/           # Pinia stores (stock data, chart state, settings)
      router/           # Vue Router config
      utils/            # ECharts helpers, data transformers
      api/              # Axios service layer calling FastAPI
    package.json
    vite.config.js
  backend/
    app/
      main.py           # FastAPI app entry
      api/
        routes/
          stocks.py      # Stock list, search, daily data
          indicators.py  # Technical indicator calculations
          practice.py    # Trading practice endpoints
          backtest.py    # Backtesting engine endpoints
      models/           # SQLAlchemy models
      schemas/          # Pydantic request/response schemas
      services/         # Business logic (indicator calc, backtest engine)
      core/
        database.py     # SQLAlchemy engine, session factory
        config.py       # Settings (tushare token, DB path)
      data/
        fetcher.py      # tushare data fetching with caching
    alembic/
      versions/         # Migration scripts
    requirements.txt
    alembic.ini
  data/
    stocks.db           # SQLite database file
```

## Installation

### Frontend

```bash
cd frontend
npm create vite@latest . -- --template vue
npm install vue-echarts@^8 echarts@^6 vue-router@^4 pinia@^3 element-plus@^2 axios@^1.15
npm install -D @vitejs/plugin-vue sass
```

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install fastapi==0.136.* uvicorn[standard]==0.46.* \
  sqlalchemy==2.0.* aiosqlite==0.20.* alembic==1.6.* \
  pandas==2.3.* numpy==2.4.* tushare==1.4.29 ta==0.11.* \
  pydantic==2.* httpx==0.28.*
pip install -D pytest black
```

## Sources

- [Vue.js Releases](https://vuejs.org/about/releases) -- Vue version info
- [vue-echarts on npm](https://www.npmjs.com/package/vue-echarts) -- Version 8.0.1, ECharts 6 compatible
- [ECharts 6 Features](https://echarts.apache.org/handbook/en/basics/release-note/v6-feature/) -- v6.0.0 release notes
- [ECharts npm](https://www.npmjs.com/package/echarts) -- Version 6.0.0 confirmed
- [ECharts 6 Upgrade Guide](https://echarts.apache.org/handbook/en/basics/release-note/v6-upgrade-guide/) -- Migration from v5
- [Vue Router npm](https://www.npmjs.com/package/vue-router) -- Version 4.6.4
- [Pinia on npm](https://www.npmjs.com/package/pinia) -- Version 3.0.4
- [Element Plus](https://element-plus.org/) -- Version 2.11.7
- [Axios on npm](https://www.npmjs.com/package/axios) -- Version 1.15.2 (safe version post supply chain incident)
- [FastAPI on PyPI](https://pypi.org/project/fastapi/) -- Version 0.136.1
- [Uvicorn Release Notes](https://uvicorn.dev/release-notes/) -- Version 0.46.0
- [SQLAlchemy on PyPI](https://pypi.org/project/SQLAlchemy/) -- Version 2.0.49 (stable), 2.1 in beta
- [pandas on PyPI](https://pypi.org/project/pandas/) -- Version 3.0.2 (using 2.3.x per decision above)
- [NumPy News](https://numpy.org/news/) -- Version 2.4.x
- [tushare on PyPI](https://pypi.org/project/tushare/) -- Version 1.4.29
- [ta on PyPI](https://pypi.org/project/ta/) -- Technical analysis library
- [pandas-ta situation](https://www.reddit.com/r/algotrading/comments/1ldm0kb/what_happened_to_pandasta_python_package/) -- Original repo offline
- [Alembic on PyPI](https://pypi.org/project/alembic/) -- Version 1.6.5
- [Vite 8.0 Blog](https://vite.dev/blog/announcing-vite8) -- Vite 8 exists but Vite 6 recommended for stability
- [Vue 3 Ecosystem 2026 Guide (Juejin)](https://juejin.cn/post/7629228640290816019) -- Confirms Vue 3.5 + Vite 6 stack
- [SQLModel vs SQLAlchemy benchmarks](https://medium.com/@sparknp1/10-sqlmodel-vs-sqlalchemy-choices-with-real-benchmarks-dde68459d88f) -- SQLModel async rough edges
- [Axios supply chain incident](https://www.microsoft.com/en-us/security/blog/2026/04/01/mitigating-the-axios-npm-supply-chain-compromise/) -- CVE context for version selection
