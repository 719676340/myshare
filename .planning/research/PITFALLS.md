# Domain Pitfalls

**Domain:** Volume-Price Trading Analysis Platform (A-share market, local tool)
**Researched:** 2026-04-30

---

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: pandas EWM `adjust` Parameter Silently Produces Wrong MACD/RSI Values

**What goes wrong:** pandas `DataFrame.ewm()` defaults to `adjust=True`, which uses a weighted-average normalization formula. This produces EMA values that diverge from every standard financial platform (TradingView, TongDaXin, TongHuaShun). MACD, RSI, KDJ, and BOLL all depend on EMA -- one wrong parameter poisons every indicator.

**Why it happens:** The pandas default (`adjust=True`) was designed for statistical smoothing, not financial EMA. Financial platforms use the recursive formula `EMA_t = alpha * price_t + (1-alpha) * EMA_{t-1}`. With `adjust=True`, pandas uses a different normalization that produces noticeably different values, especially in the first 50-100 periods.

**Consequences:** All technical indicators calculated with the wrong EMA will differ from what users see on any standard platform. Users will notice the discrepancy immediately and lose trust in the tool. Recalculating and re-storing all indicator data is a full database rewrite.

**Prevention:** Always use `adjust=False` for all EWM calculations. Write a shared utility function for EMA that enforces this, and never call `ewm()` without explicitly setting the parameter.

```python
# Correct: matches TradingView / TongDaXin
ema_12 = df['close'].ewm(span=12, adjust=False).mean()

# Wrong (pandas default): diverges from financial platforms
ema_12 = df['close'].ewm(span=12).mean()
```

**Detection:** Compare your MACD values against TradingView for a known stock (e.g., 000001.SZ). If the histogram shape is similar but values are shifted or scaled, this is the culprit. If only the first 50 bars are wrong, it is the warm-up issue (see Pitfall 2).

**Phase:** Phase 1 (Strategy Analysis -- indicator calculation). This is foundational -- get it wrong here and every phase that depends on indicators is corrupted.

---

### Pitfall 2: EMA Warm-Up Period Produces NaN or Garbage Values

**What goes wrong:** EMA requires a seed value. Most implementations use the first price as the seed, meaning the first N-1 values of an N-period EMA are unreliable or NaN. MACD (26-period EMA) needs roughly 50 data points before values stabilize. RSI needs 14+ periods. For a stock with only 30 days of data (e.g., newly listed), indicators are meaningless.

**Why it happens:** The recursive EMA formula `EMA_t = alpha * price_t + (1-alpha) * EMA_{t-1}` needs an initial `EMA_0`. Using `price_0` as the seed means the first several values are heavily influenced by the arbitrary starting price, not by the actual data pattern.

**Consequences:** Indicators displayed for recent IPOs or stocks with limited history will show wildly incorrect values. If these values are stored in the database and used for pattern recognition or backtesting, they produce phantom signals.

**Prevention:**
1. Require minimum data length before computing any indicator (e.g., at least `2 * period` data points).
2. When storing indicators, mark the first N values as `NULL` or compute but flag them as "warm-up period" in the database.
3. When displaying on the K-line chart, do not show indicator lines for the warm-up period or show them as dashed/faded lines.
4. For the seed, use SMA of the first N periods rather than the first price -- this reduces warm-up noise.

**Detection:** Plot MACD for a newly listed stock. If the MACD line shows extreme swings in the first 30-50 bars that do not match TradingView, this is the issue.

**Phase:** Phase 1 (Strategy Analysis). Must be handled when building the indicator calculation pipeline.

---

### Pitfall 3: KDJ Division by Zero in Flat Markets

**What goes wrong:** KDJ (Stochastic Oscillator) calculates `%K = (Close - LLV) / (HHV - LLV) * 100`. When a stock trades at a flat price for the lookback period (High == Low), `HHV - LLV = 0`, causing division by zero. This produces `inf` or `NaN` values.

**Why it happens:** A-share stocks sometimes trade at the limit-up or limit-down price for consecutive days (especially ST stocks at the 5% limit). During these periods, the daily range is zero.

