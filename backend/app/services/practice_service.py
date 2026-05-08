"""Practice session management service.

Handles trading practice lifecycle: session creation, daily advancement,
trade execution with A-share rule enforcement (T+1, price limits, fees),
and performance statistics computation.
"""

import logging
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DailyBar, Position, PracticeSession, Stock, Trade

logger = logging.getLogger(__name__)


class PracticeService:
    """Manages trading practice sessions with A-share rule enforcement."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session.

        Args:
            db: Async SQLAlchemy session.
        """
        self.db = db

    async def create_session(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
        initial_capital: float = 1000000.0,
    ) -> PracticeSession:
        """Create a new practice session.

        Args:
            ts_code: Stock code (e.g. "000001.SZ").
            start_date: Practice start date YYYYMMDD.
            end_date: Practice end date YYYYMMDD.
            initial_capital: Starting cash (default 1,000,000).

        Returns:
            Created PracticeSession object.

        Raises:
            ValueError: If stock not found or no data in range.
        """
        # Validate stock exists
        stock_result = await self.db.execute(
            select(Stock).where(Stock.ts_code == ts_code)
        )
        stock = stock_result.scalar_one_or_none()
        if not stock:
            raise ValueError("股票代码不存在")

        # Validate data exists in the requested range
        range_result = await self.db.execute(
            select(DailyBar)
            .where(
                DailyBar.ts_code == ts_code,
                DailyBar.trade_date >= start_date,
                DailyBar.trade_date <= end_date,
            )
            .order_by(DailyBar.trade_date.asc())
        )
        range_bars = range_result.scalars().all()
        if not range_bars:
            raise ValueError("该时间范围内无可用数据")

        # Set current_date to last trading day before start_date
        # so user sees context before practice begins
        pre_result = await self.db.execute(
            select(DailyBar)
            .where(
                DailyBar.ts_code == ts_code,
                DailyBar.trade_date < start_date,
            )
            .order_by(DailyBar.trade_date.desc())
            .limit(1)
        )
        pre_bar = pre_result.scalar_one_or_none()
        if pre_bar:
            current_date = pre_bar.trade_date
        else:
            current_date = start_date

        session = PracticeSession(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            current_date=current_date,
            cash=initial_capital,
            status="active",
            created_at=datetime.now().isoformat(),
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: int) -> dict:
        """Get full session state with visible data, positions, and trades.

        Args:
            session_id: Practice session ID.

        Returns:
            Dict with session info, daily data, positions, trades, and portfolio stats.

        Raises:
            ValueError: If session not found.
        """
        session = await self._get_session_or_raise(session_id)

        # Get visible bars (trade_date <= current_date)
        bars_result = await self.db.execute(
            select(DailyBar)
            .where(
                DailyBar.ts_code == session.ts_code,
                DailyBar.trade_date <= session.current_date,
            )
            .order_by(DailyBar.trade_date.asc())
        )
        visible_bars = bars_result.scalars().all()

        # Get total practice days for progress calculation
        total_result = await self.db.execute(
            select(DailyBar)
            .where(
                DailyBar.ts_code == session.ts_code,
                DailyBar.trade_date >= session.start_date,
                DailyBar.trade_date <= session.end_date,
            )
            .order_by(DailyBar.trade_date.asc())
        )
        total_bars = total_result.scalars().all()
        total_days = len(total_bars)

        # Count how many practice days have been revealed
        revealed_result = await self.db.execute(
            select(DailyBar)
            .where(
                DailyBar.ts_code == session.ts_code,
                DailyBar.trade_date >= session.start_date,
                DailyBar.trade_date <= session.current_date,
            )
            .order_by(DailyBar.trade_date.asc())
        )
        revealed_bars = revealed_result.scalars().all()
        current_day = len(revealed_bars)

        progress_pct = round(current_day / total_days * 100, 1) if total_days > 0 else 0

        # Get trades
        trades_result = await self.db.execute(
            select(Trade)
            .where(Trade.session_id == session_id)
            .order_by(Trade.trade_date.asc())
        )
        trades = trades_result.scalars().all()

        # Get open positions
        positions_result = await self.db.execute(
            select(Position).where(
                Position.session_id == session_id,
                Position.remaining_shares > 0,
            )
        )
        positions = positions_result.scalars().all()

        # Get current bar for market value calculation
        current_bar_result = await self.db.execute(
            select(DailyBar).where(
                DailyBar.ts_code == session.ts_code,
                DailyBar.trade_date == session.current_date,
            )
        )
        current_bar = current_bar_result.scalar_one_or_none()
        current_price = current_bar.close if current_bar else 0

        # Enrich positions with market value
        position_dicts = []
        total_market_value = 0.0
        for pos in positions:
            market_value = pos.remaining_shares * current_price
            floating_pnl = pos.remaining_shares * (current_price - pos.buy_price)
            total_market_value += market_value
            position_dicts.append(
                {
                    "id": pos.id,
                    "ts_code": pos.ts_code,
                    "buy_date": pos.buy_date,
                    "buy_price": pos.buy_price,
                    "total_shares": pos.total_shares,
                    "remaining_shares": pos.remaining_shares,
                    "market_value": round(market_value, 2),
                    "floating_pnl": round(floating_pnl, 2),
                    "floating_pnl_pct": round(
                        (current_price - pos.buy_price) / pos.buy_price * 100, 2
                    )
                    if pos.buy_price > 0
                    else 0,
                }
            )

        # Get stock info
        stock_result = await self.db.execute(
            select(Stock).where(Stock.ts_code == session.ts_code)
        )
        stock = stock_result.scalar_one_or_none()

        total_assets = session.cash + total_market_value
        total_pnl = total_assets - session.initial_capital
        total_pnl_pct = (
            round(total_pnl / session.initial_capital * 100, 2)
            if session.initial_capital > 0
            else 0
        )

        return {
            "session": {
                "id": session.id,
                "ts_code": session.ts_code,
                "start_date": session.start_date,
                "end_date": session.end_date,
                "initial_capital": session.initial_capital,
                "current_date": session.current_date,
                "cash": round(session.cash, 2),
                "status": session.status,
                "created_at": session.created_at,
            },
            "stock": {
                "ts_code": stock.ts_code,
                "name": stock.name,
                "symbol": stock.symbol,
            }
            if stock
            else None,
            "daily_data": [
                {
                    "id": b.id,
                    "ts_code": b.ts_code,
                    "trade_date": b.trade_date,
                    "open": b.open,
                    "high": b.high,
                    "low": b.low,
                    "close": b.close,
                    "pre_close": b.pre_close,
                    "change_pct": b.change_pct,
                    "vol": b.vol,
                    "amount": b.amount,
                }
                for b in visible_bars
            ],
            "positions": position_dicts,
            "trades": [
                {
                    "id": t.id,
                    "trade_type": t.trade_type,
                    "ts_code": t.ts_code,
                    "trade_date": t.trade_date,
                    "shares": t.shares,
                    "price": t.price,
                    "amount": round(t.amount, 2),
                    "commission": round(t.commission, 2),
                    "stamp_tax": round(t.stamp_tax, 2),
                }
                for t in trades
            ],
            "total_market_value": round(total_market_value, 2),
            "total_assets": round(total_assets, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": total_pnl_pct,
            "progress": {
                "current": current_day,
                "total": total_days,
                "pct": progress_pct,
            },
        }

    async def advance_day(self, session_id: int) -> dict:
        """Advance session to next trading day.

        Args:
            session_id: Practice session ID.

        Returns:
            Dict with new current_date, revealed bar data, and is_final flag.

        Raises:
            ValueError: If session finished or already at last day.
        """
        session = await self._get_session_or_raise(session_id)
        if session.status != "active":
            raise ValueError("练习已结束")

        # Find the next bar after current_date
        next_result = await self.db.execute(
            select(DailyBar)
            .where(
                DailyBar.ts_code == session.ts_code,
                DailyBar.trade_date > session.current_date,
            )
            .order_by(DailyBar.trade_date.asc())
            .limit(1)
        )
        next_bar = next_result.scalar_one_or_none()

        if not next_bar:
            raise ValueError("已是最后一个交易日")

        session.current_date = next_bar.trade_date
        await self.db.commit()

        return {
            "current_date": next_bar.trade_date,
            "bar": {
                "id": next_bar.id,
                "ts_code": next_bar.ts_code,
                "trade_date": next_bar.trade_date,
                "open": next_bar.open,
                "high": next_bar.high,
                "low": next_bar.low,
                "close": next_bar.close,
                "pre_close": next_bar.pre_close,
                "change_pct": next_bar.change_pct,
                "vol": next_bar.vol,
                "amount": next_bar.amount,
            },
            "is_final": next_bar.trade_date >= session.end_date,
        }

    async def buy_order(
        self, session_id: int, shares: int, price: float
    ) -> dict:
        """Execute a buy order.

        Enforces price limits based on stock type and available cash.

        Args:
            session_id: Practice session ID.
            shares: Number of shares to buy (must be multiple of 100).
            price: Limit price for the buy order.

        Returns:
            Dict with trade details and confirmation message.

        Raises:
            ValueError: If session inactive, price outside limits, or insufficient cash.
        """
        session = await self._get_session_or_raise(session_id)
        if session.status != "active":
            raise ValueError("练习已结束")

        # Get stock info for price limit calculation
        stock_result = await self.db.execute(
            select(Stock).where(Stock.ts_code == session.ts_code)
        )
        stock = stock_result.scalar_one_or_none()
        stock_name = stock.name if stock else ""

        # Determine price limit percentage
        limit_pct = self._get_price_limit_pct(stock_name, session.ts_code)

        # Get current bar for pre_close
        bar_result = await self.db.execute(
            select(DailyBar).where(
                DailyBar.ts_code == session.ts_code,
                DailyBar.trade_date == session.current_date,
            )
        )
        current_bar = bar_result.scalar_one_or_none()
        if not current_bar:
            raise ValueError("当前日期无行情数据")

        pre_close = current_bar.pre_close if current_bar.pre_close else current_bar.close

        # Validate price within limits
        lower_limit = round(pre_close * (1 - limit_pct), 2)
        upper_limit = round(pre_close * (1 + limit_pct), 2)
        if price < lower_limit or price > upper_limit:
            raise ValueError(
                f"价格超出涨跌停限制 [{lower_limit}, {upper_limit}]"
            )

        # Calculate costs
        amount = shares * price
        commission = round(amount * 0.00025, 2)  # 万2.5
        total_cost = amount + commission

        # Validate sufficient cash
        if session.cash < total_cost:
            raise ValueError(
                f"可用资金不足，需要 {total_cost:.2f}，可用 {session.cash:.2f}"
            )

        # Create trade record
        trade = Trade(
            session_id=session_id,
            trade_type="buy",
            ts_code=session.ts_code,
            trade_date=session.current_date,
            shares=shares,
            price=price,
            amount=amount,
            commission=commission,
            stamp_tax=0.0,
        )
        self.db.add(trade)
        await self.db.flush()  # Get trade.id

        # Create position record
        position = Position(
            session_id=session_id,
            buy_trade_id=trade.id,
            ts_code=session.ts_code,
            buy_date=session.current_date,
            buy_price=price,
            total_shares=shares,
            remaining_shares=shares,
        )
        self.db.add(position)

        # Update session cash
        session.cash -= total_cost
        await self.db.commit()

        return {
            "trade": {
                "id": trade.id,
                "trade_type": trade.trade_type,
                "ts_code": trade.ts_code,
                "trade_date": trade.trade_date,
                "shares": trade.shares,
                "price": trade.price,
                "amount": round(trade.amount, 2),
                "commission": round(trade.commission, 2),
                "stamp_tax": round(trade.stamp_tax, 2),
            },
            "position_id": position.id,
            "message": f"买入 {shares} 股，成交价 {price}，佣金 {commission}，共 {total_cost:.2f}",
        }

    async def sell_order(
        self,
        session_id: int,
        position_id: int,
        shares: int,
        price: float,
    ) -> dict:
        """Execute a sell order.

        Enforces T+1 rule, price limits, and position availability.

        Args:
            session_id: Practice session ID.
            position_id: Position to sell from.
            shares: Number of shares to sell.
            price: Limit price for the sell order.

        Returns:
            Dict with trade details and confirmation message.

        Raises:
            ValueError: If T+1 violation, insufficient shares, or price outside limits.
        """
        session = await self._get_session_or_raise(session_id)
        if session.status != "active":
            raise ValueError("练习已结束")

        # Validate position exists and belongs to session
        pos_result = await self.db.execute(
            select(Position).where(
                Position.id == position_id,
                Position.session_id == session_id,
            )
        )
        position = pos_result.scalar_one_or_none()
        if not position:
            raise ValueError("持仓不存在")

        # T+1 validation: cannot sell same-day buys
        if position.buy_date == session.current_date:
            raise ValueError("T+1规则：当日买入不可当日卖出")

        # Validate sufficient remaining shares
        if position.remaining_shares < shares:
            raise ValueError(
                f"可卖数量不足，当前可卖 {position.remaining_shares} 股"
            )

        # Get stock info for price limit
        stock_result = await self.db.execute(
            select(Stock).where(Stock.ts_code == session.ts_code)
        )
        stock = stock_result.scalar_one_or_none()
        stock_name = stock.name if stock else ""
        limit_pct = self._get_price_limit_pct(stock_name, session.ts_code)

        # Get current bar for pre_close
        bar_result = await self.db.execute(
            select(DailyBar).where(
                DailyBar.ts_code == session.ts_code,
                DailyBar.trade_date == session.current_date,
            )
        )
        current_bar = bar_result.scalar_one_or_none()
        if not current_bar:
            raise ValueError("当前日期无行情数据")

        pre_close = current_bar.pre_close if current_bar.pre_close else current_bar.close

        # Validate price within limits
        lower_limit = round(pre_close * (1 - limit_pct), 2)
        upper_limit = round(pre_close * (1 + limit_pct), 2)
        if price < lower_limit or price > upper_limit:
            raise ValueError(
                f"价格超出涨跌停限制 [{lower_limit}, {upper_limit}]"
            )

        # Calculate proceeds
        amount = shares * price
        commission = round(amount * 0.00025, 2)  # 万2.5
        stamp_tax = round(amount * 0.001, 2)  # 千1
        net_proceeds = amount - commission - stamp_tax

        # Create trade record
        trade = Trade(
            session_id=session_id,
            trade_type="sell",
            ts_code=session.ts_code,
            trade_date=session.current_date,
            shares=shares,
            price=price,
            amount=amount,
            commission=commission,
            stamp_tax=stamp_tax,
        )
        self.db.add(trade)

        # Update position remaining shares
        position.remaining_shares -= shares

        # Update session cash
        session.cash += net_proceeds
        await self.db.commit()

        total_fees = commission + stamp_tax
        return {
            "trade": {
                "id": trade.id,
                "trade_type": trade.trade_type,
                "ts_code": trade.ts_code,
                "trade_date": trade.trade_date,
                "shares": trade.shares,
                "price": trade.price,
                "amount": round(trade.amount, 2),
                "commission": round(trade.commission, 2),
                "stamp_tax": round(trade.stamp_tax, 2),
            },
            "message": f"卖出 {shares} 股，成交价 {price}，费用 {total_fees:.2f}，到账 {net_proceeds:.2f}",
        }

    async def end_session(self, session_id: int) -> dict:
        """End a practice session early.

        Args:
            session_id: Practice session ID.

        Returns:
            Dict with finished status.

        Raises:
            ValueError: If session not found or already finished.
        """
        session = await self._get_session_or_raise(session_id)
        if session.status != "active":
            raise ValueError("练习已结束")

        session.status = "finished"
        await self.db.commit()

        return {"status": "finished", "message": "练习已结束"}

    async def get_stats(self, session_id: int) -> dict:
        """Compute comprehensive trading statistics.

        Pairs buy/sell trades using FIFO matching, calculates performance
        metrics, and builds equity curve.

        Args:
            session_id: Practice session ID.

        Returns:
            Dict with paired trades, equity curve, and summary statistics.

        Raises:
            ValueError: If session not found.
        """
        session = await self._get_session_or_raise(session_id)

        # Get all trades ordered chronologically
        trades_result = await self.db.execute(
            select(Trade)
            .where(Trade.session_id == session_id)
            .order_by(Trade.trade_date.asc(), Trade.id.asc())
        )
        all_trades = trades_result.scalars().all()

        # Get all positions
        positions_result = await self.db.execute(
            select(Position).where(Position.session_id == session_id)
        )
        all_positions = positions_result.scalars().all()

        # Pair buy/sell trades using FIFO
        trade_pairs = self._pair_trades_fifo(all_trades, all_positions)

        # Calculate aggregate statistics
        total_trades = len(trade_pairs)
        win_count = sum(1 for p in trade_pairs if p["profit_amount"] > 0)
        loss_count = sum(1 for p in trade_pairs if p["profit_amount"] < 0)
        win_rate = round(win_count / total_trades * 100, 2) if total_trades > 0 else 0

        total_commission = sum(t.commission for t in all_trades)
        total_stamp_tax = sum(t.stamp_tax for t in all_trades)

        # Calculate final capital
        # Get last available price for open positions
        open_positions = [p for p in all_positions if p.remaining_shares > 0]
        final_market_value = 0.0
        if open_positions:
            # Use the last bar up to current_date
            last_bar_result = await self.db.execute(
                select(DailyBar)
                .where(
                    DailyBar.ts_code == session.ts_code,
                    DailyBar.trade_date <= session.current_date,
                )
                .order_by(DailyBar.trade_date.desc())
                .limit(1)
            )
            last_bar = last_bar_result.scalar_one_or_none()
            if last_bar:
                for pos in open_positions:
                    final_market_value += pos.remaining_shares * last_bar.close

        final_capital = session.cash + final_market_value
        total_return = final_capital - session.initial_capital
        total_return_pct = (
            round(total_return / session.initial_capital * 100, 2)
            if session.initial_capital > 0
            else 0
        )

        # Build equity curve
        equity_curve = await self._build_equity_curve(session, all_trades)

        # --- Max drawdown from equity curve ---
        max_drawdown_pct = 0.0
        max_drawdown_amount = 0.0
        max_drawdown_start = ""
        max_drawdown_end = ""
        if equity_curve:
            peak = equity_curve[0]["net_worth"]
            peak_idx = 0
            for i, pt in enumerate(equity_curve):
                if pt["net_worth"] > peak:
                    peak = pt["net_worth"]
                    peak_idx = i
                dd = peak - pt["net_worth"]
                dd_pct = dd / peak * 100 if peak > 0 else 0
                if dd > max_drawdown_amount:
                    max_drawdown_amount = round(dd, 2)
                    max_drawdown_pct = round(-dd_pct, 2)
                    max_drawdown_start = equity_curve[peak_idx]["date"]
                    max_drawdown_end = pt["date"]

        # --- Win/loss distribution ---
        wins = [p["profit_amount"] for p in trade_pairs if p["profit_amount"] > 0]
        losses = [p["profit_amount"] for p in trade_pairs if p["profit_amount"] < 0]
        avg_win_amount = round(sum(wins) / len(wins), 2) if wins else 0
        avg_loss_amount = round(sum(losses) / len(losses), 2) if losses else 0
        max_win_amount = round(max(wins), 2) if wins else 0
        max_loss_amount = round(min(losses), 2) if losses else 0

        # --- Profit factor ---
        gross_profit = round(sum(wins), 2) if wins else 0
        gross_loss = round(abs(sum(losses)), 2) if losses else 0
        if gross_loss > 0:
            profit_factor = round(gross_profit / gross_loss, 2)
        elif total_trades > 0:
            profit_factor = float("inf")
        else:
            profit_factor = 0

        # --- Average holding period ---
        avg_holding_days = (
            round(sum(p["holding_days"] for p in trade_pairs) / total_trades, 1)
            if total_trades > 0
            else 0
        )

        # --- Per-trade cumulative P&L ---
        cumulative_pnl = 0.0
        for pair in trade_pairs:
            cumulative_pnl += pair["profit_amount"]
            pair["cumulative_pnl"] = round(cumulative_pnl, 2)

        return {
            "ts_code": session.ts_code,
            "start_date": session.start_date,
            "end_date": session.end_date,
            "initial_capital": session.initial_capital,
            "final_capital": round(final_capital, 2),
            "total_return": round(total_return, 2),
            "total_return_pct": total_return_pct,
            "total_trades": total_trades,
            "win_count": win_count,
            "loss_count": loss_count,
            "win_rate": win_rate,
            "total_commission": round(total_commission, 2),
            "total_stamp_tax": round(total_stamp_tax, 2),
            "trade_pairs": trade_pairs,
            "equity_curve": equity_curve,
            "all_trades": [
                {
                    "id": t.id,
                    "trade_type": t.trade_type,
                    "ts_code": t.ts_code,
                    "trade_date": t.trade_date,
                    "shares": t.shares,
                    "price": t.price,
                    "amount": round(t.amount, 2),
                    "commission": round(t.commission, 2),
                    "stamp_tax": round(t.stamp_tax, 2),
                }
                for t in all_trades
            ],
            # New metrics
            "max_drawdown_pct": max_drawdown_pct,
            "max_drawdown_amount": max_drawdown_amount,
            "max_drawdown_start": max_drawdown_start,
            "max_drawdown_end": max_drawdown_end,
            "avg_win_amount": avg_win_amount,
            "avg_loss_amount": avg_loss_amount,
            "max_win_amount": max_win_amount,
            "max_loss_amount": max_loss_amount,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "profit_factor": profit_factor,
            "avg_holding_days": avg_holding_days,
        }

    # --- Private helper methods ---

    async def _get_session_or_raise(self, session_id: int) -> PracticeSession:
        """Fetch session or raise ValueError if not found."""
        result = await self.db.execute(
            select(PracticeSession).where(PracticeSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("会话不存在")
        return session

    def _get_price_limit_pct(self, stock_name: str, ts_code: str) -> float:
        """Determine price limit percentage based on stock type.

        Args:
            stock_name: Stock name (check for ST).
            ts_code: Stock code (check for ChiNext/STAR).

        Returns:
            Price limit as decimal (0.05, 0.10, or 0.20).
        """
        if "ST" in stock_name:
            return 0.05
        if ts_code.startswith("30") or ts_code.startswith("688"):
            return 0.20
        return 0.10

    def _pair_trades_fifo(
        self, all_trades: list, all_positions: list
    ) -> list:
        """Pair buy and sell trades using FIFO matching.

        Each sell is matched against the earliest open buy position.
        Partial matches are supported (sell across multiple buys).

        Args:
            all_trades: All Trade records for the session, chronologically ordered.
            all_positions: All Position records for the session.

        Returns:
            List of trade pair dicts with profit info.
        """
        # Build a map of position_id -> position for quick lookup
        pos_map = {p.id: p for p in all_positions}

        # Build FIFO queue of buy lots from positions
        # Each lot: {position_id, buy_date, buy_price, remaining}
        buy_queue = []
        for pos in sorted(all_positions, key=lambda p: p.buy_date):
            buy_queue.append(
                {
                    "position_id": pos.id,
                    "buy_date": pos.buy_date,
                    "buy_price": pos.buy_price,
                    "remaining": pos.total_shares,
                }
            )

        # Process sell trades to pair with buys
        pairs = []
        sell_trades = [t for t in all_trades if t.trade_type == "sell"]

        for sell in sell_trades:
            shares_to_match = sell.shares
            while shares_to_match > 0 and buy_queue:
                lot = buy_queue[0]
                if lot["remaining"] <= 0:
                    buy_queue.pop(0)
                    continue

                matched = min(shares_to_match, lot["remaining"])
                profit_amount = matched * (sell.price - lot["buy_price"]) - (
                    sell.commission + sell.stamp_tax
                ) * (matched / sell.shares)
                profit_pct = (
                    round(
                        (sell.price - lot["buy_price"])
                        / lot["buy_price"]
                        * 100,
                        2,
                    )
                    if lot["buy_price"] > 0
                    else 0
                )

                # Calculate holding days
                try:
                    buy_dt = datetime.strptime(lot["buy_date"], "%Y%m%d")
                    sell_dt = datetime.strptime(sell.trade_date, "%Y%m%d")
                    holding_days = (sell_dt - buy_dt).days
                except (ValueError, TypeError):
                    holding_days = 0

                pairs.append(
                    {
                        "buy_date": lot["buy_date"],
                        "buy_price": lot["buy_price"],
                        "buy_shares": matched,
                        "sell_date": sell.trade_date,
                        "sell_price": sell.price,
                        "sell_shares": matched,
                        "profit_amount": round(profit_amount, 2),
                        "profit_pct": profit_pct,
                        "holding_days": holding_days,
                    }
                )

                lot["remaining"] -= matched
                shares_to_match -= matched

                if lot["remaining"] <= 0:
                    buy_queue.pop(0)

        return pairs

    async def _build_equity_curve(
        self, session: PracticeSession, all_trades: list
    ) -> list:
        """Build daily equity curve for the practice period.

        For each trading day from start_date to current_date, calculates
        net worth = cash + market value of positions.

        Args:
            session: PracticeSession object.
            all_trades: All Trade records for the session.

        Returns:
            List of {date, net_worth, cash, market_value} dicts.
        """
        # Get all bars in the practice range
        bars_result = await self.db.execute(
            select(DailyBar)
            .where(
                DailyBar.ts_code == session.ts_code,
                DailyBar.trade_date >= session.start_date,
                DailyBar.trade_date <= session.current_date,
            )
            .order_by(DailyBar.trade_date.asc())
        )
        bars = bars_result.scalars().all()
        if not bars:
            return []

        # Build a price lookup: trade_date -> close price
        price_lookup = {b.trade_date: b.close for b in bars}

        # Build trade lookup: trade_date -> list of trades
        trade_lookup = {}
        for t in all_trades:
            trade_lookup.setdefault(t.trade_date, []).append(t)

        # Track positions: list of {buy_price, remaining_shares, buy_date}
        positions = []
        cash = session.initial_capital
        curve = []

        for bar in bars:
            date = bar.trade_date
            close_price = bar.close

            # Apply trades for this date
            if date in trade_lookup:
                for t in trade_lookup[date]:
                    if t.trade_type == "buy":
                        cost = t.amount + t.commission
                        cash -= cost
                        positions.append(
                            {
                                "buy_price": t.price,
                                "remaining_shares": t.shares,
                                "buy_date": t.trade_date,
                            }
                        )
                    elif t.trade_type == "sell":
                        proceeds = t.amount - t.commission - t.stamp_tax
                        cash += proceeds
                        # Reduce positions (FIFO)
                        shares_left = t.shares
                        for pos in positions:
                            if shares_left <= 0:
                                break
                            if pos["remaining_shares"] <= 0:
                                continue
                            deduct = min(shares_left, pos["remaining_shares"])
                            pos["remaining_shares"] -= deduct
                            shares_left -= deduct

            # Calculate market value of open positions
            market_value = sum(
                pos["remaining_shares"] * close_price
                for pos in positions
                if pos["remaining_shares"] > 0
            )

            net_worth = cash + market_value
            curve.append(
                {
                    "date": date,
                    "net_worth": round(net_worth, 2),
                    "cash": round(cash, 2),
                    "market_value": round(market_value, 2),
                }
            )

        return curve
