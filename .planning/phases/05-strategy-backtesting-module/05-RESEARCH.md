# Phase 5: Strategy Backtesting Module - Research

**Researched:** 2026-05-07
**Domain:** Expression parser, condition builder UI, backtest execution engine, A-share trading simulation
**Confidence:** HIGH

## Summary

Phase 5 builds the strategy backtesting module on top of the existing Phase 4 trading practice infrastructure. The key new technical challenge is the **custom indicator expression parser** -- safely evaluating user-defined formulas like `VOL/MA(VOL,20)` against pandas DataFrames of OHLCV data. The recommended approach is a custom AST-based parser using Python's built-in `ast` module with a strict node whitelist, which avoids adding an external dependency and gives full control over allowed operations and functions.

The **condition builder** (AND/OR nested groups) is a UI-only challenge best solved with a recursive Vue component pair (ConditionGroup + ConditionRule), following the standard query builder pattern. No external library needed -- Element Plus provides all the form controls (el-select, el-input, el-button, el-radio-group) required.

The **backtest execution engine** should be a synchronous Python function that iterates daily through OHLCV data, applies user-defined buy/sell conditions, manages positions with FIFO tracking and T+1 enforcement, and computes statistics. It should **reuse PracticeService's fee calculation logic** (commission 0.00025 + stamp tax 0.001) and statistics methods (FIFO trade pairing, equity curve building, win rate, etc.) by extracting shared logic into a utility module or by having BacktestService delegate to the same calculation functions.

**Primary recommendation:** Build a custom AST parser (no external dependency), use recursive Vue components for condition groups, and extract shared calculation logic from PracticeService into reusable functions.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Users input indicator expressions via text input, e.g. `VOL/MA(VOL,20)` or `CLOSE-MA(CLOSE,10)`. System parses and computes daily values
- **D-02:** Expression base fields: OPEN, HIGH, LOW, CLOSE, VOL, AMOUNT, PRE_CLOSE, CHANGE_PCT
- **D-03:** Expression functions: MA(field, period), EMA(field, period), STD(field, period), MAX(field, period), MIN(field, period), REF(field, n), CROSS(field1, field2)
- **D-04:** Expression arithmetic: +, -, *, / with parentheses
- **D-05:** Buy/sell rules each have a group of conditions, combined with nested AND/OR
- **D-06:** Each condition: select indicator + operator + threshold/other indicator
- **D-07:** 10+ operators: >, <, >=, <=, ==, golden cross, death cross, break below, break above, enter overbought, enter oversold
- **D-08:** No built-in stop-loss/take-profit -- buy/sell fully driven by user conditions
- **D-09:** 3 preset strategies as quick-start: MA crossover, volume breakout, MACD divergence. User can modify presets
- **D-10:** Presets are pre-filled expression+condition configs, not hardcoded logic
- **D-11:** Top-bottom layout: config area above, results area below
- **D-12:** Config area has 3 step blocks: 1) Stock & time range 2) Custom indicators (multiple) 3) Buy/sell condition groups
- **D-13:** Click "Run Backtest" to show results below; results area can collapse
- **D-14:** Full 4-part results: 1) Core metric cards (total return, annualized return, max drawdown, trade count, win rate, profit factor, Sharpe ratio, avg holding days) 2) Equity curve (strategy NAV vs buy-and-hold baseline, dual-line) 3) K-line chart with buy/sell markers 4) Trade detail table
- **D-15:** Reuse Phase 4 PracticeStats display pattern: same card styles, same ECharts line chart for equity curve, same buySellMarkers prop
- **D-16:** Equity curve: strategy NAV line (blue solid) + buy-and-hold baseline (gray dashed)

### Claude's Discretion
- Expression parser implementation method (AST parser, safe sandbox eval, etc.)
- Nested condition group UI component design (recursive component vs flat rendering)
- Preset template default parameter values
- Indicator builder real-time preview and error display details
- Result area exact layout and sizing
- Backtest execution sync/async strategy
- Operator precise mathematical definitions and edge case handling

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BACK-01 | Preset strategy templates (MA crossover, volume breakout, MACD divergence) + parameter tuning | D-09/D-10: Presets as pre-filled configs. 3 templates defined as JSON configs of expressions + conditions. User selects template, sees and can modify the underlying config. |
| BACK-02 | User-adjustable strategy parameters (thresholds, lookback days, MA periods) | D-06/D-07: Condition builder lets users set indicator parameters in expressions and threshold values in conditions. Expression functions accept period parameters. |
| BACK-03 | Backtest output metrics: total return, annualized return, max drawdown, trade count, win rate, profit factor, Sharpe ratio, avg holding days | Reuse PracticeService stats calculation pattern. Add annualized return, max drawdown, profit factor, Sharpe ratio calculations. Standard financial formulas. |
| BACK-04 | Equity curve: strategy NAV vs buy-and-hold baseline (dual-line) | PracticeStats equity curve pattern extended with second line. Buy-and-hold = initial_capital * (close_T / close_0). ECharts dual-line chart. |
| BACK-05 | Buy/sell markers on K-line chart | KLineChart already supports `buySellMarkers` prop. BacktestView passes trade list in same format `[{date, type, price}]`. |
| DATA-05 | Custom indicator builder (expression parser for derived indicators) | AST-based expression parser. User types formula, system computes daily values as pandas Series. 8 base fields + 7 functions + 4 arithmetic operators. |
</phase_requirements>

