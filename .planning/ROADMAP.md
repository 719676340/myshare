# Roadmap: 量价交易学习平台

## Overview

Build a local A-share volume-price trading learning platform in five phases. Start with the data pipeline and K-line chart (the shared foundation), then layer on indicators and volume-price analysis, add advanced analysis features, build the trading practice simulator, and finish with the strategy backtesting engine. Each phase delivers a complete, verifiable capability that builds on the previous one.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Data Foundation + K-Line Charting** - Stock search, tushare data pipeline, K-line + volume chart with dark theme and A-share color convention
- [ ] **Phase 2: Technical Indicators + Volume-Price Analysis** - MACD/RSI/KDJ/BOLL indicators, MA overlays, volume-price signal markers, K-line pattern recognition
- [ ] **Phase 3: Advanced Analysis Features** - Support/resistance detection, trend lines, market cycle annotation, VAP distribution, multi-timeframe analysis
- [ ] **Phase 4: Trading Practice Module** - Day-by-day forward simulation with A-share rules (T+1, price limits, fees), position management, performance stats
- [ ] **Phase 5: Strategy Backtesting Module** - Preset strategy templates, custom indicator builder, condition groups, comprehensive metrics, equity curve with buy/sell markers

## Phase Details

### Phase 1: Data Foundation + K-Line Charting
**Goal**: Users can search for A-share stocks and view interactive K-line charts with volume bars on a dark-themed interface
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, CHART-01, CHART-02, CHART-03, CHART-04, CHART-05, INDIC-05
**Success Criteria** (what must be TRUE):
  1. User can search for a stock by code or name and see fuzzy-matched results
  2. Selecting a stock displays a K-line candlestick chart with synchronized volume bars below
  3. Chart supports crosshair, zoom, drag-to-pan, and time-axis navigation, showing OHLCV on hover
  4. Chart uses A-share color convention (red=up, green=down) with TradingView-style dark theme
  5. MA5/MA10/MA20/MA60 moving average lines are displayed on the K-line chart
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Backend: FastAPI server, SQLite database, tushare data pipeline, stock search and daily K-line API endpoints
- [x] 01-02-PLAN.md — Frontend: Vue 3 app, dark theme, stock search autocomplete, interactive K-line chart with volume and MA overlays, human verification

### Phase 2: Technical Indicators + Volume-Price Analysis
**Goal**: Users can view technical indicator sub-charts and see automatic volume-price signal markers and K-line pattern annotations on the chart
**Depends on**: Phase 1
**Requirements**: DATA-03, DATA-04, VPA-01, VPA-02, VPA-03, INDIC-01, INDIC-02, INDIC-03, INDIC-04, INDIC-06
**Success Criteria** (what must be TRUE):
  1. User can view MACD, RSI, KDJ indicators in sub-charts below the K-line chart, with BOLL bands overlaid on the main chart
  2. User can adjust indicator parameters (periods, thresholds) and see recalculated results
  3. Volume-price confirmation signals (volume-up on rise, volume-down on fall) are automatically marked on the chart
  4. Volume-price anomaly signals (long candle + low volume trap, short candle + high volume weakness) are automatically marked
  5. K-line patterns (hammer, shooting star, doji, hanging man) are automatically identified and annotated
**Plans**: 3 plans

Plans:
- [x] 02-01-PLAN.md — Backend: IndicatorValue model, indicator computation service (MACD/RSI/KDJ/BOLL), VPA signal detection, K-line pattern recognition, API endpoints
- [x] 02-02-PLAN.md — Frontend: Indicator sub-charts (MACD/RSI/KDJ) with toggle buttons, BOLL overlay, Popover parameter panels, dynamic multi-grid chart layout
- [x] 02-03-PLAN.md — Frontend: VPA signal markers and K-line pattern annotations rendering, human verification of all Phase 2 features

