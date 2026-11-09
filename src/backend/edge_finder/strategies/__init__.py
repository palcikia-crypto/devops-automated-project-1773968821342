"""
Polymarket Crypto Lab - Strategies Module
Contains all trading strategies for signal generation
"""
from .base import BaseStrategy
from .undervalued import UndervaluedStrategy
from .arbitrage import ArbitrageStrategy
from .trending import TrendingStrategy
from .correlation import CorrelationStrategy
from .liquidity import LiquidityStrategy
from .sentiment import SentimentStrategy
from .seasonality import SeasonalityStrategy
from .mean_reversion import MeanReversionStrategy
from .breakout import BreakoutStrategy
from .volume_spike import VolumeSpikeStrategy

__all__ = [
    "BaseStrategy",
    "UndervaluedStrategy",
    "ArbitrageStrategy",
    "TrendingStrategy",
    "CorrelationStrategy",
    "LiquidityStrategy",
    "SentimentStrategy",
    "SeasonalityStrategy",
    "MeanReversionStrategy",
    "BreakoutStrategy",
    "VolumeSpikeStrategy",
]
