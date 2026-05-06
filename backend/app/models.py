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


class PracticeSession(Base):
    """Trading practice session."""

    __tablename__ = "practice_sessions"
    __table_args__ = {"sqlite_autoincrement": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(
        String(16),
        ForeignKey("stocks.ts_code"),
        nullable=False,
        comment="股票代码",
    )
    start_date = Column(String(8), nullable=False, comment="练习起始日期 YYYYMMDD")
    end_date = Column(String(8), nullable=False, comment="练习结束日期 YYYYMMDD")
    initial_capital = Column(Float, nullable=False, default=1000000.0, comment="初始资金")
    current_date = Column(String(8), nullable=True, comment="当前推进到的日期")
    cash = Column(Float, nullable=False, comment="当前可用资金")
    status = Column(String(16), nullable=False, default="active", comment="状态: active/finished")
    created_at = Column(String(19), nullable=False, comment="创建时间 ISO datetime")

    stock = relationship("Stock")
    trades = relationship("Trade", back_populates="session", lazy="selectin")
    positions = relationship("Position", back_populates="session", lazy="selectin")

    def __repr__(self):
        return f"<PracticeSession({self.id} {self.ts_code} {self.status})>"


class Trade(Base):
    """Individual buy/sell trade record."""

    __tablename__ = "practice_trades"
    __table_args__ = {"sqlite_autoincrement": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        Integer,
        ForeignKey("practice_sessions.id"),
        nullable=False,
        index=True,
        comment="会话ID",
    )
    trade_type = Column(String(4), nullable=False, comment="交易类型: buy/sell")
    ts_code = Column(String(16), nullable=False, comment="股票代码")
    trade_date = Column(String(8), nullable=False, comment="交易日期 YYYYMMDD")
    shares = Column(Integer, nullable=False, comment="股数（手x100）")
    price = Column(Float, nullable=False, comment="成交价格")
    amount = Column(Float, nullable=False, comment="成交金额 = shares * price")
    commission = Column(Float, nullable=False, default=0.0, comment="佣金")
    stamp_tax = Column(Float, nullable=False, default=0.0, comment="印花税(仅卖出)")

    session = relationship("PracticeSession", back_populates="trades")

    def __repr__(self):
        return f"<Trade({self.id} {self.trade_type} {self.ts_code} {self.trade_date})>"


class Position(Base):
    """Open position lot tracking (FIFO sell matching)."""

    __tablename__ = "practice_positions"
    __table_args__ = {"sqlite_autoincrement": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        Integer,
        ForeignKey("practice_sessions.id"),
        nullable=False,
        index=True,
        comment="会话ID",
    )
    buy_trade_id = Column(
        Integer,
        ForeignKey("practice_trades.id"),
        nullable=False,
        comment="对应的买入交易ID",
    )
    ts_code = Column(String(16), nullable=False, comment="股票代码")
    buy_date = Column(String(8), nullable=False, comment="买入日期 YYYYMMDD")
    buy_price = Column(Float, nullable=False, comment="买入价格")
    total_shares = Column(Integer, nullable=False, comment="初始买入股数")
    remaining_shares = Column(Integer, nullable=False, comment="剩余可卖股数")

    session = relationship("PracticeSession", back_populates="positions")
    buy_trade = relationship("Trade", foreign_keys=[buy_trade_id])

    def __repr__(self):
        return f"<Position({self.id} {self.ts_code} remaining={self.remaining_shares})>"
