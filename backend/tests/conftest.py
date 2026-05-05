"""Test fixtures for backend API tests."""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models import DailyBar, Stock


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite://"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override get_db to use test database."""
    async with TestSessionLocal() as session:
        yield session


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a test database session."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def seed_stocks(db_session: AsyncSession) -> list[Stock]:
    """Seed test stock data."""
    stocks = [
        Stock(
            ts_code="000001.SZ",
            symbol="000001",
            name="平安银行",
            area="深圳",
            industry="银行",
            market="主板",
        ),
        Stock(
            ts_code="600519.SH",
            symbol="600519",
            name="贵州茅台",
            area="贵州",
            industry="白酒",
            market="主板",
        ),
        Stock(
            ts_code="000002.SZ",
            symbol="000002",
            name="万科A",
            area="深圳",
            industry="房地产",
            market="主板",
        ),
    ]
    db_session.add_all(stocks)
    await db_session.commit()
    for s in stocks:
        await db_session.refresh(s)
    return stocks


@pytest_asyncio.fixture
async def seed_daily_bars(db_session: AsyncSession, seed_stocks: list[Stock]) -> list[DailyBar]:
    """Seed test daily bar data for 000001.SZ."""
    bars = [
        DailyBar(
            ts_code="000001.SZ",
            trade_date="20240102",
            open=10.5,
            high=10.8,
            low=10.3,
            close=10.7,
            pre_close=10.4,
            change_pct=2.88,
            vol=100000.0,
            amount=107000.0,
        ),
        DailyBar(
            ts_code="000001.SZ",
            trade_date="20240103",
            open=10.7,
            high=10.9,
            low=10.5,
            close=10.6,
            pre_close=10.7,
            change_pct=-0.93,
            vol=80000.0,
            amount=84800.0,
        ),
        DailyBar(
            ts_code="000001.SZ",
            trade_date="20240104",
            open=10.6,
            high=11.0,
            low=10.5,
            close=10.9,
            pre_close=10.6,
            change_pct=2.83,
            vol=120000.0,
            amount=130800.0,
        ),
        DailyBar(
            ts_code="000001.SZ",
            trade_date="20240501",
            open=11.0,
            high=11.2,
            low=10.9,
            close=11.1,
            pre_close=10.9,
            change_pct=1.83,
            vol=90000.0,
            amount=99900.0,
        ),
    ]
    db_session.add_all(bars)
    await db_session.commit()
    for b in bars:
        await db_session.refresh(b)
    return bars