## Standard Stack

### Core (New for This Phase)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python `ast` (stdlib) | 3.12 built-in | Expression parser for custom indicators | Zero-dependency, full control over node whitelist, no supply chain risk. Preferred over simpleeval/asteval to avoid external dependency for a well-scoped problem. |

### Supporting (Already Installed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pandas | 2.3.3 | Expression evaluation on OHLCV DataFrame columns | Core data structure for indicator computation |
| numpy | 2.4.3 | Numerical operations in indicator functions | MA, EMA, STD calculations |
| ta | (installed) | Reference for MA/EMA/STD calculation patterns | Reuse existing calculation approach from indicator_service.py |
| ECharts | 6.0.0 | Equity curve dual-line chart | Via vue-echarts, same pattern as PracticeStats |
| Element Plus | 2.11.7 | Condition builder form controls (el-select, el-input, el-button, el-radio-group) | All UI form elements |
| Pinia | 3.0.4 | Backtest store (config + results state) | Same Option Store pattern as practice.js |

### Alternatives Considered for Expression Parser
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom AST parser | simpleeval (1.0.7) | simpler API but adds dependency, less control over custom function signatures (our functions take pandas Series, not scalars) |
| Custom AST parser | asteval | more features than needed, designed for scientific computing eval, not financial formula parsing |
| Custom AST parser | `eval()` with restricted globals | fundamentally unsafe, even with `__builtins__: {}` there are escape vectors |

**Installation:**
```bash
# No new packages needed -- Python ast module is stdlib
# All other dependencies already installed from previous phases
```

## Architecture Patterns

### Recommended Backend Structure
```
backend/app/
├── services/
│   ├── backtest_service.py     # Main backtest orchestration
│   ├── expression_parser.py    # AST-based formula parser + evaluator
│   └── practice_service.py     # Existing -- extract shared calculation helpers
├── api/
│   └── backtest.py             # REST endpoints for backtest
└── models.py                   # Add BacktestSession, BacktestTrade models
```

### Recommended Frontend Structure
```
frontend/src/
├── views/
│   └── BacktestView.vue            # Main page (replace placeholder)
├── components/backtest/
│   ├── BacktestConfig.vue           # Config area (stock, time, indicators, conditions)
│   ├── IndicatorBuilder.vue         # Single indicator expression input + validation
│   ├── ConditionGroup.vue           # Recursive AND/OR condition group
│   ├── ConditionRule.vue            # Single condition row (indicator + operator + value)
│   ├── BacktestResults.vue          # Results container (collapsible)
│   └── PresetSelector.vue           # Preset strategy template picker
├── stores/
│   └── backtest.js                  # Pinia store for backtest state
└── api/
    └── index.js                     # Add backtest API functions
```

