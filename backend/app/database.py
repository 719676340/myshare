"""Async SQLAlchemy database setup."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=False,
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class."""
    pass


async def get_db():
    """FastAPI dependency that provides an async database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables. Called on application startup."""
    async with engine.begin() as conn:
        # Import models so they register with Base.metadata
        from app.models import Stock, DailyBar, IndicatorValue  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
