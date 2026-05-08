---
phase: quick
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/services/practice_service.py
  - frontend/src/components/practice/PracticeStats.vue
autonomous: true
must_haves:
  truths:
    - "User can see max drawdown (percentage and amount) in the stats summary"
    - "User can see average win/loss amount and largest win/loss trade"
    - "User can see average holding period and profit factor"
    - "Equity curve shows a baseline reference line at initial capital"
    - "Trade pairs table has a running cumulative P&L column"
    - "Key performance metrics are visually prominent with color-coded P&L"
  artifacts:
    - path: "backend/app/services/practice_service.py"
      provides: "Enhanced get_stats with max drawdown, avg win/loss, profit factor, per-trade cumulative P&L"
    - path: "frontend/src/components/practice/PracticeStats.vue"
      provides: "Redesigned stats page with expanded metric cards, baseline on equity curve, cumulative P&L in trade table"
  key_links:
    - from: "frontend/src/components/practice/PracticeStats.vue"
      to: "backend/app/api/practice.py GET /stats"
      via: "getPracticeStats API call, practiceStore.stats"
      pattern: "practiceStore\\.stats"
---

<objective>
Optimize the post-practice statistics display to give users a clear, comprehensive view of their trading performance and P&L impact.

Purpose: The current stats page shows basic metrics (return %, trade count, win rate, fees) but lacks key performance indicators that help users understand the magnitude and risk of their trading decisions. Users need to see drawdown, win/loss distribution, and cumulative P&L progression to evaluate their performance.

Output: Enhanced PracticeStats.vue with richer metrics, improved equity curve with baseline, and a trade table with cumulative P&L tracking.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/STATE.md
@backend/app/services/practice_service.py
@backend/app/api/practice.py
@frontend/src/components/practice/PracticeStats.vue
@frontend/src/stores/practice.js

<interfaces>
<!-- Backend get_stats response (current shape) -->
```python
# GET /practice/sessions/{id}/stats returns:
{
    "ts_code": str,
    "start_date": str, "end_date": str,
    "initial_capital": float,
    "final_capital": float,
    "total_return": float,
    "total_return_pct": float,
    "total_trades": int,
    "win_count": int, "loss_count": int,
    "win_rate": float,
    "total_commission": float, "total_stamp_tax": float,
    "trade_pairs": [{ "buy_date", "buy_price", "buy_shares", "sell_date", "sell_price", "sell_shares", "profit_amount", "profit_pct", "holding_days" }],
    "equity_curve": [{ "date", "net_worth", "cash", "market_value" }],
    "all_trades": [{ "id", "trade_type", "ts_code", "trade_date", "shares", "price", "amount", "commission", "stamp_tax" }]
}
```

<!-- Frontend store practice.stats consumed by PracticeStats.vue -->
practiceStore.stats = stats  // set in endSession() via getPracticeStats()

<!-- Style variables (A-share convention: red=up, green=down) -->
$color-up: #ef5350 (red, profit)
$color-down: #26a69a (green, loss)
$bg-primary: #131722, $bg-secondary: #1e222d
$text-primary: #d1d4dc, $text-secondary: #787b86
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Enhance backend stats with drawdown, win/loss distribution, and profit factor</name>
  <files>backend/app/services/practice_service.py</files>
  <action>
Add the following computed metrics to the `get_stats` method's return dict in PracticeService:

1. **Max drawdown** — From the equity_curve, compute the maximum peak-to-trough decline:
   - Track running peak of net_worth
   - For each point, compute drawdown = (peak - net_worth) / peak
   - Record max_drawdown_pct (as percentage, e.g. -12.34) and max_drawdown_amount (peak - trough dollar amount)
   - Also record the drawdown start date (peak date) and end date (trough date) as `max_drawdown_start` and `max_drawdown_end`

2. **Win/loss distribution** — From trade_pairs:
   - `avg_win_amount`: average profit_amount for trades where profit_amount > 0 (0 if no wins)
   - `avg_loss_amount`: average profit_amount for trades where profit_amount < 0 (0 if no losses)
   - `max_win_amount`: highest profit_amount
   - `max_loss_amount`: lowest profit_amount (most negative)

3. **Profit factor** — gross_profit / gross_loss:
   - `gross_profit`: sum of positive profit_amounts
   - `gross_loss`: absolute value of sum of negative profit_amounts
   - `profit_factor`: gross_profit / gross_loss (Infinity if gross_loss == 0, 0 if no trades)

4. **Average holding period** — average of holding_days across all trade_pairs

