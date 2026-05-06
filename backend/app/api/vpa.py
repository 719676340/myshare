"""Volume-Price Analysis (VPA) API endpoints."""

import logging
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.vpa_service import VPAService

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


@router.get("/vpa/{ts_code}")
async def get_vpa_analysis(
    ts_code: str,
    db: AsyncSession = Depends(get_db),
):
    """Get volume-price analysis (signals + patterns) for a stock.

    Args:
        ts_code: Stock code (e.g. "000001.SZ").
        db: Async database session.

    Returns:
        Dict with ts_code, signals (volume-price), and patterns (K-line).

    Raises:
        HTTPException: 400 for invalid ts_code, 500 for computation errors.
    """
    _validate_ts_code(ts_code)

    service = VPAService(db)
    try:
        signals_result = await service.detect_volume_price_signals(ts_code)
        patterns_result = await service.detect_kline_patterns(ts_code)

        return {
            "ts_code": ts_code,
            "signals": signals_result["signals"],
            "patterns": patterns_result["patterns"],
        }
    except Exception as e:
        logger.error(f"Error computing VPA for {ts_code}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "VPA分析失败",
                "detail": str(e),
            },
        )