**Consequences:** NaN propagates through subsequent KDJ calculations (since `%D` and `%J` depend on `%K`). If stored in the database, it corrupts downstream pattern recognition and backtesting queries. If sent to ECharts, it can cause rendering errors or blank chart segments.

**Prevention:**
```python
lowest_low = df['low'].rolling(window=9).min()
highest_high = df['high'].rolling(window=9).max()
rsv = np.where(
    (highest_high - lowest_low) != 0,
    (df['close'] - lowest_low) / (highest_high - lowest_low) * 100,
    50  # Default to neutral when range is zero
)
```

**Detection:** Check KDJ values for stocks that hit consecutive limit-up/limit-down. If any K, D, or J values are `inf`, `NaN`, or exceed the -100 to 200 range, this is the issue.

**Phase:** Phase 1 (Strategy Analysis -- indicator calculation).

---

### Pitfall 4: Backtesting with Limit-Up/Limit-Down Assumes Impossible Execution

**What goes wrong:** A-share stocks have daily price limits: mainboard +/-10%, ChiNext/STAR board +/-20%, ST stocks +/-5%. When a stock hits the limit-up price, buy orders cannot be filled (no sellers). When it hits limit-down, sell orders cannot be filled (no buyers). Naive backtests assume execution at the limit price.

**Why it happens:** Backtesting engines typically use `close` price for execution simulation without checking whether the stock closed at the limit price. If `close == high == limit_up_price`, no buy orders can fill. If `close == low == limit_down_price`, no sell orders can fill.

**Consequences:** The backtest reports trades that would be impossible in reality. Strategies that buy at limit-up prices (momentum strategies) appear wildly profitable in backtests but would fail in live trading. This is one of the most deceptive backtesting errors in the A-share market.

**Prevention:**
1. Store the daily limit prices (or calculate from previous close: `prev_close * 1.10` for mainboard).
2. In the backtesting engine, before executing a buy, check `close < daily_limit_up`. If at limit, reject the trade.
3. Before executing a sell, check `close > daily_limit_down`. If at limit, reject the trade.
4. For more accuracy, also check trading volume -- if volume is extremely low at the limit, fills are unlikely even if not technically at the limit.

**Detection:** Run your backtest and count how many trades execute at exactly the limit-up or limit-down price. If any exist, the engine has a bug.

**Phase:** Phase 3 (Auto Backtesting). This is critical for the backtest module. Must be built into the order execution simulation from day one.

---

### Pitfall 5: Suspension Days Create Silent Data Gaps

**What goes wrong:** When an A-share stock is suspended (停牌), tushare returns no row for that date. This creates gaps in the time series. If your code assumes consecutive calendar dates or consecutive trading days, these gaps cause misalignment between price data, indicator values, and volume data.

**Why it happens:** Suspension is common in A-shares. A stock can be suspended for days, weeks, or even months. The `daily` endpoint simply omits rows for suspended dates. There is no explicit "suspended" flag in the daily data response.

**Consequences:**
- Rolling window calculations (moving averages, RSI, KDJ) silently skip suspension days, producing incorrect indicator values because the window covers the wrong number of actual trading days.
- The trading simulation module might allow "trading" on a suspended day if the date is not validated.
- Volume analysis (critical for volume-price strategy) will show zero volume on the resumption day but no indication of why, confusing the volume-price pattern recognition.

**Prevention:**
1. After fetching data, use the `trade_cal` (trading calendar) endpoint to identify all trading days.
2. Reindex the DataFrame to include all trading days, filling suspension days with the last known close price and zero volume, and add a `suspended` boolean column.
3. Use tushare's `suspend` endpoint to explicitly fetch suspension information.
4. In the trading simulation, check the `suspended` flag and reject any trades on suspended days.
5. In volume-price analysis, explicitly mark suspension days and skip them from volume pattern calculations.

**Detection:** Pick a stock known to have been suspended (e.g., many stocks were suspended during the 2015 crash). Plot its data. If there is a visible gap or discontinuity in the date axis, or if volume suddenly drops to zero without explanation, the suspension is not being handled.

**Phase:** Phase 1 (data management layer) -- this must be handled when building the data fetching pipeline, before any analysis or simulation.

---

### Pitfall 6: Look-Ahead Bias in Technical Indicator Calculation

