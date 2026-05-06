"""Advanced analysis service for support/resistance, trend lines,
market cycle, VAP, K-line aggregation, and divergence detection.

Implements core algorithms from the user's study notes:
- Chapter 07: Isolated pivot detection for support/resistance
- Chapter 08: Dynamic trend line construction
- Chapter 05: Market cycle four-phase detection
- Chapter 09: Volume-at-Price (VAP) distribution
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DailyBar

logger = logging.getLogger(__name__)


class AdvancedAnalysisService:
    """Computes advanced analysis features from daily OHLCV data.

    Provides pivot detection, support/resistance levels, trend lines,
    market cycle phases, VAP distribution, K-line aggregation, and
    volume-price divergence detection.
    """

    def __init__(self, session: AsyncSession):
        """Initialize with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self.session = session

    async def _load_daily_data(self, ts_code: str) -> pd.DataFrame:
        """Load daily OHLCV data from database into pandas DataFrame.

        Args:
            ts_code: Stock code.

        Returns:
            DataFrame sorted by trade_date ascending with columns
            [trade_date, open, high, low, close, vol].
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

    # ------------------------------------------------------------------
    # 1. Pivot Detection (Chapter 07: isolated pivot algorithm)
    # ------------------------------------------------------------------

    async def detect_pivots(self, ts_code: str) -> dict:
        """Detect isolated high and low pivots per Chapter 07.

        Isolated high pivot: bar[i].high > bar[i-1].high AND bar[i].high > bar[i+1].high
                             AND bar[i].low > bar[i-1].low AND bar[i].low > bar[i+1].low
        Isolated low pivot:  bar[i].low < bar[i-1].low AND bar[i].low < bar[i+1].low
                             AND bar[i].high < bar[i-1].high AND bar[i].high < bar[i+1].high

        Args:
            ts_code: Stock code.

        Returns:
            Dict with pivots list: [{trade_date, type, price, bar_index}].
        """
        df = await self._load_daily_data(ts_code)
        if df.empty or len(df) < 3:
            return {"pivots": []}

        pivots = []
        for i in range(1, len(df) - 1):
            curr = df.iloc[i]
            left = df.iloc[i - 1]
            right = df.iloc[i + 1]

            # Isolated high pivot: middle bar completely above neighbors
            if (
                curr["high"] > left["high"]
                and curr["high"] > right["high"]
                and curr["low"] > left["low"]
                and curr["low"] > right["low"]
            ):
                pivots.append({
                    "trade_date": curr["trade_date"],
                    "type": "high",
                    "price": float(curr["high"]),
                    "bar_index": i,
                })

            # Isolated low pivot: middle bar completely below neighbors
            if (
                curr["low"] < left["low"]
                and curr["low"] < right["low"]
                and curr["high"] < left["high"]
                and curr["high"] < right["high"]
            ):
                pivots.append({
                    "trade_date": curr["trade_date"],
                    "type": "low",
                    "price": float(curr["low"]),
                    "bar_index": i,
                })

        return {"pivots": pivots}

    # ------------------------------------------------------------------
    # 2. Support/Resistance Level Detection
    # ------------------------------------------------------------------

    async def detect_support_resistance(self, ts_code: str) -> dict:
        """Detect support and resistance levels from pivot groups.

        Groups nearby pivot prices (within 2% tolerance) into levels.
        Classifies as support/resistance relative to current close price.

        Args:
            ts_code: Stock code.

        Returns:
            Dict with levels list: [{price, type, strength, trade_dates}].
        """
        pivots_result = await self.detect_pivots(ts_code)
        pivots = pivots_result["pivots"]

        if not pivots:
            return {"levels": []}

        # Load data to get current close price
        df = await self._load_daily_data(ts_code)
        if df.empty:
            return {"levels": []}

        current_close = float(df.iloc[-1]["close"])

        # Group pivots within 2% tolerance
        groups: list[list[dict]] = []
        for pivot in pivots:
            placed = False
            for group in groups:
                group_price = np.mean([p["price"] for p in group])
                if abs(pivot["price"] - group_price) / group_price < 0.02:
                    group.append(pivot)
                    placed = True
                    break
            if not placed:
                groups.append([pivot])

        # Build levels from groups
        levels = []
        for group in groups:
            price = float(np.mean([p["price"] for p in group]))
            strength = len(group)
            trade_dates = [p["trade_date"] for p in group]

            # Classify relative to current close
            if abs(price - current_close) / current_close < 0.005:
                level_type = "both"
            elif price > current_close:
                level_type = "resistance"
            else:
                level_type = "support"

            levels.append({
                "price": round(price, 4),
                "type": level_type,
                "strength": strength,
                "trade_dates": trade_dates,
            })

        return {"levels": levels}

    # ------------------------------------------------------------------
    # 3. Trend Line Detection (Chapter 08: dynamic trend lines)
    # ------------------------------------------------------------------

    async def detect_trend_lines(self, ts_code: str) -> dict:
        """Detect trend lines connecting consecutive pivots.

        Connects consecutive high pivots and consecutive low pivots
        within 60 bars apart. Classifies trend by slope direction.

        Args:
            ts_code: Stock code.

        Returns:
            Dict with lines list: [{start_date, end_date, start_price,
            end_price, type, pivot_type}].
        """
        pivots_result = await self.detect_pivots(ts_code)
        pivots = pivots_result["pivots"]

        if len(pivots) < 2:
            return {"lines": []}

        # Load data for date references
        df = await self._load_daily_data(ts_code)
        if df.empty:
            return {"lines": []}

        high_pivots = sorted(
            [p for p in pivots if p["type"] == "high"],
            key=lambda p: p["bar_index"],
        )
        low_pivots = sorted(
            [p for p in pivots if p["type"] == "low"],
            key=lambda p: p["bar_index"],
        )

        lines = []

        # Connect consecutive high pivots
        for i in range(len(high_pivots) - 1):
            p1 = high_pivots[i]
            p2 = high_pivots[i + 1]
            if abs(p2["bar_index"] - p1["bar_index"]) <= 60:
                slope = (p2["price"] - p1["price"]) / (
                    p2["bar_index"] - p1["bar_index"]
                )
                if slope > 0.01:
                    trend_type = "up"
                elif slope < -0.01:
                    trend_type = "down"
                else:
                    trend_type = "horizontal"
                lines.append({
                    "start_date": p1["trade_date"],
                    "end_date": p2["trade_date"],
                    "start_price": p1["price"],
                    "end_price": p2["price"],
                    "type": trend_type,
                    "pivot_type": "high",
                })

        # Connect consecutive low pivots
        for i in range(len(low_pivots) - 1):
            p1 = low_pivots[i]
            p2 = low_pivots[i + 1]
            if abs(p2["bar_index"] - p1["bar_index"]) <= 60:
                slope = (p2["price"] - p1["price"]) / (
                    p2["bar_index"] - p1["bar_index"]
                )
                if slope > 0.01:
                    trend_type = "up"
                elif slope < -0.01:
                    trend_type = "down"
                else:
                    trend_type = "horizontal"
                lines.append({
                    "start_date": p1["trade_date"],
                    "end_date": p2["trade_date"],
                    "start_price": p1["price"],
                    "end_price": p2["price"],
                    "type": trend_type,
                    "pivot_type": "low",
                })

        return {"lines": lines}

    # ------------------------------------------------------------------
    # 4. Market Cycle Detection (Chapter 05: four phases)
    # ------------------------------------------------------------------

    async def detect_market_cycle(self, ts_code: str) -> dict:
        """Detect market cycle phases: accumulation, markup, distribution, markdown.

        Uses a sliding window approach analyzing volume patterns, price trends,
        and range characteristics per Chapter 05.

        Args:
            ts_code: Stock code.

        Returns:
            Dict with phases list: [{phase, start_date, end_date, description}].
        """
        df = await self._load_daily_data(ts_code)
        if df.empty or len(df) < 20:
            return {"phases": []}

        df = df.copy()
        df["ma20"] = df["close"].rolling(20, min_periods=1).mean()
        df["vol_ma20"] = df["vol"].rolling(20, min_periods=1).mean()
        df["atr14"] = (df["high"] - df["low"]).rolling(14, min_periods=1).mean()

        # Overall averages for comparison
        atr14_mean = df["atr14"].mean()
        window_size = 20

        # Classify each position
        phase_labels = []
        for i in range(len(df)):
            if i < window_size:
                phase_labels.append("markup")
                continue

            row = df.iloc[i]
            window = df.iloc[i - window_size + 1 : i + 1]

            ma20 = row["ma20"]
            vol_ma20 = row["vol_ma20"]
            atr14 = row["atr14"]
            close = row["close"]
            vol = row["vol"]

            if pd.isna(ma20) or pd.isna(vol_ma20) or pd.isna(atr14):
                phase_labels.append(phase_labels[-1] if phase_labels else "markup")
                continue

            # Count higher highs and lower lows in recent window
            higher_highs = sum(
                1 for j in range(len(window) - 5)
                if window.iloc[j + 5]["close"] > window.iloc[j]["close"]
            )
            lower_lows = sum(
                1 for j in range(len(window) - 5)
                if window.iloc[j + 5]["close"] < window.iloc[j]["close"]
            )

            # Accumulation: low volume, narrow range, close near MA
            if (
                vol < vol_ma20 * 0.8
                and atr14 < atr14_mean * 0.7
                and abs(close - ma20) / ma20 < 0.03
            ):
                phase_labels.append("accumulation")
            # Markup: close above MA, making higher highs, volume on up days
            elif (
                close > ma20
                and higher_highs > lower_lows
            ):
                phase_labels.append("markup")
            # Distribution: high volume, narrow range, near recent high
            elif (
                vol > vol_ma20 * 1.2
                and atr14 < atr14_mean * 0.8
                and close >= ma20 * 0.97
            ):
                phase_labels.append("distribution")
            # Markdown: close below MA, making lower lows
            elif close < ma20 and lower_lows >= higher_highs:
                phase_labels.append("markdown")
            else:
                # Default to previous phase
                phase_labels.append(phase_labels[-1] if phase_labels else "markup")

        # Merge consecutive same-phase segments
        phases = []
        current_phase = phase_labels[0]
        start_idx = 0

        for i in range(1, len(phase_labels)):
            if phase_labels[i] != current_phase:
                phases.append({
                    "phase": current_phase,
                    "start_date": df.iloc[start_idx]["trade_date"],
                    "end_date": df.iloc[i - 1]["trade_date"],
                    "description": self._phase_description(current_phase),
                })
                current_phase = phase_labels[i]
                start_idx = i

        # Add last segment
        phases.append({
            "phase": current_phase,
            "start_date": df.iloc[start_idx]["trade_date"],
            "end_date": df.iloc[-1]["trade_date"],
            "description": self._phase_description(current_phase),
        })

        return {"phases": phases}

    @staticmethod
    def _phase_description(phase: str) -> str:
        """Return Chinese description for a market cycle phase.

        Args:
            phase: Phase name.

        Returns:
            Description string.
        """
        descriptions = {
            "accumulation": "吸筹阶段：低成交量，窄幅震荡，局内人买入",
            "markup": "上涨阶段：价格突破均线，成交量放大，更高高点",
            "distribution": "派发阶段：高成交量，窄幅区间，局内人卖出",
            "markdown": "下跌阶段：价格跌破均线，成交量放大，更低低点",
        }
        return descriptions.get(phase, phase)

    # ------------------------------------------------------------------
    # 5. VAP (Volume at Price) (Chapter 09)
    # ------------------------------------------------------------------

    async def compute_vap(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """Compute Volume at Price distribution.

        Distributes each bar's volume across overlapping price bins.
        Tracks up/down volume separately.

        Args:
            ts_code: Stock code.
            start_date: Optional start date filter (YYYYMMDD).
            end_date: Optional end date filter (YYYYMMDD).

        Returns:
            Dict with vap list, price_range, and total_volume.
        """
        df = await self._load_daily_data(ts_code)
        if df.empty:
            return {
                "vap": [],
                "price_range": {"min": 0, "max": 0},
                "total_volume": 0,
            }

        # Apply date filters
        if start_date:
            df = df[df["trade_date"] >= start_date]
        if end_date:
            df = df[df["trade_date"] <= end_date]

        if df.empty:
            return {
                "vap": [],
                "price_range": {"min": 0, "max": 0},
                "total_volume": 0,
            }

        min_price = float(df["low"].min())
        max_price = float(df["high"].max())
        total_volume = float(df["vol"].sum())

        if max_price == min_price:
            # Edge case: all prices are the same
            is_up = df["close"] >= df["open"]
            return {
                "vap": [{
                    "price_level": round(min_price, 4),
                    "volume": total_volume,
                    "up_volume": float(df.loc[is_up, "vol"].sum()),
                    "down_volume": float(df.loc[~is_up, "vol"].sum()),
                }],
                "price_range": {"min": min_price, "max": max_price},
                "total_volume": total_volume,
            }

        # Create 30 price bins
        num_bins = 30
        bin_size = (max_price - min_price) / num_bins
        bin_edges = [min_price + i * bin_size for i in range(num_bins + 1)]

        # Initialize bin data
        vap_data = []
        for i in range(num_bins):
            vap_data.append({
                "price_level": round((bin_edges[i] + bin_edges[i + 1]) / 2, 4),
                "volume": 0.0,
                "up_volume": 0.0,
                "down_volume": 0.0,
            })

        # Distribute each bar's volume across overlapping bins
        for _, bar in df.iterrows():
            bar_low = bar["low"]
            bar_high = bar["high"]
            bar_vol = bar["vol"]
            bar_range = bar_high - bar_low
            is_up = bar["close"] >= bar["open"]

            if bar_range == 0:
                # Zero-range bar: assign to the bin that contains the price
                for i in range(num_bins):
                    if bin_edges[i] <= bar_low < bin_edges[i + 1]:
                        vap_data[i]["volume"] += bar_vol
                        if is_up:
                            vap_data[i]["up_volume"] += bar_vol
                        else:
                            vap_data[i]["down_volume"] += bar_vol
                        break
            else:
                for i in range(num_bins):
                    bin_low = bin_edges[i]
                    bin_high = bin_edges[i + 1]

                    # Calculate overlap
                    overlap_low = max(bar_low, bin_low)
                    overlap_high = min(bar_high, bin_high)

                    if overlap_high > overlap_low:
                        overlap = overlap_high - overlap_low
                        vol_share = bar_vol * (overlap / bar_range)
                        vap_data[i]["volume"] += vol_share
                        if is_up:
                            vap_data[i]["up_volume"] += vol_share
                        else:
                            vap_data[i]["down_volume"] += vol_share

        # Round volumes
        for entry in vap_data:
            entry["volume"] = round(entry["volume"], 4)
            entry["up_volume"] = round(entry["up_volume"], 4)
            entry["down_volume"] = round(entry["down_volume"], 4)

        return {
            "vap": vap_data,
            "price_range": {"min": min_price, "max": max_price},
            "total_volume": total_volume,
        }

    # ------------------------------------------------------------------
    # 6. K-line Aggregation (weekly / monthly)
    # ------------------------------------------------------------------

    async def aggregate_kline(
        self, ts_code: str, timeframe: str = "weekly"
    ) -> dict:
        """Aggregate daily K-line data into weekly or monthly bars.

        Weekly: grouped by ISO year + week number (Monday start).
        Monthly: grouped by YYYYMM.

        Args:
            ts_code: Stock code.
            timeframe: "weekly" or "monthly".

        Returns:
            Dict with timeframe and data list of aggregated bars.
        """
        df = await self._load_daily_data(ts_code)
        if df.empty:
            return {"timeframe": timeframe, "data": []}

        df = df.copy()

        # Parse trade_date to datetime for grouping
        df["date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")

        if timeframe == "weekly":
            df["group_key"] = (
                df["date"].dt.isocalendar().year.astype(str)
                + "-"
                + df["date"].dt.isocalendar().week.astype(str).str.zfill(2)
            )
        elif timeframe == "monthly":
            df["group_key"] = df["trade_date"].str[:6]
        else:
            return {"timeframe": timeframe, "data": []}

        aggregated = []
        for _key, group in df.groupby("group_key", sort=True):
            aggregated.append({
                "trade_date": group.iloc[0]["trade_date"],
                "open": float(group.iloc[0]["open"]),
                "high": float(group["high"].max()),
                "low": float(group["low"].min()),
                "close": float(group.iloc[-1]["close"]),
                "vol": float(group["vol"].sum()),
            })

        return {"timeframe": timeframe, "data": aggregated}

    # ------------------------------------------------------------------
    # 7. Divergence Detection (VPA-04: price-volume bearish divergence)
    # ------------------------------------------------------------------

    async def detect_divergence(self, ts_code: str) -> dict:
        """Detect price-volume bearish divergence.

        Finds bars where close makes a new 20-day high but volume is
        below the 20-day average (price-volume bearish divergence).

        Args:
            ts_code: Stock code.

        Returns:
            Dict with divergences list: [{trade_date, price, volume,
            vol_ma20, description}].
        """
        df = await self._load_daily_data(ts_code)
        if df.empty or len(df) < 20:
            return {"divergences": []}

        df = df.copy()
        df["close_20_high"] = df["close"].rolling(20, min_periods=20).max()
        df["vol_ma20"] = df["vol"].rolling(20, min_periods=20).mean()

        divergences = []
        for i in range(19, len(df)):
            row = df.iloc[i]
            if pd.isna(row["close_20_high"]) or pd.isna(row["vol_ma20"]):
                continue

            # New 20-day high and volume below 80% of 20-day average
            if (
                row["close"] == row["close_20_high"]
                and row["vol"] < row["vol_ma20"] * 0.8
            ):
                divergences.append({
                    "trade_date": row["trade_date"],
                    "price": float(row["close"]),
                    "volume": float(row["vol"]),
                    "vol_ma20": float(row["vol_ma20"]),
                    "description": "量价背离：价格创20日新高但成交量低于均量",
                })

        return {"divergences": divergences}
