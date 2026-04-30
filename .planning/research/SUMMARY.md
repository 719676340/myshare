# Project Research Summary

**Project:** 量价交易学习平台 (Volume-Price Trading Learning Platform)
**Domain:** A-share market technical analysis education tool (local desktop web app)
**Researched:** 2026-04-30
**Confidence:** HIGH

## Executive Summary

This is a local-only, single-user educational platform for learning A-share volume-price trading analysis. It consists of three modules (Strategy Analysis, Trading Practice, Auto Backtesting) that share a common chart component and data layer. The product category is well-understood -- trading charting tools like TradingView, TongDaXin, and QuantConnect establish clear patterns for K-line rendering, indicator calculation, and backtesting engines. The key differentiator for this platform is its educational focus on volume-price theory (Wyckoff-derived), with auto-detected volume-price patterns and market cycle annotations that free tools do not provide.

The recommended approach is a four-phase build starting with the K-line chart and data pipeline, then indicators and pattern recognition, then the trading practice simulation, and finally the backtesting engine. This order is dictated by strict technical dependencies: the chart component is reused by all three modules, indicators are needed by both strategy analysis and backtesting, and the A-stock rules engine (T+1, price limits, fees) developed for trading practice is reused by the backtester. The stack is fully decided: Vue 3 + ECharts 6 frontend, FastAPI + SQLAlchemy 2.0 backend, SQLite storage, tushare data source, `ta` library for indicator computation.

The primary risks are A-share-specific data pitfalls that silently produce wrong results: pandas EWM `adjust` parameter poisoning all indicator calculations, suspension-day gaps creating misaligned time series, adjusted vs. unadjusted price confusion corrupting both charts and backtests, and look-ahead bias in the backtesting engine. All of these are preventable with explicit decisions made during Phase 1 architecture, and the research documents concrete prevention strategies for each. A secondary risk is ECharts memory management in Vue, which requires careful use of `shallowRef`, `dispose()`, and `notMerge` options to prevent progressive slowdown.

## Key Findings

### Recommended Stack

The stack is pre-decided by project requirements (Vue + JS + ECharts, FastAPI, SQLite, tushare). Research pinned specific versions and resolved library choices within those constraints. The key decisions: ECharts 6 (not KLineChart or Lightweight Charts) for its multi-grid sync system and Vue integration; SQLAlchemy 2.0 (not SQLModel) for mature async support; `ta` library (not pandas-ta or TA-Lib) for pure-Python indicator calculation with no C dependencies; pandas 2.3.x (not 3.0.x) for stability; Element Plus for UI components; Pinia 3 for state management.

**Core technologies:**
- Vue 3.5 + Vite 6: UI framework and build tool -- stable versions, avoid beta releases
- ECharts 6 + vue-echarts 8: Charting engine -- native candlestick series, multi-grid sync, dark theme
- FastAPI 0.136 + SQLAlchemy 2.0: Backend framework and ORM -- async-capable, mature migration path
- `ta` 0.11: Technical indicator library -- pure Python, covers MACD/RSI/KDJ/BOLL without C dependencies
- pandas 2.3 + numpy 2.4: Data manipulation -- pinned to stable versions, avoiding 3.0 breaking changes
- tushare 1.4.29: A-share market data -- the designated data source, daily OHLCV
- Element Plus 2.11: UI component library -- de facto standard for Chinese dev teams, dark theme support
- SQLite + aiosqlite + Alembic: Local storage -- zero-config, WAL mode, schema migrations

### Expected Features

**Must have (table stakes):**
- K-line candlestick chart with volume bars, crosshair, zoom/pan, dark theme -- every trading platform has this
- Red-up/green-down A-share color convention -- getting this wrong signals the tool is not for A-share
- Stock search by code/name with fuzzy matching -- immediate usability requirement
- Technical indicators: MA, MACD, RSI, KDJ, Bollinger Bands -- explicitly required, universally expected
- Volume-price confirmation/anomaly markers and basic K-line pattern recognition -- core educational value
- A-stock trading rules: T+1 enforcement, price limit checks, commission/stamp tax simulation

**Should have (differentiators):**
- VAP (Volume at Price) distribution chart -- identifies support/resistance by volume concentration
- Market cycle phase annotation (Wyckoff: accumulation -> markup -> distribution -> markdown) -- unique to this platform
- Support/resistance auto-detection and dynamic trend lines -- saves manual effort
- Day-by-day forward-only simulation for trading practice -- strong educational mechanic
- Comprehensive backtest metrics (Sharpe ratio, max drawdown, profit factor) with equity curve visualization

