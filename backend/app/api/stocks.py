"""Stock search API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Stock

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stocks/search")
async def search_stocks(
    keyword: str = Query(default="", description="Search keyword (code or name)"),
    db: AsyncSession = Depends(get_db),
):
    """Search stocks by code or name with fuzzy matching.

    Args:
        keyword: Search term to match against ts_code, symbol, or name.
        db: Async database session.

    Returns:
        List of matching stocks with ts_code, name, symbol, limited to 20 results.

    Raises:
        HTTPException: 400 if keyword is empty.
    """
    if not keyword or not keyword.strip():
        raise HTTPException(
            status_code=400,
            detail="Search keyword cannot be empty",
        )

    keyword = keyword.strip()

    # Fuzzy search across ts_code, symbol, and name
    pattern = f"%{keyword}%"
    from sqlalchemy import select

    stmt = (
        select(Stock.ts_code, Stock.name, Stock.symbol)
        .where(
            or_(
                Stock.ts_code.like(pattern),
                Stock.symbol.like(pattern),
                Stock.name.like(pattern),
            )
        )
        .order_by(Stock.ts_code)
        .limit(20)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {"ts_code": row.ts_code, "name": row.name, "symbol": row.symbol}
        for row in rows
    ]


@router.get("/stocks/{ts_code}")
async def get_stock(
    ts_code: str,
    db: AsyncSession = Depends(get_db),
):
    """Get single stock info by ts_code.

    Args:
        ts_code: Stock code (e.g. "000001.SZ").
        db: Async database session.

    Returns:
        Stock details.

    Raises:
        HTTPException: 404 if stock not found.
    """
    from sqlalchemy import select

    stmt = select(Stock).where(Stock.ts_code == ts_code)
    result = await db.execute(stmt)
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(
            status_code=404,
            detail=f"Stock {ts_code} not found",
        )

    return {
        "ts_code": stock.ts_code,
        "symbol": stock.symbol,
        "name": stock.name,
        "area": stock.area,
        "industry": stock.industry,
        "market": stock.market,
        "list_date": stock.list_date,
    }
