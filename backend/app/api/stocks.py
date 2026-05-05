"""Stock search API endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/stocks/search")
async def search_stocks(keyword: str = ""):
    """Search stocks by code or name. Placeholder - implemented in Task 2."""
    return []
