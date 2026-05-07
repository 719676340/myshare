---
status: resolved
phase: 05-strategy-backtesting-module
source: [05-VERIFICATION.md]
started: 2026-05-07T13:00:00Z
updated: 2026-05-07T14:30:00Z
---

## Current Test

All items verified by user.

## Tests

### 1. End-to-End Backtest Run
expected: Select preset strategy, run backtest, see 8 metric cards, equity curve, K-line with markers, trade table
result: PASSED

### 2. Visual Equity Curve Dual Lines
expected: Blue solid line (strategy NAV) and gray dashed line (buy-and-hold baseline) both visible
result: PASSED

### 3. K-line Buy/Sell Markers
expected: Red up-triangle markers on buy dates, green down-triangle markers on sell dates
result: PASSED (after offset fix to avoid overlapping candles)

### 4. Nested Condition Builder
expected: Indented nested group renders correctly, operator toggle works
result: PASSED

### 5. History Row Click Reload
expected: Full results re-display with metrics, charts, trades from saved session
result: PASSED

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

None. All human verification items passed after gap closure and additional UI fixes.