**What goes wrong:** Indicators are calculated using future data that would not have been available at the time of the trade decision. This is the single most common backtesting error and the most deceptive because results look great but are completely unreliable.

**Why it happens:**
- Calculating indicators on the entire dataset first, then slicing for backtesting -- the indicator values at time T already "know" about prices at T+1, T+2, etc.
- Using adjusted prices (前复权/后复权) that incorporate future corporate actions. If you use forward-adjusted prices, a split in 2020 changes the prices displayed for 2018.
- Pattern recognition that scans both forward and backward from the current bar.

**Consequences:** The backtest shows impossible returns. The strategy appears to "predict" moves that it actually saw in advance. Any confidence built from these results is false.

**Prevention:**
1. Calculate indicators incrementally: at each time step, only use data from time 0 to time T. Never calculate on the full dataset then iterate.
2. Use unadjusted prices for backtesting. Apply adjustment factors only at the point of display.
3. If storing pre-calculated indicators, ensure they are computed on a rolling basis, not a whole-series basis.
4. Validate: run a backtest where the strategy always "knows" tomorrow's close. If the results are similar to your actual strategy, you have look-ahead bias.

**Detection:** Check if indicator values at time T change when you append more data after time T. If they do, you have look-ahead bias.

**Phase:** Phase 1 (indicator calculation) and Phase 3 (backtesting). The data pipeline must be designed to prevent this from the start.

---

### Pitfall 7: Memory Leaks from Undisposed ECharts Instances in Vue

**What goes wrong:** Each time a user selects a new stock or switches between modules, a new ECharts instance is created. If the old instance is not properly disposed, the DOM node and its associated canvas, event listeners, and animation frames remain in memory. After switching stocks 10-20 times, the browser becomes sluggish or crashes.

**Why it happens:** ECharts creates a canvas element, attaches resize observers, registers internal timers, and allocates GPU textures. Simply removing the DOM node does not clean these up. Vue's component lifecycle does not automatically dispose third-party library instances.

**Consequences:** The application becomes progressively slower. After extended use, the tab consumes gigabytes of RAM and becomes unresponsive. The user has to refresh the page.

**Prevention:**
```javascript
// In Vue 3 Composition API
import { ref, onMounted, onUnmounted, shallowRef } from 'vue'
import * as echarts from 'echarts'

const chartRef = ref(null)
const chartInstance = shallowRef(null)

onMounted(() => {
  chartInstance.value = echarts.init(chartRef.value)
})

onUnmounted(() => {
  if (chartInstance.value) {
    chartInstance.value.dispose()
    chartInstance.value = null  // Must null the reference
  }
})

// When switching stocks, reuse the instance:
function updateChart(newOption) {
  if (chartInstance.value) {
    chartInstance.value.setOption(newOption, true)  // true = notMerge, replaces old option
  }
}
```

Critical details:
1. Use `shallowRef` not `ref` for the chart instance -- Vue's reactivity system tries to deeply proxy the ECharts object, which causes performance issues and can interfere with ECharts internals.
2. Always call `dispose()` AND set the variable to `null`.
3. Do NOT recreate instances when switching stocks -- reuse the same instance with `setOption(option, true)`.
4. If using `ResizeObserver`, disconnect it in `onUnmounted`.

**Detection:** Open Chrome DevTools Memory tab. Select 10 different stocks. Take a heap snapshot. If memory grows linearly and does not drop after switching, there is a leak.

**Phase:** Phase 1 (K-line chart component). This must be built correctly from the first chart component.

---

## Moderate Pitfalls

### Pitfall 8: ECharts Candlestick Color Convention Mismatch

**What goes wrong:** ECharts defaults to Western stock chart conventions: green for up (close > open), red for down (close < open). A-share market convention is the opposite: red for up, green for down. Users will be confused and annoyed.

**Prevention:** Explicitly set candlestick colors in the ECharts option:
```javascript
series: [{
  type: 'candlestick',
  itemStyle: {
    color: '#ef232a',        // Up candle body fill (red for A-share)
    color0: '#00b368',       // Down candle body fill (green for A-share)
    borderColor: '#ef232a',  // Up candle border
    borderColor0: '#00b368'  // Down candle border
  }
}]
```

