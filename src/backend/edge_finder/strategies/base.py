"""
Base Strategy Class for Polymarket Crypto Lab
All strategies inherit from this base class
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import logging

from config import settings
from ...data.polymarket import PolymarketClient
from ...models.schemas import Signal, SignalType
from ...utils.logger import get_logger
from ...utils.helpers import generate_id

logger = get_logger(__name__)


class BaseStrategy(ABC):
    """
    Base class for all trading strategies
    """
    
    def __init__(
        self,
        polymarket_client: Optional[PolymarketClient] = None,
        **kwargs
    ):
        """Initialize the strategy"""
        self.polymarket = polymarket_client or PolymarketClient()
        self.kwargs = kwargs
        self.historical_data: Dict[str, List[float]] = {}
    
    @property
    @abstractmethod
    def signal_type(self) -> SignalType:
        """Return the signal type for this strategy"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the strategy"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of the strategy"""
        pass
    
    @abstractmethod
    async def generate_signals(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[Signal]:
        """
        Generate signals for a list of markets
        
        Args:
            markets: List of market dictionaries
            
        Returns:
            List of Signal objects
        """
        pass
    
    def _create_signal(
        self,
        market: Dict[str, Any],
        outcome: str = "Yes",
        outcome_index: int = 0,
        entry_price: float = 0.5,
        current_price: float = 0.5,
        position_size: float = 100.0,
        risk_per_trade: float = 0.01,
        **kwargs
    ) -> Signal:
        """
        Create a Signal object with common parameters
        
        Args:
            market: Market dictionary
            outcome: Outcome (Yes/No)
            outcome_index: Outcome index
            entry_price: Entry price (0-1)
            current_price: Current price (0-1)
            position_size: Position size in pUSD
            risk_per_trade: Risk per trade
            **kwargs: Additional signal-specific parameters
            
        Returns:
            Signal object
        """
        signal_data = {
            "id": generate_id(),
            "type": self.signal_type,
            "market_id": market["id"],
            "market_title": market["title"],
            "market_slug": market["slug"],
            "outcome": outcome,
            "outcome_index": outcome_index,
            "entry_price": entry_price,
            "current_price": current_price,
            "position_size": position_size,
            "risk_per_trade": risk_per_trade,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Add strategy-specific parameters
        signal_data.update(kwargs)
        
        return Signal(**signal_data)
    
    async def _get_price_history(
        self,
        market_slug: str,
        limit: int = 100
    ) -> List[float]:
        """
        Get price history for a market
        
        Args:
            market_slug: Market slug
            limit: Number of historical prices
            
        Returns:
            List of historical prices
        """
        market = await self.polymarket.get_market_by_slug(market_slug)
        if not market:
            return []
        
        clob_token_ids = market.get("clobTokenIds", [])
        if not clob_token_ids:
            return []
        
        # Get price for the first outcome (usually "Yes")
        token_id = clob_token_ids[0]
        price_history = await self.polymarket.get_price_history(token_id, limit=limit)
        
        return [p["price"] for p in price_history if "price" in p]
    
    def _calculate_edge(
        self,
        my_prediction: float,
        market_price: float
    ) -> float:
        """
        Calculate the edge between a prediction and market price
        
        Args:
            my_prediction: Your predicted probability (0-1)
            market_price: Market probability (0-1)
            
        Returns:
            Edge (difference between prediction and market)
        """
        return my_prediction - market_price
    
    def _is_mutually_exclusive(
        self,
        market_a: Dict[str, Any],
        market_b: Dict[str, Any]
    ) -> bool:
        """
        Check if two markets are mutually exclusive
        
        Args:
            market_a: First market
            market_b: Second market
            
        Returns:
            True if markets are mutually exclusive
        """
        title_a = market_a.get("title", "").lower()
        title_b = market_b.get("title", "").lower()
        
        # Check for opposite conditions
        if "btc" in title_a and "btc" in title_b:
            if (">" in title_a and "<=" in title_b) or ("<" in title_a and ">=" in title_b):
                return True
            if ("up" in title_a and "down" in title_b) or ("down" in title_a and "up" in title_b):
                return True
        
        # Check for same event with different outcomes
        if market_a.get("conditionId") == market_b.get("conditionId"):
            return True
        
        return False
    
    def _filter_markets(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter markets based on common criteria
        
        Args:
            markets: List of market dictionaries
            
        Returns:
            Filtered list of markets
        """
        filtered = []
        for market in markets:
            # Skip markets not accepting orders
            if not market.get("acceptingOrders", True):
                continue
            
            # Skip markets with low liquidity
            liquidity = market.get("liquidity", 0)
            if liquidity < settings.MIN_LIQUIDITY:
                continue
            
            # Skip markets with low volume
            volume_24hr = market.get("volume24hr", 0)
            if volume_24hr < settings.MIN_VOLUME_24HR:
                continue
            
            filtered.append(market)
        
        return filtered
