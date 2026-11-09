"""
Breakout Strategy for Polymarket Crypto Lab
Identifies breakout opportunities where prices move beyond key levels
"""
from typing import List, Dict, Optional, Any, Tuple
import logging
import numpy as np

from config import settings
from ...models.schemas import Signal, SignalType
from .base import BaseStrategy
from ...utils.logger import get_logger

logger = get_logger(__name__)


class BreakoutStrategy(BaseStrategy):
    """
    Strategy that identifies breakout opportunities
    
    A breakout occurs when the price moves outside a defined support or resistance level
    
    Looks for:
    1. Price breaking above resistance
    2. Price breaking below support
    3. Price breaking out of trading ranges
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.BREAKOUT
    
    @property
    def name(self) -> str:
        return "Breakout"
    
    @property
    def description(self) -> str:
        return "Identifies when prices break out of established trading ranges or key levels"
    
    def __init__(
        self,
        polymarket_client: Optional[Any] = None,
        lookback_period: int = 20,
        **kwargs
    ):
        """Initialize the strategy"""
        super().__init__(polymarket_client, **kwargs)
        self.lookback_period = lookback_period
    
    async def generate_signals(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[Signal]:
        """
        Generate breakout signals
        
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
        Analyze a single market for breakout opportunities
        
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
        
        current_price = market.get("outcomePrices", [0.5])[0]
        outcomes = market.get("outcomes", [])
        
        # Calculate support and resistance levels
        support, resistance = self._calculate_support_resistance(price_history)
        
        # Check for breakout above resistance
        if current_price > resistance:
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
                        target_price=min(0.99, resistance * 1.1),  # 10% above resistance
                        stop_loss=resistance  # Stop loss at resistance level
                    )
                    signals.append(signal)
                    
                    logger.info(
                        f"🔼 Breakout above resistance: {market['title']} | "
                        f"Outcome: {outcome} | Price: {current_price:.2%} | "
                        f"Resistance: {resistance:.2%}"
                    )
        
        # Check for breakdown below support
        elif current_price < support:
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
                        target_price=max(0.01, support * 0.9),  # 10% below support
                        stop_loss=support  # Stop loss at support level
                    )
                    signals.append(signal)
                    
                    logger.info(
                        f"🔽 Breakdown below support: {market['title']} | "
                        f"Outcome: {outcome} | Price: {current_price:.2%} | "
                        f"Support: {support:.2%}"
                    )
        
        return signals
    
    def _calculate_support_resistance(
        self,
        prices: List[float]
    ) -> Tuple[float, float]:
        """
        Calculate support and resistance levels
        
        Args:
            prices: List of historical prices
            
        Returns:
            Tuple of (support, resistance)
        """
        if len(prices) < 5:
            return 0.0, 1.0
        
        # Simple method: use min and max of recent prices
        recent_prices = prices[-self.lookback_period:]
        support = min(recent_prices)
        resistance = max(recent_prices)
        
        return support, resistance
    
    def _calculate_pivot_points(
        self,
        prices: List[float]
    ) -> Dict[str, float]:
        """
        Calculate pivot points (more sophisticated support/resistance)
        
        Args:
            prices: List of historical prices
            
        Returns:
            Dictionary with pivot point, support, and resistance levels
        """
        if len(prices) < 3:
            return {}
        
        # Get high, low, close from recent prices
        recent_prices = prices[-self.lookback_period:]
        high = max(recent_prices)
        low = min(recent_prices)
        close = recent_prices[-1]
        
        # Calculate pivot point
        pivot = (high + low + close) / 3
        
        # Calculate support and resistance levels
        r1 = (2 * pivot) - low
        s1 = (2 * pivot) - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        
        return {
            "pivot": pivot,
            "r1": r1,
            "r2": r2,
            "s1": s1,
            "s2": s2,
            "high": high,
            "low": low
        }
    
    async def _analyze_with_pivot_points(
        self,
        market: Dict[str, Any]
    ) -> List[Signal]:
        """
        Analyze market using pivot points
        
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
        
        # Calculate pivot points
        pivots = self._calculate_pivot_points(price_history)
        
        if not pivots:
            return signals
        
        current_price = market.get("outcomePrices", [0.5])[0]
        outcomes = market.get("outcomes", [])
        
        # Check for breakout above R1
        if current_price > pivots.get("r1", 0):
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
                        target_price=min(0.99, pivots.get("r2", current_price * 1.1)),
                        stop_loss=pivots.get("r1", current_price)
                    )
                    signals.append(signal)
        
        # Check for breakdown below S1
        elif current_price < pivots.get("s1", 1):
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
                        target_price=max(0.01, pivots.get("s2", current_price * 0.9)),
                        stop_loss=pivots.get("s1", current_price)
                    )
                    signals.append(signal)
        
        return signals