**Detection:** Open the chart. If a day where close > open shows a green candle, the convention is wrong.

**Phase:** Phase 1 (K-line chart component). Fix immediately when building the chart.

---

### Pitfall 9: tushare Rate Limiting Causes Silent Data Failures

**What goes wrong:** tushare Pro enforces rate limits (calls per minute) and a credit/point system (积分制度). Rapid sequential API calls (e.g., looping through 5000+ A-share tickers) exhaust the quota. The API returns an error, but if your code does not handle it, you get empty DataFrames that silently write NULL or missing data to the database.

**Why it happens:** Fetching the full A-share stock list and daily data for all tickers requires many sequential calls. Without rate limiting logic, the code hammers the API and gets throttled.

**Consequences:** Incomplete data in the database. Gaps that are not obvious because the code does not crash -- it just writes fewer rows than expected.

**Prevention:**
1. Implement retry logic with exponential backoff for all tushare API calls.
2. Add `time.sleep(0.5)` between consecutive API calls.
3. Use batch endpoints where possible (fetch by date range instead of per-stock).
4. After fetching, validate: assert that the returned DataFrame is not empty and has the expected number of rows.
5. Cache aggressively -- never re-fetch data you already have in SQLite.
6. Pre-load the stock list once, then fetch daily data on-demand when the user selects a stock.

```python
import time
import tushare as ts

def fetch_with_retry(api_func, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            result = api_func(**kwargs)
            if result is None or (hasattr(result, 'empty') and result.empty):
                raise ValueError("Empty response from tushare")
            return result
        except Exception as e:
            if '每分钟' in str(e) or 'limit' in str(e).lower() or '积分' in str(e):
                wait = 61 * (attempt + 1)  # Wait past the per-minute window
                print(f"Rate limited, waiting {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Failed after {max_retries} retries")
```

**Detection:** After bulk data fetch, count rows in the database and compare against expected trading days * number of stocks. A significant shortfall indicates throttled requests.

**Phase:** Phase 1 (data management layer). Build retry logic into the data fetching module from the start.

---

### Pitfall 10: SQLite Write Performance with Bulk Data Inserts

**What goes wrong:** Inserting daily data for thousands of stocks one row at a time is extremely slow in SQLite. Each INSERT is an individual transaction. Inserting 5000 stocks * 250 trading days = 1.25 million rows can take hours.

**Why it happens:** SQLite's default autocommit mode wraps every INSERT in its own transaction, which requires a disk flush. This is the #1 SQLite performance mistake.

**Prevention:**
1. Wrap bulk inserts in explicit transactions:
```python
conn = sqlite3.connect('trading.db')
conn.execute("PRAGMA journal_mode=WAL")      # Concurrent read/write
conn.execute("PRAGMA synchronous=NORMAL")    # Safe with WAL, much faster
conn.execute("PRAGMA cache_size=-64000")      # 64MB cache

cursor = conn.cursor()
cursor.execute("BEGIN TRANSACTION")
try:
    for row in data:
        cursor.execute("INSERT INTO daily_data VALUES (?,?,?,?,?,?,?)", row)
    conn.commit()
except:
    conn.rollback()
    raise
```
2. For initial bulk load, drop indexes, insert all data, then recreate indexes.
3. Use `executemany()` instead of individual `execute()` calls.
4. Consider using `pandas.to_sql()` with `method='multi'` for batch inserts.

**Detection:** Time the first data load. If inserting 100K rows takes more than a few seconds, the approach is wrong.

**Phase:** Phase 1 (data management). This affects the initial data load experience.

---

### Pitfall 11: SQLite Missing Composite Indexes for Time-Range Queries

**What goes wrong:** Queries like "get all daily data for stock 000001.SZ between 2024-01-01 and 2025-12-31" are slow because the default rowid index does not help. Full table scans on 1M+ rows take seconds.

**Why it happens:** Developers create a primary key on an auto-increment ID or forget to create indexes on the actual query patterns.

**Prevention:** Create composite indexes matching the query patterns:
```sql
-- This is the most important index for the entire application
CREATE INDEX idx_daily_tscode_date ON daily_data (ts_code, trade_date);

-- For queries that also filter on specific fields
CREATE INDEX idx_daily_tscode_date_close
  ON daily_data (ts_code, trade_date, open, high, low, close, vol);
```

