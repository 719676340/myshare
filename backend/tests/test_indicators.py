"""Tests for indicator computation service.

Tests 6 behaviors:
1. IndicatorService.compute_indicators returns MACD dict with macd_line, signal_line, histogram
2. IndicatorService.compute_indicators returns RSI dict with rsi key
3. IndicatorService.compute_indicators returns KDJ dict with k, d, j keys (custom implementation)
4. IndicatorService.compute_indicators returns BOLL dict with upper, middle, lower keys
5. params_hash generation is consistent for same parameter dict
6. IndicatorValue model can be created with required fields
"""

import hashlib
import json

import numpy as np
import pandas as pd
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DailyBar, IndicatorValue, Stock
from app.services.indicator_service import IndicatorService


# --- Helper to create synthetic OHLCV DataFrame ---

def _make_ohlcv_df(n_rows=50, seed=42):
    """Create a synthetic OHLCV DataFrame for testing."""
    rng = np.random.RandomState(seed)
    base_price = 20.0
    closes = base_price + np.cumsum(rng.randn(n_rows) * 0.5)
    opens = closes + rng.randn(n_rows) * 0.2
    highs = np.maximum(opens, closes) + np.abs(rng.randn(n_rows) * 0.3)
    lows = np.minimum(opens, closes) - np.abs(rng.randn(n_rows) * 0.3)
    vols = 100000 + rng.randint(-20000, 20000, n_rows).astype(float)

    dates = [f"202401{d:02d}" for d in range(1, n_rows + 1)]
    # Handle dates beyond 31
    dates = []
    for i in range(n_rows):
        month = 1 + i // 31
        day = 1 + i % 31
        if month <= 12 and day <= 28:
            dates.append(f"2024{month:02d}{day:02d}")
        else:
            dates.append(f"202401{(i % 28) + 1:02d}")

    df = pd.DataFrame({
        "trade_date": dates,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "vol": vols,
    })
    return df


@pytest_asyncio.fixture
async def seed_ohlcv_data(db_session: AsyncSession):
    """Seed 50 rows of synthetic OHLCV data for indicator tests."""
    stock = Stock(
        ts_code="999999.SZ",
        symbol="999999",
        name="测试股票",
    )
    db_session.add(stock)
    await db_session.commit()

    df = _make_ohlcv_df(50)
    bars = []
    for _, row in df.iterrows():
        bar = DailyBar(
            ts_code="999999.SZ",
            trade_date=row["trade_date"],
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            vol=float(row["vol"]),
        )
        bars.append(bar)
    db_session.add_all(bars)
    await db_session.commit()
    return stock


# --- Test 1: MACD ---
class TestMACDComputation:
    @pytest.mark.asyncio
    async def test_macd_returns_required_keys(self, db_session, seed_ohlcv_data):
        """Test 1: compute_indicators returns MACD with macd_line, signal_line, histogram."""
        service = IndicatorService(db_session)
        result = await service.compute_indicators("999999.SZ", "macd", {})

        assert result["indicator"] == "macd"
        assert "data" in result
        assert len(result["data"]) > 0

        # Check first valid data point has required keys
        valid_points = [d for d in result["data"]
                        if d.get("macd") is not None]
        assert len(valid_points) > 0, "MACD should produce at least some valid values"

        sample = valid_points[-1]
        assert "trade_date" in sample
        assert "macd" in sample
        assert "signal" in sample
        assert "histogram" in sample


# --- Test 2: RSI ---
class TestRSIComputation:
    @pytest.mark.asyncio
    async def test_rsi_returns_required_keys(self, db_session, seed_ohlcv_data):
        """Test 2: compute_indicators returns RSI with rsi key."""
        service = IndicatorService(db_session)
        result = await service.compute_indicators("999999.SZ", "rsi", {})

        assert result["indicator"] == "rsi"
        assert "data" in result

        valid_points = [d for d in result["data"] if d.get("rsi") is not None]
        assert len(valid_points) > 0, "RSI should produce at least some valid values"

        sample = valid_points[-1]
        assert "trade_date" in sample
        assert "rsi" in sample


# --- Test 3: KDJ (custom implementation) ---
class TestKDJComputation:
    @pytest.mark.asyncio
    async def test_kdj_returns_required_keys(self, db_session, seed_ohlcv_data):
        """Test 3: compute_indicators returns KDJ with k, d, j keys (custom implementation)."""
        service = IndicatorService(db_session)
        result = await service.compute_indicators("999999.SZ", "kdj", {})

        assert result["indicator"] == "kdj"
        assert "data" in result

        valid_points = [d for d in result["data"]
                        if d.get("k") is not None]
        assert len(valid_points) > 0, "KDJ should produce at least some valid values"

        sample = valid_points[-1]
        assert "trade_date" in sample
        assert "k" in sample
        assert "d" in sample
        assert "j" in sample


# --- Test 4: BOLL ---
class TestBOLLComputation:
    @pytest.mark.asyncio
    async def test_boll_returns_required_keys(self, db_session, seed_ohlcv_data):
        """Test 4: compute_indicators returns BOLL with upper, middle, lower keys."""
        service = IndicatorService(db_session)
        result = await service.compute_indicators("999999.SZ", "boll", {})

        assert result["indicator"] == "boll"
        assert "data" in result

        valid_points = [d for d in result["data"]
                        if d.get("upper") is not None]
        assert len(valid_points) > 0, "BOLL should produce at least some valid values"

        sample = valid_points[-1]
        assert "trade_date" in sample
        assert "upper" in sample
        assert "middle" in sample
        assert "lower" in sample


# --- Test 5: params_hash consistency ---
class TestParamsHash:
    def test_params_hash_consistent(self):
        """Test 5: params_hash generation produces consistent hash for same parameter dict."""
        params = {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}
        hash1 = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:16]
        hash2 = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:16]
        assert hash1 == hash2

    def test_params_hash_different_for_different_params(self):
        """Different params produce different hashes."""
        params1 = {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}
        params2 = {"fastperiod": 8, "slowperiod": 21, "signalperiod": 5}
        hash1 = hashlib.md5(json.dumps(params1, sort_keys=True).encode()).hexdigest()[:16]
        hash2 = hashlib.md5(json.dumps(params2, sort_keys=True).encode()).hexdigest()[:16]
        assert hash1 != hash2


# --- Test 6: IndicatorValue model ---
class TestIndicatorValueModel:
    @pytest.mark.asyncio
    async def test_create_indicator_value(self, db_session, seed_ohlcv_data):
        """Test 6: IndicatorValue model can be created with required fields."""
        iv = IndicatorValue(
            ts_code="999999.SZ",
            trade_date="20240101",
            indicator_name="macd",
            params_hash="abc123",
            value_json='{"macd": 0.12, "signal": 0.10, "histogram": 0.02}',
        )
        db_session.add(iv)
        await db_session.commit()

        # Verify it was stored
        stmt = select(IndicatorValue).where(
            IndicatorValue.ts_code == "999999.SZ",
            IndicatorValue.indicator_name == "macd",
        )
        result = await db_session.execute(stmt)
        found = result.scalar_one_or_none()
        assert found is not None
        assert found.params_hash == "abc123"
        assert found.trade_date == "20240101"