### Pattern 1: AST-Based Expression Parser
**What:** Parse user expressions like `VOL/MA(VOL,20)` into an AST, validate against a whitelist, then evaluate against a pandas DataFrame to produce a daily-value Series.
**When to use:** For all custom indicator expressions.
**Example:**
```python
# Source: Custom design based on Python ast module
import ast
import pandas as pd
import numpy as np

# Allowed AST node types -- strict whitelist
SAFE_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name, ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub,
    ast.Load,
)

# Allowed function names -> implementations (take pandas Series + args)
SAFE_FUNCTIONS = {
    'MA': lambda series, period: series.rolling(window=int(period), min_periods=1).mean(),
    'EMA': lambda series, period: series.ewm(span=int(period), adjust=False).mean(),
    'STD': lambda series, period: series.rolling(window=int(period), min_periods=1).std(),
    'MAX': lambda series, period: series.rolling(window=int(period), min_periods=1).max(),
    'MIN': lambda series, period: series.rolling(window=int(period), min_periods=1).min(),
    'REF': lambda series, n: series.shift(int(n)),
}

def parse_expression(expr_str: str) -> ast.Expression:
    """Parse expression string to AST, validate safety.
    
    Raises SyntaxError if expression is malformed.
    Raises ValueError if expression contains disallowed operations.
    """
    tree = ast.parse(expr_str, mode='eval')
    _validate_ast(tree)
    return tree

def _validate_ast(node):
    """Recursively validate AST nodes against whitelist."""
    if type(node) not in SAFE_NODES:
        raise ValueError(f"Disallowed operation: {type(node).__name__}")
    for child in ast.iter_child_nodes(node):
        _validate_ast(child)
    # Additional: validate Call nodes only call whitelisted functions
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id not in SAFE_FUNCTIONS and node.func.id not in SAFE_FIELDS:
                raise ValueError(f"Unknown function: {node.func.id}")

def evaluate_expression(tree: ast.Expression, df: pd.DataFrame) -> pd.Series:
    """Evaluate validated AST against DataFrame columns.
    
    Returns a pandas Series with one value per row in df.
    """
    namespace = {name: df[col] for name, col in SAFE_FIELDS.items()}
    namespace.update(SAFE_FUNCTIONS)
    return eval(compile(tree, '<expr>', 'eval'), {"__builtins__": {}}, namespace)
```

### Pattern 2: Recursive Condition Group Component
**What:** Two recursive Vue components for building nested AND/OR condition trees.
**When to use:** Buy/sell rule configuration.
**Data model:**
```javascript
// A condition group tree structure
const conditionTree = {
  operator: 'AND',  // 'AND' | 'OR'
  children: [
    { type: 'rule', indicator: 'custom_1', field: 'value', operator: '>', threshold: 0.5 },
    { type: 'rule', indicator: 'CLOSE', field: 'value', operator: 'golden_cross', threshold_indicator: 'MA_CLOSE_20' },
    {
      type: 'group',
      operator: 'OR',
      children: [
        { type: 'rule', indicator: 'custom_2', field: 'value', operator: '>', threshold: 100 },
        { type: 'rule', indicator: 'VOL', field: 'value', operator: '>', threshold_indicator: 'MA_VOL_20' },
      ]
    }
  ]
}
```

### Pattern 3: Backtest Engine Daily Iteration
**What:** Synchronous function that iterates day-by-day through OHLCV data, checks buy/sell conditions, executes trades, tracks positions.
**When to use:** Core backtest execution.
**Example:**
```python
def run_backtest(df: pd.DataFrame, indicators: dict, buy_conditions: dict,
                 sell_conditions: dict, initial_capital: float) -> dict:
    """Run backtest by iterating daily through data.
    
    Args:
        df: OHLCV DataFrame sorted by trade_date
        indicators: Dict of {name: pandas Series} for custom indicators
        buy_conditions: Condition tree for buy signals
        sell_conditions: Condition tree for sell signals
        initial_capital: Starting cash
    
    Returns:
        Dict with trades list, equity curve, and raw statistics
    """
    cash = initial_capital
    positions = []  # FIFO queue of {buy_date, buy_price, shares}
    today_bought = False  # T+1 tracking
    trades = []
    equity_curve = []
    
    for i in range(len(df)):
        row = df.iloc[i]
        date = row['trade_date']
        close = row['close']
        today_bought = False
        
        # Build indicator context for condition evaluation
        context = {name: series.iloc[i] for name, series in indicators.items()}
        context.update({
            'OPEN': row['open'], 'HIGH': row['high'], 'LOW': row['low'],
            'CLOSE': close, 'VOL': row['vol'], 'AMOUNT': row.get('amount', 0),
        })
        
        # Check sell conditions first (if holding positions)
        sellable_shares = sum(p['shares'] for p in positions if p['buy_date'] != date)
        if sellable_shares > 0 and evaluate_conditions(sell_conditions, context, indicators, i):
            # Sell all sellable shares (simplified: full position exit)
            sell_shares = sellable_shares
            amount = sell_shares * close
            commission = round(amount * 0.00025, 2)
            stamp_tax = round(amount * 0.001, 2)
            net = amount - commission - stamp_tax
            cash += net
            # FIFO matching...
            trades.append({...})
            positions = [p for p in positions if p['buy_date'] == date]  # Remove sold
        
        # Check buy conditions (if no position or can add)
        if not positions and evaluate_conditions(buy_conditions, context, indicators, i):
            amount = cash * 0.95  # Use ~95% of cash, leave buffer for fees
            shares = int(amount / close / 100) * 100  # Round to board lot
            if shares >= 100:
                cost = shares * close
                commission = round(cost * 0.00025, 2)
                cash -= (cost + commission)
                positions.append({'buy_date': date, 'buy_price': close, 'shares': shares})
                today_bought = True
                trades.append({...})
        
        # Record equity
        market_value = sum(p['shares'] * close for p in positions)
        equity_curve.append({
            'date': date, 'net_worth': cash + market_value,
            'cash': cash, 'market_value': market_value
        })
    
    return {'trades': trades, 'equity_curve': equity_curve, ...}
```

