"""Tests for AdvancedAnalysisService: pivot detection, support/resistance,
trend lines, market cycle, VAP, K-line aggregation, and divergence detection."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DailyBar, Stock
from app.services.advanced_analysis_service import AdvancedAnalysisService


# --- Helpers to seed structured test data ---


async def _seed_stock(db_session: AsyncSession, ts_code: str = "000001.SZ") -> Stock:
    """Seed a single stock record."""
    stock = Stock(
        ts_code=ts_code,
        symbol=ts_code.split(".")[0],
        name="TestStock",
        area="Test",
        industry="Test",
        market="Test",
    )
    db_session.add(stock)
    await db_session.commit()
    await db_session.refresh(stock)
    return stock


async def _seed_bars(db_session: AsyncSession, ts_code: str, bars_data: list[dict]):
    """Seed daily bars from list of dicts. Each dict must have trade_date, open, high, low, close, vol."""
    bars = []
    for bd in bars_data:
        bars.append(
            DailyBar(
                ts_code=ts_code,
                trade_date=bd["trade_date"],
                open=bd["open"],
                high=bd["high"],
                low=bd["low"],
                close=bd["close"],
                pre_close=bd.get("pre_close", bd["open"]),
                change_pct=bd.get("change_pct", 0),
                vol=bd["vol"],
                amount=bd.get("amount", 0),
            )
        )
    db_session.add_all(bars)
    await db_session.commit()


def _make_pivot_data():
    """Create test data with clear isolated high and low pivots.

    Layout (5 bars):
      Bar 0: normal
      Bar 1: isolated HIGH pivot (both high and low > neighbors)
      Bar 2: normal (lower than bar 1, higher than bar 3)
      Bar 3: isolated LOW pivot (both high and low < neighbors)
      Bar 4: normal
    """
    return [
        {"trade_date": "20240102", "open": 10.0, "high": 10.5, "low": 9.5, "close": 10.2, "vol": 100000},
        # Isolated high pivot: high=12.0 > 10.5 and 11.0; low=10.0 > 9.5 and 9.0
        {"trade_date": "20240103", "open": 11.0, "high": 12.0, "low": 10.0, "close": 11.5, "vol": 120000},
        {"trade_date": "20240104", "open": 10.5, "high": 11.0, "low": 9.0, "close": 10.0, "vol": 90000},
        # Isolated low pivot: low=8.0 < 9.0 and 9.0; high=10.0 < 11.0 and 11.0
        {"trade_date": "20240105", "open": 9.0, "high": 10.0, "low": 8.0, "close": 9.0, "vol": 110000},
        {"trade_date": "20240108", "open": 9.5, "high": 11.0, "low": 9.0, "close": 10.0, "vol": 95000},
    ]


def _make_trending_data(n=60):
    """Create trending data with a clear up-then-down pattern.

    First 30 bars: gradual uptrend (markup phase)
    Next 30 bars: gradual downtrend (markdown phase)
    """
    bars = []
    base_date = 20240101
    for i in range(n):
        day = i + 1
        trade_date = f"{base_date + day:08d}"
        if i < 30:
            # Uptrend: prices rising, volume rising on up days
            price = 10.0 + i * 0.2
            vol = 80000 + i * 1000
        else:
            # Downtrend: prices falling, volume high on down days
            price = 16.0 - (i - 30) * 0.2
            vol = 100000 + (i - 30) * 500
        bars.append({
            "trade_date": trade_date,
            "open": price - 0.1,
            "high": price + 0.3,
            "low": price - 0.3,
            "close": price + 0.1 if i < 30 else price - 0.1,
            "vol": vol,
        })
    return bars


# --- Test: Isolated High Pivot Detection ---


@pytest.mark.asyncio
async def test_detect_isolated_high_pivot(db_session: AsyncSession):
    """detect_pivots returns bar index where middle bar high > left high AND
    middle bar high > right high AND middle bar low > left low AND
    middle bar low > right low (isolated high pivot per Chapter 07)."""
    await _seed_stock(db_session)
    data = _make_pivot_data()
    await _seed_bars(db_session, "000001.SZ", data)

    service = AdvancedAnalysisService(db_session)
    result = await service.detect_pivots("000001.SZ")

    high_pivots = [p for p in result["pivots"] if p["type"] == "high"]
    assert len(high_pivots) >= 1, "Should detect at least one high pivot"
    # Bar at index 1 should be a high pivot
    hp = high_pivots[0]
    assert hp["bar_index"] == 1
    assert hp["trade_date"] == "20240103"
    assert hp["price"] == 12.0  # high of the pivot bar


# --- Test: Isolated Low Pivot Detection ---


@pytest.mark.asyncio
async def test_detect_isolated_low_pivot(db_session: AsyncSession):
    """detect_pivots returns bar index where middle bar low < left low AND
    middle bar low < right low AND middle bar high < left high AND
    middle bar high < right high (isolated low pivot per Chapter 07)."""
    await _seed_stock(db_session)
    data = _make_pivot_data()
    await _seed_bars(db_session, "000001.SZ", data)

    service = AdvancedAnalysisService(db_session)
    result = await service.detect_pivots("000001.SZ")

    low_pivots = [p for p in result["pivots"] if p["type"] == "low"]
    assert len(low_pivots) >= 1, "Should detect at least one low pivot"
    # Bar at index 3 should be a low pivot
    lp = low_pivots[0]
    assert lp["bar_index"] == 3
    assert lp["trade_date"] == "20240105"
    assert lp["price"] == 8.0  # low of the pivot bar


# --- Test: Support/Resistance Level Grouping ---


@pytest.mark.asyncio
async def test_detect_support_resistance(db_session: AsyncSession):
    """detect_support_resistance groups nearby pivot prices (within 2%
    tolerance) into levels, returns list of {price, type, strength, trade_dates}."""
    await _seed_stock(db_session)
    # Create data with multiple pivots at similar price levels
    data = [
        # First group of pivots around price ~12
        {"trade_date": "20240102", "open": 10.0, "high": 10.5, "low": 9.5, "close": 10.2, "vol": 100000},
        {"trade_date": "20240103", "open": 11.0, "high": 12.0, "low": 10.0, "close": 11.5, "vol": 120000},  # high pivot ~12
        {"trade_date": "20240104", "open": 10.5, "high": 11.0, "low": 9.0, "close": 10.0, "vol": 90000},
        {"trade_date": "20240105", "open": 9.0, "high": 10.0, "low": 8.0, "close": 9.0, "vol": 110000},  # low pivot ~8
        {"trade_date": "20240108", "open": 9.5, "high": 11.0, "low": 9.0, "close": 10.0, "vol": 95000},
        # Second group with another pivot near 12
        {"trade_date": "20240109", "open": 10.0, "high": 10.5, "low": 9.5, "close": 10.2, "vol": 100000},
        {"trade_date": "20240110", "open": 11.5, "high": 12.2, "low": 10.5, "close": 11.8, "vol": 130000},  # high pivot ~12.2
        {"trade_date": "20240111", "open": 10.5, "high": 11.0, "low": 9.0, "close": 10.0, "vol": 90000},
        {"trade_date": "20240112", "open": 9.0, "high": 10.0, "low": 8.0, "close": 9.0, "vol": 110000},  # low pivot ~8
        {"trade_date": "20240115", "open": 9.5, "high": 11.0, "low": 9.0, "close": 10.0, "vol": 95000},
    ]
    await _seed_bars(db_session, "000001.SZ", data)

    service = AdvancedAnalysisService(db_session)
    result = await service.detect_support_resistance("000001.SZ")

    assert "levels" in result
    levels = result["levels"]
    assert len(levels) >= 1, "Should detect at least one support/resistance level"

    # Each level should have price, type, strength, trade_dates
    for level in levels:
        assert "price" in level
        assert "type" in level
        assert level["type"] in ("support", "resistance", "both")
        assert "strength" in level
        assert "trade_dates" in level
        assert isinstance(level["strength"], int)
        assert level["strength"] >= 1


# --- Test: Trend Line Detection ---


@pytest.mark.asyncio
async def test_detect_trend_lines(db_session: AsyncSession):
    """detect_trend_lines connects consecutive high pivots with line and
    consecutive low pivots with line, returns [{start_date, end_date,
    start_price, end_price, type: 'up'|'down'|'horizontal'}]."""
    await _seed_stock(db_session)
    # Create data with clear consecutive pivots for trend lines
    data = [
        {"trade_date": "20240102", "open": 10.0, "high": 10.5, "low": 9.5, "close": 10.2, "vol": 100000},
        {"trade_date": "20240103", "open": 11.0, "high": 12.0, "low": 10.0, "close": 11.5, "vol": 120000},  # high pivot 1
        {"trade_date": "20240104", "open": 10.5, "high": 11.0, "low": 9.0, "close": 10.0, "vol": 90000},
        {"trade_date": "20240105", "open": 9.0, "high": 10.0, "low": 8.0, "close": 9.0, "vol": 110000},  # low pivot 1
        {"trade_date": "20240108", "open": 9.5, "high": 11.0, "low": 9.0, "close": 10.0, "vol": 95000},
        {"trade_date": "20240109", "open": 10.0, "high": 10.5, "low": 9.5, "close": 10.2, "vol": 100000},
        {"trade_date": "20240110", "open": 11.5, "high": 13.0, "low": 10.5, "close": 12.0, "vol": 130000},  # high pivot 2 (higher)
        {"trade_date": "20240111", "open": 11.0, "high": 11.5, "low": 9.5, "close": 10.5, "vol": 90000},
        {"trade_date": "20240112", "open": 9.5, "high": 10.5, "low": 8.5, "close": 9.0, "vol": 110000},  # low pivot 2 (higher than 1st low)
        {"trade_date": "20240115", "open": 9.5, "high": 11.0, "low": 9.0, "close": 10.0, "vol": 95000},
    ]
    await _seed_bars(db_session, "000001.SZ", data)

    service = AdvancedAnalysisService(db_session)
    result = await service.detect_trend_lines("000001.SZ")

    assert "lines" in result
    lines = result["lines"]
    assert len(lines) >= 1, "Should detect at least one trend line"

    for line in lines:
        assert "start_date" in line
        assert "end_date" in line
        assert "start_price" in line
        assert "end_price" in line
        assert "type" in line
        assert line["type"] in ("up", "down", "horizontal")
        assert "pivot_type" in line


# --- Test: Market Cycle Phase Detection ---


@pytest.mark.asyncio
async def test_detect_market_cycle(db_session: AsyncSession):
    """detect_market_cycle segments data into phases: accumulation, markup,
    distribution, markdown. Returns [{phase, start_date, end_date, description}]."""
    await _seed_stock(db_session)
    data = _make_trending_data(60)
    await _seed_bars(db_session, "000001.SZ", data)

    service = AdvancedAnalysisService(db_session)
    result = await service.detect_market_cycle("000001.SZ")

    assert "phases" in result
    phases = result["phases"]
    assert len(phases) >= 1, "Should detect at least one market phase"

    valid_phases = {"accumulation", "markup", "distribution", "markdown"}
    for phase in phases:
        assert "phase" in phase
        assert phase["phase"] in valid_phases
        assert "start_date" in phase
        assert "end_date" in phase
        assert "description" in phase


# --- Test: VAP (Volume at Price) ---


@pytest.mark.asyncio
async def test_compute_vap(db_session: AsyncSession):
    """compute_vap bins visible range data into price levels (auto-sized bins),
    returns [{price_level, volume, up_volume, down_volume}]."""
    await _seed_stock(db_session)
    data = [
        {"trade_date": "20240102", "open": 10.0, "high": 11.0, "low": 9.0, "close": 10.5, "vol": 100000},  # up bar
        {"trade_date": "20240103", "open": 10.5, "high": 11.5, "low": 9.5, "close": 10.0, "vol": 80000},  # down bar
        {"trade_date": "20240104", "open": 10.0, "high": 11.0, "low": 9.0, "close": 10.8, "vol": 120000},  # up bar
    ]
    await _seed_bars(db_session, "000001.SZ", data)

    service = AdvancedAnalysisService(db_session)
    result = await service.compute_vap("000001.SZ")

    assert "vap" in result
    assert "price_range" in result
    assert "total_volume" in result
    assert result["total_volume"] == 300000.0

    vap = result["vap"]
    assert len(vap) > 0, "VAP should have price bins"
    for entry in vap:
        assert "price_level" in entry
        assert "volume" in entry
        assert "up_volume" in entry
        assert "down_volume" in entry


@pytest.mark.asyncio
async def test_compute_vap_with_date_range(db_session: AsyncSession):
    """compute_vap respects start_date and end_date filters."""
    await _seed_stock(db_session)
    data = [
        {"trade_date": "20240102", "open": 10.0, "high": 11.0, "low": 9.0, "close": 10.5, "vol": 100000},
        {"trade_date": "20240103", "open": 10.5, "high": 11.5, "low": 9.5, "close": 10.0, "vol": 80000},
        {"trade_date": "20240104", "open": 10.0, "high": 11.0, "low": 9.0, "close": 10.8, "vol": 120000},
    ]
    await _seed_bars(db_session, "000001.SZ", data)

    service = AdvancedAnalysisService(db_session)
    result = await service.compute_vap("000001.SZ", start_date="20240103", end_date="20240103")

    assert result["total_volume"] == 80000.0


# --- Test: Weekly K-line Aggregation ---


@pytest.mark.asyncio
async def test_aggregate_weekly(db_session: AsyncSession):
    """aggregate_kline(weekly) returns OHLCV bars grouped by ISO week,
    open=first open, high=max high, low=min low, close=last close, vol=sum vol."""
    await _seed_stock(db_session)
    # 2024-01-02 (Tue) to 2024-01-08 (Mon) = two ISO weeks
    data = [
        {"trade_date": "20240102", "open": 10.0, "high": 10.5, "low": 9.5, "close": 10.2, "vol": 100000},
        {"trade_date": "20240103", "open": 10.2, "high": 10.8, "low": 9.8, "close": 10.5, "vol": 110000},
        {"trade_date": "20240104", "open": 10.5, "high": 11.0, "low": 10.0, "close": 10.8, "vol": 120000},
        {"trade_date": "20240105", "open": 10.8, "high": 11.2, "low": 10.3, "close": 10.6, "vol": 90000},
        # Next week (ISO week 2: Jan 8-12)
        {"trade_date": "20240108", "open": 10.6, "high": 10.9, "low": 10.0, "close": 10.3, "vol": 80000},
        {"trade_date": "20240109", "open": 10.3, "high": 10.7, "low": 9.8, "close": 10.5, "vol": 95000},
    ]
    await _seed_bars(db_session, "000001.SZ", data)

    service = AdvancedAnalysisService(db_session)
    result = await service.aggregate_kline("000001.SZ", timeframe="weekly")

    assert result["timeframe"] == "weekly"
    weekly_data = result["data"]
    assert len(weekly_data) == 2  # Two weeks

    # First week: Jan 2-5 (ISO week 1)
    week1 = weekly_data[0]
    assert week1["open"] == 10.0  # first open
    assert week1["high"] == 11.2  # max high
    assert week1["low"] == 9.5  # min low
    assert week1["close"] == 10.6  # last close
    assert week1["vol"] == 420000  # sum vol (100k+110k+120k+90k)

    # Second week: Jan 8-9 (ISO week 2)
    week2 = weekly_data[1]
    assert week2["open"] == 10.6
    assert week2["high"] == 10.9
    assert week2["low"] == 9.8
    assert week2["close"] == 10.5
    assert week2["vol"] == 175000  # 80k + 95k


# --- Test: Monthly K-line Aggregation ---


@pytest.mark.asyncio
async def test_aggregate_monthly(db_session: AsyncSession):
    """aggregate_kline(monthly) returns OHLCV bars grouped by YYYYMM,
    same aggregation rules as weekly."""
    await _seed_stock(db_session)
    data = [
        {"trade_date": "20240102", "open": 10.0, "high": 10.5, "low": 9.5, "close": 10.2, "vol": 100000},
        {"trade_date": "20240103", "open": 10.2, "high": 10.8, "low": 9.8, "close": 10.5, "vol": 110000},
        {"trade_date": "20240201", "open": 10.5, "high": 11.0, "low": 10.0, "close": 10.8, "vol": 120000},
        {"trade_date": "20240202", "open": 10.8, "high": 11.2, "low": 10.3, "close": 10.6, "vol": 90000},
    ]
    await _seed_bars(db_session, "000001.SZ", data)

    service = AdvancedAnalysisService(db_session)
    result = await service.aggregate_kline("000001.SZ", timeframe="monthly")

    assert result["timeframe"] == "monthly"
    monthly_data = result["data"]
    assert len(monthly_data) == 2  # Two months

    # January
    jan = monthly_data[0]
    assert jan["open"] == 10.0
    assert jan["high"] == 10.8
    assert jan["low"] == 9.5
    assert jan["close"] == 10.5
    assert jan["vol"] == 210000

    # February
    feb = monthly_data[1]
    assert feb["open"] == 10.5
    assert feb["high"] == 11.2
    assert feb["low"] == 10.0
    assert feb["close"] == 10.6
    assert feb["vol"] == 210000


# --- Test: Divergence Detection ---


@pytest.mark.asyncio
async def test_detect_divergence(db_session: AsyncSession):
    """detect_divergence finds bars where close makes new 20-day high but
    vol < avg_vol_20 (price-volume bearish divergence per VPA-04)."""
    await _seed_stock(db_session)
    # Create 25 bars where bar 24 makes new 20-day high but on low volume
    data = []
    for i in range(25):
        day = i + 2
        trade_date = f"202401{day:02d}"
        # Most bars: moderate price, moderate volume
        if i < 24:
            price = 10.0 + i * 0.1
            vol = 100000
        else:
            # Last bar: new 20-day high but very low volume
            price = 15.0  # well above previous 20-day range
            vol = 30000  # very low volume
        data.append({
            "trade_date": trade_date,
            "open": price - 0.1,
            "high": price + 0.2,
            "low": price - 0.2,
            "close": price,
            "vol": vol,
        })
    await _seed_bars(db_session, "000001.SZ", data)

    service = AdvancedAnalysisService(db_session)
    result = await service.detect_divergence("000001.SZ")

    assert "divergences" in result
    divergences = result["divergences"]
    assert len(divergences) >= 1, "Should detect at least one divergence"

    # The divergence should be at the last bar
    div = divergences[0]
    assert "trade_date" in div
    assert "price" in div
    assert "volume" in div
    assert "vol_ma20" in div
    assert "description" in div
    assert div["volume"] < div["vol_ma20"] * 0.8  # volume below threshold


# --- Test: Empty data returns empty results ---


@pytest.mark.asyncio
async def test_empty_data_returns_empty(db_session: AsyncSession):
    """Service methods return empty results when no data exists for ts_code."""
    await _seed_stock(db_session, "999999.SZ")

    service = AdvancedAnalysisService(db_session)

    pivots = await service.detect_pivots("999999.SZ")
    assert pivots == {"pivots": []}

    sr = await service.detect_support_resistance("999999.SZ")
    assert sr == {"levels": []}

    tl = await service.detect_trend_lines("999999.SZ")
    assert tl == {"lines": []}

    mc = await service.detect_market_cycle("999999.SZ")
    assert mc == {"phases": []}

    vap = await service.compute_vap("999999.SZ")
    assert vap == {"vap": [], "price_range": {"min": 0, "max": 0}, "total_volume": 0}

    kl = await service.aggregate_kline("999999.SZ", timeframe="weekly")
    assert kl == {"timeframe": "weekly", "data": []}

    div = await service.detect_divergence("999999.SZ")
    assert div == {"divergences": []}
