"""FastAPI application for the 量价交易学习平台 backend."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import async_session, init_db

logger = logging.getLogger(__name__)


async def _preload_stock_list():
    """Pre-load stock list into DB on startup if table is empty."""
    from app.services.data_fetcher import DataFetcher
    from app.services.tushare_client import TushareClient

    async with async_session() as session:
        try:
            tushare_client = TushareClient(settings.tushare_token)
            fetcher = DataFetcher(session, tushare_client)
            await fetcher.ensure_stock_list()
            logger.info("Stock list pre-loaded successfully")
        except Exception as e:
            # Non-fatal: stock list can be loaded on first search request
            logger.warning(f"Failed to pre-load stock list: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized")

    # Pre-load stock list if tushare token is available
    if settings.tushare_token:
        await _preload_stock_list()
    else:
        logger.warning(
            "TUSHARE_TOKEN not set. Stock list will not be pre-loaded. "
            "Set TUSHARE_TOKEN environment variable or add it to .env file."
        )

    yield

    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title="量价交易学习平台 API",
    description="Backend API for A-share market data and analysis",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "db": "connected"}


# Import and mount routers (registered after app creation to avoid circular imports)
from app.api.stocks import router as stocks_router  # noqa: E402
from app.api.daily import router as daily_router  # noqa: E402
from app.api.indicators import router as indicators_router  # noqa: E402
from app.api.vpa import router as vpa_router  # noqa: E402
from app.api.advanced import router as advanced_router  # noqa: E402
from app.api.practice import router as practice_router  # noqa: E402
from app.api.backtest import router as backtest_router  # noqa: E402

app.include_router(stocks_router, prefix="/api")
app.include_router(daily_router, prefix="/api")
app.include_router(indicators_router, prefix="/api")
app.include_router(vpa_router, prefix="/api")
app.include_router(advanced_router, prefix="/api")
app.include_router(practice_router, prefix="/api")
app.include_router(backtest_router, prefix="/api")