### Anti-Patterns to Avoid
- **Never use bare `eval()` on user input**: Even with `__builtins__: {}`, Python's eval has known escape vectors. Always parse to AST first and whitelist nodes.
- **Do not run backtest computation as async**: The backtest engine is CPU-bound (iterating thousands of rows), not IO-bound. Running it in an async handler blocks the event loop. Use `asyncio.to_thread()` or run synchronously within a single API call (backtests for single stock over 1-3 years complete in < 1 second).
- **Do not build condition builder with flat component hierarchy**: Nested AND/OR groups require recursive components. A flat list of conditions with a "group" toggle leads to confusing UX.
- **Do not duplicate PracticeService fee/stats logic**: Extract shared helpers (fee calculation, FIFO pairing, stats computation) into reusable functions. Both services call the same helpers.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Moving averages / EMA / STD | Custom loop implementations | pandas `.rolling()`, `.ewm()` | Battle-tested, handles edge cases (min_periods, NaN), vectorized performance |
| A-share fee calculation | New fee functions in BacktestService | Extract `_calc_commission(amount)` and `_calc_stamp_tax(amount)` from PracticeService | Same rules (0.00025 commission, 0.001 stamp tax on sell). Single source of truth. |
| FIFO trade pairing for stats | New FIFO logic | Extract `_pair_trades_fifo()` from PracticeService into shared utility | Same algorithm, avoids divergence. |
| Equity curve building | New curve builder | Extract `_build_equity_curve()` pattern from PracticeService | Same daily iteration logic, adapted for backtest trades. |
| K-line buy/sell markers | New marker system | KLineChart `buySellMarkers` prop (already implemented) | Already renders triangles for buy (red up) and sell (green down). |

**Key insight:** The backtest engine and practice module solve the same problem domain (A-share trading simulation) from different angles (automated vs manual). Shared logic MUST be extracted, not duplicated.

## Common Pitfalls

### Pitfall 1: Expression Parser Injection
**What goes wrong:** User types malicious Python code like `__import__('os').system('rm -rf /')` in the indicator expression field.
**Why it happens:** Using `eval()` directly on user input.
**How to avoid:** Parse with `ast.parse(mode='eval')`, walk the AST tree, reject any node type not in the explicit whitelist. Only allow `BinOp`, `UnaryOp`, `Call`, `Name`, `Constant` nodes. Only allow calls to whitelisted function names.
**Warning signs:** Any use of `eval()` or `exec()` without prior AST validation.

### Pitfall 2: Indicator NaN Propagation
**What goes wrong:** MA(20) returns NaN for the first 19 rows. If a condition checks `custom_1 > 0.5` and custom_1 is NaN, the comparison returns False, which is correct. But CROSS(field1, field2) needs to handle NaN in lookback values.
**Why it happens:** Rolling window functions produce NaN for periods where insufficient data exists.
**How to avoid:** Use `min_periods=1` in rolling calculations so partial windows still produce values. For CROSS, check that both current and previous values are not NaN before declaring a cross. Document that early-period signals may be unreliable.
**Warning signs:** Backtest generates zero trades for the first N days of data.

### Pitfall 3: T+1 Rule in Backtest
**What goes wrong:** Backtest buys and sells on the same day, which is illegal for A-shares.
**Why it happens:** Forgetting to check that shares bought on day T cannot be sold until day T+1.
**How to avoid:** Track `buy_date` for each position lot. Before selling, filter out lots where `buy_date == current_date`. Same logic as PracticeService's T+1 enforcement.
**Warning signs:** Same-day buy-sell pairs appear in trade results.

### Pitfall 4: Division by Zero in Expressions
**What goes wrong:** User writes `CLOSE/MA(CLOSE,5)` and MA returns 0 for edge cases, or `VOL/REF(VOL,1)` when REF returns 0 (stock halted).
**Why it happens:** Real market data contains zero values (halted stocks, no volume).
**How to avoid:** Wrap division operations to return NaN when divisor is 0 (using `np.where(divisor != 0, numerator / divisor, np.nan)`). Document that expressions with division may produce NaN on halted days.
**Warning signs:** Backtest crashes with ZeroDivisionError, or produces inf values in indicator calculations.

