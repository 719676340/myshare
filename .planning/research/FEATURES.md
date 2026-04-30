# Feature Landscape

**Domain:** Volume-Price Trading Learning Platform (A-Stock, Chinese Market)
**Researched:** 2026-04-30

## Table Stakes

Features users expect from any trading charting or analysis tool. Missing these = product feels incomplete or amateur.

### K-Line Charting Core

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Candlestick (K-line) chart with OHLCV | The foundational visualization for any stock analysis tool; every platform from TradingView to TongDaXin has this | Low | ECharts has native candlestick series; straightforward |
| Volume bar chart synchronized with K-line | Volume is displayed below the price chart in every professional platform; it is inseparable from price analysis | Low | ECharts bar chart in a linked sub-chart |
| Crosshair cursor with OHLCV tooltip | Hovering shows exact data values; this is muscle memory for traders | Low | ECharts `axisPointer` + tooltip built-in |
| Zoom and pan (time-axis navigation) | Users need to zoom into specific date ranges and scroll through history | Low | ECharts `dataZoom` component handles this natively |
| Dark theme (TradingView-style) | Industry standard for trading platforms; reduces eye strain during long sessions | Low | ECharts theme configuration |
| Stock search (code/name fuzzy match) | Users expect to type "600519" or "茅台" and find the stock instantly | Low | Requires preloaded stock list in SQLite |
| Red-up / green-down color convention | A-stock market convention; opposite of US markets; getting this wrong signals the tool is not for A-stock | Low | Color config in chart options |

**Confidence: HIGH** -- These are universal across all trading platforms (TradingView, TongDaXin, THS). Verified via multiple charting platform comparisons.

### Technical Indicators

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Moving Averages (MA, EMA, SMA) | The most basic and widely-used indicator; even casual investors use MA5/MA10/MA20 | Low | Simple calculation, ECharts line series overlay |
| MACD | The de-facto standard momentum indicator; present in every trading platform worldwide | Medium | Requires histogram + signal line + MACD line in sub-chart |
| RSI | Standard overbought/oversold oscillator; taught in every technical analysis course | Medium | Sub-chart display, configurable period |
| KDJ | Particularly popular in Chinese trading platforms (TongDaXin, THS); Chinese traders expect it | Medium | Stochastic variant, sub-chart display |
| Bollinger Bands (BOLL) | Standard volatility indicator | Medium | Three-line overlay on price chart |

**Confidence: HIGH** -- These four indicators (MACD, RSI, KDJ, BOLL) are explicitly listed in the PROJECT.md requirements and are universally present in A-stock analysis tools.

### Volume-Price Analysis Markers

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Volume-price confirmation markers | Core to the platform's value proposition: mark "rising price + rising volume" as bullish confirmation | Medium | Requires algorithm to detect patterns; mark on chart with annotations |
| Volume-price anomaly markers | Mark "rising price + declining volume" as potential trap/divergence; this is the key educational content | Medium | Annotation system on ECharts |
| Basic K-line pattern recognition | Hammer, shooting star, doji, hanging man -- these are the first patterns every trader learns | Medium | Pattern detection algorithm; mark patterns on chart |

**Confidence: HIGH** -- These are the core educational value of the platform, explicitly listed in PROJECT.md requirements. The volume-price analysis theory (Wyckoff-derived) is well-documented.

## Differentiators

Features that set this platform apart from generic charting tools. Not universally expected, but highly valued for the target audience.

### Advanced Volume-Price Visualization

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| VAP (Volume at Price) distribution chart | Shows where volume concentrated at specific price levels; identifies support/resistance by volume; rare in free tools | High | Horizontal histogram overlaid on price chart; requires binning volume by price level. Professional tool (Quantower, Trading Technologies) feature. |
| Market cycle phase annotation | Automatically annotate accumulation -> markup -> distribution -> markdown phases based on Wyckoff theory; unique educational value | High | Requires multi-indicator algorithm combining price action, volume trends, and support/resistance. No free tool does this well. |
| Dynamic trend line drawing | Automatically identify and draw trend lines connecting swing highs/lows; saves manual effort | High | Algorithm to detect swing points and fit trend lines; render as overlay on chart |
| Support/resistance auto-detection | Identify key price levels using pivot point detection or volume concentration; educational value in showing where levels come from | High | Isolated pivot detection or volume-based level identification |
| Volume-price divergence detection | Automatically flag when price makes new highs but volume declines (bearish divergence) or vice versa; educational for learning divergence concepts | High | Compare price trend direction with volume trend; mark divergence zones |
| Multi-timeframe linked analysis | View daily, weekly, monthly charts simultaneously with linked crosshair; helps users see the same stock at different scales | High | Multiple chart instances sharing data and cursor state; significant UI coordination |