**Defer (v2+):**
- Multi-timeframe linked analysis -- high UI coordination complexity
- Custom indicator builder (arithmetic expression parser) -- nice-to-have for power users
- Trade history with reasoning notes -- useful but not critical for launch
- Manual drawing tools -- project scope explicitly defers this

### Architecture Approach

The architecture follows a standard three-tier pattern: Vue 3 SPA frontend, FastAPI REST backend, SQLite local database. All three modules share a common data layer (stocks, daily_quotes, indicators tables) and a shared chart component (KlineChart.vue + IndicatorPanel.vue). The backend uses a Router -> Service -> Repository layering with a separate `engines/` directory for computation-heavy modules (indicators, patterns, backtesting). Indicators are computed on the backend with `ta`/pandas and cached in SQLite -- the frontend never calculates indicators, avoiding logic duplication. The ECharts multi-grid linked layout (candlestick + volume + indicator sub-charts sharing one `dataZoom`) is the foundational chart pattern. A `useChartOption.js` composable builds the option object programmatically to avoid unmaintainable inline configuration.

**Major components:**
1. **KlineChart + IndicatorPanel** -- ECharts multi-grid component with linked zoom, crosshair, and dynamic indicator series; shared by all three modules
2. **Data Pipeline (TushareClient + StockRepo)** -- On-demand fetch from tushare with SQLite cache, retry logic, suspension gap handling, and adjusted/unadjusted price management
3. **Indicator Engine** -- Backend computation using `ta` library with EWM `adjust=False` enforcement, warm-up period handling, and NaN protection for edge cases
4. **Practice Service** -- State machine (CREATED -> IN_PROGRESS -> COMPLETED) with forward-only day advancement, T+1 enforcement, price limit checks, and commission calculation
5. **Backtest Engine** -- Pure function `(strategy_config, stock_data) -> backtest_result` with rolling indicator calculation to prevent look-ahead bias

### Critical Pitfalls

1. **pandas EWM `adjust` parameter (Critical)** -- Default `adjust=True` produces EMA values that diverge from every financial platform. Always use `adjust=False`. This poisons MACD, RSI, KDJ, BOLL -- every EMA-dependent indicator. Must be enforced via a shared utility function from Phase 1.

2. **Suspension-day data gaps (Critical)** -- tushare omits rows for suspended trading days, silently creating misaligned time series. Reindex using the `trade_cal` trading calendar, fill with last close + zero volume + `suspended` flag. Must be handled in the data pipeline before any analysis.

3. **Adjusted vs. unadjusted price confusion (Critical)** -- Different use cases require different price types: unadjusted for trading simulation and limit calculations, forward-adjusted (qfq) for chart display, backward-adjusted (hfq) for return calculations. Store unadjusted + adjustment factor; compute adjusted on demand.

4. **Look-ahead bias in backtesting (Critical)** -- Calculating indicators on the full dataset then slicing for backtesting lets the strategy "see the future." Must use rolling/incremental calculation. Validate by checking if indicator values at time T change when future data is appended.

5. **ECharts memory leaks in Vue (Critical)** -- Failing to dispose ECharts instances on component unmount, using `ref` instead of `shallowRef`, or accumulating options via merge mode causes progressive memory growth. Use vue-echarts `<v-chart>` wrapper, `shallowRef`, `notMerge: true` when switching stocks.

6. **A-share limit-up/limit-down execution in backtests (Moderate)** -- Stocks at daily price limits cannot be traded. The backtesting engine must reject buy orders at limit-up and sell orders at limit-down. Failure means the backtest reports impossible trades.

7. **KDJ division by zero in flat markets (Moderate)** -- When High == Low over the lookback period, KDJ calculation divides by zero. Default RSV to 50 (neutral) when the range is zero.

## Implications for Roadmap

Based on combined research, the recommended phase structure:

