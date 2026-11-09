"""
Undervalued Strategy for Polymarket Crypto Lab
Finds markets where the current probability is undervalued compared to predictions
"""
from typing import List, Dict, Optional, Any, Tuple
import logging
import numpy as np

from config import settings
from ...models.schemas import Signal, SignalType
from .base import BaseStrategy
from ...utils.logger import get_logger

logger = get_logger(__name__)


class UndervaluedStrategy(BaseStrategy):
    """
    Strategy that identifies undervalued outcomes in prediction markets
    
    The idea is to compare market probabilities with:
    1. Historical averages
    2. Statistical models
    3. External predictions (if available)
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.UNDERVALUED
    
    @property
    def name(self) -> str:
        return "Undervalued Outcomes"
    
    @property
    def description(self) -> str:
        return "Finds markets where the current probability is significantly different from expected value"
    
    def __init__(
        self,
        polymarket_client: Optional[Any] = None,
        min_edge: float = 0.10,  # Minimum 10% edge
        max_edge: float = 0.50,  # Maximum 50% edge (too good to be true)
        **kwargs
    ):
        """Initialize the strategy"""
        super().__init__(polymarket_client, **kwargs)
        self.min_edge = min_edge
        self.max_edge = max_edge
    
    async def generate_signals(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[Signal]:
        """
        Generate undervalued signals
        
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
        Analyze a single market for undervalued opportunities
        
        Args:
            market: Market dictionary
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        # Get market data
        outcomes = market.get("outcomes", [])
        outcome_prices = market.get("outcomePrices", [])
        
        if not outcomes or not outcome_prices:
            return signals
        
        # Calculate expected probabilities based on historical data
        expected_probs = await self._calculate_expected_probabilities(market)
        
        # Compare with current prices
        for i, (outcome, current_price, expected_prob) in enumerate(
            zip(outcomes, outcome_prices, expected_probs)
        ):
            # Calculate edge
            edge = self._calculate_edge(expected_prob, current_price)
            
            # Check if edge meets criteria
            if self.min_edge <= abs(edge) <= self.max_edge:
                # Determine if we should buy or sell
                # If expected > current, buy (undervalued)
                # If expected < current, sell (overvalued)
                
                if edge > 0:  # Undervalued - buy
                    signal = self._create_signal(
                        market=market,
                        outcome=outcome,
                        outcome_index=i,
                        entry_price=current_price,
                        current_price=current_price,
                        edge=edge,
                        position_size=min(
                            settings.MAX_POSITION_SIZE,
                            market.get("liquidity", 1000) * 0.1  # 10% of liquidity
                        ),
                        target_price=expected_prob,  # Target is expected probability
                        stop_loss=max(0.01, current_price - 0.1)  # 10% stop loss
                    )
                    signals.append(signal)
                    logger.info(
                        f"🎯 Undervalued signal: {market['title']} | "
                        f"Outcome: {outcome} | Edge: {edge:.2%}"
                    )
                
                elif edge < 0:  # Overvalued - sell
                    signal = self._create_signal(
                        market=market,
                        outcome=outcome,
                        outcome_index=i,
                        entry_price=current_price,
                        current_price=current_price,
                        edge=edge,
                        position_size=min(
                            settings.MAX_POSITION_SIZE,
                            market.get("liquidity", 1000) * 0.1
                        ),
                        target_price=expected_prob,
                        stop_loss=min(0.99, current_price + 0.1)  # 10% stop loss
                    )
                    signals.append(signal)
                    logger.info(
                        f"🎯 Overvalued signal: {market['title']} | "
                        f"Outcome: {outcome} | Edge: {edge:.2%}"
                    )
        
        return signals
    
    async def _calculate_expected_probabilities(
        self,
        market: Dict[str, Any]
    ) -> List[float]:
        """
        Calculate expected probabilities for market outcomes
        
        Uses multiple methods:
        1. Historical average
        2. Statistical models
        3. Simple heuristics
        
        Args:
            market: Market dictionary
            
        Returns:
            List of expected probabilities for each outcome
        """
        outcomes = market.get("outcomes", [])
        outcome_prices = market.get("outcomePrices", [])
        
        if not outcomes or not outcome_prices:
            # Return uniform distribution if no data
            return [1.0 / len(outcomes)] * len(outcomes)
        
        # Method 1: Historical average (if we have historical data)
        historical_probs = await self._get_historical_averages(market)
        
        # Method 2: Simple heuristic based on market characteristics
        heuristic_probs = self._calculate_heuristic_probabilities(market)
        
        # Combine methods (simple average for now)
        expected_probs = []
        for i in range(len(outcomes)):
            historical = historical_probs[i] if i < len(historical_probs) else 0.5
            heuristic = heuristic_probs[i] if i < len(heuristic_probs) else 0.5
            
            # Weighted average
            expected = (historical * 0.6) + (heuristic * 0.4)
            expected_probs.append(expected)
        
        # Normalize to sum to 1.0
        total = sum(expected_probs)
        if total > 0:
            expected_probs = [p / total for p in expected_probs]
        
        return expected_probs
    
    async def _get_historical_averages(
        self,
        market: Dict[str, Any]
    ) -> List[float]:
        """
        Get historical average probabilities for a market
        
        Args:
            market: Market dictionary
            
        Returns:
            List of historical average probabilities
        """
        # For now, use current prices as a fallback
        # In a real implementation, we would query historical data
        outcome_prices = market.get("outcomePrices", [])
        return outcome_prices.copy()
    
    def _calculate_heuristic_probabilities(
        self,
        market: Dict[str, Any]
    ) -> List[float]:
        """
        Calculate heuristic probabilities based on market characteristics
        
        Args:
            market: Market dictionary
            
        Returns:
            List of heuristic probabilities
        """
        outcomes = market.get("outcomes", [])
        title = market.get("title", "").lower()
        
        # Simple heuristics based on market title
        if "bitcoin" in title or "btc" in title:
            # Bitcoin tends to go up over time
            if len(outcomes) >= 2:
                return [0.6, 0.4]  # 60% chance of "Yes"
        
        elif "ethereum" in title or "eth" in title:
            # Ethereum also tends to go up
            if len(outcomes) >= 2:
                return [0.55, 0.45]
        
        elif "up" in title or "rise" in title or "increase" in title:
            # Markets about going up
            if len(outcomes) >= 2:
                return [0.55, 0.45]
        
        elif "down" in title or "fall" in title or "decrease" in title:
            # Markets about going down
            if len(outcomes) >= 2:
                return [0.45, 0.55]
        
        # Default: uniform distribution
        return [1.0 / len(outcomes)] * len(outcomes)
