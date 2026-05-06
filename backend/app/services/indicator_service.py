"""Technical indicator computation service.

Computes MACD, RSI, KDJ (custom), BOLL indicators using ta library + pandas.
Results are cached in indicator_values table using params_hash for dedup.
"""

import hashlib
import json
import logging
from typing import Any, Optional

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DailyBar, IndicatorValue

logger = logging.getLogger(__name__)

# Default indicator parameters
DEFAULT_PARAMS = {
    "macd": {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9},
    "rsi": {"window": 14},
    "kdj": {"n": 9, "m1": 3, "m2": 3},
    "boll": {"window": 20, "window_dev": 2},
}


def _generate_params_hash(params: dict) -> str:
    """Generate a short MD5 hash from parameter dict for cache keying.

    Args:
        params: Indicator parameters dict.

    Returns:
        16-char hex string hash.
    """
    return hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:16]


class IndicatorService:
    """Computes and caches technical indicators from daily OHLCV data."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self.session = session

    async def compute_indicators(
        self,
        ts_code: str,
        indicator_name: str,
        params: Optional[dict] = None,
    ) -> dict:
        """Compute technical indicators for a stock.

        Args:
            ts_code: Stock code (e.g. "000001.SZ").
            indicator_name: One of macd, rsi, kdj, boll.
            params: Optional parameter overrides. Uses defaults if not provided.

        Returns:
            Dict with indicator name, params, params_hash, and data list.

        Raises:
            ValueError: If indicator_name is not supported.
        """
        if indicator_name not in DEFAULT_PARAMS:
            raise ValueError(
                f"Unsupported indicator: {indicator_name}. "
                f"Supported: {list(DEFAULT_PARAMS.keys())}"
            )

        # Merge with defaults
        effective_params = {**DEFAULT_PARAMS[indicator_name], **(params or {})}
        params_hash = _generate_params_hash(effective_params)

        # Check cache
        cached = await self._check_cache(ts_code, indicator_name, params_hash)
        if cached is not None:
            return cached

        # Load OHLCV data
        df = await self._load_daily_data(ts_code)
        if df.empty:
            return {
                "indicator": indicator_name,
                "params": effective_params,
                "params_hash": params_hash,
                "data": [],
            }

        # Compute indicator
        if indicator_name == "macd":
            result_df = self._compute_macd(df, effective_params)
        elif indicator_name == "rsi":
            result_df = self._compute_rsi(df, effective_params)
        elif indicator_name == "kdj":
            result_df = self._compute_kdj(df, effective_params)
        elif indicator_name == "boll":
            result_df = self._compute_boll(df, effective_params)
        else:
            raise ValueError(f"Unsupported indicator: {indicator_name}")

        # Build result data
        data = self._df_to_list(result_df, indicator_name)

        # Cache results
        await self._cache_results(
            ts_code, indicator_name, params_hash, data
        )

        return {
            "indicator": indicator_name,
            "params": effective_params,
            "params_hash": params_hash,
            "data": data,
        }

    async def _load_daily_data(self, ts_code: str) -> pd.DataFrame:
        """Load daily OHLCV data from database into pandas DataFrame.

        Args:
            ts_code: Stock code.

        Returns:
            DataFrame with trade_date, open, high, low, close, vol columns.
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

    def _compute_macd(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """Compute MACD indicator using ta library.

        Args:
            df: OHLCV DataFrame.
            params: MACD params (fastperiod, slowperiod, signalperiod).

        Returns:
            DataFrame with macd, signal, histogram columns added.
        """
        import ta

        fast = params.get("fastperiod", 12)
        slow = params.get("slowperiod", 26)
        signal = params.get("signalperiod", 9)

        macd = ta.trend.MACD(
            close=df["close"],
            window_slow=slow,
            window_fast=fast,
            window_sign=signal,
        )

        df = df.copy()
        df["macd"] = macd.macd()
        df["signal"] = macd.macd_signal()
        df["histogram"] = macd.macd_diff()
        return df

    def _compute_rsi(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """Compute RSI indicator using ta library.

        Args:
            df: OHLCV DataFrame.
            params: RSI params (window).

        Returns:
            DataFrame with rsi column added.
        """
        import ta

        window = params.get("window", 14)

        rsi_ind = ta.momentum.RSIIndicator(close=df["close"], window=window)

        df = df.copy()
        df["rsi"] = rsi_ind.rsi()
        return df

    def _compute_kdj(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """Compute KDJ indicator using custom Stochastic Oscillator formula.

        K = 2/3 * prev_K + 1/3 * (C - Ln) / (Hn - Ln) * 100
        D = 2/3 * prev_D + 1/3 * K
        J = 3 * K - 2 * D

        Args:
            df: OHLCV DataFrame.
            params: KDJ params (n, m1, m2).

        Returns:
            DataFrame with k, d, j columns added.
        """
        n = params.get("n", 9)
        m1 = params.get("m1", 3)
        m2 = params.get("m2", 3)

        df = df.copy()

        # Rolling highest high and lowest low over n periods
        low_n = df["low"].rolling(window=n, min_periods=1).min()
        high_n = df["high"].rolling(window=n, min_periods=1).max()

        # Raw stochastic value (RSV)
        denom = high_n - low_n
        rsv = pd.Series(np.where(denom != 0, (df["close"] - low_n) / denom * 100, 50),
                        index=df.index)

        # K and D smoothing
        k_values = [50.0]  # Initialize K at 50
        d_values = [50.0]  # Initialize D at 50

        for i in range(1, len(df)):
            k = (2 / m1) * k_values[-1] + (1 / m1) * rsv.iloc[i]
            d = (2 / m2) * d_values[-1] + (1 / m2) * k
            k_values.append(k)
            d_values.append(d)

        df["k"] = k_values
        df["d"] = d_values
        # J = 3K - 2D, clamped to [0, 100]
        df["j"] = np.clip(3 * df["k"] - 2 * df["d"], 0, 100)

        return df

    def _compute_boll(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """Compute Bollinger Bands using ta library.

        Args:
            df: OHLCV DataFrame.
            params: BOLL params (window, window_dev).

        Returns:
            DataFrame with upper, middle, lower columns added.
        """
        import ta

        window = params.get("window", 20)
        window_dev = int(params.get("window_dev", 2))

        boll = ta.volatility.BollingerBands(
            close=df["close"],
            window=window,
            window_dev=window_dev,
        )

        df = df.copy()
        df["upper"] = boll.bollinger_hband()
        df["middle"] = boll.bollinger_mavg()
        df["lower"] = boll.bollinger_lband()
        return df

    def _df_to_list(self, df: pd.DataFrame, indicator_name: str) -> list[dict]:
        """Convert computed DataFrame to list of dicts for API response.

        Args:
            df: DataFrame with computed indicator columns.
            indicator_name: Name of the indicator.

        Returns:
            List of dicts with trade_date and indicator values.
        """
        # Select relevant columns based on indicator type
        if indicator_name == "macd":
            value_cols = ["macd", "signal", "histogram"]
        elif indicator_name == "rsi":
            value_cols = ["rsi"]
        elif indicator_name == "kdj":
            value_cols = ["k", "d", "j"]
        elif indicator_name == "boll":
            value_cols = ["upper", "middle", "lower"]
        else:
            value_cols = []

        data = []
        for _, row in df.iterrows():
            entry = {"trade_date": row["trade_date"]}
            for col in value_cols:
                val = row.get(col)
                if pd.isna(val):
                    entry[col] = None
                else:
                    entry[col] = round(float(val), 4)
            data.append(entry)
        return data

    async def _check_cache(
        self, ts_code: str, indicator_name: str, params_hash: str
    ) -> Optional[dict]:
        """Check if indicator results are cached in the database.

        Args:
            ts_code: Stock code.
            indicator_name: Indicator name.
            params_hash: Parameter hash.

        Returns:
            Cached result dict or None if cache miss.
        """
        stmt = (
            select(IndicatorValue)
            .where(
                IndicatorValue.ts_code == ts_code,
                IndicatorValue.indicator_name == indicator_name,
                IndicatorValue.params_hash == params_hash,
            )
            .order_by(IndicatorValue.trade_date)
        )
        result = await self.session.execute(stmt)
        cached = result.scalars().all()

        if not cached:
            return None

        # Reconstruct the data list from cached values
        data = []
        for iv in cached:
            values = json.loads(iv.value_json)
            entry = {"trade_date": iv.trade_date, **values}
            data.append(entry)

        logger.info(
            f"Cache hit for {indicator_name} ({ts_code}, hash={params_hash}): "
            f"{len(data)} rows"
        )

        return {
            "indicator": indicator_name,
            "params": None,  # Params not stored per-row, caller already has them
            "params_hash": params_hash,
            "data": data,
        }

    async def _cache_results(
        self,
        ts_code: str,
        indicator_name: str,
        params_hash: str,
        data: list[dict],
    ) -> None:
        """Cache indicator computation results in the database.

        Args:
            ts_code: Stock code.
            indicator_name: Indicator name.
            params_hash: Parameter hash.
            data: List of result dicts (each with trade_date and indicator values).
        """
        value_cols = {
            "macd": ["macd", "signal", "histogram"],
            "rsi": ["rsi"],
            "kdj": ["k", "d", "j"],
            "boll": ["upper", "middle", "lower"],
        }

        cols = value_cols.get(indicator_name, [])
        for entry in data:
            values = {col: entry.get(col) for col in cols}
            iv = IndicatorValue(
                ts_code=ts_code,
                trade_date=entry["trade_date"],
                indicator_name=indicator_name,
                params_hash=params_hash,
                value_json=json.dumps(values),
            )
            self.session.add(iv)

        await self.session.commit()
        logger.info(
            f"Cached {len(data)} rows for {indicator_name} "
            f"({ts_code}, hash={params_hash})"
        )