### Pitfall 5: Board Lot Rounding
**What goes wrong:** Backtest buys 7 shares of a stock, which is impossible on A-shares (minimum 100 shares, must trade in multiples of 100).
**Why it happens:** Calculating shares as `cash / price` without rounding to board lots.
**How to avoid:** Always calculate shares as `int(amount / price / 100) * 100`. If result < 100, cannot buy. Same as Phase 4 practice module.
**Warning signs:** Trade records show non-multiple-of-100 share counts.

### Pitfall 6: Condition CROSS Operator Edge Cases
**What goes wrong:** CROSS(field1, field2) fires incorrectly when both values are NaN, or fires multiple times for the same cross event.
**Why it happens:** CROSS checks `prev_field1 <= prev_field2 AND curr_field1 > curr_field2`. If prev values are NaN, comparison is unreliable.
**How to avoid:** Only trigger CROSS when both current values AND both previous values are valid (not NaN). Use `pd.notna()` checks.
**Warning signs:** Spurious buy/sell signals on the first days of the backtest period.

### Pitfall 7: Max Drawdown Calculation
**What goes wrong:** Calculating max drawdown as simple `(trough - peak) / peak` on equity curve without properly tracking the running peak.
**Why it happens:** Naive approach of checking all pairs, or using the first value as peak.
**How to avoid:** Track running maximum of equity curve. For each day: `drawdown = (current - running_max) / running_max`. Max drawdown = minimum drawdown value.
**Warning signs:** Max drawdown is 0% when equity curve clearly has declines.

## Code Examples

### Expression Parser: Complete Validation Flow
```python
# Source: Custom design based on Python ast module best practices
import ast
import pandas as pd
import numpy as np
from typing import Dict, Any

# Field name -> DataFrame column mapping
SAFE_FIELDS = {
    'OPEN': 'open', 'HIGH': 'high', 'LOW': 'low', 'CLOSE': 'close',
    'VOL': 'vol', 'AMOUNT': 'amount', 'PRE_CLOSE': 'pre_close', 'CHANGE_PCT': 'change_pct',
}

# Allowed AST node types
SAFE_NODE_TYPES = {
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name, ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.UAdd, ast.USub, ast.Load,
}

def parse_and_validate(expr_str: str) -> tuple[ast.Expression, list[str]]:
    """Parse expression and return (AST, list_of_required_fields).
    
    Raises SyntaxError for malformed expressions.
    Raises ValueError for disallowed operations or unknown names.
    """
    if not expr_str or not expr_str.strip():
        raise ValueError("Expression cannot be empty")
    
    tree = ast.parse(expr_str, mode='eval')
    used_fields = []
    _walk_and_validate(tree, used_fields)
    return tree, used_fields

def _walk_and_validate(node, used_fields: list):
    """Recursively validate AST nodes."""
    if type(node) not in SAFE_NODE_TYPES:
        raise ValueError(f"Disallowed syntax: {type(node).__name__}")
    
    if isinstance(node, ast.Name):
        if node.id in SAFE_FIELDS:
            if node.id not in used_fields:
                used_fields.append(node.id)
        elif node.id not in ('MA', 'EMA', 'STD', 'MAX', 'MIN', 'REF', 'CROSS'):
            raise ValueError(f"Unknown variable: {node.id}")
    
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Function calls must use simple names (no dot notation)")
        func_name = node.func.id
        allowed_funcs = {'MA', 'EMA', 'STD', 'MAX', 'MIN', 'REF', 'CROSS'}
        if func_name not in allowed_funcs:
            raise ValueError(f"Unknown function: {func_name}")
        # Validate argument count
        arg_count = len(node.args)
        if func_name == 'CROSS' and arg_count != 2:
            raise ValueError(f"CROSS requires exactly 2 arguments, got {arg_count}")
        elif func_name in ('MA', 'EMA', 'STD', 'MAX', 'MIN', 'REF') and arg_count != 2:
            raise ValueError(f"{func_name} requires exactly 2 arguments, got {arg_count}")
        # Check keyword args not used
        if node.keywords:
            raise ValueError("Keyword arguments not supported")
    
    for child in ast.iter_child_nodes(node):
        _walk_and_validate(child, used_fields)

def evaluate_expression(tree: ast.Expression, df: pd.DataFrame) -> pd.Series:
    """Evaluate a validated expression AST against a DataFrame.
    
    Returns a pandas Series with one value per row.
    NaN values are preserved (e.g., MA(20) has NaN for first 19 rows).
    """
    # Build namespace with field Series
    namespace = {}
    for name, col in SAFE_FIELDS.items():
        if col in df.columns:
            namespace[name] = df[col]
    
    # Add safe functions
    namespace['MA'] = lambda series, period: series.rolling(window=int(period), min_periods=1).mean()
    namespace['EMA'] = lambda series, period: series.ewm(span=int(period), adjust=False).mean()
    namespace['STD'] = lambda series, period: series.rolling(window=int(period), min_periods=1).std()
    namespace['MAX'] = lambda series, period: series.rolling(window=int(period), min_periods=1).max()
    namespace['MIN'] = lambda series, period: series.rolling(window=int(period), min_periods=1).min()
    namespace['REF'] = lambda series, n: series.shift(int(n))
    namespace['CROSS'] = lambda a, b: (a.shift(1) <= b.shift(1)) & (a > b)  # Boolean Series
    
    return eval(compile(tree, '<expr>', 'eval'), {"__builtins__": {}}, namespace)
```