The column order matters: `ts_code` first (equality filter), `trade_date` second (range filter). Do not reverse this order.

**Detection:** Run `EXPLAIN QUERY PLAN` on a typical query. If it shows "SCAN TABLE" instead of "SEARCH TABLE USING INDEX", the index is missing.

**Phase:** Phase 1 (data management). Create indexes immediately after table creation.

---

### Pitfall 12: ECharts dataZoom Performance Degradation with Full Dataset

**What goes wrong:** ECharts loads all data points into memory and renders all of them (even off-screen ones) unless properly configured. For a stock with 20 years of daily data (~5000 bars), this is manageable. But if multiple stocks are loaded or the user opens many chart panels, performance degrades.

**Why it happens:** ECharts' default behavior renders the entire series. The `dataZoom` component visually clips but does not reduce the rendering workload unless configured with `filterMode: 'filter'`.

**Prevention:**
```javascript
option = {
  dataZoom: [{
    type: 'inside',
    start: 70,        // Show only the most recent 30% by default
    end: 100,
    filterMode: 'filter'  // Critical: actually removes off-screen data from rendering
  }, {
    type: 'slider',
    start: 70,
    end: 100,
    filterMode: 'filter'
  }],
  series: [{
    type: 'candlestick',
    data: klineData,
    large: true,          // Enable optimized rendering mode
    largeThreshold: 2000  // Activate when data exceeds 2000 points
  }]
};
```

Key: `filterMode: 'filter'` actually removes data points outside the zoom range from the rendering pipeline. Without it, ECharts renders all points and just clips visually.

**Detection:** Load a stock with 10+ years of data. Zoom to show only 1 month. If the chart still feels sluggish (slow tooltip, choppy drag), data is not being filtered.

**Phase:** Phase 1 (K-line chart component).

---

### Pitfall 13: T+1 Rule Not Enforced in Trading Simulation

**What goes wrong:** A-share market enforces T+1 settlement: shares bought today cannot be sold until the next trading day. If the trading simulation allows same-day sell-after-buy, it produces unrealistic results.

**Why it happens:** It is the natural default to allow any order at any time. T+1 is an A-share specific rule that must be explicitly coded.

**Consequences:** The simulation allows day-trading strategies that would be illegal in the A-share market. Results are meaningless for A-share traders.

**Prevention:**
1. Track position lots with purchase dates.
2. When processing a sell order, check that the shares were purchased on a previous trading day (not the current day).
3. If the user attempts to sell same-day shares, reject the order with a clear message ("T+1: 今日买入的股票不可卖出").

**Detection:** In the simulation, buy and immediately sell on the same day. If the order goes through, T+1 is not enforced.

**Phase:** Phase 2 (Trading Practice). Build this into the order validation logic from the start.

---

### Pitfall 14: Survivorship Bias in Stock Universe

**What goes wrong:** When building the stock list or backtesting universe, only currently listed stocks are included. Delisted stocks (退市) are excluded. This means the backtest never encounters the worst-performing stocks, inflating strategy performance.

**Why it happens:** tushare's default stock list queries may exclude delisted stocks unless explicitly requested. The user naturally selects from currently active stocks.

**Consequences:** For a learning tool, this means the user never sees examples of stocks that went bankrupt or were delisted. Volume-price patterns on delisted stocks are some of the most instructive examples of what to avoid.

**Prevention:**
1. When fetching the stock list from tushare, include delisted stocks (use the appropriate parameter in the `stock_basic` endpoint).
2. Store listing and delisting dates in the stock master table.
3. In the stock search UI, show delisted stocks with a "(已退市)" tag.
4. For the trading simulation, allow selecting historical periods where the stock was still listed.
5. For backtesting, always use a point-in-time stock universe -- the list of stocks that existed at the start of the backtest period.

**Detection:** Check if your stock list includes stocks that were delisted before 2024 (e.g., 000029.SZ 美都能源, delisted 2020). If not, you have survivorship bias.

**Phase:** Phase 1 (data management) and Phase 3 (backtesting).

---

### Pitfall 15: Adjusted Price Confusion (前复权 vs 后复权 vs 不复权)

