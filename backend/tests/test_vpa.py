"""Tests for VPA signal detection and K-line pattern recognition.

Tests 10 behaviors:
1. VPAService detects volume_up_rise (confirmation: close > open AND vol > avg_vol_5 * 1.2)
2. VPAService detects volume_down_fall (confirmation: close < open AND vol < avg_vol_5 * 0.8)
3. VPAService detects long_candle_low_volume (anomaly: body_ratio > 0.6 AND vol < avg_vol_5 * 0.7)
4. VPAService detects short_candle_high_volume (anomaly: body_ratio < 0.3 AND vol > avg_vol_5 * 1.5)
5. VPAService detects hammer pattern (lower_shadow >= 2 * body, upper_shadow <= body)
6. VPAService detects shooting star pattern (upper_shadow >= 2 * body, lower_shadow <= body)
7. VPAService detects doji pattern (body / range < 0.1)
8. VPAService detects hanging man (hammer shape in uptrend context)
9. GET /api/indicators/{ts_code}?indicator=macd returns 200 with MACD data
10. GET /api/vpa/{ts_code} returns 200 with signals and patterns arrays
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DailyBar, Stock
from app.services.vpa_service import VPAService


@pytest_asyncio.fixture
async def seed_vpa_data(db_session: AsyncSession):
    """Seed stock data crafted to trigger specific VPA signals and K-line patterns."""
    stock = Stock(
        ts_code="888888.SZ",
        symbol="888888",
        name="VPA测试",
    )
    db_session.add(stock)
    await db_session.commit()

    bars = [
        # Base bars to establish volume average
        DailyBar(
            ts_code="888888.SZ", trade_date="20240101",
            open=10.0, high=10.2, low=9.8, close=10.0, vol=100000.0,
        ),
        DailyBar(
            ts_code="888888.SZ", trade_date="20240102",
            open=10.0, high=10.2, low=9.8, close=10.1, vol=100000.0,
        ),
        DailyBar(
            ts_code="888888.SZ", trade_date="20240103",
            open=10.0, high=10.2, low=9.8, close=10.0, vol=100000.0,
        ),
        DailyBar(
            ts_code="888888.SZ", trade_date="20240104",
            open=10.0, high=10.2, low=9.8, close=10.1, vol=100000.0,
        ),
        DailyBar(
            ts_code="888888.SZ", trade_date="20240105",
            open=10.0, high=10.2, low=9.8, close=10.0, vol=100000.0,
        ),
        # Signal bars
        # Test 1: volume_up_rise - up day with high volume
        DailyBar(
            ts_code="888888.SZ", trade_date="20240106",
            open=10.0, high=10.5, low=9.9, close=10.4, vol=150000.0,
        ),
        # Test 2: volume_down_fall - down day with low volume
        DailyBar(
            ts_code="888888.SZ", trade_date="20240107",
            open=10.4, high=10.4, low=9.8, close=9.9, vol=60000.0,
        ),
        # Test 3: long_candle_low_volume - large body, low volume
        DailyBar(
            ts_code="888888.SZ", trade_date="20240108",
            open=10.0, high=10.7, low=9.9, close=10.6, vol=50000.0,
        ),
        # Test 4: short_candle_high_volume - small body, high volume
        DailyBar(
            ts_code="888888.SZ", trade_date="20240109",
            open=10.0, high=10.3, low=9.7, close=10.05, vol=200000.0,
        ),
        # Test 5: hammer - long lower shadow, small body at top
        DailyBar(
            ts_code="888888.SZ", trade_date="20240110",
            open=9.9, high=10.3, low=9.0, close=10.2, vol=100000.0,
        ),
        # Test 6: shooting star - long upper shadow, small body at bottom
        DailyBar(
            ts_code="888888.SZ", trade_date="20240111",
            open=10.0, high=11.0, low=9.9, close=10.15, vol=100000.0,
        ),
        # Test 7: doji - very small body relative to range
        DailyBar(
            ts_code="888888.SZ", trade_date="20240112",
            open=10.0, high=10.5, low=9.5, close=10.02, vol=100000.0,
        ),
        # Bars for hanging man setup (need uptrend context)
        DailyBar(
            ts_code="888888.SZ", trade_date="20240113",
            open=10.0, high=10.3, low=9.8, close=10.2, vol=100000.0,
        ),
        DailyBar(
            ts_code="888888.SZ", trade_date="20240114",
            open=10.2, high=10.5, low=10.1, close=10.4, vol=100000.0,
        ),
        DailyBar(
            ts_code="888888.SZ", trade_date="20240115",
            open=10.4, high=10.6, low=10.3, close=10.5, vol=100000.0,
        ),
        DailyBar(
            ts_code="888888.SZ", trade_date="20240116",
            open=10.5, high=10.8, low=10.4, close=10.7, vol=100000.0,
        ),
        DailyBar(
            ts_code="888888.SZ", trade_date="20240117",
            open=10.7, high=10.9, low=10.6, close=10.8, vol=100000.0,
        ),
        # Test 8: hanging man - hammer shape but in uptrend
        DailyBar(
            ts_code="888888.SZ", trade_date="20240118",
            open=10.4, high=10.8, low=9.5, close=10.65, vol=100000.0,
        ),
    ]
    db_session.add_all(bars)
    await db_session.commit()
    return stock


# --- Test 1: volume_up_rise ---
class TestVolumeUpRise:
    @pytest.mark.asyncio
    async def test_detects_volume_up_rise(self, db_session, seed_vpa_data):
        """Test 1: up day with vol > avg_vol_5 * 1.2 detected as volume_up_rise."""
        service = VPAService(db_session)
        result = await service.detect_volume_price_signals("888888.SZ")

        signals = result["signals"]
        up_rise = [s for s in signals if s["signal_type"] == "volume_up_rise"]
        assert len(up_rise) > 0, f"Expected volume_up_rise signal, got {signals}"
        # The 20240106 bar should be detected
        up_rise_dates = [s["trade_date"] for s in up_rise]
        assert "20240106" in up_rise_dates


# --- Test 2: volume_down_fall ---
class TestVolumeDownFall:
    @pytest.mark.asyncio
    async def test_detects_volume_down_fall(self, db_session, seed_vpa_data):
        """Test 2: down day with vol < avg_vol_5 * 0.8 detected as volume_down_fall."""
        service = VPAService(db_session)
        result = await service.detect_volume_price_signals("888888.SZ")

        signals = result["signals"]
        down_fall = [s for s in signals if s["signal_type"] == "volume_down_fall"]
        assert len(down_fall) > 0, f"Expected volume_down_fall signal, got {signals}"
        down_dates = [s["trade_date"] for s in down_fall]
        assert "20240107" in down_dates


# --- Test 3: long_candle_low_volume ---
class TestLongCandleLowVolume:
    @pytest.mark.asyncio
    async def test_detects_long_candle_low_volume(self, db_session, seed_vpa_data):
        """Test 3: large body ratio with low volume detected as anomaly."""
        service = VPAService(db_session)
        result = await service.detect_volume_price_signals("888888.SZ")

        signals = result["signals"]
        anomaly = [s for s in signals if s["signal_type"] == "long_candle_low_volume"]
        assert len(anomaly) > 0, f"Expected long_candle_low_volume, got signals: {[s['signal_type'] for s in signals]}"
        anomaly_dates = [s["trade_date"] for s in anomaly]
        assert "20240108" in anomaly_dates


# --- Test 4: short_candle_high_volume ---
class TestShortCandleHighVolume:
    @pytest.mark.asyncio
    async def test_detects_short_candle_high_volume(self, db_session, seed_vpa_data):
        """Test 4: small body with high volume detected as anomaly."""
        service = VPAService(db_session)
        result = await service.detect_volume_price_signals("888888.SZ")

        signals = result["signals"]
        anomaly = [s for s in signals if s["signal_type"] == "short_candle_high_volume"]
        assert len(anomaly) > 0, f"Expected short_candle_high_volume, got signals: {[s['signal_type'] for s in signals]}"
        anomaly_dates = [s["trade_date"] for s in anomaly]
        assert "20240109" in anomaly_dates


# --- Test 5: hammer pattern ---
class TestHammerPattern:
    @pytest.mark.asyncio
    async def test_detects_hammer(self, db_session, seed_vpa_data):
        """Test 5: hammer pattern with long lower shadow, small body."""
        service = VPAService(db_session)
        result = await service.detect_kline_patterns("888888.SZ")

        patterns = result["patterns"]
        hammers = [p for p in patterns if p["pattern_type"] == "hammer"]
        assert len(hammers) > 0, f"Expected hammer pattern, got {[p['pattern_type'] for p in patterns]}"
        hammer_dates = [p["trade_date"] for p in hammers]
        assert "20240110" in hammer_dates


# --- Test 6: shooting star pattern ---
class TestShootingStarPattern:
    @pytest.mark.asyncio
    async def test_detects_shooting_star(self, db_session, seed_vpa_data):
        """Test 6: shooting star pattern with long upper shadow, small body."""
        service = VPAService(db_session)
        result = await service.detect_kline_patterns("888888.SZ")

        patterns = result["patterns"]
        stars = [p for p in patterns if p["pattern_type"] == "shooting_star"]
        assert len(stars) > 0, f"Expected shooting_star pattern, got {[p['pattern_type'] for p in patterns]}"
        star_dates = [p["trade_date"] for p in stars]
        assert "20240111" in star_dates


# --- Test 7: doji pattern ---
class TestDojiPattern:
    @pytest.mark.asyncio
    async def test_detects_doji(self, db_session, seed_vpa_data):
        """Test 7: doji with very small body / range ratio."""
        service = VPAService(db_session)
        result = await service.detect_kline_patterns("888888.SZ")

        patterns = result["patterns"]
        dojis = [p for p in patterns if p["pattern_type"] == "doji"]
        assert len(dojis) > 0, f"Expected doji pattern, got {[p['pattern_type'] for p in patterns]}"
        doji_dates = [p["trade_date"] for p in dojis]
        assert "20240112" in doji_dates


# --- Test 8: hanging man pattern ---
class TestHangingManPattern:
    @pytest.mark.asyncio
    async def test_detects_hanging_man(self, db_session, seed_vpa_data):
        """Test 8: hanging man (hammer shape in uptrend context)."""
        service = VPAService(db_session)
        result = await service.detect_kline_patterns("888888.SZ")

        patterns = result["patterns"]
        hanging_men = [p for p in patterns if p["pattern_type"] == "hanging_man"]
        assert len(hanging_men) > 0, f"Expected hanging_man pattern, got {[p['pattern_type'] for p in patterns]}"
        hm_dates = [p["trade_date"] for p in hanging_men]
        assert "20240118" in hm_dates


# --- Test 9: API endpoint /api/indicators/{ts_code} ---
class TestIndicatorsAPI:
    @pytest.mark.asyncio
    async def test_get_indicators_macd_returns_200(
        self, client: AsyncClient, db_session
    ):
        """Test 9: GET /api/indicators/{ts_code}?indicator=macd returns 200."""
        # Seed data for the indicator API test
        stock = Stock(
            ts_code="777777.SZ", symbol="777777", name="指标测试"
        )
        db_session.add(stock)
        await db_session.commit()

        # Seed enough bars for MACD (need at least 26 + 9 = 35 for full MACD)
        import numpy as np
        from datetime import date, timedelta
        rng = np.random.RandomState(42)
        base = 20.0
        start = date(2024, 1, 1)
        for i in range(50):
            close = base + rng.randn() * 0.5
            o = close + rng.randn() * 0.2
            h = max(o, close) + abs(rng.randn() * 0.3)
            l = min(o, close) - abs(rng.randn() * 0.3)
            d = (start + timedelta(days=i)).strftime("%Y%m%d")
            bar = DailyBar(
                ts_code="777777.SZ",
                trade_date=d,
                open=o, high=h, low=l, close=close, vol=100000.0,
            )
            db_session.add(bar)
        await db_session.commit()

        response = await client.get("/api/indicators/777777.SZ?indicator=macd")
        assert response.status_code == 200
        data = response.json()
        assert "indicator" in data
        assert data["indicator"] == "macd"
        assert "data" in data


# --- Test 10: API endpoint /api/vpa/{ts_code} ---
class TestVPAAPI:
    @pytest.mark.asyncio
    async def test_get_vpa_returns_200_with_signals_and_patterns(
        self, client: AsyncClient, seed_vpa_data
    ):
        """Test 10: GET /api/vpa/{ts_code} returns 200 with signals and patterns."""
        response = await client.get("/api/vpa/888888.SZ")
        assert response.status_code == 200
        data = response.json()
        assert data["ts_code"] == "888888.SZ"
        assert "signals" in data
        assert "patterns" in data
        assert isinstance(data["signals"], list)
        assert isinstance(data["patterns"], list)
