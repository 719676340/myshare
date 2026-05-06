"""SQLAlchemy ORM models for Stock and DailyBar tables."""

from sqlalchemy import Column, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Stock(Base):
    """A-share stock listing model."""

    __tablename__ = "stocks"
    __table_args__ = {"sqlite_autoincrement": True}

    ts_code = Column(String(16), primary_key=True, comment="股票代码，如 000001.SZ")
    symbol = Column(String(6), index=True, nullable=False, comment="股票代码数字部分")
    name = Column(String(32), index=True, nullable=False, comment="股票名称")
    area = Column(String(16), nullable=True, comment="地域")
    industry = Column(String(32), nullable=True, comment="所属行业")
    market = Column(String(16), nullable=True, comment="市场类型")
    list_date = Column(String(8), nullable=True, comment="上市日期 YYYYMMDD")

    # Relationship to daily bars
    daily_bars = relationship("DailyBar", back_populates="stock", lazy="selectin")
    # Relationship to indicator values
    indicator_values = relationship("IndicatorValue", back_populates="stock", lazy="selectin")

    def __repr__(self):
        return f"<Stock({self.ts_code} {self.name})>"


class DailyBar(Base):
    """Daily K-line data (OHLCV) model."""

    __tablename__ = "daily_bars"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_daily_ts_code_date"),
        {"sqlite_autoincrement": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(
        String(16),
        ForeignKey("stocks.ts_code"),
        index=True,
        nullable=False,
        comment="股票代码",
    )
    trade_date = Column(String(8), index=True, nullable=False, comment="交易日期 YYYYMMDD")
    open = Column(Float, nullable=False, comment="开盘价")
    high = Column(Float, nullable=False, comment="最高价")
    low = Column(Float, nullable=False, comment="最低价")
    close = Column(Float, nullable=False, comment="收盘价")
    pre_close = Column(Float, nullable=True, comment="昨收价")
    change_pct = Column(Float, nullable=True, comment="涨跌幅(%)")
    vol = Column(Float, nullable=False, comment="成交量(手)")
    amount = Column(Float, nullable=True, comment="成交额(千元)")

    # Relationship back to stock
    stock = relationship("Stock", back_populates="daily_bars")

    def __repr__(self):
        return f"<DailyBar({self.ts_code} {self.trade_date} close={self.close})>"


class IndicatorValue(Base):
    """Technical indicator computed values."""

    __tablename__ = "indicator_values"
    __table_args__ = (
        UniqueConstraint(
            "ts_code",
            "trade_date",
            "indicator_name",
            "params_hash",
            name="uq_indicator_ts_code_date_name_params",
        ),
        {"sqlite_autoincrement": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(
        String(16),
        ForeignKey("stocks.ts_code"),
        index=True,
        nullable=False,
        comment="股票代码",
    )
    trade_date = Column(
        String(8), index=True, nullable=False, comment="交易日期 YYYYMMDD"
    )
    indicator_name = Column(
        String(16),
        index=True,
        nullable=False,
        comment="Indicator: macd/rsi/kdj/boll",
    )
    params_hash = Column(
        String(16),
        index=True,
        nullable=False,
        comment="MD5 hash of params dict",
    )
    value_json = Column(
        String, nullable=False, comment="JSON-encoded indicator values for this date"
    )

    # Relationship back to stock
    stock = relationship("Stock", back_populates="indicator_values")

    def __repr__(self):
        return f"<IndicatorValue({self.ts_code} {self.trade_date} {self.indicator_name})>"
