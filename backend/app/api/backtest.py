"""Backtest API endpoints for strategy backtesting module."""

import logging
from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.backtest_service import BacktestService
from app.services.expression_parser import parse_and_validate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backtest", tags=["backtest"])


# --- Request models ---


class IndicatorConfig(BaseModel):
    """Custom indicator configuration."""

    name: str
    expression: str


class ConditionRule(BaseModel):
    """Individual condition rule."""

    type: str = "rule"
    indicator: str
    operator: str
    threshold: Optional[float] = None
    threshold_indicator: Optional[str] = None


class ConditionGroup(BaseModel):
    """Group of conditions with AND/OR logic."""

    type: str = "group"
    operator: str
    children: list[Union["ConditionRule", "ConditionGroup"]]


# Support recursive model
ConditionGroup.model_rebuild()


class RunBacktestRequest(BaseModel):
    """Request body for running a backtest."""

    ts_code: str
    stock_name: str = ""
    start_date: str
    end_date: str
    initial_capital: float = 1000000.0
    indicators_config: list[IndicatorConfig]
    buy_conditions: ConditionGroup
    sell_conditions: ConditionGroup


class ValidateExpressionRequest(BaseModel):
    """Request body for expression validation."""

    expression: str


# --- Endpoints ---


@router.post("/run")
async def run_backtest(
    body: RunBacktestRequest,
    db: AsyncSession = Depends(get_db),
):
    """Run a strategy backtest.

    Validates indicator expressions, runs day-by-day simulation with
    A-share rules, and returns trades, equity curve, and metrics.

    Args:
        body: Backtest configuration including indicators and conditions.
        db: Async database session.

    Returns:
        Full backtest result with session_id, trades, curves, and statistics.

    Raises:
        HTTPException: 400 for invalid expressions/config; 500 on server error.
    """
    try:
        # Pre-validate all indicator expressions
        for ind in body.indicators_config:
            try:
                parse_and_validate(ind.expression)
            except (SyntaxError, ValueError) as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid indicator '{ind.name}': {str(e)}",
                )

        service = BacktestService(db)
        result = await service.run_backtest(
            ts_code=body.ts_code,
            start_date=body.start_date,
            end_date=body.end_date,
            initial_capital=body.initial_capital,
            indicators_config=[ind.model_dump() for ind in body.indicators_config],
            buy_conditions=body.buy_conditions.model_dump(),
            sell_conditions=body.sell_conditions.model_dump(),
            stock_name=body.stock_name,
        )
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to run backtest: {e}")
        raise HTTPException(status_code=500, detail="回测运行失败")


@router.get("/presets")
async def get_presets(
    db: AsyncSession = Depends(get_db),
):
    """List preset strategy templates.

    Returns predefined strategy configurations that users can use
    as starting points for their own backtests.

    Args:
        db: Async database session.

    Returns:
        List of preset strategy config dicts.
    """
    try:
        service = BacktestService(db)
        return await service.get_presets()
    except Exception as e:
        logger.error(f"Failed to get presets: {e}")
        raise HTTPException(status_code=500, detail="获取预设策略失败")


@router.get("/sessions")
async def list_sessions(
    ts_code: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List backtest session history.

    Args:
        ts_code: Optional stock code filter.
        limit: Maximum results (default 20).
        offset: Pagination offset.
        db: Async database session.

    Returns:
        Dict with total count and sessions list.
    """
    try:
        service = BacktestService(db)
        return await service.list_sessions(
            ts_code=ts_code, limit=limit, offset=offset
        )
    except Exception as e:
        logger.error(f"Failed to list backtest sessions: {e}")
        raise HTTPException(status_code=500, detail="获取回测记录失败")


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single backtest session result.

    Args:
        session_id: Backtest session ID.
        db: Async database session.

    Returns:
        Full session data with trades and configuration.

    Raises:
        HTTPException: 404 if session not found.
    """
    try:
        service = BacktestService(db)
        return await service.get_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get backtest session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="获取回测详情失败")


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a backtest session and its trades.

    Args:
        session_id: Backtest session ID.
        db: Async database session.

    Returns:
        Dict with success status.

    Raises:
        HTTPException: 404 if session not found.
    """
    try:
        service = BacktestService(db)
        return await service.delete_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete backtest session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="删除回测记录失败")


@router.post("/validate-expression")
async def validate_expression(
    body: ValidateExpressionRequest,
):
    """Validate an expression without running a backtest.

    Checks syntax and whitelist compliance. Returns field list on success
    or error message on failure.

    Args:
        body: Dict with expression string.

    Returns:
        Dict with valid flag, fields list (on success) or error message.
    """
    try:
        tree, fields = parse_and_validate(body.expression)
        return {"valid": True, "fields": fields}
    except (SyntaxError, ValueError) as e:
        return {"valid": False, "error": str(e)}
