"""
Seasonality Strategy for Polymarket Crypto Lab
Identifies seasonal patterns in crypto markets
"""
from typing import List, Dict, Optional, Any, Tuple
import logging
from datetime import datetime, timedelta
import numpy as np

from config import settings
from ...models.schemas import Signal, SignalType
from .base import BaseStrategy
from ...utils.logger import get_logger

logger = get_logger(__name__)


class SeasonalityStrategy(BaseStrategy):
    """
    Strategy that identifies seasonal patterns in crypto markets
    
    Looks for:
    1. Monthly patterns (e.g., Bitcoin tends to rise in certain months)
    2. Weekly patterns (e.g., weekends vs weekdays)
    3. Daily patterns (e.g., specific times of day)
    4. Event-based patterns (e.g., before/after halving, ETF approvals)
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.SEASONALITY
    
    @property
    def name(self) -> str:
        return "Seasonal Patterns"
    
    @property
    def description(self) -> str:
        return "Identifies seasonal patterns and cycles in crypto markets"
    
    def __init__(
        self,
        polymarket_client: Optional[Any] = None,
        **kwargs
    ):
        """Initialize the strategy"""
        super().__init__(polymarket_client, **kwargs)
        
        # Known seasonal patterns for crypto
        self.seasonal_patterns = {
            "bitcoin": {
                "monthly": {
                    1: 0.6,   # January: +6%
                    4: 0.5,   # April: +5%
                    10: 0.7,  # October: +7%
                    11: 0.65, # November: +6.5%
                    12: 0.6,  # December: +6%
                },
                "halving_cycle": {
                    "pre_halving": 0.7,   # 3-6 months before halving
                    "post_halving": 0.65, # 6-12 months after halving
                }
            },
            "ethereum": {
                "monthly": {
                    1: 0.55,
                    5: 0.5,
                    10: 0.6,
                    11: 0.55,
                }
            },
            "altcoins": {
                "monthly": {
                    1: 0.6,
                    4: 0.55,
                    10: 0.65,
                }
            }
        }
    
    async def generate_signals(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[Signal]:
        """
        Generate seasonality signals
        
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
        Analyze a single market for seasonal patterns
        
        Args:
            market: Market dictionary
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        title = market.get("title", "").lower()
        slug = market.get("slug", "")
        current_price = market.get("outcomePrices", [0.5])[0]
        end_date = market.get("endDate")
        
        # Get current date
        now = datetime.utcnow()
        
        # Check for monthly patterns
        monthly_signals = self._check_monthly_patterns(market, now)
        signals.extend(monthly_signals)
        
        # Check for halving cycle patterns
        halving_signals = await self._check_halving_patterns(market, now)
        signals.extend(halving_signals)
        
        # Check for event-based patterns
        event_signals = await self._check_event_patterns(market, now)
        signals.extend(event_signals)
        
        return signals
    
    def _check_monthly_patterns(
        self,
        market: Dict[str, Any],
        now: datetime
    ) -> List[Signal]:
        """
        Check for monthly seasonal patterns
        
        Args:
            market: Market dictionary
            now: Current datetime
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        title = market.get("title", "").lower()
        current_price = market.get("outcomePrices", [0.5])[0]
        month = now.month
        
        # Determine asset type
        asset_type = self._determine_asset_type(title)
        
        # Get seasonal pattern for this asset
        seasonal_data = self.seasonal_patterns.get(asset_type, {})
        monthly_pattern = seasonal_data.get("monthly", {})
        
        if month not in monthly_pattern:
            return signals
        
        # Get expected performance for this month
        expected_performance = monthly_pattern[month]
        
        # If expected performance is positive, look for "Yes" opportunities
        if expected_performance > 0.5:
            for i, outcome in enumerate(market.get("outcomes", [])):
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
                        target_price=min(0.99, current_price * (1 + (expected_performance - 0.5))),
                        stop_loss=max(0.01, current_price * (1 - (expected_performance - 0.5) * 0.5))
                    )
                    signals.append(signal)
                    
                    logger.info(
                        f"📅 Monthly seasonality: {market['title']} | "
                        f"Month: {month} | Expected: {expected_performance:.0%}"
                    )
        
        return signals
    
    def _determine_asset_type(self, title: str) -> str:
        """
        Determine the asset type from market title
        
        Args:
            title: Market title
            
        Returns:
            Asset type (bitcoin, ethereum, altcoins)
        """
        title_lower = title.lower()
        
        if "bitcoin" in title_lower or "btc" in title_lower:
            return "bitcoin"
        elif "ethereum" in title_lower or "eth" in title_lower:
            return "ethereum"
        else:
            return "altcoins"
    
    async def _check_halving_patterns(
        self,
        market: Dict[str, Any],
        now: datetime
    ) -> List[Signal]:
        """
        Check for halving cycle patterns
        
        Args:
            market: Market dictionary
            now: Current datetime
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        title = market.get("title", "").lower()
        current_price = market.get("outcomePrices", [0.5])[0]
        end_date = market.get("endDate")
        
        # Only check for Bitcoin halving patterns
        if "bitcoin" not in title and "btc" not in title:
            return signals
        
        # Get next Bitcoin halving date (approximately April 2028)
        next_halving = datetime(2028, 4, 1)
        
        # Calculate time until halving
        days_until_halving = (next_halving - now).days
        
        # Pre-halving period (3-6 months before)
        if 90 <= days_until_halving <= 180:
            for i, outcome in enumerate(market.get("outcomes", [])):
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
                        target_price=min(0.99, current_price * 1.15),
                        stop_loss=max(0.01, current_price * 0.9)
                    )
                    signals.append(signal)
                    
                    logger.info(
                        f"⛏️ Pre-halving pattern: {market['title']} | "
                        f"Days until halving: {days_until_halving}"
                    )
        
        # Post-halving period (6-12 months after)
        if -180 <= days_until_halving <= -90:
            for i, outcome in enumerate(market.get("outcomes", [])):
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
                        target_price=min(0.99, current_price * 1.2),
                        stop_loss=max(0.01, current_price * 0.85)
                    )
                    signals.append(signal)
                    
                    logger.info(
                        f"⛏️ Post-halving pattern: {market['title']} | "
                        f"Days since halving: {abs(days_until_halving)}"
                    )
        
        return signals
    
    async def _check_event_patterns(
        self,
        market: Dict[str, Any],
        now: datetime
    ) -> List[Signal]:
        """
        Check for event-based seasonal patterns
        
        Args:
            market: Market dictionary
            now: Current datetime
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        title = market.get("title", "").lower()
        current_price = market.get("outcomePrices", [0.5])[0]
        end_date = market.get("endDate")
        
        # Check for ETF-related patterns
        if "etf" in title:
            # ETF approvals often happen in specific timeframes
            # Look for patterns based on SEC decision timelines
            
            # If market is about ETF approval and end date is within 30 days
            if end_date:
                end_datetime = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                days_until_end = (end_datetime - now).days
                
                if 0 <= days_until_end <= 30:
                    # Increased probability of approval as deadline approaches
                    for i, outcome in enumerate(market.get("outcomes", [])):
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
                                target_price=min(0.99, current_price * 1.1),
                                stop_loss=max(0.01, current_price * 0.95)
                            )
                            signals.append(signal)
                            
                            logger.info(
                                f"📈 ETF deadline approaching: {market['title']} | "
                                f"Days until deadline: {days_until_end}"
                            )
        
        return signals
