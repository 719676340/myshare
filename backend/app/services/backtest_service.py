"""Backtest engine for strategy backtesting module.

Runs day-by-day backtest simulation with A-share rules (T+1, fees, board lots),
evaluates buy/sell conditions from expression-based indicators, and computes
comprehensive performance metrics.
"""

import json
import logging
import math
from datetime import datetime

import numpy as np
import pandas as pd
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DailyBar, BacktestSession, BacktestTrade, Stock
from app.services.expression_parser import (
    parse_and_validate,
    evaluate_expression,
    evaluate_expression_with_custom,
    SAFE_FIELDS,
    SAFE_FUNCTIONS,
)

logger = logging.getLogger(__name__)

# Fee constants (same as PracticeService)
COMMISSION_RATE = 0.00025  # 0.025%
STAMP_TAX_RATE = 0.001  # 0.1% on sells only


class BacktestService:
    """Strategy backtest engine with condition evaluation and statistics."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session.

        Args:
            db: Async SQLAlchemy session.
        """
        self.db = db

    # D-09/D-10: Preset strategy templates as data configs
    PRESET_STRATEGIES = [
        {
            "id": "ma_crossover",
            "name": "MA交叉策略",
            "description": "短期均线上穿长期均线买入，下穿卖出",
            "indicators": [
                {"name": "MA5", "expression": "MA(CLOSE,5)"},
                {"name": "MA20", "expression": "MA(CLOSE,20)"},
            ],
            "buy_conditions": {
                "operator": "AND",
                "children": [
                    {
                        "type": "rule",
                        "indicator": "MA5",
                        "operator": "golden_cross",
                        "threshold_indicator": "MA20",
                    }
                ],
            },
            "sell_conditions": {
                "operator": "AND",
                "children": [
                    {
                        "type": "rule",
                        "indicator": "MA5",
                        "operator": "death_cross",
                        "threshold_indicator": "MA20",
                    }
                ],
            },
        },
        {
            "id": "volume_breakout",
            "name": "放量突破策略",
            "description": "成交量突破20日均量2倍且收盘价上涨时买入，跌幅超3%卖出",
            "indicators": [
                {"name": "VOL_RATIO", "expression": "VOL/MA(VOL,20)"},
                {"name": "CHANGE", "expression": "CHANGE_PCT"},
            ],
            "buy_conditions": {
                "operator": "AND",
                "children": [
                    {
                        "type": "rule",
                        "indicator": "VOL_RATIO",
                        "operator": ">",
                        "threshold": 2.0,
                    },
                    {
                        "type": "rule",
                        "indicator": "CHANGE",
                        "operator": ">",
                        "threshold": 0,
                    },
                ],
            },
            "sell_conditions": {
                "operator": "AND",
                "children": [
                    {
                        "type": "rule",
                        "indicator": "CHANGE",
                        "operator": "<",
                        "threshold": -3,
                    }
                ],
            },
        },
        {
            "id": "macd_divergence",
            "name": "MACD背离策略",
            "description": "MACD金叉买入，死叉卖出",
            "indicators": [
                {"name": "MACD_DIF", "expression": "EMA(CLOSE,12)-EMA(CLOSE,26)"},
                {"name": "MACD_DEA", "expression": "EMA(MACD_DIF,9)"},
            ],
            "buy_conditions": {
                "operator": "AND",
                "children": [
                    {
                        "type": "rule",
                        "indicator": "MACD_DIF",
                        "operator": "golden_cross",
                        "threshold_indicator": "MACD_DEA",
                    }
                ],
            },
            "sell_conditions": {
                "operator": "AND",
                "children": [
                    {
                        "type": "rule",
                        "indicator": "MACD_DIF",
                        "operator": "death_cross",
                        "threshold_indicator": "MACD_DEA",
                    }
                ],
            },
        },
    ]

    async def run_backtest(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
        initial_capital: float,
        indicators_config: list,
        buy_conditions: dict,
        sell_conditions: dict,
        stock_name: str = "",
    ) -> dict:
        """Run a complete backtest simulation.

        Args:
            ts_code: Stock code (e.g. "000001.SZ").
            start_date: Backtest start date YYYYMMDD.
            end_date: Backtest end date YYYYMMDD.
            initial_capital: Starting cash amount.
            indicators_config: List of {name, expression} dicts for custom indicators.
            buy_conditions: Condition tree for buy signals.
            sell_conditions: Condition tree for sell signals.
            stock_name: Display name for the stock.

        Returns:
            Dict with session_id, trades, equity_curve, baseline_curve, statistics.

        Raises:
            ValueError: If no data, invalid expressions, or circular dependencies.
        """
        # Fetch daily bar data
        bars_result = await self.db.execute(
            select(DailyBar)
            .where(
                DailyBar.ts_code == ts_code,
                DailyBar.trade_date >= start_date,
                DailyBar.trade_date <= end_date,
            )
            .order_by(DailyBar.trade_date.asc())
        )
        bars = bars_result.scalars().all()
        if not bars:
            raise ValueError("该时间范围内无可用数据")

        # Convert to DataFrame
        data = []
        for b in bars:
            data.append(
                {
                    "trade_date": b.trade_date,
                    "open": b.open,
                    "high": b.high,
                    "low": b.low,
                    "close": b.close,
                    "vol": b.vol,
                    "amount": b.amount or 0,
                    "pre_close": b.pre_close or b.close,
                    "change_pct": b.change_pct or 0,
                }
            )
        df = pd.DataFrame(data)

        # Parse and validate all indicator expressions
        parsed_indicators = []
        for ind in indicators_config:
            tree, fields = parse_and_validate(ind["expression"])
            parsed_indicators.append(
                {
                    "name": ind["name"],
                    "expression": ind["expression"],
                    "tree": tree,
                    "fields": fields,
                }
            )

        # Build dependency graph and topological sort
        eval_order = self._topological_sort(parsed_indicators)

        # Evaluate indicators in dependency order
        custom_series = {}
        for idx in eval_order:
            ind = parsed_indicators[idx]
            series = evaluate_expression_with_custom(
                ind["tree"], df, custom_series
            )
            # Add to both DataFrame and custom_series for subsequent indicators
            df[ind["name"]] = series
            custom_series[ind["name"]] = series

        # Run the daily simulation
        trades = self._run_simulation(
            df, initial_capital, buy_conditions, sell_conditions, custom_series
        )

        # Build equity curve
        equity_curve = self._build_equity_curve(df, trades, initial_capital)

        # Build buy-and-hold baseline curve
        baseline_curve = self._build_baseline_curve(df, initial_capital)

        # Calculate statistics
        statistics = self._calc_statistics(
            trades, equity_curve, initial_capital, start_date, end_date
        )

        # Save to database
        session_record = BacktestSession(
            ts_code=ts_code,
            stock_name=stock_name,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            indicators_config=json.dumps(indicators_config, ensure_ascii=False),
            buy_conditions=json.dumps(buy_conditions, ensure_ascii=False),
            sell_conditions=json.dumps(sell_conditions, ensure_ascii=False),
            statistics=json.dumps(statistics, ensure_ascii=False),
            status="completed",
            created_at=datetime.now().isoformat(),
        )
        self.db.add(session_record)
        await self.db.flush()

        # Save trade records
        for t in trades:
            trade_record = BacktestTrade(
                session_id=session_record.id,
                trade_type=t["trade_type"],
                trade_date=t["trade_date"],
                shares=t["shares"],
                price=t["price"],
                amount=t["amount"],
                commission=t["commission"],
                stamp_tax=t["stamp_tax"],
            )
            self.db.add(trade_record)

        await self.db.commit()

        return {
            "session_id": session_record.id,
            "trades": trades,
            "equity_curve": equity_curve,
            "baseline_curve": baseline_curve,
            "statistics": statistics,
        }

    def _topological_sort(self, parsed_indicators: list) -> list:
        """Topological sort of indicators by dependency order.

        Scans expressions for references to other indicator names and
        produces an evaluation order that satisfies all dependencies.

        Args:
            parsed_indicators: List of parsed indicator dicts.

        Returns:
            List of indices in evaluation order.

        Raises:
            ValueError: If circular dependency detected.
        """
        indicator_names = {ind["name"] for ind in parsed_indicators}
        name_to_idx = {ind["name"]: i for i, ind in enumerate(parsed_indicators)}

        # Build dependency map: idx -> set of idx it depends on
        deps = {}
        for i, ind in enumerate(parsed_indicators):
            deps[i] = set()
            # Walk the AST to find references to other indicator names
            for node in self._walk_ast(ind["tree"]):
                if hasattr(node, "id") and node.id in indicator_names:
                    dep_idx = name_to_idx[node.id]
                    if dep_idx != i:  # Don't depend on self
                        deps[i].add(dep_idx)

        # Kahn's algorithm for topological sort
        in_degree = {i: 0 for i in range(len(parsed_indicators))}
        for i, dep_set in deps.items():
            for dep in dep_set:
                in_degree[i] += 1

        queue = [i for i in range(len(parsed_indicators)) if in_degree[i] == 0]
        order = []

        while queue:
            node = queue.pop(0)
            order.append(node)
            for i, dep_set in deps.items():
                if node in dep_set:
                    in_degree[i] -= 1
                    if in_degree[i] == 0:
                        queue.append(i)

        if len(order) != len(parsed_indicators):
            raise ValueError(
                "Circular dependency detected among indicators. "
                "Please check your indicator expressions."
            )

        return order

    def _walk_ast(self, tree):
        """Recursively walk an AST tree yielding all nodes."""
        import ast as ast_mod

        for node in ast_mod.walk(tree):
            yield node

    def _run_simulation(
        self,
        df: pd.DataFrame,
        initial_capital: float,
        buy_conditions: dict,
        sell_conditions: dict,
        custom_series: dict,
    ) -> list:
        """Run the day-by-day backtest simulation.

        Args:
            df: DataFrame with OHLCV + custom indicator columns.
            initial_capital: Starting cash.
            buy_conditions: Condition tree for buy signals.
            sell_conditions: Condition tree for sell signals.
            custom_series: Dict of custom indicator name -> Series.

        Returns:
            List of trade dicts.
        """
        cash = initial_capital
        position = None  # {buy_date, shares, buy_price} or None
        trades = []

        for i in range(len(df)):
            row = df.iloc[i]
            trade_date = row["trade_date"]
            close = row["close"]

            # Build row values dict for condition evaluation
            row_values = {}
            for col in df.columns:
                row_values[col] = row[col]
            # Add custom indicator values
            for name, series in custom_series.items():
                row_values[name] = series.iloc[i]

            # Check sell conditions FIRST (T+1: only sell if buy_date != today)
            if position is not None and position["buy_date"] != trade_date:
                if self._evaluate_condition_tree(
                    sell_conditions, row_values, custom_series, i
                ):
                    # Sell all shares at close price
                    shares = position["shares"]
                    amount = shares * close
                    commission = round(amount * COMMISSION_RATE, 2)
                    stamp_tax = round(amount * STAMP_TAX_RATE, 2)
                    net_proceeds = amount - commission - stamp_tax

                    trades.append(
                        {
                            "trade_type": "sell",
                            "trade_date": trade_date,
                            "shares": shares,
                            "price": close,
                            "amount": round(amount, 2),
                            "commission": commission,
                            "stamp_tax": stamp_tax,
                        }
                    )
                    cash += net_proceeds
                    position = None

            # Check buy conditions (only buy if no position - full position)
            if position is None:
                if self._evaluate_condition_tree(
                    buy_conditions, row_values, custom_series, i
                ):
                    # Calculate shares: 95% of cash, rounded to board lot (100)
                    if close > 0:
                        shares = int(cash * 0.95 / close / 100) * 100
                        if shares >= 100:
                            amount = shares * close
                            commission = round(amount * COMMISSION_RATE, 2)
                            total_cost = amount + commission

                            if total_cost <= cash:
                                trades.append(
                                    {
                                        "trade_type": "buy",
                                        "trade_date": trade_date,
                                        "shares": shares,
                                        "price": close,
                                        "amount": round(amount, 2),
                                        "commission": commission,
                                        "stamp_tax": 0.0,
                                    }
                                )
                                cash -= total_cost
                                position = {
                                    "buy_date": trade_date,
                                    "shares": shares,
                                    "buy_price": close,
                                }

        # If still holding at end, mark as forced sell at last close
        # (for statistics only - not recorded as a trade)

        return trades

    def _evaluate_condition_tree(
        self,
        condition: dict,
        row_values: dict,
        indicator_series: dict,
        idx: int,
    ) -> bool:
        """Recursively evaluate a condition tree.

        Args:
            condition: Condition node (group or rule).
            row_values: Dict of current row values.
            indicator_series: Dict of full Series for cross/break operations.
            idx: Current row index in the DataFrame.

        Returns:
            True if condition is satisfied, False otherwise.
        """
        cond_type = condition.get("type", "group")

        if cond_type == "group":
            operator = condition.get("operator", "AND")
            children = condition.get("children", [])
            if not children:
                return True
            if operator == "AND":
                return all(
                    self._evaluate_condition_tree(c, row_values, indicator_series, idx)
                    for c in children
                )
            elif operator == "OR":
                return any(
                    self._evaluate_condition_tree(c, row_values, indicator_series, idx)
                    for c in children
                )
            return False

        # Rule type
        indicator_name = condition.get("indicator", "")
        op = condition.get("operator", "")
        threshold = condition.get("threshold")
        threshold_indicator = condition.get("threshold_indicator")

        # Get current value
        curr_val = row_values.get(indicator_name)
        if curr_val is None or (isinstance(curr_val, float) and math.isnan(curr_val)):
            return False

        # Get comparison value
        if threshold_indicator:
            other_val = row_values.get(threshold_indicator)
            if other_val is None or (isinstance(other_val, float) and math.isnan(other_val)):
                return False
        else:
            other_val = threshold
            if other_val is None:
                return False

        # Simple comparison operators
        if op == ">":
            return float(curr_val) > float(other_val)
        elif op == "<":
            return float(curr_val) < float(other_val)
        elif op == ">=":
            return float(curr_val) >= float(other_val)
        elif op == "<=":
            return float(curr_val) <= float(other_val)
        elif op == "==":
            return abs(float(curr_val) - float(other_val)) < 1e-9

        # Cross/break operators need previous values
        if idx < 1:
            return False

        # Get previous values
        series_a = indicator_series.get(indicator_name)
        if series_a is None:
            return False

        prev_val_a = series_a.iloc[idx - 1]
        if prev_val_a is None or (isinstance(prev_val_a, float) and math.isnan(prev_val_a)):
            return False

        if threshold_indicator:
            series_b = indicator_series.get(threshold_indicator)
            if series_b is None:
                return False
            prev_val_b = series_b.iloc[idx - 1]
            if prev_val_b is None or (isinstance(prev_val_b, float) and math.isnan(prev_val_b)):
                return False
        else:
            prev_val_b = other_val

        curr_a = float(curr_val)
        prev_a = float(prev_val_a)
        curr_b = float(other_val) if threshold_indicator else float(other_val)
        prev_b = float(prev_val_b)

        if op == "golden_cross":
            return prev_a <= prev_b and curr_a > curr_b
        elif op == "death_cross":
            return prev_a >= prev_b and curr_a < curr_b
        elif op == "break_above":
            return curr_a > curr_b and prev_a <= curr_b
        elif op == "break_below":
            return curr_a < curr_b and prev_a >= curr_b
        elif op == "enter_overbought":
            return curr_a > curr_b and prev_a <= curr_b
        elif op == "enter_oversold":
            return curr_a < curr_b and prev_a >= curr_b

        return False

    def _build_equity_curve(
        self, df: pd.DataFrame, trades: list, initial_capital: float
    ) -> list:
        """Build daily equity curve from trades.

        Args:
            df: DataFrame with OHLCV data.
            trades: List of trade dicts.
            initial_capital: Starting cash.

        Returns:
            List of {date, net_worth} dicts.
        """
        if df.empty:
            return []

        # Build trade lookup by date
        trade_lookup = {}
        for t in trades:
            trade_lookup.setdefault(t["trade_date"], []).append(t)

        cash = initial_capital
        position_shares = 0
        curve = []

        for i in range(len(df)):
            row = df.iloc[i]
            date = row["trade_date"]
            close = row["close"]

            # Apply trades for this date
            if date in trade_lookup:
                for t in trade_lookup[date]:
                    if t["trade_type"] == "buy":
                        cost = t["amount"] + t["commission"]
                        cash -= cost
                        position_shares += t["shares"]
                    elif t["trade_type"] == "sell":
                        proceeds = t["amount"] - t["commission"] - t["stamp_tax"]
                        cash += proceeds
                        position_shares -= t["shares"]

            market_value = position_shares * close
            net_worth = cash + market_value
            curve.append({"date": date, "net_worth": round(net_worth, 2)})

        return curve

    def _build_baseline_curve(
        self, df: pd.DataFrame, initial_capital: float
    ) -> list:
        """Build buy-and-hold baseline equity curve.

        Args:
            df: DataFrame with OHLCV data.
            initial_capital: Starting capital.

        Returns:
            List of {date, net_worth} dicts.
        """
        if df.empty:
            return []

        first_close = df.iloc[0]["close"]
        if first_close <= 0:
            return []

        curve = []
        for i in range(len(df)):
            row = df.iloc[i]
            worth = initial_capital * (row["close"] / first_close)
            curve.append({"date": row["trade_date"], "net_worth": round(worth, 2)})

        return curve

    def _calc_statistics(
        self,
        trades: list,
        equity_curve: list,
        initial_capital: float,
        start_date: str,
        end_date: str,
    ) -> dict:
        """Calculate all 8 backtest performance metrics.

        Args:
            trades: List of trade dicts.
            equity_curve: List of {date, net_worth} dicts.
            initial_capital: Starting capital.
            start_date: Backtest start date YYYYMMDD.
            end_date: Backtest end date YYYYMMDD.

        Returns:
            Dict with 8 statistics.
        """
        # 1. Total return
        final_equity = equity_curve[-1]["net_worth"] if equity_curve else initial_capital
        total_return_pct = (
            (final_equity - initial_capital) / initial_capital * 100
        )

        # 2. Annualized return
        try:
            start_dt = datetime.strptime(start_date, "%Y%m%d")
            end_dt = datetime.strptime(end_date, "%Y%m%d")
            total_days = (end_dt - start_dt).days
        except (ValueError, TypeError):
            total_days = 365
        if total_days <= 0:
            total_days = 1
        annualized_return_pct = total_return_pct * (365 / total_days)

        # 3. Max drawdown
        max_drawdown_pct = 0.0
        if equity_curve:
            running_max = equity_curve[0]["net_worth"]
            for point in equity_curve:
                if point["net_worth"] > running_max:
                    running_max = point["net_worth"]
                if running_max > 0:
                    dd = (point["net_worth"] - running_max) / running_max * 100
                    if dd < max_drawdown_pct:
                        max_drawdown_pct = dd

        # Pair up buy/sell trades
        buy_sell_pairs = self._pair_trades(trades)

        # 4. Trade count
        trade_count = len(buy_sell_pairs)

        # 5. Win rate
        win_count = sum(1 for p in buy_sell_pairs if p["profit"] > 0)
        win_rate_pct = (win_count / trade_count * 100) if trade_count > 0 else 0

        # 6. Profit factor
        winning_profits = sum(p["profit"] for p in buy_sell_pairs if p["profit"] > 0)
        losing_losses = sum(abs(p["profit"]) for p in buy_sell_pairs if p["profit"] < 0)
        profit_factor = winning_profits / losing_losses if losing_losses > 0 else (
            float("inf") if winning_profits > 0 else 0
        )

        # 7. Sharpe ratio (annualized)
        if len(equity_curve) > 1:
            returns = []
            for i in range(1, len(equity_curve)):
                prev = equity_curve[i - 1]["net_worth"]
                curr = equity_curve[i]["net_worth"]
                if prev > 0:
                    returns.append((curr - prev) / prev)
                else:
                    returns.append(0)
            if returns:
                mean_return = np.mean(returns)
                std_return = np.std(returns, ddof=1)
                sharpe_ratio = (
                    (mean_return / std_return) * math.sqrt(252)
                    if std_return > 0
                    else 0
                )
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0

        # 8. Average holding days
        if buy_sell_pairs:
            avg_holding_days = sum(p["holding_days"] for p in buy_sell_pairs) / len(
                buy_sell_pairs
            )
        else:
            avg_holding_days = 0

        return {
            "total_return_pct": round(total_return_pct, 2),
            "annualized_return_pct": round(annualized_return_pct, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "trade_count": trade_count,
            "win_rate_pct": round(win_rate_pct, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else "Inf",
            "sharpe_ratio": round(sharpe_ratio, 4),
            "avg_holding_days": round(avg_holding_days, 1),
        }

    def _pair_trades(self, trades: list) -> list:
        """Pair buy/sell trades chronologically for statistics.

        Args:
            trades: List of trade dicts in chronological order.

        Returns:
            List of paired trade dicts with profit info.
        """
        pairs = []
        pending_buy = None

        for t in trades:
            if t["trade_type"] == "buy":
                pending_buy = t
            elif t["trade_type"] == "sell" and pending_buy is not None:
                profit = t["amount"] - pending_buy["amount"]
                profit -= t["commission"] + t["stamp_tax"] + pending_buy["commission"]

                try:
                    buy_dt = datetime.strptime(pending_buy["trade_date"], "%Y%m%d")
                    sell_dt = datetime.strptime(t["trade_date"], "%Y%m%d")
                    holding_days = (sell_dt - buy_dt).days
                except (ValueError, TypeError):
                    holding_days = 0

                pairs.append(
                    {
                        "buy_date": pending_buy["trade_date"],
                        "buy_price": pending_buy["price"],
                        "sell_date": t["trade_date"],
                        "sell_price": t["price"],
                        "shares": t["shares"],
                        "profit": round(profit, 2),
                        "holding_days": holding_days,
                    }
                )
                pending_buy = None

        return pairs

    async def list_sessions(
        self, ts_code: str = None, limit: int = 20, offset: int = 0
    ) -> dict:
        """List backtest sessions with optional filtering.

        Args:
            ts_code: Optional stock code filter.
            limit: Maximum results to return.
            offset: Pagination offset.

        Returns:
            Dict with total count and sessions list.
        """
        query = select(BacktestSession).order_by(
            BacktestSession.created_at.desc()
        )

        if ts_code:
            query = query.where(BacktestSession.ts_code == ts_code)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()

        # Apply pagination
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        sessions = result.scalars().all()

        items = []
        for s in sessions:
            stats = json.loads(s.statistics) if s.statistics else {}
            items.append(
                {
                    "id": s.id,
                    "ts_code": s.ts_code,
                    "stock_name": s.stock_name or "",
                    "start_date": s.start_date,
                    "end_date": s.end_date,
                    "initial_capital": s.initial_capital,
                    "total_return_pct": stats.get("total_return_pct", 0),
                    "trade_count": stats.get("trade_count", 0),
                    "win_rate_pct": stats.get("win_rate_pct", 0),
                    "created_at": s.created_at,
                }
            )

        return {"total": total, "sessions": items}

    async def get_session(self, session_id: int) -> dict:
        """Get full backtest session result.

        Args:
            session_id: Backtest session ID.

        Returns:
            Full session data with trades, curves, and statistics.

        Raises:
            ValueError: If session not found.
        """
        result = await self.db.execute(
            select(BacktestSession).where(BacktestSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("回测会话不存在")

        # Get trades
        trades_result = await self.db.execute(
            select(BacktestTrade)
            .where(BacktestTrade.session_id == session_id)
            .order_by(BacktestTrade.trade_date.asc())
        )
        trades = trades_result.scalars().all()

        # Get stock name
        stock_result = await self.db.execute(
            select(Stock).where(Stock.ts_code == session.ts_code)
        )
        stock = stock_result.scalar_one_or_none()

        return {
            "session": {
                "id": session.id,
                "ts_code": session.ts_code,
                "stock_name": session.stock_name or (stock.name if stock else ""),
                "start_date": session.start_date,
                "end_date": session.end_date,
                "initial_capital": session.initial_capital,
                "indicators_config": json.loads(session.indicators_config),
                "buy_conditions": json.loads(session.buy_conditions),
                "sell_conditions": json.loads(session.sell_conditions),
                "statistics": json.loads(session.statistics) if session.statistics else {},
                "created_at": session.created_at,
            },
            "trades": [
                {
                    "id": t.id,
                    "trade_type": t.trade_type,
                    "trade_date": t.trade_date,
                    "shares": t.shares,
                    "price": t.price,
                    "amount": t.amount,
                    "commission": t.commission,
                    "stamp_tax": t.stamp_tax,
                }
                for t in trades
            ],
        }

    async def delete_session(self, session_id: int) -> dict:
        """Delete a backtest session and its trades.

        Args:
            session_id: Backtest session ID.

        Returns:
            Dict with success status.

        Raises:
            ValueError: If session not found.
        """
        result = await self.db.execute(
            select(BacktestSession).where(BacktestSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("回测会话不存在")

        await self.db.execute(
            delete(BacktestTrade).where(BacktestTrade.session_id == session_id)
        )
        await self.db.delete(session)
        await self.db.commit()

        return {"success": True, "message": f"已删除回测记录 #{session_id}"}

    async def get_presets(self) -> list:
        """Return preset strategy templates.

        Returns:
            List of preset strategy config dicts.
        """
        return self.PRESET_STRATEGIES