**Confidence: MEDIUM** -- These are aspirational features. VAP is well-understood (Trading Technologies, Quantower docs). Market cycle annotation is unique to this platform -- no direct competitor does this for free. Complexity estimates based on algorithm design needs.

### Trading Practice Module

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Day-by-day forward simulation | User sees one day at a time and cannot go back; simulates real trading where you cannot see the future; strong educational value | Medium | Core mechanic: sequential data reveal with no rewind. State management for position and cash. |
| Position sizing (half position, full position) | Teaches position management; most simulators only support buy/sell, not proportional sizing | Low | UI for selecting position percentage; calculation is straightforward |
| A-stock trading fee simulation | Commission 0.025% + stamp duty 0.1% on sell only; realistic cost teaching; most platforms ignore fees or use wrong rates | Low | Simple formula application per trade |
| T+1 enforcement | Cannot sell shares bought on the same day; fundamental A-stock rule; teaching this rule is itself educational | Medium | Track purchase dates per lot; enforce sell eligibility |
| Price limit enforcement | Cannot buy at upper limit or sell at lower limit (+/-10% for regular stocks, +/-5% for ST, +/-20% for ChiNext/STAR) | Medium | Calculate daily limits from previous close; enforce on trade execution |
| Final performance statistics | Total return, annualized return, max drawdown, win rate; gives closure and learning feedback | Low | Calculation from trade history |
| Trade history log with reasoning | User can optionally note why they bought/sold; self-reflection tool for learning | Low | Text input per trade; stored in SQLite |

**Confidence: HIGH** -- A-stock trading rules (T+1, price limits, fees) are well-documented. The day-by-day forward simulation is a known pattern in trading education (similar to TradingSim, Forex Tester). Verified through Chinese trading competition rule documents.

### Strategy Backtesting Module

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Preset strategy templates | Users can select common strategies (MA crossover, MACD divergence, volume breakout) without coding; lowers the barrier | Medium | Define strategy as configurable rules; provide sensible defaults |
| Parameter adjustment sliders | Users can tune strategy parameters (e.g., MA periods) and immediately see backtest results change; interactive learning | Medium | UI sliders + real-time recalculation; cache results for responsiveness |
| Comprehensive backtest metrics | Total return, annualized return, max drawdown, win rate, profit factor, Sharpe ratio, average holding period; professional-grade reporting | Medium | Standard quantitative metrics; well-documented formulas |
| Equity curve visualization | Plot portfolio value over time with buy/sell points marked on K-line chart; makes backtest results tangible | Medium | Line chart overlay on K-line or separate sub-chart |
| Strategy vs. benchmark comparison | Compare strategy returns against holding the stock (buy-and-hold); shows whether the strategy actually adds value | Low | Simple comparison line on equity curve chart |

**Confidence: HIGH** -- Backtesting metrics are industry-standard (Sharpe ratio, max drawdown, profit factor confirmed by multiple sources). Preset templates are common in platforms like QuantConnect, Backtrader.

### Data Management

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Custom indicator builder | Combine existing indicators with arithmetic operations (e.g., "MA5 / MA20"); power users can create their own signals without coding | Medium | Expression parser for indicator arithmetic; store custom indicator results in DB |
| Indicator results cached in database | Pre-computed indicators avoid repeated calculation; faster chart loading | Low | SQLite table for indicator values keyed by stock + date + indicator params |

**Confidence: HIGH** -- Standard data engineering pattern; PROJECT.md explicitly requires this.

## Anti-Features