### Condition Evaluation: Recursive Tree Walker
```python
def evaluate_condition_tree(tree: dict, row_values: dict, indicator_series: dict, idx: int) -> bool:
    """Recursively evaluate a condition tree against current day's values.
    
    Args:
        tree: Condition tree with 'operator' and 'children' keys
        row_values: Dict of current-day values for base fields and indicators
        indicator_series: Dict of {name: full pandas Series} for lookback operations
        idx: Current row index (for lookback operations like CROSS)
    
    Returns:
        Boolean indicating if conditions are met
    """
    if tree.get('type') == 'rule':
        return _evaluate_single_rule(tree, row_values, indicator_series, idx)
    
    operator = tree['operator']  # 'AND' or 'OR'
    children = tree['children']
    
    if operator == 'AND':
        return all(evaluate_condition_tree(child, row_values, indicator_series, idx) for child in children)
    elif operator == 'OR':
        return any(evaluate_condition_tree(child, row_values, indicator_series, idx) for child in children)
    
    return False

def _evaluate_single_rule(rule: dict, row_values: dict, indicator_series: dict, idx: int) -> bool:
    """Evaluate a single condition rule."""
    left_val = row_values.get(rule['indicator'])
    op = rule['operator']
    
    # Get right-hand value
    if rule.get('threshold_indicator'):
        right_val = row_values.get(rule['threshold_indicator'])
    else:
        right_val = rule.get('threshold')
    
    if left_val is None or right_val is None:
        return False
    if pd.isna(left_val) or pd.isna(right_val):
        return False
    
    # Standard comparison operators
    if op == '>': return left_val > right_val
    if op == '<': return left_val < right_val
    if op == '>=': return left_val >= right_val
    if op == '<=': return left_val <= right_val
    if op == '==': return abs(left_val - right_val) < 1e-9
    
    # Cross operators (need lookback via series)
    if op == 'golden_cross':
        series_left = indicator_series.get(rule['indicator'])
        series_right = indicator_series.get(rule['threshold_indicator'])
        if series_left is None or series_right is None or idx < 1:
            return False
        prev_left = series_left.iloc[idx - 1]
        prev_right = series_right.iloc[idx - 1]
        if pd.isna(prev_left) or pd.isna(prev_right):
            return False
        return prev_left <= prev_right and left_val > right_val
    
    if op == 'death_cross':
        series_left = indicator_series.get(rule['indicator'])
        series_right = indicator_series.get(rule['threshold_indicator'])
        if series_left is None or series_right is None or idx < 1:
            return False
        prev_left = series_left.iloc[idx - 1]
        prev_right = series_right.iloc[idx - 1]
        if pd.isna(prev_left) or pd.isna(prev_right):
            return False
        return prev_left >= prev_right and left_val < right_val
    
    # Break operators (similar to cross but with price context)
    if op == 'break_above':
        return _check_break(rule, indicator_series, idx, 'above')
    if op == 'break_below':
        return _check_break(rule, indicator_series, idx, 'below')
    
    # Overbought/oversold zones
    if op == 'enter_overbought':
        return left_val > right_val and _was_below(rule['indicator'], indicator_series, idx, right_val)
    if op == 'enter_oversold':
        return left_val < right_val and _was_above(rule['indicator'], indicator_series, idx, right_val)
    
    return False
```

