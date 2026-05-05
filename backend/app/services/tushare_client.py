"""Tushare Pro API wrapper for fetching A-share market data."""

import logging
from typing import Optional

import tushare as ts
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class TushareClient:
    """Wrapper around tushare Pro API for stock data retrieval."""

    def __init__(self, token: str):
        """Initialize with tushare API token.

        Args:
            token: Tushare Pro API token.
        """
        self.token = token
        ts.set_token(token)
        self.pro = ts.pro_api()

    def get_stock_list(self) -> list[dict]:
        """Fetch all listed A-share stocks.

        Returns:
            List of dicts with keys: ts_code, symbol, name, area, industry, market, list_date

        Raises:
            HTTPException: If tushare API call fails.
        """
        try:
            df = self.pro.stock_basic(
                exchange="",
                list_status="L",
                fields="ts_code,symbol,name,area,industry,market,list_date",
            )
            if df is None or df.empty:
                raise HTTPException(
                    status_code=502,
                    detail="tushare API error: empty response for stock list",
                )
            return df.to_dict(orient="records")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Tushare stock_basic error: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"tushare API error: {str(e)}",
            )

    def get_daily(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[dict]:
        """Fetch daily K-line data for a stock.

        Args:
            ts_code: Stock code (e.g. "000001.SZ")
            start_date: Start date in YYYYMMDD format (optional)
            end_date: End date in YYYYMMDD format (optional)

        Returns:
            List of dicts with keys: ts_code, trade_date, open, high, low, close,
            pre_close, change, pct_chg, vol, amount

        Raises:
            HTTPException: If tushare API call fails.
        """
        try:
            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
            )
            if df is None or df.empty:
                # No data available, return empty list (not an error)
                return []
            return df.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Tushare daily error for {ts_code}: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"tushare API error: {str(e)}",
            )

    def get_trade_cal(self, exchange: str = "SSE") -> list[dict]:
        """Fetch trade calendar.

        Args:
            exchange: Exchange code ("SSE" for Shanghai, "SZSE" for Shenzhen)

        Returns:
            List of dicts with trade calendar info.

        Raises:
            HTTPException: If tushare API call fails.
        """
        try:
            df = self.pro.trade_cal(exchange=exchange)
            if df is None or df.empty:
                raise HTTPException(
                    status_code=502,
                    detail="tushare API error: empty response for trade calendar",
                )
            return df.to_dict(orient="records")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Tushare trade_cal error: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"tushare API error: {str(e)}",
            )