Features to explicitly NOT build. These are traps that would waste development time or harm the product.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Real-time/intraday data feeds | Only using daily K-line data per project scope; intraday requires WebSocket infrastructure, tick-level storage, and significantly more complexity | Stick to daily OHLCV data from tushare; refresh on demand |
| User accounts / authentication | Single-user local tool; adding auth is pure overhead with no value | No login system; localhost-only access |
| Short selling / margin trading | A-stock restricts short selling; the learning focus is long-only stock picking | Only support buy/sell long positions |
| Social features (sharing, leaderboards, community) | This is a personal learning tool, not a social platform; social features add complexity (moderation, privacy) with no learning value | Focus on individual progress tracking |
| Alert/notification system | Requires background process, push infrastructure, and real-time data; outside project scope | User views charts and backtests on demand |
| Mobile app / responsive design | Local desktop web app; mobile adds responsive design overhead and touch interaction complexity | Desktop-first layout; fixed-width design is acceptable |
| News/sentiment feed integration | This is a technical analysis tool focused on volume-price theory; news integration is a different product category | Keep the tool focused on chart-based analysis |
| AI/ML-powered predictions | Overpromises and underdelivers for a learning tool; the goal is to teach users to analyze, not to give them black-box predictions | Provide clear, explainable indicators and markers based on defined rules |
| Manual drawing tools (freehand) | Project scope explicitly defers this; drawing tools are complex (multiple tool modes, undo/redo, state persistence) | Auto-detected trend lines and support/resistance instead; manual drawing in future iteration |
| Multi-market support (HK, US, crypto) | Only A-stock; adding other markets means different trading rules, data sources, and color conventions | A-stock only; clean, focused experience |
| Paper trading with real-time execution | Blurs the line between learning tool and actual trading platform; adds regulatory concerns | Simulated practice on historical data only |
| Export to broker / API trading | This is a learning tool, not a trading terminal; broker integration adds security requirements and liability | Results stay within the platform for educational review |

**Confidence: HIGH** -- Anti-features are derived directly from PROJECT.md "Out of Scope" section plus general trading platform design principles (avoiding feature bloat per fintech UX best practices).

## Feature Dependencies

```
K-line chart + Volume bars
  --> Volume-price markers (confirmation, anomaly)
  --> K-line pattern recognition
  --> Technical indicators (MACD, RSI, KDJ, BOLL)
      --> Custom indicator builder (depends on having base indicators)
      --> Multi-timeframe analysis (indicators must work on weekly/monthly data)

K-line chart
  --> Support/resistance auto-detection
  --> Dynamic trend lines (depends on swing point detection)
  --> Market cycle phase annotation (depends on support/resistance + volume trends)
  --> VAP distribution chart (depends on volume data processing)

Trading Practice Module
  --> K-line chart (reuse chart component)
  --> A-stock rules engine (T+1, price limits, fees)
  --> Trade history storage (SQLite)
  --> Performance statistics (depends on trade history)

Strategy Backtesting Module
  --> Technical indicators (strategies reference indicator values)
  --> K-line chart (display buy/sell points)
  --> A-stock rules engine (reuse from practice module)
  --> Equity curve visualization (depends on backtest results)
  --> Preset strategy templates (depends on indicator framework)

Stock list (preloaded in SQLite)
  --> Stock search (fuzzy match)

tushare data fetch
  --> Stock list
  --> Daily OHLCV data
  --> Stock info (name, industry, listing date)
```

## MVP Recommendation

### Phase 1: Foundation (Strategy Analysis Core)
Prioritize:
1. K-line chart with volume bars + crosshair/zoom/pan + dark theme
2. Stock search with fuzzy matching
3. Volume-price confirmation/anomaly markers
4. Basic K-line pattern recognition (hammer, doji, shooting star, hanging man)
5. Moving averages (MA5, MA10, MA20, MA60)

Rationale: The K-line chart is the foundation for ALL other modules. Volume-price markers are the core educational value. These must be solid before building anything else.

### Phase 2: Technical Indicators
1. MACD, RSI, KDJ, Bollinger Bands with sub-chart display
2. Indicator parameter adjustment
3. Indicator results cached in SQLite
4. A-stock color convention enforcement (red up, green down)

Rationale: Technical indicators are needed before backtesting can reference them. Caching in DB is needed for performance.

### Phase 3: Advanced Analysis
1. Support/resistance auto-detection
2. Dynamic trend line drawing
3. Market cycle phase annotation
4. VAP volume distribution chart

