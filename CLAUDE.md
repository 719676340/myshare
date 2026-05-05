<!-- GSD:project-start source:PROJECT.md -->
## Project

**量价交易学习平台**

一个本地运行的 A 股量价分析学习工具，通过 tushare 获取日 K 数据，结合量价分析理论，在 K 线图上直观展示分析结果。支持策略分析、交易练习、自动回测三大模块，帮助用户通过看、练、测的方式学习量价交易。

**Core Value:** 在真实 A 股数据上可视化量价分析理论 — 让用户通过看图、模拟练习、策略回测来学习交易。

### Constraints

- **Tech Stack**: Vue + JS + ECharts（前端）、Python FastAPI（后端）、SQLite（数据库）、tushare（数据源）
- **Data Source**: 仅日 K 线数据（OHLCV），仅 A 股
- **Deployment**: 本地开发运行，前后端 localhost 访问
- **Cost**: tushare 有接口调用限制，需注意数据缓存
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
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
### Data & Computation
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| pandas | 2.3.x | Data manipulation | Use 2.3.x (not 3.0.x which is very new and may have breaking changes). DataFrames for OHLCV data, indicator calculations, tushare output parsing. |
| numpy | 2.4.x | Numerical computation | Dependency of pandas. Used directly for indicator math (moving averages, standard deviations). |
| tushare | 1.4.29 | A-share market data | The only choice for the project (pre-decided). Pro API with token auth. Provides daily K-line data (OHLCV), stock list, trade calendar. |
| ta (Technical Analysis Library) | 0.11.x | Technical indicators calculation | Pure Python, pandas-based, ~40 indicators (MACD, RSI, Bollinger Bands, KDJ, etc.). Easy `pip install ta`. No C dependencies unlike TA-Lib. Sufficient for all indicators in the requirements. |
### Database
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| SQLite | 3.x (built-in) | Local database | Pre-decided. Zero-config, file-based, perfect for single-user local app. Stores stock daily data, computed indicators, practice trades, backtest results. |
### Dev Dependencies
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| @vitejs/plugin-vue | 5.x | Vite Vue plugin | Required for Vue SFC support in Vite. |
| sass | 1.x | CSS preprocessor | For TradingView dark theme styling. Element Plus supports SCSS customization. |
| eslint | 9.x | Linting | Standard JS linting. |
| black | 24.x+ | Python formatting | Opinionated formatter for backend code. |
| pytest | 8.x | Python testing | Backend API and indicator calculation tests. |
| httpx | 0.28.x | Async HTTP client for tests | Needed for testing FastAPI async endpoints. |
## Key Technical Decisions
### Decision 1: ECharts 6 (not KLineChart or Lightweight Charts)
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
### Decision 2: SQLAlchemy 2.0 (not SQLModel)
### Decision 3: `ta` library (not pandas-ta or TA-Lib)
| Library | Indicators | Install | Status |
|---------|-----------|---------|--------|
| **ta** | ~40 | `pip install ta` (pure Python) | Active, maintained |
| **pandas-ta** | 130+ | `pip install pandas-ta` | Original repo went offline; forked to `pandas-ta-classic` |
| **TA-Lib** | 200+ | Requires C library compilation | Stable but hard to install |
| **talipp** | 30+ | Pure Python | Active, incremental updates |
### Decision 4: pandas 2.3.x (not 3.0.x)
### Decision 5: Element Plus for UI (not Vuetify, Naive UI, or Ant Design Vue)
| Library | Stars | Dark Theme | Chinese Stock UI Fit |
|---------|-------|------------|---------------------|
| **Element Plus** | 27K+ | Supported via CSS vars | Industry standard for Chinese dev teams |
| Vuetify | 19K+ | Built-in | Material Design doesn't fit trading UIs |
| Naive UI | 16K+ | Built-in | Good but smaller ecosystem |
| Ant Design Vue | 20K+ | Supported | Good but heavier |
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
## Installation
### Frontend
### Backend
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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
