"""Daily K-line data API endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/daily/{ts_code}")
async def get_daily_data(ts_code: str):
    """Get daily K-line data for a stock. Placeholder - implemented in Task 2."""
    return {"ts_code": ts_code, "data": []}
