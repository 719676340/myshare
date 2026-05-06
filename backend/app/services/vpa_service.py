"""Volume-Price Analysis (VPA) service.

Detects volume-price confirmation/anomaly signals and K-line patterns.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DailyBar

logger = logging.getLogger(__name__)


class VPAService:
    """Detects volume-price signals and K-line patterns from daily OHLCV data."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self.session = session

    async def detect_volume_price_signals(self, ts_code: str) -> dict:
        """Detect volume-price confirmation and anomaly signals.

        Signal types:
        - volume_up_rise: close > open AND vol > avg_vol_5 * 1.2 (放量上涨)
        - volume_down_fall: close < open AND vol < avg_vol_5 * 0.8 (缩量下跌)
        - long_candle_low_volume: body_ratio > 0.6 AND vol < avg_vol_5 * 0.7 (长阳低量陷阱)
        - short_candle_high_volume: body_ratio < 0.3 AND vol > avg_vol_5 * 1.5 (短阳高量走弱)
        - rising_volume_decline: close rising but vol declining over 3 bars (量价背离)

        Args:
            ts_code: Stock code.

        Returns:
            Dict with signals list.
        """
        df = await self._load_daily_data(ts_code)
        if df.empty or len(df) < 6:
            return {"signals": []}

        df = self._add_derived_columns(df)

        signals = []

        for i in range(5, len(df)):
            row = df.iloc[i]
            avg_vol_5 = df.iloc[i - 5:i]["vol"].mean()
            vol = row["vol"]
            body = abs(row["close"] - row["open"])
            range_val = row["high"] - row["low"]
            body_ratio = body / range_val if range_val > 0 else 0
            is_up = row["close"] > row["open"]
            is_down = row["close"] < row["open"]

            # Confirmation signals
            if is_up and vol > avg_vol_5 * 1.2:
                signals.append({
                    "trade_date": row["trade_date"],
                    "signal_type": "volume_up_rise",
                    "direction": "up",
                    "description": "放量上涨",
                })

            if is_down and vol < avg_vol_5 * 0.8:
                signals.append({
                    "trade_date": row["trade_date"],
                    "signal_type": "volume_down_fall",
                    "direction": "down",
                    "description": "缩量下跌",
                })

            # Anomaly signals
            if body_ratio > 0.6 and vol < avg_vol_5 * 0.7:
                signals.append({
                    "trade_date": row["trade_date"],
                    "signal_type": "long_candle_low_volume",
                    "direction": "up" if is_up else "down",
                    "description": "长阳低量陷阱",
                })

            if body_ratio < 0.3 and vol > avg_vol_5 * 1.5:
                signals.append({
                    "trade_date": row["trade_date"],
                    "signal_type": "short_candle_high_volume",
                    "direction": "neutral",
                    "description": "短阳高量走弱",
                })

            # Rising volume decline (3-bar divergence)
            if i >= 2:
                bar_curr = df.iloc[i]
                bar_prev1 = df.iloc[i - 1]
                bar_prev2 = df.iloc[i - 2]
                if (
                    bar_curr["close"] > bar_prev1["close"] > bar_prev2["close"]
                    and bar_curr["vol"] < bar_prev1["vol"] < bar_prev2["vol"]
                ):
                    signals.append({
                        "trade_date": row["trade_date"],
                        "signal_type": "rising_volume_decline",
                        "direction": "up",
                        "description": "量价背离：价格上涨但成交量递减",
                    })

        return {"signals": signals}

    async def detect_kline_patterns(self, ts_code: str) -> dict:
        """Detect K-line patterns (candlestick formations).

        Pattern types:
        - hammer (锤头线): lower_shadow >= 2 * body AND upper_shadow <= body AND body > 0
        - shooting_star (射击十字星): upper_shadow >= 2 * body AND lower_shadow <= body AND body > 0
        - doji (十字星): body / range < 0.1 where range > 0
        - hanging_man (吊人线): hammer shape in uptrend (close > open, close > 5-day MA)

        Args:
            ts_code: Stock code.

        Returns:
            Dict with patterns list.
        """
        df = await self._load_daily_data(ts_code)
        if df.empty or len(df) < 5:
            return {"patterns": []}

        df = self._add_derived_columns(df)

        # Calculate 5-day MA of close for trend context
        df["ma5"] = df["close"].rolling(window=5, min_periods=5).mean()

        patterns = []

        for i in range(len(df)):
            row = df.iloc[i]
            body = row["body"]
            lower_shadow = row["lower_shadow"]
            upper_shadow = row["upper_shadow"]
            range_val = row["range"]
            body_ratio = row["body_ratio"]

            # Doji: very small body relative to range
            if range_val > 0 and body_ratio < 0.1:
                patterns.append({
                    "trade_date": row["trade_date"],
                    "pattern_type": "doji",
                    "name": "十字星",
                    "description": "犹豫信号：开盘价与收盘价几乎相同，多空力量均衡",
                })
                continue  # Doji is not hammer/shooting star

            if body <= 0:
                continue

            # Hammer: long lower shadow, small upper shadow
            if lower_shadow >= 2 * body and upper_shadow <= body:
                # Check if in uptrend for hanging man classification
                is_up_bar = row["close"] > row["open"]
                ma5_val = row.get("ma5")
                if (
                    is_up_bar
                    and ma5_val is not None
                    and not pd.isna(ma5_val)
                    and row["close"] > ma5_val
                ):
                    patterns.append({
                        "trade_date": row["trade_date"],
                        "pattern_type": "hanging_man",
                        "name": "吊人线",
                        "description": "看跌信号：出现在上涨趋势中，下影线长，实体小，可能预示反转",
                    })
                else:
                    patterns.append({
                        "trade_date": row["trade_date"],
                        "pattern_type": "hammer",
                        "name": "锤头线",
                        "description": "看涨信号：下影线长，实体小，出现在下跌趋势中",
                    })

            # Shooting star: long upper shadow, small lower shadow
            elif upper_shadow >= 2 * body and lower_shadow <= body:
                patterns.append({
                    "trade_date": row["trade_date"],
                    "pattern_type": "shooting_star",
                    "name": "射击十字星",
                    "description": "看跌信号：上影线长，实体小，出现在上涨趋势中",
                })

        return {"patterns": patterns}

    async def _load_daily_data(self, ts_code: str) -> pd.DataFrame:
        """Load daily OHLCV data from database into pandas DataFrame.

        Args:
            ts_code: Stock code.

        Returns:
            DataFrame sorted by trade_date ascending.
        """
        stmt = (
            select(DailyBar)
            .where(DailyBar.ts_code == ts_code)
            .order_by(DailyBar.trade_date)
        )
        result = await self.session.execute(stmt)
        bars = result.scalars().all()

        if not bars:
            return pd.DataFrame()

        data = [
            {
                "trade_date": bar.trade_date,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "vol": bar.vol,
            }
            for bar in bars
        ]
        return pd.DataFrame(data)

    def _add_derived_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived columns for signal/pattern detection.

        Args:
            df: OHLCV DataFrame.

        Returns:
            DataFrame with additional columns: body, range, body_ratio,
            upper_shadow, lower_shadow.
        """
        df = df.copy()
        df["body"] = abs(df["close"] - df["open"])
        df["range"] = df["high"] - df["low"]
        df["body_ratio"] = np.where(
            df["range"] > 0, df["body"] / df["range"], 0
        )
        df["upper_shadow"] = df["high"] - df[["open", "close"]].max(axis=1)
        df["lower_shadow"] = df[["open", "close"]].min(axis=1) - df["low"]
        return df