5. **Per-trade cumulative P&L** — Add a `cumulative_pnl` field to each item in the trade_pairs list:
   - Running sum of profit_amount across trade_pairs in order
   - This lets the frontend show cumulative P&L progression in the trade table

Add all new fields to the return dict at the end of `get_stats`, alongside the existing fields. Do NOT remove or rename any existing fields.
  </action>
  <verify>curl -s http://localhost:8000/api/practice/sessions/1/stats | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'max_drawdown_pct' in d; assert 'avg_win_amount' in d; assert 'profit_factor' in d; assert 'avg_holding_days' in d; assert all('cumulative_pnl' in p for p in d.get('trade_pairs',[])); print('OK')" 2>&1 || echo "Backend not running or no session 1 - check code manually"</verify>
  <done>get_stats returns 10+ new metrics: max_drawdown_pct, max_drawdown_amount, max_drawdown_start, max_drawdown_end, avg_win_amount, avg_loss_amount, max_win_amount, max_loss_amount, profit_factor, gross_profit, gross_loss, avg_holding_days, and cumulative_pnl on each trade_pair</done>
</task>

<task type="auto">
  <name>Task 2: Redesign PracticeStats.vue with expanded metrics and improved visualizations</name>
  <files>frontend/src/components/practice/PracticeStats.vue</files>
  <action>
Enhance the PracticeStats component to display the new metrics with clear visual hierarchy. Keep the existing structure (header, metrics row, equity curve, K-line, trade table) but enrich each section:

**1. Expanded metrics cards** — Replace the current single-row metrics with a two-tier layout:

Tier 1 (top, large cards — most important):
- Total return % (existing, keep prominent with large font)
- Max drawdown % (new, show in red/green color, format like "-12.34%")
- Win rate (existing, keep)
- Profit factor (new, format to 2 decimal places, e.g. "2.15")

Tier 2 (below, smaller cards — supporting detail):
- Final capital (existing)
- Total trades (existing)
- Avg holding period (new, show as "X.X天")
- Avg win amount (new, green color for context)
- Avg loss amount (new, red color for context)
- Total fees (existing, combine commission + stamp_tax)
- Max single win (new, colored green)
- Max single loss (new, colored red)

Each metric card should use the existing `.metric-card` pattern but arrange in two rows with flex-wrap. Use `$color-up` (red) for profit and `$color-down` (green) for loss throughout, following A-share convention.

**2. Equity curve with baseline** — Add a horizontal reference line at initial_capital on the equity curve chart:
- Use ECharts `markLine` on the series to draw a dashed horizontal line at initial_capital value
- Style: dashed line, color `$text-secondary` (#787b86), label "初始资金"
- This makes it immediately obvious whether the user is above or below breakeven

**3. Trade pairs table with cumulative P&L** — Add a "累计盈亏" (cumulative P&L) column at the end of the trade pairs table:
- Display `row.cumulative_pnl` with +/- prefix
- Color code: positive = `$color-up`, negative = `$color-down`
- This shows the user how their P&L accumulated over time, making the impact of each trade visible

**4. Drawdown info** — Below the equity curve, add a small text line showing the drawdown period:
- "最大回撤: {max_drawdown_pct}% ({max_drawdown_start} ~ {max_drawdown_end})" 
- Color: `$color-down` since drawdown is always negative
- Only show if trade_pairs exist (skip if no trades)

All formatting functions (formatMoney, formatPct) are already defined in the component. Reuse them. Follow existing patterns for metric cards, chart sections, and table columns.
  </action>
  <verify>cd "/Users/heqijie/交易学习/量价策略 web/frontend" && npm run build 2>&1 | tail -5</verify>
  <done>PracticeStats shows 12+ metric cards in two tiers, equity curve with initial capital baseline, trade table with cumulative P&L column, and drawdown period info. All values properly formatted and color-coded per A-share convention.</done>
</task>

</tasks>

<verification>
1. Backend: `get_stats` returns all new fields without breaking existing response shape
2. Frontend: `npm run build` succeeds with no errors
3. Visual: Stats page renders with expanded metrics, baseline on equity curve, cumulative P&L in table
</verification>

<success_criteria>
- Backend `get_stats` computes max drawdown, win/loss distribution, profit factor, avg holding days, and cumulative P&L per trade
- PracticeStats.vue displays these metrics in a visually clear two-tier card layout
- Equity curve has a dashed baseline at initial capital
- Trade table has a cumulative P&L column with color coding
- Drawdown period is shown below the equity curve
- No existing functionality is broken
</success_criteria>

<output>
After completion, create `.planning/quick/260508-wtu/260508-wtu-SUMMARY.md`
</output>
