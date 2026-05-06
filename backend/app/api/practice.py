"""Practice session API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.practice_service import PracticeService

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Request models ---


class CreateSessionRequest(BaseModel):
    """Request body for creating a practice session."""

    ts_code: str
    start_date: str
    end_date: str
    initial_capital: float = 1000000.0


class OrderRequest(BaseModel):
    """Request body for placing a buy order."""

    shares: int
    price: float


class SellOrderRequest(BaseModel):
    """Request body for placing a sell order."""

    position_id: int
    shares: int
    price: float


# --- Endpoints ---


@router.post("/practice/sessions")
async def create_session(
    body: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new practice session.

    Creates a trading practice session for the given stock and date range.
    The session starts with bars visible up to the day before start_date.
    The first advance_day call reveals the start_date bar.

    Args:
        body: Session parameters (ts_code, start_date, end_date, initial_capital).
        db: Async database session.

    Returns:
        Dict with session_id and status.

    Raises:
        HTTPException: 400 if stock not found or no data; 500 on server error.
    """
    try:
        service = PracticeService(db)
        result = await service.create_session(
            ts_code=body.ts_code,
            start_date=body.start_date,
            end_date=body.end_date,
            initial_capital=body.initial_capital,
        )
        return {"status": "created", "session_id": result.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail="创建练习会话失败")


@router.get("/practice/sessions/{session_id}")
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get full session state.

    Returns session info, visible K-line data up to current_date,
    positions with market values, trade history, and portfolio stats.

    Args:
        session_id: Practice session ID.
        db: Async database session.

    Returns:
        Full session state dict.

    Raises:
        HTTPException: 400 if session not found; 500 on server error.
    """
    try:
        service = PracticeService(db)
        return await service.get_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="获取练习会话失败")


@router.post("/practice/sessions/{session_id}/advance")
async def advance_day(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Advance session to the next trading day.

    Reveals the next K-line bar and updates the session's current_date.
    Cannot advance past the last trading day.

    Args:
        session_id: Practice session ID.
        db: Async database session.

    Returns:
        Dict with new current_date, revealed bar data, and is_final flag.

    Raises:
        HTTPException: 400 if session finished or no more days; 500 on server error.
    """
    try:
        service = PracticeService(db)
        return await service.advance_day(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to advance session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="推进日期失败")


@router.post("/practice/sessions/{session_id}/buy")
async def buy_order(
    session_id: int,
    body: OrderRequest,
    db: AsyncSession = Depends(get_db),
):
    """Execute a buy order.

    Validates price limits and available cash before executing.
    Creates a new position lot for FIFO tracking.

    Args:
        session_id: Practice session ID.
        body: Order parameters (shares, price).
        db: Async database session.

    Returns:
        Dict with trade details and confirmation message.

    Raises:
        HTTPException: 400 if validation fails; 500 on server error.
    """
    try:
        service = PracticeService(db)
        return await service.buy_order(
            session_id=session_id,
            shares=body.shares,
            price=body.price,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute buy for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="买入操作失败")


@router.post("/practice/sessions/{session_id}/sell")
async def sell_order(
    session_id: int,
    body: SellOrderRequest,
    db: AsyncSession = Depends(get_db),
):
    """Execute a sell order.

    Validates T+1 rule, price limits, and position availability.
    Applies commission and stamp tax on sell side.

    Args:
        session_id: Practice session ID.
        body: Sell order parameters (position_id, shares, price).
        db: Async database session.

    Returns:
        Dict with trade details and confirmation message.

    Raises:
        HTTPException: 400 if validation fails; 500 on server error.
    """
    try:
        service = PracticeService(db)
        return await service.sell_order(
            session_id=session_id,
            position_id=body.position_id,
            shares=body.shares,
            price=body.price,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute sell for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="卖出操作失败")


@router.post("/practice/sessions/{session_id}/end")
async def end_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    """End a practice session.

    Marks the session as finished. After ending, no more trades or
    day advances are allowed.

    Args:
        session_id: Practice session ID.
        db: Async database session.

    Returns:
        Dict with finished status.

    Raises:
        HTTPException: 400 if session already finished; 500 on server error.
    """
    try:
        service = PracticeService(db)
        return await service.end_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to end session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="结束练习失败")


@router.get("/practice/sessions/{session_id}/stats")
async def get_stats(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive trading statistics.

    Returns paired trade history (FIFO), equity curve, and summary
    metrics including total return, win rate, and fee totals.

    Args:
        session_id: Practice session ID.
        db: Async database session.

    Returns:
        Dict with trade pairs, equity curve, and aggregate statistics.

    Raises:
        HTTPException: 400 if session not found; 500 on server error.
    """
    try:
        service = PracticeService(db)
        return await service.get_stats(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get stats for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")
