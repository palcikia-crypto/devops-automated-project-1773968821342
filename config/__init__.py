"""
Configuration module for Polymarket Crypto Lab
"""
from pydantic_settings import BaseSettings
from pydantic import Field, HttpUrl
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Polymarket API
    POLYMARKET_GAMMA_API_URL: HttpUrl = Field(
        default="https://gamma-api.polymarket.com",
        description="Gamma API base URL"
    )
    POLYMARKET_CLOB_API_URL: HttpUrl = Field(
        default="https://clob.polymarket.com",
        description="CLOB API base URL"
    )
    POLYMARKET_DATA_API_URL: HttpUrl = Field(
        default="https://data-api.polymarket.com",
        description="Data API base URL"
    )
    POLYMARKET_WS_URL: str = Field(
        default="wss://ws-subscriptions-clob.polymarket.com",
        description="WebSocket URL"
    )
    
    # API Keys (optional for trading)
    POLYMARKET_API_KEY: Optional[str] = Field(
        default=None,
        description="Polymarket API key for trading"
    )
    POLYMARKET_API_SECRET: Optional[str] = Field(
        default=None,
        description="Polymarket API secret"
    )
    POLYMARKET_API_PASSPHRASE: Optional[str] = Field(
        default=None,
        description="Polymarket API passphrase"
    )
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/polymarket.db",
        description="Database connection URL"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # Paper Trading
    PAPER_TRADING_ENABLED: bool = Field(
        default=True,
        description="Enable paper trading mode"
    )
    PAPER_TRADING_INITIAL_BALANCE: float = Field(
        default=10000.0,
        description="Initial balance for paper trading"
    )
    
    # Web Server
    WEB_HOST: str = Field(
        default="0.0.0.0",
        description="Web server host"
    )
    WEB_PORT: int = Field(
        default=8000,
        description="Web server port"
    )
    
    # Frontend
    FRONTEND_URL: HttpUrl = Field(
        default="http://localhost:3000",
        description="Frontend application URL"
    )
    
    # Notifications
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(
        default=None,
        description="Telegram bot token"
    )
    TELEGRAM_CHAT_ID: Optional[str] = Field(
        default=None,
        description="Telegram chat ID"
    )
    DISCORD_WEBHOOK_URL: Optional[str] = Field(
        default=None,
        description="Discord webhook URL"
    )
    
    # External APIs
    COINGECKO_API_KEY: Optional[str] = Field(
        default=None,
        description="CoinGecko API key"
    )
    TWITTER_BEARER_TOKEN: Optional[str] = Field(
        default=None,
        description="Twitter API bearer token"
    )
    NEWSAPI_KEY: Optional[str] = Field(
        default=None,
        description="NewsAPI key"
    )
    
    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    LOG_FILE: str = Field(
        default="logs/polymarket-lab.log",
        description="Log file path"
    )
    LOGS_DIR: str = Field(
        default="logs",
        description="Logs directory"
    )
    
    # Scheduler
    MARKET_SCAN_INTERVAL: int = Field(
        default=300,
        description="Market scan interval in seconds (5 minutes)"
    )
    SIGNAL_GENERATION_INTERVAL: int = Field(
        default=900,
        description="Signal generation interval in seconds (15 minutes)"
    )
    POSITION_UPDATE_INTERVAL: int = Field(
        default=60,
        description="Position update interval in seconds (1 minute)"
    )
    PORTFOLIO_SNAPSHOT_INTERVAL: int = Field(
        default=3600,
        description="Portfolio snapshot interval in seconds (1 hour)"
    )
    BACKTEST_INTERVAL_HOURS: int = Field(
        default=24,
        description="Backtest interval in hours"
    )
    
    # Trading
    ENABLE_REAL_TRADING: bool = Field(
        default=False,
        description="Enable real trading (requires wallet configuration)"
    )
    ENABLE_PAPER_TRADING: bool = Field(
        default=True,
        description="Enable paper trading"
    )
    AUTO_TRADE: bool = Field(
        default=False,
        description="Automatically execute trades from signals"
    )
    MAX_AUTO_TRADES: int = Field(
        default=5,
        description="Maximum number of auto-trades per cycle"
    )
    MAX_POSITION_SIZE: float = Field(
        default=1000.0,
        description="Maximum position size in USD"
    )
    MAX_PORTFOLIO_RISK: float = Field(
        default=0.05,
        description="Maximum portfolio risk (5%)"
    )
    STOP_LOSS_PCT: float = Field(
        default=0.10,
        description="Stop loss percentage (10%)"
    )
    TAKE_PROFIT_PCT: float = Field(
        default=0.20,
        description="Take profit percentage (20%)"
    )
    
    # Wallet
    WALLET_ADDRESS: Optional[str] = Field(
        default=None,
        description="Wallet address for trading"
    )
    WALLET_PRIVATE_KEY: Optional[str] = Field(
        default=None,
        description="Wallet private key for signing (keep secure!)"
    )
    CLOB_API_URL: HttpUrl = Field(
        default="https://clob.polymarket.com",
        description="CLOB API URL"
    )
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(
        default=100,
        description="Rate limit requests"
    )
    RATE_LIMIT_PERIOD: int = Field(
        default=60,
        description="Rate limit period in seconds"
    )
    
    # Environment
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment (development, staging, production)"
    )
    DEBUG: bool = Field(
        default=True,
        description="Debug mode"
    )
    
    # Crypto Tag IDs
    CRYPTO_TAG_ID: int = Field(
        default=21,
        description="Tag ID for Crypto markets"
    )
    BITCOIN_TAG_ID: int = Field(
        default=21,
        description="Tag ID for Bitcoin markets"
    )
    ETHEREUM_TAG_ID: int = Field(
        default=21,
        description="Tag ID for Ethereum markets"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Initialize settings
settings = Settings()

# Create directories if they don't exist
os.makedirs("data", exist_ok=True)
os.makedirs("logs", exist_ok=True)
