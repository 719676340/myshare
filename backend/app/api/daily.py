"""Daily K-line data API endpoints."""

import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.data_fetcher import DataFetcher

logger = logging.getLogger(__name__)

router = APIRouter()


def _validate_ts_code(ts_code: str) -> None:
    """Validate ts_code format (6 digits + . + 2 letters).

    Args:
        ts_code: Stock code to validate.

    Raises:
        HTTPException: 400 if format is invalid.
    """
    pattern = r"^\d{6}\.[A-Z]{2}$"
    if not re.match(pattern, ts_code):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ts_code format: {ts_code}. Expected format: 000001.SZ",
        )


@router.get("/daily/{ts_code}")
async def get_daily_data(
    ts_code: str,
    start_date: Optional[str] = Query(default=None, description="Start date YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="End date YYYYMMDD"),
    db: AsyncSession = Depends(get_db),
):
    """Get daily K-line data for a stock.

    Fetches data from cache if available, otherwise from tushare API.
    On first request, fetches all historical data and caches it.

    Args:
        ts_code: Stock code (e.g. "000001.SZ").
        start_date: Optional start date filter.
        end_date: Optional end date filter.
        db: Async database session.

    Returns:
        Dict with ts_code, name, data (OHLCV list), and cache_info.

    Raises:
        HTTPException: 400 for invalid ts_code, 404 for nonexistent stock,
                       502 for tushare errors.
    """
    _validate_ts_code(ts_code)

    fetcher = DataFetcher(db)
    try:
        result = await fetcher.fetch_daily_data(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching daily data for {ts_code}: {e}")
        raise HTTPException(
            status_code=502,
            detail={
                "error": "数据获取失败",
                "detail": str(e),
                "retry": True,
            },
        )


@router.post("/daily/{ts_code}/refresh")
async def refresh_daily_data(
    ts_code: str,
    db: AsyncSession = Depends(get_db),
):
    """Force re-fetch daily data from tushare, updating the cache.

    Args:
        ts_code: Stock code.
        db: Async database session.

    Returns:
        Fresh data from tushare.

    Raises:
        HTTPException: 400 for invalid ts_code, 404 for nonexistent stock,
                       502 for tushare errors.
    """
    _validate_ts_code(ts_code)

    fetcher = DataFetcher(db)
    try:
        result = await fetcher.refresh_daily_data(ts_code)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing daily data for {ts_code}: {e}")
        raise HTTPException(
            status_code=502,
            detail={
                "error": "数据获取失败",
                "detail": str(e),
                "retry": True,
            },
        )