### Phase 1: Data Foundation + K-Line Charting
**Rationale:** The K-line chart is the single shared component used by all three modules. The data pipeline (tushare -> SQLite -> API) must be solid before anything can be built on top of it. Getting the adjusted/unadjusted price strategy right here prevents cascading errors in every subsequent phase.
**Delivers:** Working K-line chart with volume bars, stock search, dark theme, on-demand data fetching with SQLite caching
**Addresses:** Table-stakes charting features, stock search, data pipeline
**Avoids:** Suspension gap pitfalls (P5), price adjustment confusion (P15), ECharts memory leaks (P7), color convention mismatch (P8), DOM-ready timing (P20), tushare rate limiting (P9), SQLite performance pitfalls (P10, P11)
**Stack:** Vue 3 + Vite + ECharts 6 + vue-echarts, FastAPI + SQLAlchemy + aiosqlite, tushare SDK, SQLite with WAL mode

### Phase 2: Technical Indicators + Volume-Price Analysis
**Rationale:** Indicators must be computed and cached before the backtesting module can reference them. Volume-price markers and K-line pattern recognition are the core educational value proposition of the platform. All indicator calculation pitfalls (EWM adjust, warm-up, division by zero) must be solved here.
**Delivers:** MACD/RSI/KDJ/BOLL indicator sub-charts, volume-price confirmation/anomaly markers, basic K-line pattern recognition (hammer, doji, shooting star), indicator caching in SQLite
**Addresses:** Technical indicator features, volume-price analysis markers, K-line pattern recognition
**Avoids:** EWM adjust pitfall (P1), warm-up period issues (P2), KDJ division by zero (P3), Bollinger std deviation (P17), RSI Wilder's smoothing (P22), crosshair desync (P16), ECharts dataZoom performance (P12), adjusted-data false signals (P21)
**Stack:** `ta` library + pandas for backend computation, ECharts multi-grid with linked axisPointer, IndicatorPanel Vue component

### Phase 3: Advanced Analysis (Differentiators)
**Rationale:** Support/resistance detection, dynamic trend lines, market cycle annotation, and VAP charts are high-complexity features that depend on having a solid charting + indicator infrastructure. These can be built independently and are not prerequisites for the practice or backtest modules.
**Delivers:** Auto-detected S/R levels, trend lines, Wyckoff market cycle annotations, VAP volume distribution chart
**Addresses:** Platform differentiators that set it apart from generic charting tools
**Stack:** Pattern detection algorithms in backend `engines/`, ChartOverlay Vue component for annotations

### Phase 4: Trading Practice Module
**Rationale:** Reuses the K-line chart component with a restricted data view (forward-only). The A-stock rules engine (T+1, price limits, commission/tax) developed here will be reused by the backtesting module in Phase 5. The practice session state machine is self-contained.
**Delivers:** Day-by-day forward simulation, buy/sell with position sizing, T+1 enforcement, price limit enforcement, fee simulation, performance statistics
**Addresses:** Trading practice features -- the experiential learning module
**Avoids:** T+1 rule violation (P13), limit-up/down impossible execution (P4), suspension-day trading (P5)
**Stack:** Pinia store for session state, PracticeService with state machine, TradePanel/PositionTable Vue components

### Phase 5: Strategy Backtesting Module
**Rationale:** Depends on completed indicator framework (strategies reference indicator values) and reuses the A-stock rules engine from Phase 4. The backtest engine is a pure function that requires careful look-ahead bias prevention.
**Delivers:** Preset strategy templates, parameter tuning with live recalculation, comprehensive metrics (Sharpe, max drawdown, profit factor, win rate), equity curve with buy/sell markers, benchmark comparison
**Addresses:** Auto-backtesting features -- the systematic learning module
**Avoids:** Look-ahead bias (P6), survivorship bias (P14), limit-up/down execution (P4), adjusted price confusion in returns (P15)
**Stack:** BacktestEngine as pure function, BacktestReport Vue component, equity curve ECharts visualization

### Phase Ordering Rationale

