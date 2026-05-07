# Phase 5: Strategy Backtesting Module - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-07
**Phase:** 05-strategy-backtesting-module
**Areas discussed:** Scope direction, Page layout, Indicator builder, Condition combiner, Preset templates, Results display, Risk management, Condition operators

---

## Scope Direction

| Option | Description | Selected |
|--------|-------------|----------|
| Preset templates + parameter tuning | BACK-01 original scope: pick a template, adjust params | |
| Condition combiner | Select base strategy, then combine buy/sell conditions freely | |
| Fully custom rules | Define own indicators with expressions + combine conditions + no preset limits | ✓ |

**User's choice:** Fully custom rules — 指标创建+条件组合
**Notes:** User wants to define their own quantitative rules and see returns. DATA-05 (custom indicator builder, deferred to v2) pulled forward into Phase 5. Original BACK-01 preset templates kept as quick-start options.

---

## Custom Indicator Builder

| Option | Description | Selected |
|--------|-------------|----------|
| Visual builder | Dropdown to select fields/indicators, buttons for arithmetic ops | |
| Expression input box | Text input for expressions like `VOL/MA(VOL,20)` | ✓ |

**User's choice:** Expression input box — more flexible, power-user friendly
**Notes:** Supports basic fields (OPEN, HIGH, LOW, CLOSE, VOL, etc.), functions (MA, EMA, STD, REF, CROSS, etc.), and arithmetic ops (+, -, *, /).

---

## Condition Combination

| Option | Description | Selected |
|--------|-------------|----------|
| Row-based condition table | Each condition one row, all connected by AND. Simple and clear | |
| Nested condition groups | Support AND/OR nesting with groups. More flexible | ✓ |

**User's choice:** Nested condition groups — support AND/OR nesting
**Notes:** Each condition: indicator + operator + threshold/indicator. Operators include >, <, >=, <=, ==, crossover, crossunder, break above, break below, etc. (10+ operators).

---

## Page Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Top-bottom layout | Config area on top, results below. Click "Run" to see results | ✓ |
| Left-right split | K-line on left, config/results panel on right (like Practice module) | |

**User's choice:** Top-bottom layout
**Notes:** Config area has three blocks: 1) stock selection + time range, 2) custom indicators, 3) buy/sell conditions. Results below after running.

---

## Preset Templates

| Option | Description | Selected |
|--------|-------------|----------|
| Preset + custom coexist | Presets as quick-start, user can modify or start from blank | ✓ |
| Pure custom, no presets | No templates, always start from blank | |

**User's choice:** Preset + custom coexist
**Notes:** 3 presets (MA crossover, volume breakout, MACD divergence) as quick-start. Presets are pre-filled expressions + conditions, user can modify.

---

## Results Display

| Option | Description | Selected |
|--------|-------------|----------|
| Full four parts | Metrics cards + equity curve (strategy vs benchmark) + K-line with markers + trade table | ✓ |
| Simplified two parts | Only metrics cards + equity curve | |

**User's choice:** Full four parts — reuses Phase 4 PracticeStats pattern
**Notes:** Equity curve shows strategy net value vs buy-and-hold benchmark (two lines). K-line marks buy/sell points. Metrics: total return, annualized return, max drawdown, trade count, win rate, profit factor, Sharpe ratio, avg holding period.

---

## Risk Management

| Option | Description | Selected |
|--------|-------------|----------|
| Condition-only buy/sell | No built-in stop-loss/take-profit. User writes conditions | ✓ |
| Add stop-loss/take-profit | Extra options for fixed stop-loss/take-profit percentages | |

**User's choice:** Condition-only buy/sell — simpler, more flexible
**Notes:** Users who want stop-loss can write it as a sell condition.

---

## Condition Operators

| Option | Description | Selected |
|--------|-------------|----------|
| 10+ operators | >, <, >=, <=, ==, crossover, crossunder, break above, break below, overbought, oversold | ✓ |
| 5 core operators | >, <, ==, crossover, crossunder only | |

**User's choice:** 10+ operators — comprehensive coverage

---

## Claude's Discretion

- Expression parser implementation approach
- Nested condition group UI component design
- Preset template default parameter values
- Indicator builder real-time preview and error display
- Backtest execution sync/async strategy
- Operator mathematical definitions and edge cases

## Deferred Ideas

None — discussion stayed within phase scope