### Preset Strategy Templates (JSON Config)
```javascript
// Preset strategy definitions -- these are just data, not code
const PRESET_STRATEGIES = [
  {
    name: 'MA交叉策略',
    description: '短期均线上穿长期均线买入，下穿卖出',
    indicators: [
      { name: 'MA5', expression: 'MA(CLOSE,5)' },
      { name: 'MA20', expression: 'MA(CLOSE,20)' }
    ],
    buy_conditions: {
      operator: 'AND', children: [
        { type: 'rule', indicator: 'MA5', operator: 'golden_cross', threshold_indicator: 'MA20' }
      ]
    },
    sell_conditions: {
      operator: 'AND', children: [
        { type: 'rule', indicator: 'MA5', operator: 'death_cross', threshold_indicator: 'MA20' }
      ]
    }
  },
  {
    name: '放量突破策略',
    description: '成交量突破20日均量且收盘价上涨时买入',
    indicators: [
      { name: 'VOL_RATIO', expression: 'VOL/MA(VOL,20)' },
      { name: 'CHANGE', expression: 'CHANGE_PCT' }
    ],
    buy_conditions: {
      operator: 'AND', children: [
        { type: 'rule', indicator: 'VOL_RATIO', operator: '>', threshold: 2.0 },
        { type: 'rule', indicator: 'CHANGE', operator: '>', threshold: 0 }
      ]
    },
    sell_conditions: {
      operator: 'AND', children: [
        { type: 'rule', indicator: 'CHANGE', operator: '<', threshold: -3 }
      ]
    }
  },
  {
    name: 'MACD背离策略',
    description: 'MACD金叉买入，死叉卖出',
    indicators: [
      { name: 'MACD_DIF', expression: 'EMA(CLOSE,12)-EMA(CLOSE,26)' },
      { name: 'MACD_DEA', expression: 'EMA(MACD_DIF,9)' }  // Note: recursive reference -- needs special handling
    ],
    buy_conditions: {
      operator: 'AND', children: [
        { type: 'rule', indicator: 'MACD_DIF', operator: 'golden_cross', threshold_indicator: 'MACD_DEA' }
      ]
    },
    sell_conditions: {
      operator: 'AND', children: [
        { type: 'rule', indicator: 'MACD_DIF', operator: 'death_cross', threshold_indicator: 'MACD_DEA' }
      ]
    }
  }
]
```

**Important note on recursive indicator references:** The MACD preset above uses `EMA(MACD_DIF,9)` which references another custom indicator. The backend must support evaluating indicators in dependency order. If indicator B depends on indicator A, evaluate A first and add its Series to the DataFrame before evaluating B. Topological sort on dependencies handles this. For the initial implementation, detect circular dependencies and reject them.

