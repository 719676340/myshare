"""Data fetch orchestrator - handles cache logic and tushare data fetching."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DailyBar, Stock

logger = logging.getLogger(__name__)


class DataFetcher:
    """Orchestrates data fetching between cache (SQLite) and tushare API."""

    def __init__(
        self,
        session: AsyncSession,
        tushare_client=None,
    ):
        """Initialize with database session and optional tushare client.

        Args:
            session: Async SQLAlchemy session.
            tushare_client: Tushare API wrapper instance. If None, will be
                           created lazily when needed via settings.
        """
        self.session = session
        self._tushare_client = tushare_client

    def _get_tushare_client(self):
        """Get or create the tushare client.

        Returns:
            TushareClient instance.

        Raises:
            HTTPException: 503 if tushare token not configured.
        """
        if self._tushare_client is not None:
            return self._tushare_client

        from app.config import settings
        from app.services.tushare_client import TushareClient

        if not settings.tushare_token:
            raise HTTPException(
                status_code=503,
                detail="Tushare token not configured. Set TUSHARE_TOKEN environment variable.",
            )

        self._tushare_client = TushareClient(settings.tushare_token)
        return self._tushare_client

    async def ensure_stock_list(self) -> None:
        """Check if Stock table has data. If empty, fetch from tushare and insert.

        This is called on app startup to pre-load the stock list.
        """
        # Check if stocks already exist
        stmt = select(func.count()).select_from(Stock)
        result = await self.session.execute(stmt)
        count = result.scalar()

        if count > 0:
            logger.info(f"Stock list already loaded ({count} stocks)")
            return

        logger.info("Stock table is empty, fetching from tushare...")
        client = self._get_tushare_client()
        try:
            stocks_data = client.get_stock_list()
            for stock_dict in stocks_data:
                stock = Stock(
                    ts_code=stock_dict.get("ts_code"),
                    symbol=stock_dict.get("symbol"),
                    name=stock_dict.get("name"),
                    area=stock_dict.get("area"),
                    industry=stock_dict.get("industry"),
                    market=stock_dict.get("market"),
                    list_date=stock_dict.get("list_date"),
                )
                self.session.add(stock)

            await self.session.commit()
            logger.info(f"Loaded {len(stocks_data)} stocks into database")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to load stock list: {e}")
            raise

    async def fetch_daily_data(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """Fetch daily K-line data for a stock, using cache when available.

        Args:
            ts_code: Stock code (e.g. "000001.SZ").
            start_date: Optional start date filter (YYYYMMDD).
            end_date: Optional end date filter (YYYYMMDD).

        Returns:
            Dict with ts_code, data (list of OHLCV dicts), and cache_info.

        Raises:
            HTTPException: 404 if stock not found, 502 on tushare errors.
        """
        # Verify stock exists in database
        stock_stmt = select(Stock).where(Stock.ts_code == ts_code)
        stock_result = await self.session.execute(stock_stmt)
        stock = stock_result.scalar_one_or_none()

        if not stock:
            raise HTTPException(
                status_code=404,
                detail=f"Stock {ts_code} not found",
            )

        # Check existing cached data
        cached_stmt = (
            select(DailyBar)
            .where(DailyBar.ts_code == ts_code)
            .order_by(DailyBar.trade_date)
        )
        cached_result = await self.session.execute(cached_stmt)
        cached_bars = cached_result.scalars().all()

        if cached_bars:
            # Check if we need incremental update
            last_cached_date = cached_bars[-1].trade_date
            today = datetime.now().strftime("%Y%m%d")

            if last_cached_date < today:
                # Try to fetch incremental data from last cached date to today
                try:
                    client = self._get_tushare_client()
                    new_data = client.get_daily(
                        ts_code=ts_code,
                        start_date=last_cached_date,
                        end_date=today,
                    )
                    if new_data:
                        await self._insert_daily_bars(new_data)
                        # Re-query to get updated data
                        cached_result = await self.session.execute(cached_stmt)
                        cached_bars = cached_result.scalars().all()
                except HTTPException as e:
                    # Incremental update failed, return cached data
                    logger.warning(
                        f"Incremental fetch failed for {ts_code}: {e.detail}"
                    )
        else:
            # No cached data, fetch full history from tushare
            client = self._get_tushare_client()
            try:
                all_data = client.get_daily(ts_code=ts_code)
                if all_data:
                    await self._insert_daily_bars(all_data)
                    # Re-query to get the inserted data
                    cached_result = await self.session.execute(cached_stmt)
                    cached_bars = cached_result.scalars().all()
            except HTTPException:
                raise

        # Apply date filters if provided
        filtered_bars = cached_bars
        if start_date:
            filtered_bars = [b for b in filtered_bars if b.trade_date >= start_date]
        if end_date:
            filtered_bars = [b for b in filtered_bars if b.trade_date <= end_date]

        # Get cache info
        cache_info = self._get_cache_info(ts_code, cached_bars)

        return {
            "ts_code": ts_code,
            "name": stock.name,
            "data": [
                {
                    "trade_date": bar.trade_date,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "pre_close": bar.pre_close,
                    "change_pct": bar.change_pct,
                    "vol": bar.vol,
                    "amount": bar.amount,
                }
                for bar in filtered_bars
            ],
            "cache_info": cache_info,
        }

    async def refresh_daily_data(self, ts_code: str) -> dict:
        """Force re-fetch daily data from tushare.

        Args:
            ts_code: Stock code.

        Returns:
            Dict with ts_code, data, and cache_info.

        Raises:
            HTTPException: 404 if stock not found, 502 on tushare errors.
        """
        # Verify stock exists
        stock_stmt = select(Stock).where(Stock.ts_code == ts_code)
        stock_result = await self.session.execute(stock_stmt)
        stock = stock_result.scalar_one_or_none()

        if not stock:
            raise HTTPException(
                status_code=404,
                detail=f"Stock {ts_code} not found",
            )

        # Delete existing cached data
        from sqlalchemy import delete

        delete_stmt = delete(DailyBar).where(DailyBar.ts_code == ts_code)
        await self.session.execute(delete_stmt)
        await self.session.commit()

        # Fetch fresh data
        client = self._get_tushare_client()
        all_data = client.get_daily(ts_code=ts_code)
        if all_data:
            await self._insert_daily_bars(all_data)

        return await self.fetch_daily_data(ts_code)

    async def _insert_daily_bars(self, bars_data: list[dict]) -> None:
        """Insert daily bars into database, ignoring duplicates.

        Args:
            bars_data: List of dicts from tushare API.
        """
        for bar_dict in bars_data:
            # Check if this bar already exists (dedup)
            existing_stmt = select(DailyBar).where(
                DailyBar.ts_code == bar_dict.get("ts_code"),
                DailyBar.trade_date == bar_dict.get("trade_date"),
            )
            existing_result = await self.session.execute(existing_stmt)
            if existing_result.scalar_one_or_none():
                continue

            bar = DailyBar(
                ts_code=bar_dict.get("ts_code"),
                trade_date=bar_dict.get("trade_date"),
                open=bar_dict.get("open"),
                high=bar_dict.get("high"),
                low=bar_dict.get("low"),
                close=bar_dict.get("close"),
                pre_close=bar_dict.get("pre_close"),
                change_pct=bar_dict.get("pct_chg"),
                vol=bar_dict.get("vol"),
                amount=bar_dict.get("amount"),
            )
            self.session.add(bar)

        await self.session.commit()

    def _get_cache_info(
        self, ts_code: str, bars: list[DailyBar]
    ) -> dict:
        """Get cache metadata for a stock.

        Args:
            ts_code: Stock code.
            bars: List of DailyBar records.

        Returns:
            Dict with last_date, total_bars.
        """
        if not bars:
            return {"last_date": None, "total_bars": 0}

        last_date = bars[-1].trade_date
        total_bars = len(bars)

        return {
            "last_date": last_date,
            "total_bars": total_bars,
        }