**What goes wrong:** tushare provides three types of price data: unadjusted (不复权), forward-adjusted (前复权/qfq), and backward-adjusted (后复权/hfq). Mixing these up or using the wrong one for the wrong purpose produces silently wrong results.

**Why it happens:** Corporate actions (dividends, stock splits, rights issues) change the nominal price. Adjusted prices account for this, but each adjustment method serves a different purpose:
- **不复权 (Unadjusted):** The actual trading price. Needed for trading simulation (can you actually buy/sell at this price?) and limit-up/limit-down calculation.
- **前复权 (Forward-adjusted / qfq):** Historical prices are adjusted so the latest price is real. Best for chart display -- shows continuous price movement. But prices before corporate actions are NOT the real trading prices.
- **后复权 (Backward-adjusted / hfq):** Current prices are adjusted to be comparable with historical prices. Best for return calculation.

**Consequences:**
- Using adjusted prices for limit-up/limit-down checks produces wrong limits.
- Using unadjusted prices for chart display shows artificial price jumps at ex-dividend dates.
- Using wrong adjustment for backtest returns produces incorrect return calculations.
- The volume-price patterns look different depending on which prices you use -- volume-price analysis should use unadjusted prices for accuracy.

**Prevention:**
1. Store unadjusted prices and the adjustment factor in the database. Compute adjusted prices on the fly when needed.
2. Use unadjusted prices for: trading simulation order execution, limit price calculation, volume-price analysis.
3. Use forward-adjusted (qfq) prices for: K-line chart display.
4. Use backward-adjusted (hfq) prices for: return calculations in backtesting.
5. Document this clearly in the codebase.

**Detection:** Find a stock that had a large dividend or split. Check if your chart shows a price jump on the ex-date. If it does, you are using unadjusted prices for display. Check if your backtest allows buying at the pre-split price post-split.

**Phase:** Phase 1 (data management). This decision must be made when designing the database schema.

---

### Pitfall 16: ECharts Tooltip Crosshair Desynchronization Across Sub-Charts

**What goes wrong:** The K-line chart has multiple sub-charts (candlestick + volume + MACD + RSI, etc.). When the user hovers, the crosshair (十字光标) should align across all sub-charts. If the data arrays have different lengths or the x-axis is not shared, the crosshair desynchronizes.

**Why it happens:** Different indicators have different warm-up periods (MACD needs 33+ bars, RSI needs 14+ bars, KDJ needs 9+ bars). If each series starts at a different index, the x-axis positions misalign.

**Prevention:**
1. Use a single shared `xAxis` with all sub-charts referencing it via `xAxisIndex`.
2. Pad all indicator arrays with `null` values to match the date array length. Do NOT truncate.
3. Use the ECharts `axisPointer.link` configuration to synchronize crosshairs:
```javascript
axisPointer: {
  link: [{ xAxisIndex: 'all' }],  // Links all x-axes
  label: { show: true }
}
```
4. Use a grid layout with shared x-axis for all sub-charts.

**Detection:** Hover over the chart and check if the vertical crosshair line appears at the same date across all sub-charts (candlestick, volume, MACD). If any sub-chart is offset, this is the issue.

**Phase:** Phase 1 (K-line chart component with technical indicators).

---

### Pitfall 17: Bollinger Bands Division by Zero and Edge Cases

**What goes wrong:** Bollinger Bands calculate `middle = SMA(20)`, `upper = middle + 2*std`, `lower = middle - 2*std`. When the standard deviation is zero (flat price), the bands collapse to a single line. More subtly, using `pandas.Series.std()` defaults to sample standard deviation (ddof=1) which can produce slightly different values than the population standard deviation (ddof=0) used by some trading platforms.

**Prevention:**
```python
# Use population standard deviation (ddof=0) to match most trading platforms
std = df['close'].rolling(window=20).std(ddof=0)
```

**Detection:** Compare your Bollinger Bands against TradingView for a stock with a flat trading period.

**Phase:** Phase 1 (indicator calculation).

---

## Minor Pitfalls

### Pitfall 18: tushare Date Format Mismatch