- **Phase 1 must come first** because every module depends on the K-line chart and data pipeline. The adjusted/unadjusted price decision made here affects all downstream computation.
- **Phase 2 must come before Phase 5** because the backtesting engine needs pre-computed indicator values. It should come before or parallel to Phase 3 because indicators are table-stakes while advanced analysis features are differentiators.
- **Phase 3 can be parallel to Phase 4** -- advanced analysis features and trading practice have no mutual dependencies. However, for a sequential roadmap, placing practice before advanced analysis delivers a complete user-facing module sooner.
- **Phase 5 must come last** because it depends on both the indicator framework (Phase 2) and the A-stock rules engine (Phase 4).
- **Pitfall concentration in Phase 1** is notable: 15 of 24 identified pitfalls have their primary mitigation in Phase 1. This is where the most careful engineering is needed.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (Advanced Analysis):** Market cycle phase annotation (Wyckoff) has no open-source reference implementation. VAP distribution chart rendering in ECharts requires custom horizontal histogram overlay. Support/resistance auto-detection algorithm design needs evaluation of pivot point vs. volume concentration approaches.
- **Phase 5 (Backtesting):** Strategy template design (what strategies to include, how to parameterize them) needs domain-specific research. Rolling indicator calculation for look-ahead bias prevention adds complexity to the engine design.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** Well-documented patterns for Vue + ECharts integration, FastAPI project structure, SQLite schema design, tushare data fetching. All pitfalls are identified with concrete prevention strategies.
- **Phase 2 (Indicators):** MACD/RSI/KDJ/BOLL calculation is industry-standard. `ta` library documentation is clear. ECharts multi-grid configuration is well-documented.
- **Phase 4 (Trading Practice):** A-stock trading rules (T+1, price limits, fees) are well-documented. State machine pattern is standard. Forward-only data reveal is a known simulation pattern.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified via npm/PyPI as of April 2026. Technology choices are within pre-decided constraints. Key decisions (ECharts 6, SQLAlchemy 2.0, `ta` library) have clear rationale. |
| Features | HIGH | Table-stakes features verified against TradingView, TongDaXin, TongHuaShun. A-stock rules (T+1, price limits, fees) confirmed through official Chinese sources. Backtesting metrics are industry-standard. Differentiator features have MEDIUM confidence due to algorithm design needs. |
| Architecture | HIGH | Standard three-tier pattern with well-documented FastAPI project structure. ECharts multi-grid linked layout is documented in official examples. Data flow is straightforward (tushare -> SQLite -> API -> ECharts). Anti-patterns clearly identified. |
| Pitfalls | HIGH | 24 pitfalls identified with concrete prevention strategies and detection methods. Critical pitfalls (EWM adjust, suspension gaps, price adjustment, look-ahead bias) are well-documented in financial engineering literature and community discussions. |

**Overall confidence:** HIGH

### Gaps to Address

- **VAP (Volume at Price) rendering in ECharts:** No direct ECharts series type for horizontal volume histograms overlaid on a price chart. Will require custom rendering using ECharts `custom` series type or bar chart with rotated axes. Needs a proof-of-concept during Phase 3 planning.
- **Market cycle phase annotation algorithm:** No open-source reference implementation for automatic Wyckoff phase detection. Algorithm must combine price action trends, volume patterns, and support/resistance levels. Needs algorithm design research during Phase 3 planning.
- **`ta` library KDJ implementation:** The `ta` library may not have a direct KDJ indicator (it has stochastic oscillator which is related but not identical). KDJ is a Chinese-market variant. May need custom implementation. Should verify during Phase 2 planning.
- **tushare credit system limits:** The exact credit/point budget for the project's tushare account is unknown. If credits are insufficient for the desired stock universe, the data fetching strategy may need adjustment. Should verify at project start.

## Sources

### Primary (HIGH confidence)
- Apache ECharts 6 documentation and examples -- chart rendering patterns, multi-grid layout, dataZoom, candlestick series
- Vue.js 3 official documentation -- composition API, lifecycle, reactivity
- FastAPI official documentation -- project structure, dependency injection, async support
- tushare Pro documentation -- API endpoints, rate limits, data format (ts_code, YYYYMMDD dates)
- pandas documentation -- EWM adjust parameter, rolling calculations, std ddof parameter

### Secondary (MEDIUM confidence)
- Vue 3 ecosystem 2026 guide (Juejin) -- confirms Vue 3.5 + Vite 6 stack recommendations
- FastAPI architecture best practices (Medium) -- repository pattern, multi-file structure
- TradingView feature benchmarks -- K-line charting, indicator display conventions
- Quantower / Trading Technologies -- VAP feature specification reference
- Stack Overflow / Reddit r/algotrading -- pandas EWM calculation issues, backtesting pitfalls
- ECharts GitHub issues -- memory leak reports, disposal best practices

### Tertiary (LOW confidence)
- Wyckoff market cycle theory -- well-documented concept but no algorithmic implementation reference
- Chinese quant community (知乎) -- backtesting system design discussions
- CSDN blog posts -- ECharts performance tuning tips

---
*Research completed: 2026-04-30*
*Ready for roadmap: yes*
