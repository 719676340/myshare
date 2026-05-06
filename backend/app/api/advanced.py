"""Advanced analysis API endpoints.

Provides endpoints for support/resistance detection, trend lines,
market cycle annotation, VAP distribution, multi-timeframe K-line,
and divergence detection.
"""

import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.advanced_analysis_service import AdvancedAnalysisService

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


@router.get("/advanced/{ts_code}/support-resistance")
async def get_support_resistance(
    ts_code: str,
    db: AsyncSession = Depends(get_db),
):
    """Get auto-detected support and resistance levels for a stock.

    Uses isolated pivot detection (Chapter 07) to identify key price
    levels grouped within 2% tolerance.

    Args:
        ts_code: Stock code (e.g. "000001.SZ").
        db: Async database session.

    Returns:
        Dict with ts_code and levels list.

    Raises:
        HTTPException: 400 for invalid ts_code, 500 for computation errors.
    """
    _validate_ts_code(ts_code)

    service = AdvancedAnalysisService(db)
    try:
        result = await service.detect_support_resistance(ts_code)
        return {"ts_code": ts_code, "levels": result["levels"]}
    except Exception as e:
        logger.error(f"Error computing support/resistance for {ts_code}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "支撑/阻力检测失败",
                "detail": str(e),
            },
        )


@router.get("/advanced/{ts_code}/trend-lines")
async def get_trend_lines(
    ts_code: str,
    db: AsyncSession = Depends(get_db),
):
    """Get auto-detected trend lines for a stock.

    Connects consecutive high and low pivots with lines,
    classified as up/down/horizontal trend.

    Args:
        ts_code: Stock code (e.g. "000001.SZ").
        db: Async database session.

    Returns:
        Dict with ts_code and lines list.

    Raises:
        HTTPException: 400 for invalid ts_code, 500 for computation errors.
    """
    _validate_ts_code(ts_code)

    service = AdvancedAnalysisService(db)
    try:
        result = await service.detect_trend_lines(ts_code)
        return {"ts_code": ts_code, "lines": result["lines"]}
    except Exception as e:
        logger.error(f"Error computing trend lines for {ts_code}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "趋势线检测失败",
                "detail": str(e),
            },
        )


@router.get("/advanced/{ts_code}/market-cycle")
async def get_market_cycle(
    ts_code: str,
    db: AsyncSession = Depends(get_db),
):
    """Get market cycle phase annotations for a stock.

    Detects accumulation, markup, distribution, and markdown phases
    based on volume patterns and price trends (Chapter 05).

    Args:
        ts_code: Stock code (e.g. "000001.SZ").
        db: Async database session.

    Returns:
        Dict with ts_code and phases list.

    Raises:
        HTTPException: 400 for invalid ts_code, 500 for computation errors.
    """
    _validate_ts_code(ts_code)

    service = AdvancedAnalysisService(db)
    try:
        result = await service.detect_market_cycle(ts_code)
        return {"ts_code": ts_code, "phases": result["phases"]}
    except Exception as e:
        logger.error(f"Error computing market cycle for {ts_code}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "市场循环检测失败",
                "detail": str(e),
            },
        )


@router.get("/advanced/{ts_code}/vap")
async def get_vap(
    ts_code: str,
    start_date: Optional[str] = Query(
        default=None, description="Start date YYYYMMDD"
    ),
    end_date: Optional[str] = Query(
        default=None, description="End date YYYYMMDD"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Get Volume at Price (VAP) distribution for a stock.

    Computes a 30-bin price histogram showing volume distribution
    across price levels (Chapter 09).

    Args:
        ts_code: Stock code (e.g. "000001.SZ").
        start_date: Optional start date filter (YYYYMMDD).
        end_date: Optional end date filter (YYYYMMDD).
        db: Async database session.

    Returns:
        Dict with ts_code, vap bins, price_range, and total_volume.

    Raises:
        HTTPException: 400 for invalid ts_code, 500 for computation errors.
    """
    _validate_ts_code(ts_code)

    service = AdvancedAnalysisService(db)
    try:
        result = await service.compute_vap(ts_code, start_date, end_date)
        return {
            "ts_code": ts_code,
            "vap": result["vap"],
            "price_range": result["price_range"],
            "total_volume": result["total_volume"],
        }
    except Exception as e:
        logger.error(f"Error computing VAP for {ts_code}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "VAP计算失败",
                "detail": str(e),
            },
        )


@router.get("/advanced/{ts_code}/multi-timeframe")
async def get_multi_timeframe(
    ts_code: str,
    timeframe: str = Query(
        ..., description="Timeframe: 'weekly' or 'monthly'"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated K-line data for weekly or monthly timeframes.

    Aggregates daily OHLCV data into weekly (ISO week) or monthly
    (YYYYMM) bars without additional tushare API calls.

    Args:
        ts_code: Stock code (e.g. "000001.SZ").
        timeframe: "weekly" or "monthly".
        db: Async database session.

    Returns:
        Dict with ts_code, timeframe, and aggregated data list.

    Raises:
        HTTPException: 400 for invalid ts_code or timeframe, 500 for errors.
    """
    _validate_ts_code(ts_code)

    if timeframe not in ("weekly", "monthly"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid timeframe: {timeframe}. Must be 'weekly' or 'monthly'",
        )

    service = AdvancedAnalysisService(db)
    try:
        result = await service.aggregate_kline(ts_code, timeframe)
        return {
            "ts_code": ts_code,
            "timeframe": result["timeframe"],
            "data": result["data"],
        }
    except Exception as e:
        logger.error(f"Error aggregating {timeframe} data for {ts_code}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"{timeframe}K线聚合失败",
                "detail": str(e),
            },
        )


@router.get("/advanced/{ts_code}/divergence")
async def get_divergence(
    ts_code: str,
    db: AsyncSession = Depends(get_db),
):
    """Get price-volume divergence signals for a stock.

    Detects bearish divergences where price makes new 20-day highs
    but volume is below the 20-day average (VPA-04).

    Args:
        ts_code: Stock code (e.g. "000001.SZ").
        db: Async database session.

    Returns:
        Dict with ts_code and divergences list.

    Raises:
        HTTPException: 400 for invalid ts_code, 500 for computation errors.
    """
    _validate_ts_code(ts_code)

    service = AdvancedAnalysisService(db)
    try:
        result = await service.detect_divergence(ts_code)
        return {"ts_code": ts_code, "divergences": result["divergences"]}
    except Exception as e:
        logger.error(f"Error computing divergence for {ts_code}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "量价背离检测失败",
                "detail": str(e),
            },
        )
