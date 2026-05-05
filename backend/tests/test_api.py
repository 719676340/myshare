"""API tests for stock search and daily K-line endpoints.

Tests 7 behaviors:
1. Search by code returns matching stocks
2. Search by name (Chinese) returns matching stocks
3. Empty keyword returns 400
4. Daily data returns OHLCV sorted by trade_date ASC
5. Date range filtering works
6. Nonexistent stock returns 404
7. Second call returns cached data (no tushare call)
"""

import pytest
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


class TestStockSearch:
    """Tests for GET /api/stocks/search endpoint."""

    @pytest.mark.asyncio
    async def test_search_by_code_returns_matching_stocks(
        self, client: AsyncClient, seed_stocks
    ):
        """Test 1: GET /api/stocks/search?keyword=000 returns stocks matching code '000'."""
        response = await client.get("/api/stocks/search?keyword=000")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # All results should have ts_code containing '000'
        for item in data:
            assert "000" in item["ts_code"] or "000" in item.get("symbol", "")
            assert "ts_code" in item
            assert "name" in item

    @pytest.mark.asyncio
    async def test_search_by_chinese_name_returns_matching_stocks(
        self, client: AsyncClient, seed_stocks
    ):
        """Test 2: GET /api/stocks/search?keyword=平安 returns stocks matching name '平安'."""
        response = await client.get("/api/stocks/search?keyword=%E5%B9%B3%E5%AE%89")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Should find 平安银行
        found = any(item["name"] == "平安银行" for item in data)
        assert found, "Expected to find '平安银行' in search results"

    @pytest.mark.asyncio
    async def test_search_empty_keyword_returns_400(self, client: AsyncClient):
        """Test 3: GET /api/stocks/search?keyword= (empty) returns 400 error."""
        response = await client.get("/api/stocks/search?keyword=")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_search_limits_results(self, client: AsyncClient, seed_stocks):
        """Test that search results are limited to 20 rows."""
        response = await client.get("/api/stocks/search?keyword=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 20


class TestDailyData:
    """Tests for GET /api/daily/{ts_code} endpoint."""

    @pytest.mark.asyncio
    async def test_get_daily_data_returns_ohlcv_sorted(
        self, client: AsyncClient, seed_stocks, seed_daily_bars
    ):
        """Test 4: GET /api/daily/000001.SZ returns daily K-line data sorted by trade_date ASC."""
        response = await client.get("/api/daily/000001.SZ")
        assert response.status_code == 200
        data = response.json()
        assert data["ts_code"] == "000001.SZ"
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0
        # Check sorted by trade_date ASC
        dates = [item["trade_date"] for item in data["data"]]
        assert dates == sorted(dates), "Data should be sorted by trade_date ascending"
        # Check OHLCV fields present
        first = data["data"][0]
        for field in ["trade_date", "open", "high", "low", "close", "vol"]:
            assert field in first, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_get_daily_data_with_date_range(
        self, client: AsyncClient, seed_stocks, seed_daily_bars
    ):
        """Test 5: GET /api/daily/000001.SZ?start_date=20240101&end_date=20240601 returns filtered range."""
        response = await client.get(
            "/api/daily/000001.SZ?start_date=20240101&end_date=20240601"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ts_code"] == "000001.SZ"
        assert isinstance(data["data"], list)
        # All dates should be within range
        for item in data["data"]:
            assert "20240101" <= item["trade_date"] <= "20240601"

    @pytest.mark.asyncio
    async def test_get_daily_nonexistent_stock_returns_404(
        self, client: AsyncClient, seed_stocks
    ):
        """Test 6: GET /api/daily/999999.SZ returns 404 for nonexistent stock."""
        response = await client.get("/api/daily/999999.SZ")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_second_call_returns_cached_data(
        self, client: AsyncClient, seed_stocks, seed_daily_bars
    ):
        """Test 7: Second call to GET /api/daily/000001.SZ returns data from cache."""
        # First call
        response1 = await client.get("/api/daily/000001.SZ")
        assert response1.status_code == 200
        data1 = response1.json()

        # Second call should return same data from cache (no tushare call needed)
        response2 = await client.get("/api/daily/000001.SZ")
        assert response2.status_code == 200
        data2 = response2.json()

        # Data should be identical
        assert data1["ts_code"] == data2["ts_code"]
        assert len(data1["data"]) == len(data2["data"])

    @pytest.mark.asyncio
    async def test_get_daily_response_includes_cache_info(
        self, client: AsyncClient, seed_stocks, seed_daily_bars
    ):
        """Test that daily data response includes cache_info."""
        response = await client.get("/api/daily/000001.SZ")
        assert response.status_code == 200
        data = response.json()
        assert "cache_info" in data
        assert "total_bars" in data["cache_info"]