### Phase 3: Advanced Analysis Features
**Goal**: Users can see auto-detected support/resistance levels, trend lines, market cycle annotations, and volume-at-price distribution on the chart
**Depends on**: Phase 2
**Requirements**: VPA-04, ADVAN-01, ADVAN-02, ADVAN-03, ADVAN-04, ADVAN-05
**Success Criteria** (what must be TRUE):
  1. Support and resistance levels are auto-detected and displayed as horizontal lines on the chart
  2. Dynamic trend lines are auto-drawn connecting pivot highs and pivot lows
  3. Market cycle phases (accumulation, markup, distribution, markdown) are annotated on the chart timeline
  4. VAP volume distribution is displayed as a horizontal histogram overlaid on the price chart
  5. User can switch between daily, weekly, and monthly K-line views with linked navigation
**Plans**: 3 plans

Plans:
- [x] 03-01-PLAN.md — Backend: AdvancedAnalysisService with pivot detection, support/resistance, trend lines, market cycle, VAP, K-line aggregation, divergence detection, API endpoints
- [x] 03-02-PLAN.md — Frontend: KLineChart rendering with support/resistance lines, trend lines, market cycle bands, VAP overlay, multi-timeframe, toolbar controls, store extensions
- [ ] 03-03-PLAN.md — Human verification of all Phase 3 advanced analysis features

### Phase 4: Trading Practice Module
**Goal**: Users can practice trading on historical A-share data with full simulation of real market rules
**Depends on**: Phase 2
**Requirements**: PRACT-01, PRACT-02, PRACT-03, PRACT-04, PRACT-05, PRACT-06, PRACT-07, PRACT-08
**Success Criteria** (what must be TRUE):
  1. User can select a stock and time range, see K-line data up to the start date, then advance day-by-day without going back
  2. User can place buy/sell orders with position sizing (half, full, custom), starting from configurable initial capital (default 1M)
  3. A-share trading rules are enforced: T+1 (cannot sell same-day buys), price limits (10% normal, 5% ST, 20% ChiNext/STAR), and suspension days are respected
  4. Trading fees are simulated: 0.025% commission + 0.1% stamp tax on sells
  5. At practice end, user sees final P&L, full trade history with per-trade profit/loss
**Plans**: TBD

Plans:
- [x] 04-01: TBD
- [x] 04-02: TBD

### Phase 5: Strategy Backtesting Module
**Goal**: Users can run automated backtests with preset strategy templates and custom indicator expressions, configure buy/sell conditions with nested AND/OR groups, and see comprehensive performance metrics with equity curves and K-line trade markers
**Depends on**: Phase 2, Phase 4
**Requirements**: BACK-01, BACK-02, BACK-03, BACK-04, BACK-05, DATA-05
**Success Criteria** (what must be TRUE):
  1. User can select from preset strategy templates (MA crossover, volume breakout, MACD divergence) and adjust parameters, or build custom strategies from scratch
  2. User can define custom indicator expressions (e.g. VOL/MA(VOL,20)) with real-time validation
  3. User can build nested AND/OR buy/sell condition groups with 11 operators
  4. Backtest outputs comprehensive metrics: total return, annualized return, max drawdown, trade count, win rate, profit factor, Sharpe ratio, avg holding period
  5. Equity curve is displayed showing strategy net value vs. buy-and-hold benchmark (dual-line)
  6. Individual trade buy/sell points are marked on the K-line chart for visual inspection
**Plans**: 2 plans

Plans:
- [ ] 05-01-PLAN.md — Backend: AST expression parser, backtest engine with daily iteration + A-share rules + condition evaluation, BacktestSession/Trade models, 6 REST API endpoints, preset strategy templates
- [ ] 05-02-PLAN.md — Frontend: Backtest store, preset selector, indicator builder with validation, recursive condition group components, results display (8 metrics + dual-line equity curve + K-line markers + trade table), BacktestView page assembly, human verification

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Foundation + K-Line Charting | 0/2 | Planned | - |
| 2. Technical Indicators + Volume-Price Analysis | 0/3 | Planned | - |
| 3. Advanced Analysis Features | 0/3 | Planned | - |
| 4. Trading Practice Module | 0/? | Not started | - |
| 5. Strategy Backtesting Module | 0/2 | Planned | - |
