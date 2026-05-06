"""Technical indicators API endpoints."""

import json
import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.indicator_service import IndicatorService

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


@router.get("/indicators/{ts_code}")
async def get_indicators(
    ts_code: str,
    indicator: str = Query(..., description="Indicator name: macd/rsi/kdj/boll"),
    params: Optional[str] = Query(
        default=None, description="JSON string of indicator params"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Get computed technical indicator data for a stock.

    Args:
        ts_code: Stock code (e.g. "000001.SZ").
        indicator: Indicator name (macd, rsi, kdj, boll).
        params: Optional JSON string of parameter overrides.
        db: Async database session.

    Returns:
        Dict with indicator name, params, params_hash, and data list.

    Raises:
        HTTPException: 400 for invalid ts_code or indicator, 500 for computation errors.
    """
    _validate_ts_code(ts_code)

    # Validate indicator name
    valid_indicators = ["macd", "rsi", "kdj", "boll"]
    if indicator not in valid_indicators:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid indicator: {indicator}. Valid options: {valid_indicators}",
        )

    # Parse params
    params_dict = {}
    if params:
        try:
            params_dict = json.loads(params)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid params JSON format",
            )

    # Compute indicators
    service = IndicatorService(db)
    try:
        result = await service.compute_indicators(ts_code, indicator, params_dict)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error computing {indicator} for {ts_code}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "指标计算失败",
                "detail": str(e),
            },
        )
