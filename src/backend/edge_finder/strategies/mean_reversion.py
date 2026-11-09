"""
Mean Reversion Strategy for Polymarket Crypto Lab
Identifies opportunities where prices are expected to revert to their mean
"""
from typing import List, Dict, Optional, Any, Tuple
import logging
import numpy as np
from scipy.stats import zscore

from config import settings
from ...models.schemas import Signal, SignalType
from .base import BaseStrategy
from ...utils.logger import get_logger

logger = get_logger(__name__)


class MeanReversionStrategy(BaseStrategy):
    """
    Strategy that identifies mean reversion opportunities
    
    Based on the theory that prices tend to revert to their historical mean
    
    Looks for:
    1. Prices that are significantly above their historical average (overbought)
    2. Prices that are significantly below their historical average (oversold)
    3. Prices that have deviated far from their mean
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.MEAN_REVERSION
    
    @property
    def name(self) -> str:
        return "Mean Reversion"
    
    @property
    def description(self) -> str:
        return "Identifies overbought and oversold conditions where prices are expected to revert to their mean"
    
    def __init__(
        self,
        polymarket_client: Optional[Any] = None,
        threshold: float = 2.0,  # Z-score threshold
        lookback_period: int = 20,  # Lookback period for mean calculation
        **kwargs
    ):
        """Initialize the strategy"""
        super().__init__(polymarket_client, **kwargs)
        self.threshold = threshold
        self.lookback_period = lookback_period
    
    async def generate_signals(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[Signal]:
        """
        Generate mean reversion signals
        
        Args:
            markets: List of market dictionaries
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        # Filter markets
        filtered_markets = self._filter_markets(markets)
        
        for market in filtered_markets:
            try:
                market_signals = await self._analyze_market(market)
                signals.extend(market_signals)
            except Exception as e:
                logger.error(f"❌ Error analyzing market {market.get('title')}: {e}")
        
        return signals
    
    async def _analyze_market(
        self,
        market: Dict[str, Any]
    ) -> List[Signal]:
        """
        Analyze a single market for mean reversion opportunities
        
        Args:
            market: Market dictionary
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        # Get price history
        price_history = await self._get_price_history(
            market["slug"],
            limit=self.lookback_period * 2
        )
        
        if len(price_history) < self.lookback_period:
            return signals
        
        # Get current price
        current_price = market.get("outcomePrices", [0.5])[0]
        outcomes = market.get("outcomes", [])
        
        # Calculate mean and standard deviation
        historical_prices = price_history[-self.lookback_period:]
        mean_price = np.mean(historical_prices)
        std_price = np.std(historical_prices)
        
        if std_price == 0:
            return signals
        
        # Calculate z-score
        z_score = (current_price - mean_price) / std_price
        
        # Check for overbought conditions (z-score > threshold)
        if z_score >= self.threshold:
            for i, outcome in enumerate(outcomes):
                if outcome == "No":  # Bet on price going down
                    signal = self._create_signal(
                        market=market,
                        outcome=outcome,
                        outcome_index=i,
                        entry_price=current_price,
                        current_price=current_price,
                        position_size=min(
                            settings.MAX_POSITION_SIZE,
                            market.get("liquidity", 1000) * 0.1
                        ),
                        target_price=mean_price,  # Target is the mean
                        stop_loss=min(0.99, current_price * 1.05)  # Stop loss 5% above
                    )
                    signals.append(signal)
                    
                    logger.info(
                        f"📉 Overbought: {market['title']} | "
                        f"Outcome: {outcome} | Z-score: {z_score:.2f} | "
                        f"Current: {current_price:.2%} | Mean: {mean_price:.2%}"
                    )
        
        # Check for oversold conditions (z-score < -threshold)
        elif z_score <= -self.threshold:
            for i, outcome in enumerate(outcomes):
                if outcome == "Yes":  # Bet on price going up
                    signal = self._create_signal(
                        market=market,
                        outcome=outcome,
                        outcome_index=i,
                        entry_price=current_price,
                        current_price=current_price,
                        position_size=min(
                            settings.MAX_POSITION_SIZE,
                            market.get("liquidity", 1000) * 0.1
                        ),
                        target_price=mean_price,  # Target is the mean
                        stop_loss=max(0.01, current_price * 0.95)  # Stop loss 5% below
                    )
                    signals.append(signal)
                    
                    logger.info(
                        f"📈 Oversold: {market['title']} | "
                        f"Outcome: {outcome} | Z-score: {z_score:.2f} | "
                        f"Current: {current_price:.2%} | Mean: {mean_price:.2%}"
                    )
        
        return signals
    
    def _calculate_bollinger_bands(
        self,
        prices: List[float],
        period: int = 20,
        num_std: float = 2.0
    ) -> Dict[str, float]:
        """
        Calculate Bollinger Bands
        
        Args:
            prices: List of prices
            period: Period for moving average
            num_std: Number of standard deviations
            
        Returns:
            Dictionary with upper, middle, and lower bands
        """
        if len(prices) < period:
            return {}
        
        # Calculate moving average
        ma = np.mean(prices[-period:])
        
        # Calculate standard deviation
        std = np.std(prices[-period:])
        
        # Calculate bands
        upper_band = ma + (std * num_std)
        lower_band = ma - (std * num_std)
        
        return {
            "upper": upper_band,
            "middle": ma,
            "lower": lower_band,
            "std": std
        }
    
    async def _analyze_with_bollinger_bands(
        self,
        market: Dict[str, Any]
    ) -> List[Signal]:
        """
        Analyze market using Bollinger Bands
        
        Args:
            market: Market dictionary
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        # Get price history
        price_history = await self._get_price_history(
            market["slug"],
            limit=self.lookback_period * 2
        )
        
        if len(price_history) < self.lookback_period:
            return signals
        
        # Calculate Bollinger Bands
        bands = self._calculate_bollinger_bands(
            price_history,
            period=self.lookback_period
        )
        
        if not bands:
            return signals
        
        current_price = market.get("outcomePrices", [0.5])[0]
        outcomes = market.get("outcomes", [])
        
        # Check if price is above upper band (overbought)
        if current_price >= bands["upper"]:
            for i, outcome in enumerate(outcomes):
                if outcome == "No":
                    signal = self._create_signal(
                        market=market,
                        outcome=outcome,
                        outcome_index=i,
                        entry_price=current_price,
                        current_price=current_price,
                        position_size=min(
                            settings.MAX_POSITION_SIZE,
                            market.get("liquidity", 1000) * 0.1
                        ),
                        target_price=bands["middle"],
                        stop_loss=min(0.99, bands["upper"] * 1.02)
                    )
                    signals.append(signal)
        
        # Check if price is below lower band (oversold)
        elif current_price <= bands["lower"]:
            for i, outcome in enumerate(outcomes):
                if outcome == "Yes":
                    signal = self._create_signal(
                        market=market,
                        outcome=outcome,
                        outcome_index=i,
                        entry_price=current_price,
                        current_price=current_price,
                        position_size=min(
                            settings.MAX_POSITION_SIZE,
                            market.get("liquidity", 1000) * 0.1
                        ),
                        target_price=bands["middle"],
                        stop_loss=max(0.01, bands["lower"] * 0.98)
                    )
                    signals.append(signal)
        
        return signals
