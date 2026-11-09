"""
Pydantic schemas for Polymarket Crypto Lab
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MarketType(str, Enum):
    BINARY = "binary"
    MULTIPLE_CHOICE = "multiple_choice"
    SCALAR = "scalar"


class MarketStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class SignalType(str, Enum):
    UNDERVALUED = "undervalued"
    ARBITRAGE = "arbitrage"
    TRENDING = "trending"
    CORRELATION = "correlation"
    LIQUIDITY = "liquidity"
    SENTIMENT = "sentiment"
    SEASONALITY = "seasonality"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    VOLUME_SPIKE = "volume_spike"


class SignalStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"


class TradeSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class TradeStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class NotificationType(str, Enum):
    SIGNAL = "signal"
    TRADE = "trade"
    ALERT = "alert"
    ERROR = "error"


# ==================== MARKET SCHEMAS ====================

class MarketBase(BaseModel):
    """Base market schema"""
    id: Optional[str] = Field(default=None, description="Market ID")
    title: str = Field(..., description="Market title")
    slug: str = Field(..., description="Market slug")
    question: Optional[str] = Field(default=None, description="Market question")
    category: str = Field(..., description="Market category")
    subcategory: Optional[str] = Field(default=None, description="Market subcategory")
    

class MarketCreate(MarketBase):
    """Schema for creating a market"""
    condition_id: Optional[str] = Field(default=None, description="Condition ID")
    outcomes: List[str] = Field(default_factory=list, description="List of outcomes")
    end_date: Optional[datetime] = Field(default=None, description="Market end date")
    resolution_source: Optional[str] = Field(default=None, description="Resolution source")
    

class Market(MarketBase):
    """Full market schema"""
    condition_id: Optional[str] = Field(default=None, description="Condition ID")
    outcomes: List[str] = Field(default_factory=list, description="List of outcomes")
    outcome_prices: List[float] = Field(default_factory=list, description="Current outcome prices (0-1)")
    volume_24hr: float = Field(default=0.0, description="24-hour volume in pUSD")
    volume_1wk: float = Field(default=0.0, description="1-week volume in pUSD")
    volume_1mo: float = Field(default=0.0, description="1-month volume in pUSD")
    liquidity: float = Field(default=0.0, description="Current liquidity in pUSD")
    end_date: Optional[datetime] = Field(default=None, description="Market end date")
    start_date: Optional[datetime] = Field(default=None, description="Market start date")
    resolution_source: Optional[str] = Field(default=None, description="Resolution source")
    market_type: MarketType = Field(default=MarketType.BINARY, description="Market type")
    status: MarketStatus = Field(default=MarketStatus.ACTIVE, description="Market status")
    clob_token_ids: List[str] = Field(default_factory=list, description="CLOB token IDs")
    image: Optional[HttpUrl] = Field(default=None, description="Market image URL")
    icon: Optional[HttpUrl] = Field(default=None, description="Market icon URL")
    fee: float = Field(default=0.0, description="Market fee")
    accepting_orders: bool = Field(default=True, description="Is market accepting orders")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class MarketUpdate(BaseModel):
    """Schema for updating a market"""
    outcome_prices: Optional[List[float]] = Field(default=None, description="Updated outcome prices")
    volume_24hr: Optional[float] = Field(default=None, description="Updated 24-hour volume")
    liquidity: Optional[float] = Field(default=None, description="Updated liquidity")
    status: Optional[MarketStatus] = Field(default=None, description="Updated status")
    

class MarketData(BaseModel):
    """Schema for market data with additional fields"""
    market: Market = Field(..., description="Market object")
    order_book: Optional[Dict[str, Any]] = Field(default=None, description="Order book data")
    price_history: List[Dict[str, Any]] = Field(default_factory=list, description="Price history")
    

class OrderBook(BaseModel):
    """Schema for order book data"""
    token_id: str = Field(..., description="Token ID")
    bids: List[Dict[str, Any]] = Field(default_factory=list, description="Bid orders")
    asks: List[Dict[str, Any]] = Field(default_factory=list, description="Ask orders")
    mid_price: float = Field(default=0.0, description="Mid price")
    spread: float = Field(default=0.0, description="Spread")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class PriceData(BaseModel):
    """Schema for price data"""
    token_id: str = Field(..., description="Token ID")
    price: float = Field(..., description="Current price (0-1)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")


# ==================== SIGNAL SCHEMAS ====================

class SignalBase(BaseModel):
    """Base signal schema"""
    type: SignalType = Field(..., description="Signal type")
    market_id: str = Field(..., description="Market ID")
    market_title: str = Field(..., description="Market title")
    market_slug: str = Field(..., description="Market slug")
    

class SignalCreate(SignalBase):
    """Schema for creating a signal"""
    outcome: Optional[str] = Field(default=None, description="Outcome (Yes/No)")
    outcome_index: Optional[int] = Field(default=None, description="Outcome index")
    entry_price: float = Field(..., description="Entry price (0-1)")
    current_price: float = Field(..., description="Current price (0-1)")
    target_price: Optional[float] = Field(default=None, description="Target price (0-1)")
    stop_loss: Optional[float] = Field(default=None, description="Stop loss price (0-1)")
    take_profit: Optional[float] = Field(default=None, description="Take profit price (0-1)")
    
    # Strategy-specific fields
    edge: Optional[float] = Field(default=None, description="Edge (for undervalued)")
    arbitrage: Optional[float] = Field(default=None, description="Arbitrage opportunity")
    growth: Optional[float] = Field(default=None, description="Growth rate (for trending)")
    correlation: Optional[float] = Field(default=None, description="Correlation coefficient")
    sentiment_score: Optional[float] = Field(default=None, description="Sentiment score")
    
    # Risk management
    position_size: float = Field(default=100.0, description="Position size in pUSD")
    risk_per_trade: float = Field(default=0.01, description="Risk per trade (1%)")
    

class Signal(SignalCreate):
    """Full signal schema"""
    id: str = Field(..., description="Signal ID")
    status: SignalStatus = Field(default=SignalStatus.PENDING, description="Signal status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    closed_at: Optional[datetime] = Field(default=None, description="Closure timestamp")
    pnl: Optional[float] = Field(default=None, description="Profit/Loss in pUSD")
    pnl_pct: Optional[float] = Field(default=None, description="Profit/Loss percentage")
    
    class Config:
        from_attributes = True


# ==================== TRADING SCHEMAS ====================

class TradeBase(BaseModel):
    """Base trade schema"""
    market_id: str = Field(..., description="Market ID")
    market_title: str = Field(..., description="Market title")
    signal_id: Optional[str] = Field(default=None, description="Signal ID")
    side: TradeSide = Field(..., description="Trade side (buy/sell)")
    outcome: str = Field(..., description="Outcome (Yes/No)")
    outcome_index: int = Field(..., description="Outcome index")
    

class TradeCreate(TradeBase):
    """Schema for creating a trade"""
    amount: float = Field(..., description="Trade amount in pUSD")
    price: float = Field(..., description="Trade price (0-1)")
    fee: float = Field(default=0.0, description="Trade fee")
    

class Trade(TradeCreate):
    """Full trade schema"""
    id: str = Field(..., description="Trade ID")
    status: TradeStatus = Field(default=TradeStatus.PENDING, description="Trade status")
    filled_amount: float = Field(default=0.0, description="Filled amount")
    avg_fill_price: float = Field(default=0.0, description="Average fill price")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class Position(BaseModel):
    """Schema for position"""
    id: str = Field(..., description="Position ID")
    market_id: str = Field(..., description="Market ID")
    market_title: str = Field(..., description="Market title")
    outcome: str = Field(..., description="Outcome")
    outcome_index: int = Field(..., description="Outcome index")
    amount: float = Field(..., description="Position amount in pUSD")
    entry_price: float = Field(..., description="Entry price (0-1)")
    current_price: float = Field(..., description="Current price (0-1)")
    pnl: float = Field(default=0.0, description="Profit/Loss in pUSD")
    pnl_pct: float = Field(default=0.0, description="Profit/Loss percentage")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    
    class Config:
        from_attributes = True


class Portfolio(BaseModel):
    """Schema for portfolio"""
    total_balance: float = Field(..., description="Total balance in pUSD")
    available_balance: float = Field(..., description="Available balance in pUSD")
    positions: List[Position] = Field(default_factory=list, description="List of positions")
    total_pnl: float = Field(default=0.0, description="Total PnL in pUSD")
    total_pnl_pct: float = Field(default=0.0, description="Total PnL percentage")
    
    class Config:
        from_attributes = True


# ==================== PAPER TRADING SCHEMAS ====================

class PaperTradeBase(BaseModel):
    """Base paper trade schema"""
    market_id: str = Field(..., description="Market ID")
    market_title: str = Field(..., description="Market title")
    signal_id: Optional[str] = Field(default=None, description="Signal ID")
    

class PaperTradeCreate(PaperTradeBase):
    """Schema for creating a paper trade"""
    side: TradeSide = Field(..., description="Trade side (buy/sell)")
    outcome: str = Field(..., description="Outcome (Yes/No)")
    outcome_index: int = Field(..., description="Outcome index")
    amount: float = Field(..., description="Trade amount in pUSD")
    price: float = Field(..., description="Trade price (0-1)")
    fee: float = Field(default=0.0, description="Trade fee")
    

class PaperTrade(PaperTradeCreate):
    """Full paper trade schema"""
    id: str = Field(..., description="Paper trade ID")
    status: TradeStatus = Field(default=TradeStatus.PENDING, description="Trade status")
    filled_amount: float = Field(default=0.0, description="Filled amount")
    avg_fill_price: float = Field(default=0.0, description="Average fill price")
    current_price: float = Field(default=0.0, description="Current price (0-1)")
    pnl: float = Field(default=0.0, description="Profit/Loss in pUSD")
    pnl_pct: float = Field(default=0.0, description="Profit/Loss percentage")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    closed_at: Optional[datetime] = Field(default=None, description="Closure timestamp")
    
    class Config:
        from_attributes = True


# ==================== STRATEGY SCHEMAS ====================

class StrategyConfig(BaseModel):
    """Schema for strategy configuration"""
    name: str = Field(..., description="Strategy name")
    type: SignalType = Field(..., description="Strategy type")
    enabled: bool = Field(default=True, description="Is strategy enabled")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    
    class Config:
        from_attributes = True


# ==================== NOTIFICATION SCHEMAS ====================

class Notification(BaseModel):
    """Schema for notification"""
    id: str = Field(..., description="Notification ID")
    type: NotificationType = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional data")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    read: bool = Field(default=False, description="Is notification read")
    
    class Config:
        from_attributes = True


# ==================== USER SETTINGS SCHEMAS ====================

class UserSettings(BaseModel):
    """Schema for user settings"""
    id: str = Field(..., description="Settings ID")
    user_id: Optional[str] = Field(default=None, description="User ID")
    
    # Trading settings
    max_position_size: float = Field(default=1000.0, description="Maximum position size")
    max_portfolio_risk: float = Field(default=0.05, description="Maximum portfolio risk")
    stop_loss_pct: float = Field(default=0.10, description="Stop loss percentage")
    take_profit_pct: float = Field(default=0.20, description="Take profit percentage")
    
    # Notification settings
    telegram_enabled: bool = Field(default=False, description="Telegram notifications enabled")
    discord_enabled: bool = Field(default=False, description="Discord notifications enabled")
    email_enabled: bool = Field(default=False, description="Email notifications enabled")
    
    # Strategy settings
    strategies: List[StrategyConfig] = Field(default_factory=list, description="List of strategies")
    
    # Paper trading settings
    paper_trading_enabled: bool = Field(default=True, description="Paper trading enabled")
    paper_trading_balance: float = Field(default=10000.0, description="Paper trading balance")
    
    # Scan settings
    scan_interval_minutes: int = Field(default=5, description="Scan interval in minutes")
    signal_generation_interval_minutes: int = Field(default=15, description="Signal generation interval")
    
    # Market filters
    min_volume_24hr: float = Field(default=10000.0, description="Minimum 24-hour volume")
    min_liquidity: float = Field(default=5000.0, description="Minimum liquidity")
    
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


# ==================== DASHBOARD SCHEMAS ====================

class DashboardData(BaseModel):
    """Schema for dashboard data"""
    # Summary
    total_markets: int = Field(..., description="Total number of markets")
    active_markets: int = Field(..., description="Number of active markets")
    
    # Portfolio
    portfolio: Portfolio = Field(..., description="Portfolio data")
    
    # Signals
    active_signals: int = Field(..., description="Number of active signals")
    recent_signals: List[Signal] = Field(default_factory=list, description="Recent signals")
    
    # Trading
    recent_trades: List[Trade] = Field(default_factory=list, description="Recent trades")
    trade_history: List[Dict[str, Any]] = Field(default_factory=list, description="Trade history")
    
    # Market data
    top_markets: List[Market] = Field(default_factory=list, description="Top markets by volume")
    trending_markets: List[Market] = Field(default_factory=list, description="Trending markets")
    
    # Statistics
    stats: Dict[str, Any] = Field(default_factory=dict, description="Statistics")
    
    class Config:
        from_attributes = True
