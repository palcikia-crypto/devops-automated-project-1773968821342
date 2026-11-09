"""
Arbitrage Strategy for Polymarket Crypto Lab
Finds arbitrage opportunities between related markets
"""
from typing import List, Dict, Optional, Any, Tuple, Tuple
import logging
import itertools

from config import settings
from ...models.schemas import Signal, SignalType
from .base import BaseStrategy
from ...utils.logger import get_logger

logger = get_logger(__name__)


class ArbitrageStrategy(BaseStrategy):
    """
    Strategy that identifies arbitrage opportunities between related markets
    
    Looks for:
    1. Mutually exclusive markets where probabilities don't sum to 100%
    2. Related markets with price discrepancies
    3. Cross-market arbitrage opportunities
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.ARBITRAGE
    
    @property
    def name(self) -> str:
        return "Arbitrage Opportunities"
    
    @property
    def description(self) -> str:
        return "Finds markets where the sum of probabilities is less than 100%, allowing for risk-free arbitrage"
    
    def __init__(
        self,
        polymarket_client: Optional[Any] = None,
        min_arbitrage: float = 0.02,  # Minimum 2% arbitrage
        max_markets: int = 50,  # Maximum number of markets to compare
        **kwargs
    ):
        """Initialize the strategy"""
        super().__init__(polymarket_client, **kwargs)
        self.min_arbitrage = min_arbitrage
        self.max_markets = max_markets
    
    async def generate_signals(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[Signal]:
        """
        Generate arbitrage signals
        
        Args:
            markets: List of market dictionaries
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        # Filter and limit markets
        filtered_markets = self._filter_markets(markets)[:self.max_markets]
        
        if len(filtered_markets) < 2:
            return signals
        
        logger.info(f"🔍 Checking {len(filtered_markets)} markets for arbitrage opportunities...")
        
        # Find all pairs of mutually exclusive markets
        for market_a, market_b in itertools.combinations(filtered_markets, 2):
            try:
                # Check if markets are mutually exclusive
                if not self._is_mutually_exclusive(market_a, market_b):
                    continue
                
                # Check for arbitrage opportunity
                arbitrage_signals = await self._check_arbitrage(market_a, market_b)
                signals.extend(arbitrage_signals)
            except Exception as e:
                logger.error(f"❌ Error checking arbitrage for {market_a.get('title')} vs {market_b.get('title')}: {e}")
        
        return signals
    
    async def _check_arbitrage(
        self,
        market_a: Dict[str, Any],
        market_b: Dict[str, Any]
    ) -> List[Signal]:
        """
        Check for arbitrage opportunity between two markets
        
        Args:
            market_a: First market
            market_b: Second market
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        # Get probabilities for "Yes" outcomes
        prob_a = market_a.get("outcomePrices", [0.5])[0]
        prob_b = market_b.get("outcomePrices", [0.5])[0]
        
        # Calculate total probability
        total_prob = prob_a + prob_b
        
        # If total is less than 100%, there's an arbitrage opportunity
        if total_prob < (1.0 - self.min_arbitrage):
            arbitrage = 1.0 - total_prob
            
            logger.info(
                f"🎯 Arbitrage opportunity: {market_a['title']} ({prob_a:.2%}) + "
                f"{market_b['title']} ({prob_b:.2%}) = {total_prob:.2%} | "
                f"Arbitrage: {arbitrage:.2%}"
            )
            
            # Create signal for buying both outcomes
            signal = self._create_signal(
                market=market_a,  # Use first market as reference
                outcome="Yes",
                outcome_index=0,
                entry_price=prob_a,
                current_price=prob_a,
                arbitrage=arbitrage,
                position_size=min(
                    settings.MAX_POSITION_SIZE,
                    market_a.get("liquidity", 1000) * 0.1,
                    market_b.get("liquidity", 1000) * 0.1
                ),
                # For arbitrage, we buy both outcomes
                # The PnL will be calculated based on the arbitrage percentage
                target_price=1.0,  # Target is 100%
                stop_loss=0.0  # No stop loss for arbitrage (risk-free)
            )
            
            # Add information about the second market
            signal.market_title = f"{market_a['title']} + {market_b['title']}"
            signal.market_slug = f"{market_a['slug']}-{market_b['slug']}"
            
            signals.append(signal)
        
        return signals
    
    async def find_cross_market_arbitrage(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[Signal]:
        """
        Find arbitrage opportunities across different markets
        
        Args:
            markets: List of market dictionaries
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        # Group markets by condition ID (same event)
        markets_by_condition: Dict[str, List[Dict[str, Any]]] = {}
        for market in markets:
            condition_id = market.get("conditionId", "")
            if condition_id not in markets_by_condition:
                markets_by_condition[condition_id] = []
            markets_by_condition[condition_id].append(market)
        
        # Check each group for arbitrage
        for condition_id, condition_markets in markets_by_condition.items():
            if len(condition_markets) < 2:
                continue
            
            # Check if sum of probabilities is less than 100%
            total_prob = sum(m.get("outcomePrices", [0.5])[0] for m in condition_markets)
            
            if total_prob < (1.0 - self.min_arbitrage):
                arbitrage = 1.0 - total_prob
                
                logger.info(
                    f"🎯 Cross-market arbitrage: Condition {condition_id} | "
                    f"Total probability: {total_prob:.2%} | Arbitrage: {arbitrage:.2%}"
                )
                
                # Create signal for buying all outcomes
                signal = self._create_signal(
                    market=condition_markets[0],
                    outcome="Multiple",
                    outcome_index=0,
                    entry_price=total_prob / len(condition_markets),
                    current_price=total_prob / len(condition_markets),
                    arbitrage=arbitrage,
                    position_size=min(
                        settings.MAX_POSITION_SIZE,
                        min(m.get("liquidity", 1000) for m in condition_markets) * 0.1
                    ),
                    target_price=1.0,
                    stop_loss=0.0
                )
                
                # Update signal with information about all markets
                signal.market_title = f"Condition {condition_id} (Cross-market)"
                signal.market_slug = f"condition-{condition_id}"
                
                signals.append(signal)
        
        return signals