Rationale: These are high-complexity differentiators that depend on having solid charting and indicator infrastructure first.

### Phase 4: Trading Practice Module
1. Day-by-day forward simulation
2. Buy/sell with position sizing
3. T+1 enforcement + price limit enforcement + fee simulation
4. Performance statistics

Rationale: Reuses the K-line chart component. The A-stock rules engine is unique complexity. The forward-only mechanic is the key differentiator.

### Phase 5: Strategy Backtesting Module
1. Preset strategy templates (MA crossover, volume breakout, MACD divergence)
2. Parameter adjustment with live recalculation
3. Backtest metrics (total return, max drawdown, Sharpe ratio, win rate, profit factor)
4. Equity curve with buy/sell markers on K-line chart
5. Strategy vs. buy-and-hold benchmark comparison

Rationale: Depends on completed indicator framework. Reuses chart components and A-stock rules engine from Phase 4.

Defer:
- **Multi-timeframe linked analysis**: High UI coordination complexity; defer to post-MVP
- **Custom indicator builder**: Nice-to-have for power users; not core learning path
- **Trade history with reasoning notes**: Useful but not critical for initial launch

## Sources

- [TradingView Advanced Charts Release Notes](https://www.tradingview.com/charting-library-docs/latest/releases/release-notes/) -- K-line charting feature benchmarks
- [Apache ECharts GitHub](https://github.com/apache/echarts) -- Charting library capabilities
- [React Chart Library Comparison 2026](https://chenguangliang.com/posts/blog152_react-chart-libraries-comparison) -- ECharts vs TradingView Lightweight Charts
- [Quantower Volume Analysis Tools](https://www.quantower.com/volumeanalysistools) -- VAP and volume profile feature reference
- [Trading Technologies - Volume at Price](https://library.tradingtechnologies.com/trade/chrt-ti-volume-at-price.html) -- VAP feature specification
- [ATAS Order Flow & Volume Analysis](https://atas.net/) -- Professional volume analysis feature set
- [Tushare Pro Documentation](https://tushare.pro/document/2?doc_id=259) -- A-stock data integration reference
- [A股涨跌停价格计算规则](https://www.cnblogs.com/sljsz/p/15969026.html) -- A-stock price limit calculation rules
- [模拟交易撮合规则](https://www.stpt.edu.cn/jyxx/2024/0408/c313a36018/pagem.htm) -- A-stock simulation matching rules
- [Backtesting Metrics - 7 Key Metrics](https://medium.com/@pta.forwork/the-7-metrics-that-separate-profitable-trading-strategies-from-failures-5e9719dc687c) -- Standard backtesting metrics reference
- [Quantified Strategies - Trading Performance](https://www.quantifiedstrategies.com/trading-performance/) -- Comprehensive metric definitions
- [NautilusTrader](https://nautilustrader.io/) -- Open-source backtesting engine reference
- [QuantConnect](https://www.quantconnect.com/) -- Algorithmic trading platform feature set
- [知乎 - 量化回测系统](https://zhuanlan.zhihu.com/p/1975149995691892994) -- Chinese quant backtesting system reference
- [ResearchGate - MACD, RSI, KDJ in SH/SZ Markets](https://www.researchgate.net/publication/305298055_Technical_analysis_of_three_stock_oscillators_testing_MACD_RSI_and_KDJ_rules_in_SH_SZ_stock_markets) -- KDJ indicator relevance in Chinese markets

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| K-line charting table stakes | HIGH | Universal across all platforms; verified via multiple comparison articles |
| Technical indicators | HIGH | Industry-standard set; MACD/RSI/KDJ/BOLL confirmed in PROJECT.md and across all platforms |
| Volume-price analysis features | MEDIUM | Volume-price theory is well-documented, but auto-detection algorithms require design; no open-source reference implementation found |
| Trading practice features | HIGH | A-stock rules well-documented; simulation mechanics are standard |
| Backtesting features | HIGH | Metrics are industry-standard; templates are common in quant platforms |
| Anti-features | HIGH | Derived directly from PROJECT.md scope; validated against fintech UX best practices |
| A-stock specific considerations | HIGH | T+1, price limits, trading fees verified through official Chinese sources |