### Equity Curve with Buy-and-Hold Baseline
```javascript
// ECharts option for dual-line equity curve (extends PracticeStats pattern)
const equityCurveOption = computed(() => {
  const curve = backtestStore.results?.equity_curve || []
  const strategyData = curve.map(d => d.net_worth)
  const baselineData = curve.map(d => d.baseline_worth)  // computed by backend
  const dates = curve.map(d => d.date)
  
  return {
    backgroundColor: '#131722',
    grid: { left: 65, right: 20, top: 30, bottom: 30 },
    legend: {
      data: ['策略净值', '买入持有'],
      top: 5,
      textStyle: { color: '#787b86', fontSize: 11 }
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { color: '#787b86', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#787b86', fontSize: 11, formatter: v => (v / 10000).toFixed(0) + '万' },
      splitLine: { lineStyle: { color: '#2a2e39' } }
    },
    series: [
      {
        name: '策略净值',
        type: 'line',
        data: strategyData,
        lineStyle: { color: '#2962ff', width: 2 },  // blue solid
        symbol: 'none'
      },
      {
        name: '买入持有',
        type: 'line',
        data: baselineData,
        lineStyle: { color: '#787b86', width: 1, type: 'dashed' },  // gray dashed
        symbol: 'none'
      }
    ]
  }
})
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `eval()` with restricted builtins | AST parsing + whitelist validation | Well-established pattern since Python 3.x | Fundamentally safer. No escape vectors when done correctly. |
| Flat condition list | Recursive AND/OR tree components | Standard query builder UI pattern | Much more expressive condition logic with nested groups. |
| Separate backtest engine per strategy | Single engine + configurable conditions | Common in modern backtest frameworks | One engine handles all strategies via condition trees. |
| Store backtest results in DB per trade | Compute on-the-fly, return all results in single API response | Sufficient for local single-user app | Simpler architecture. No need for persistent backtest storage (but can add later). |

**Deprecated/outdated:**
- `simpleeval` approach: viable but adds dependency for a problem Python's stdlib `ast` solves perfectly.
- Backtrader/zipline frameworks: massive overkill for this project's scope. Custom engine is simpler and more educational.

## Open Questions

1. **Should backtest results be persisted in the database?**
   - What we know: The CONTEXT.md mentions "list history" as an integration point. The backend models reference BacktestSession.
   - What's unclear: Whether the user wants to keep a history of past backtests or just see the current result.
   - Recommendation: Store backtest configs and results in DB (new tables). This allows "re-run this backtest" and history browsing. Model it similar to PracticeSession/Trade pattern.

2. **MACD preset recursive indicator reference (`EMA(MACD_DIF,9)`)**
   - What we know: The expression parser currently evaluates one expression against the base DataFrame. Cross-indicator references are not yet designed.
   - What's unclear: Whether all user expressions will only reference base fields, or if indicator-to-indicator references should be supported.
   - Recommendation: Support it by evaluating indicators in dependency order. Add a `depends_on` field to each indicator config. Detect circular references. For the MACD preset, this is essential since MACD_DEA = EMA(MACD_DIF, 9).

3. **Position sizing in backtest**
   - What we know: Practice module uses specific share counts. Backtest needs a systematic approach.
   - What's unclear: Full position (all available cash) or fixed percentage per trade?
   - Recommendation: Use full position (all available cash, rounded to board lot) as the default. This matches the simplest and most common backtest approach. Can be made configurable in v2.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | Backend runtime | Yes | 3.12.x | -- |
| FastAPI | API endpoints | Yes | 0.136.1 | -- |
| SQLAlchemy | DB models | Yes | 2.0.49 | -- |
| pandas | Indicator calculation | Yes | 2.3.3 | -- |
| numpy | Numerical math | Yes | 2.4.3 | -- |
| Node.js | Frontend dev server | Yes | -- | -- |
| Vue 3 | Frontend framework | Yes | 3.5.13 | -- |
| ECharts | Charting | Yes | 6.0.0 | -- |
| vue-echarts | Vue-ECharts bridge | Yes | 8.0.1 | -- |
| Element Plus | UI components | Yes | 2.11.7 | -- |
| Pinia | State management | Yes | 3.0.4 | -- |
| Python `ast` (stdlib) | Expression parser | Yes | 3.12 built-in | -- |
| SQLite | Local database | Yes | 3.x built-in | -- |
| Alembic | DB migrations | Not installed | -- | Use `create_all()` on startup (project pattern) |

**Missing dependencies with no fallback:**
- None -- all required dependencies are available.

**Missing dependencies with fallback:**
- Alembic not installed: project uses `Base.metadata.create_all()` in `init_db()` for schema creation. New models will auto-create tables on server restart. Acceptable for local development.

## Sources

### Primary (HIGH confidence)
- Existing codebase: `backend/app/services/practice_service.py` -- fee calculation, FIFO pairing, equity curve building, stats computation patterns
- Existing codebase: `backend/app/services/indicator_service.py` -- indicator calculation with pandas/ta patterns
- Existing codebase: `frontend/src/components/KLineChart.vue` -- buySellMarkers prop implementation
- Existing codebase: `frontend/src/components/practice/PracticeStats.vue` -- metric cards, equity curve, trade table patterns
- Python `ast` module documentation (docs.python.org) -- AST node types, parse modes, compile/eval

### Secondary (MEDIUM confidence)
- [Safe expression parser in Python - Stack Overflow](https://stackoverflow.com/questions/3582403/safe-expression-parser-in-python) -- AST whitelist approach validation
- [Using an AST to make eval() secure - Medium](https://medium.com/@laurentkubaski/using-an-ast-to-make-eval-secure-211545f53e6c) -- AST node validation pattern
- [simpleeval GitHub](https://github.com/danthedeckie/simpleeval) -- Evaluated as alternative, decided against for this project
- Vue 3 query builder patterns -- Recursive component architecture for AND/OR groups (standard pattern)

### Tertiary (LOW confidence)
- Preset strategy parameter values -- Based on common technical analysis defaults, may need user feedback

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new external dependencies, all from Python stdlib + existing installed packages
- Architecture: HIGH -- follows established project patterns (Pinia stores, FastAPI routes, ECharts components, SQLAlchemy models)
- Pitfalls: HIGH -- well-understood domain (expression parsing, trading simulation) with clear solutions
- Expression parser: HIGH -- Python `ast` module is well-documented and widely used for safe eval patterns
- Condition builder UI: HIGH -- standard recursive component pattern in Vue

**Research date:** 2026-05-07
**Valid until:** 2026-06-07 (stable domain, no fast-moving dependencies)