**What goes wrong:** tushare expects dates in `YYYYMMDD` format as a string (e.g., `'20240101'`). Using Python `datetime` objects or `YYYY-MM-DD` format strings produces silent empty DataFrames instead of errors.

**Prevention:** Always format dates explicitly: `datetime.strftime('%Y%m%d')`. Write a utility function.

**Phase:** Phase 1 (data management).

---

### Pitfall 19: tushare `ts_code` vs `symbol` Confusion

**What goes wrong:** tushare uses `ts_code` format (e.g., `'000001.SZ'`, `'600519.SH'`) for most endpoints. Using just the numeric symbol `'000001'` returns empty data. This is different from how users typically refer to stocks ("stock code 000001").

**Prevention:** Always use `ts_code` format for API calls. Store both `ts_code` and numeric `symbol` in the stock master table. Convert user input to `ts_code` before API calls.

**Phase:** Phase 1 (data management).

---

### Pitfall 20: ECharts Render Before DOM Ready in Vue

**What goes wrong:** Calling `echarts.init(domElement)` before the DOM element has actual dimensions (width/height) produces a chart with 0x0 size. This happens when initializing in `created()` or `mounted()` before the layout is computed, or when the chart container is inside a `v-if` that has not rendered yet.

**Prevention:** Use `nextTick()` or `setTimeout(fn, 0)` in `onMounted()`. Check that the container has non-zero dimensions before initializing:
```javascript
onMounted(() => {
  nextTick(() => {
    const dom = chartRef.value
    if (dom && dom.clientWidth > 0 && dom.clientHeight > 0) {
      chartInstance.value = echarts.init(dom)
    }
  })
})
```

**Phase:** Phase 1 (K-line chart component).

---

### Pitfall 21: Volume-Price Analysis on Adjusted Data Shows False Signals

**What goes wrong:** Volume-price analysis (放量上涨, 缩量下跌, 量价背离) should be performed on unadjusted prices and raw volume. Using forward-adjusted prices can create artificial price gaps at ex-dividend dates that look like volume-price anomalies but are just adjustment artifacts.

**Prevention:** Always use unadjusted OHLCV for volume-price pattern detection. Only use adjusted prices for chart display.

**Phase:** Phase 1 (strategy analysis -- pattern recognition).

---

### Pitfall 22: RSI Wilder's Smoothing vs Simple Average Mismatch

