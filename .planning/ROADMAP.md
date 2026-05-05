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
- [ ] **Phase 5: Strategy Backtesting Module** - Preset strategy templates, parameter tuning, comprehensive metrics, equity curve with buy/sell markers

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
- [ ] 01-01-PLAN.md — Backend: FastAPI server, SQLite database, tushare data pipeline, stock search and daily K-line API endpoints
- [ ] 01-02-PLAN.md — Frontend: Vue 3 app, dark theme, stock search autocomplete, interactive K-line chart with volume and MA overlays, human verification

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
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD

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
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

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
- [ ] 04-01: TBD
- [ ] 04-02: TBD

### Phase 5: Strategy Backtesting Module
**Goal**: Users can run automated backtests with preset strategy templates and see comprehensive performance metrics visualized
**Depends on**: Phase 2, Phase 4
**Requirements**: BACK-01, BACK-02, BACK-03, BACK-04, BACK-05
**Success Criteria** (what must be TRUE):
  1. User can select from preset strategy templates (MA crossover, volume breakout, MACD divergence) and adjust parameters
  2. Backtest outputs comprehensive metrics: total return, annualized return, max drawdown, trade count, win rate, profit factor, Sharpe ratio, avg holding period
  3. Equity curve is displayed showing strategy net value vs. buy-and-hold benchmark
  4. Individual trade buy/sell points are marked on the K-line chart for visual inspection
**Plans**: TBD

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Foundation + K-Line Charting | 0/2 | Planned | - |
| 2. Technical Indicators + Volume-Price Analysis | 0/? | Not started | - |
| 3. Advanced Analysis Features | 0/? | Not started | - |
| 4. Trading Practice Module | 0/? | Not started | - |
| 5. Strategy Backtesting Module | 0/? | Not started | - |
