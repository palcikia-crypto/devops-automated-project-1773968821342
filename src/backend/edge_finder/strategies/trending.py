"""
Trending Strategy for Polymarket Crypto Lab
Finds markets with strong upward or downward trends
"""
from typing import List, Dict, Optional, Any, Tuple
import logging
import numpy as np

from config import settings
from ...models.schemas import Signal, SignalType
from .base import BaseStrategy
from ...utils.logger import get_logger

logger = get_logger(__name__)


class TrendingStrategy(BaseStrategy):
    """
    Strategy that identifies markets with strong trends
    
    Looks for:
    1. Markets with consistently increasing probabilities
    2. Markets with consistently decreasing probabilities
    3. Markets with high momentum
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.TRENDING
    
    @property
    def name(self) -> str:
        return "Trending Markets"
    
    @property
    def description(self) -> str:
        return "Finds markets where probabilities are showing strong upward or downward trends"
    
    def __init__(
        self,
        polymarket_client: Optional[Any] = None,
        min_growth: float = 0.05,  # Minimum 5% growth
        min_decline: float = 0.05,  # Minimum 5% decline
        lookback_period: int = 10,  # Look at last 10 data points
        **kwargs
    ):
        """Initialize the strategy"""
        super().__init__(polymarket_client, **kwargs)
        self.min_growth = min_growth
        self.min_decline = min_decline
        self.lookback_period = lookback_period
    
    async def generate_signals(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[Signal]:
        """
        Generate trending signals
        
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
        Analyze a single market for trending opportunities
        
        Args:
            market: Market dictionary
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        # Get price history
        price_history = await self._get_price_history(
            market["slug"],
            limit=self.lookback_period * 2  # Get more data for better analysis
        )
        
        if len(price_history) < self.lookback_period:
            return signals
        
        # Get current price
        current_price = market.get("outcomePrices", [0.5])[0]
        
        # Calculate trend for each outcome
        outcomes = market.get("outcomes", [])
        outcome_prices = market.get("outcomePrices", [])
        
        for i, (outcome, price) in enumerate(zip(outcomes, outcome_prices)):
            # Get historical prices for this outcome
            # For simplicity, we use the same history for all outcomes
            # In a real implementation, we would get history for each outcome
            
            # Calculate growth rate
            past_prices = price_history[-self.lookback_period:]
            if len(past_prices) < 2:
                continue
            
            past_avg = np.mean(past_prices)
            growth = (price - past_avg) / past_avg if past_avg > 0 else 0
            
            # Check for upward trend
            if growth >= self.min_growth:
                signal = self._create_signal(
                    market=market,
                    outcome=outcome,
                    outcome_index=i,
                    entry_price=price,
                    current_price=price,
                    growth=growth,
                    position_size=min(
                        settings.MAX_POSITION_SIZE,
                        market.get("liquidity", 1000) * 0.1
                    ),
                    target_price=min(0.99, price * (1 + growth)),  # Target based on growth
                    stop_loss=max(0.01, price * (1 - growth * 0.5))  # Stop loss at 50% of growth
                )
                signals.append(signal)
                logger.info(
                    f"📈 Upward trend: {market['title']} | "
                    f"Outcome: {outcome} | Growth: {growth:.2%}"
                )
            
            # Check for downward trend
            elif growth <= -self.min_decline:
                signal = self._create_signal(
                    market=market,
                    outcome=outcome,
                    outcome_index=i,
                    entry_price=price,
                    current_price=price,
                    growth=growth,
                    position_size=min(
                        settings.MAX_POSITION_SIZE,
                        market.get("liquidity", 1000) * 0.1
                    ),
                    target_price=max(0.01, price * (1 + growth)),  # Target based on decline
                    stop_loss=min(0.99, price * (1 - growth * 0.5))  # Stop loss at 50% of decline
                )
                signals.append(signal)
                logger.info(
                    f"📉 Downward trend: {market['title']} | "
                    f"Outcome: {outcome} | Decline: {abs(growth):.2%}"
                )
        
        return signals
    
    def _calculate_momentum(
        self,
        prices: List[float],
        period: int = 10
    ) -> float:
        """
        Calculate momentum of price series
        
        Args:
            prices: List of prices
            period: Period for momentum calculation
            
        Returns:
            Momentum value
        """
        if len(prices) < period:
            return 0.0
        
        current = prices[-1]
        past = prices[-period]
        
        return (current - past) / past if past > 0 else 0.0
    
    def _calculate_slope(
        self,
        prices: List[float]
    ) -> float:
        """
        Calculate slope of price series using linear regression
        
        Args:
            prices: List of prices
            
        Returns:
            Slope value
        """
        if len(prices) < 2:
            return 0.0
        
        n = len(prices)
        x = np.arange(n)
        y = np.array(prices)
        
        # Simple linear regression: slope = cov(x, y) / var(x)
        cov = np.cov(x, y)[0, 1]
        var = np.var(x)
        
        return cov / var if var > 0 else 0.0