**What goes wrong:** The standard RSI (Wilder's RSI) uses Wilder's smoothing method (equivalent to EMA with `span=2*N-1`, i.e., `alpha=1/N`) for average gain/loss, not a simple moving average. Using SMA produces RSI values that differ from TradingView.

**Prevention:**
```python
# Wilder's smoothing: use ewm with alpha=1/period, adjust=False
alpha = 1.0 / period
avg_gain = gains.ewm(alpha=alpha, adjust=False).mean()
avg_loss = losses.ewm(alpha=alpha, adjust=False).mean()
```

Note: `ewm(alpha=1/14)` is equivalent to `ewm(span=27)` -- both give `alpha = 2/(27+1) = 1/14`.

**Detection:** Compare RSI values against TradingView for any stock. Values should match within floating-point precision.

**Phase:** Phase 1 (indicator calculation).

---

### Pitfall 23: SQLite WAL File Growth

**What goes wrong:** In WAL mode, the WAL file can grow unbounded if there are long-running read transactions that prevent checkpointing. For a local tool, this is less critical but can still happen if the user opens multiple browser tabs.

**Prevention:** Set `PRAGMA wal_autocheckpoint = 1000;` and periodically run `PRAGMA wal_checkpoint(TRUNCATE);`.

**Phase:** Phase 1 (data management). Configure at database initialization.

---

### Pitfall 24: ECharts `setOption` Memory Growth with Accumulated Options

**What goes wrong:** When updating chart data (e.g., switching stocks), calling `setOption(newOption)` without the `notMerge` parameter causes ECharts to merge the new option with the old one. Over many updates, the internal option tree grows and consumes increasing memory.

**Prevention:** Always use `setOption(newOption, true)` or `setOption(newOption, { notMerge: true })` when replacing data entirely (e.g., switching stocks). Only use merge mode when incrementally adding data points.

**Phase:** Phase 1 (K-line chart component).

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation | Phase |
|-------------|---------------|------------|-------|
| Database schema design | Mixed adjusted/unadjusted prices (Pitfall 15) | Store unadjusted + adj_factor, compute adjusted on-the-fly | Phase 1 |
| Data fetching pipeline | Rate limiting + suspension gaps (Pitfalls 5, 9) | Retry logic, trade_cal reindexing, suspend flag | Phase 1 |
| Technical indicators | EWM adjust, warm-up, division by zero (Pitfalls 1, 2, 3, 17, 22) | Shared utility functions, minimum data length checks | Phase 1 |
| K-line chart component | Memory leaks, color convention, crosshair sync (Pitfalls 7, 8, 16, 20, 24) | Proper dispose, shallowRef, explicit colors, linked axes | Phase 1 |
| Volume-price pattern detection | Using adjusted data (Pitfall 21) | Explicit use of unadjusted OHLCV | Phase 1 |
| Trading simulation | T+1, suspension, limit-up/down (Pitfalls 4, 5, 13) | Order validation pipeline with all A-share rules | Phase 2 |
| Backtesting engine | Look-ahead bias, survivorship bias, execution at limits (Pitfalls 4, 6, 14) | Rolling calculation, point-in-time universe, limit price checks | Phase 3 |
| Full dataset performance | ECharts large mode, dataZoom filtering, SQLite indexes (Pitfalls 10, 11, 12) | large:true, filterMode:'filter', composite indexes | All phases |

## Sources

- ECharts official documentation: [https://echarts.apache.org/en/option.html](https://echarts.apache.org/en/option.html)
- ECharts candlestick-large example: [https://echarts.apache.org/examples/en/editor.html?c=candlestick-large](https://echarts.apache.org/examples/en/editor.html?c=candlestick-large)
- ECharts large dataset optimization: [https://mintlify.com/apache/echarts/examples/large-datasets](https://mintlify.com/apache/echarts/examples/large-datasets)
- ECharts performance tuning guide (CSDN): [https://blog.csdn.net/gitblog_00447/article/details/152348798](https://blog.csdn.net/gitblog_00447/article/details/152348798)
- ECharts memory leak issue #20751: [https://github.com/apache/echarts/issues/20751](https://github.com/apache/echarts/issues/20751)
- pandas EWM adjust parameter docs: [https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html)
- pandas EWM calculation wrong (Stack Overflow): [https://stackoverflow.com/questions/37924377/does-pandas-calculate-ewm-wrong](https://stackoverflow.com/questions/37924377/does-pandas-calculate-ewm-wrong)
- MACD inaccurate with pandas (Reddit r/algotrading): [https://www.reddit.com/r/algotrading/comments/kq17gv/macd_inaccurate_with_pandas/](https://www.reddit.com/r/algotrading/comments/kq17gv/macd_inaccurate_with_pandas/)
- Compute MACD without pandas EWM (Quant StackExchange): [https://quant.stackexchange.com/questions/79602/how-to-compute-moving-average-convergence-divergence-without-using-pandas-ewm-fu](https://quant.stackexchange.com/questions/79602/how-to-compute-moving-average-convergence-divergence-without-using-pandas-ewm-fu)
- tushare Pro documentation: [https://tushare.pro/document/2](https://tushare.pro/document/2)
- A-share market microstructure (ScienceDirect): [https://www.sciencedirect.com/science/article/pii/S0927538X24003032](https://www.sciencedirect.com/science/article/pii/S0927538X24003032)
- Vue memory leak prevention: [https://vuejs.org/v2/cookbook/avoiding-memory-leaks.html](https://vuejs.org/v2/cookbook/avoiding-memory-leaks.html)
- ECharts memory leak disposal: [https://medium.com/@kelvinausoftware/memory-leak-from-echarts-occurs-if-not-properly-disposed-7050c5d93028](https://medium.com/@kelvinausoftware/memory-leak-from-echarts-occurs-if-not-properly-disposed-7050c5d93028)
- Python backtesting strategy MACD+KDJ: [https://medium.com/@rusekd/backtesting-trading-strategies-with-python-ae8e467300ee](https://medium.com/@rusekd/backtesting-trading-strategies-with-python-ae8e467300ee)
