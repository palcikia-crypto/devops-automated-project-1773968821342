"""
Correlation Strategy for Polymarket Crypto Lab
Finds correlated markets and identifies trading opportunities
"""
from typing import List, Dict, Optional, Any, Tuple, Tuple
import logging
import numpy as np
from scipy.stats import pearsonr, spearmanr
import itertools

from config import settings
from ...models.schemas import Signal, SignalType
from .base import BaseStrategy
from ...utils.logger import get_logger

logger = get_logger(__name__)


class CorrelationStrategy(BaseStrategy):
    """
    Strategy that identifies correlated markets and trading opportunities
    
    Looks for:
    1. Markets with high positive correlation
    2. Markets with high negative correlation
    3. Divergence between correlated markets
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.CORRELATION
    
    @property
    def name(self) -> str:
        return "Correlated Markets"
    
    @property
    def description(self) -> str:
        return "Finds markets that are highly correlated and identifies divergence opportunities"
    
    def __init__(
        self,
        polymarket_client: Optional[Any] = None,
        min_correlation: float = 0.8,  # Minimum correlation coefficient
        max_markets: int = 30,  # Maximum number of markets to compare
        lookback_period: int = 20,  # Lookback period for correlation
        **kwargs
    ):
        """Initialize the strategy"""
        super().__init__(polymarket_client, **kwargs)
        self.min_correlation = min_correlation
        self.max_markets = max_markets
        self.lookback_period = lookback_period
    
    async def generate_signals(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[Signal]:
        """
        Generate correlation signals
        
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
        
        logger.info(f"🔗 Checking {len(filtered_markets)} markets for correlations...")
        
        # Get price history for all markets
        price_histories = {}
        for market in filtered_markets:
            price_history = await self._get_price_history(
                market["slug"],
                limit=self.lookback_period
            )
            if price_history:
                price_histories[market["id"]] = {
                    "market": market,
                    "prices": price_history
                }
        
        # Find correlated market pairs
        for (id_a, data_a), (id_b, data_b) in itertools.combinations(price_histories.items(), 2):
            try:
                correlation_signals = await self._check_correlation(data_a, data_b)
                signals.extend(correlation_signals)
            except Exception as e:
                logger.error(f"❌ Error checking correlation between markets: {e}")
        
        return signals
    
    async def _check_correlation(
        self,
        data_a: Dict[str, Any],
        data_b: Dict[str, Any]
    ) -> List[Signal]:
        """
        Check correlation between two markets
        
        Args:
            data_a: Data for first market
            data_b: Data for second market
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        market_a = data_a["market"]
        market_b = data_b["market"]
        prices_a = data_a["prices"]
        prices_b = data_b["prices"]
        
        # Ensure we have enough data
        if len(prices_a) < 5 or len(prices_b) < 5:
            return signals
        
        # Calculate correlation
        correlation, _ = pearsonr(prices_a, prices_b)
        
        # Check for high correlation
        if abs(correlation) >= self.min_correlation:
            logger.info(
                f"🔗 High correlation: {market_a['title']} vs {market_b['title']} | "
                f"Correlation: {correlation:.3f}"
            )
            
            # Check for divergence
            current_price_a = market_a.get("outcomePrices", [0.5])[0]
            current_price_b = market_b.get("outcomePrices", [0.5])[0]
            
            # Calculate recent trends
            recent_a = prices_a[-5:]
            recent_b = prices_b[-5:]
            
            trend_a = (current_price_a - np.mean(recent_a)) / np.mean(recent_a) if np.mean(recent_a) > 0 else 0
            trend_b = (current_price_b - np.mean(recent_b)) / np.mean(recent_b) if np.mean(recent_b) > 0 else 0
            
            # If correlation is positive and trends diverge, there's an opportunity
            if correlation > 0 and trend_a * trend_b < 0:
                # Positive correlation but diverging trends
                # Buy the one that's going down, sell the one that's going up
                
                if trend_a < 0 and trend_b > 0:
                    # Market A is going down, Market B is going up
                    # Buy Market A (it should catch up)
                    signal = self._create_signal(
                        market=market_a,
                        outcome="Yes",
                        outcome_index=0,
                        entry_price=current_price_a,
                        current_price=current_price_a,
                        correlation=correlation,
                        position_size=min(
                            settings.MAX_POSITION_SIZE,
                            market_a.get("liquidity", 1000) * 0.1
                        ),
                        target_price=current_price_a * (1 + abs(trend_a)),
                        stop_loss=current_price_a * (1 - abs(trend_a) * 0.5)
                    )
                    signals.append(signal)
                
                elif trend_a > 0 and trend_b < 0:
                    # Market A is going up, Market B is going down
                    # Buy Market B (it should catch up)
                    signal = self._create_signal(
                        market=market_b,
                        outcome="Yes",
                        outcome_index=0,
                        entry_price=current_price_b,
                        current_price=current_price_b,
                        correlation=correlation,
                        position_size=min(
                            settings.MAX_POSITION_SIZE,
                            market_b.get("liquidity", 1000) * 0.1
                        ),
                        target_price=current_price_b * (1 + abs(trend_b)),
                        stop_loss=current_price_b * (1 - abs(trend_b) * 0.5)
                    )
                    signals.append(signal)
            
            # If correlation is negative and trends converge, there's an opportunity
            elif correlation < 0 and trend_a * trend_b > 0:
                # Negative correlation but converging trends
                # This might indicate a mean reversion opportunity
                pass
        
        return signals
    
    async def find_correlated_groups(
        self,
        markets: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find groups of highly correlated markets
        
        Args:
            markets: List of market dictionaries
            
        Returns:
            Dictionary of correlation groups
        """
        # Get price history for all markets
        price_histories = {}
        for market in markets:
            price_history = await self._get_price_history(
                market["slug"],
                limit=self.lookback_period
            )
            if price_history:
                price_histories[market["id"]] = {
                    "market": market,
                    "prices": price_history
                }
        
        # Build correlation matrix
        market_ids = list(price_histories.keys())
        correlation_matrix = np.zeros((len(market_ids), len(market_ids)))
        
        for i, id_a in enumerate(market_ids):
            for j, id_b in enumerate(market_ids):
                if i < j:
                    prices_a = price_histories[id_a]["prices"]
                    prices_b = price_histories[id_b]["prices"]
                    
                    if len(prices_a) >= 5 and len(prices_b) >= 5:
                        correlation, _ = pearsonr(prices_a, prices_b)
                        correlation_matrix[i, j] = correlation
                        correlation_matrix[j, i] = correlation
        
        # Cluster markets based on correlation
        # Simple clustering: group markets with correlation > min_correlation
        groups = {}
        visited = set()
        
        for i, id_a in enumerate(market_ids):
            if id_a in visited:
                continue
            
            # Start a new group
            group_id = f"group_{len(groups) + 1}"
            groups[group_id] = [price_histories[id_a]]
            visited.add(id_a)
            
            # Find all markets correlated with this one
            for j, id_b in enumerate(market_ids):
                if i != j and id_b not in visited:
                    if correlation_matrix[i, j] >= self.min_correlation:
                        groups[group_id].append(price_histories[id_b])
                        visited.add(id_b)
        
        return groups
