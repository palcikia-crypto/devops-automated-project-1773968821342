"""
Liquidity Strategy for Polymarket Crypto Lab
Finds opportunities in low-liquidity markets
"""
from typing import List, Dict, Optional, Any, Tuple
import logging

from config import settings
from ...models.schemas import Signal, SignalType
from .base import BaseStrategy
from ...utils.logger import get_logger

logger = get_logger(__name__)


class LiquidityStrategy(BaseStrategy):
    """
    Strategy that identifies opportunities in low-liquidity markets
    
    In low-liquidity markets:
    1. Small orders can have a large impact on prices
    2. There may be opportunities to "pump and dump"
    3. Spreads are often wider, creating arbitrage opportunities
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.LIQUIDITY
    
    @property
    def name(self) -> str:
        return "Low Liquidity Opportunities"
    
    @property
    def description(self) -> str:
        return "Finds markets with low liquidity where small orders can have a large impact"
    
    def __init__(
        self,
        polymarket_client: Optional[Any] = None,
        max_liquidity: float = 10000.0,  # Maximum liquidity threshold
        min_spread: float = 0.05,  # Minimum spread of 5%
        **kwargs
    ):
        """Initialize the strategy"""
        super().__init__(polymarket_client, **kwargs)
        self.max_liquidity = max_liquidity
        self.min_spread = min_spread
    
    async def generate_signals(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[Signal]:
        """
        Generate liquidity signals
        
        Args:
            markets: List of market dictionaries
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        # Filter markets with low liquidity
        low_liquidity_markets = [
            m for m in markets 
            if m.get("liquidity", 0) <= self.max_liquidity
        ]
        
        logger.info(f"💧 Found {len(low_liquidity_markets)} low-liquidity markets")
        
        for market in low_liquidity_markets:
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
        Analyze a single low-liquidity market
        
        Args:
            market: Market dictionary
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        liquidity = market.get("liquidity", 0)
        volume_24hr = market.get("volume24hr", 0)
        clob_token_ids = market.get("clobTokenIds", [])
        
        if not clob_token_ids:
            return signals
        
        # Check order book for each outcome
        for i, token_id in enumerate(clob_token_ids):
            try:
                # Get order book
                order_book = await self.polymarket.get_order_book(token_id)
                if not order_book:
                    continue
                
                # Calculate spread
                bids = order_book.get("bids", [])
                asks = order_book.get("asks", [])
                
                if not bids or not asks:
                    continue
                
                best_bid = bids[0].get("price", 0)
                best_ask = asks[0].get("price", 0)
                spread = best_ask - best_bid
                spread_pct = (spread / best_bid) * 100 if best_bid > 0 else 0
                
                # Check for wide spread
                if spread_pct >= self.min_spread:
                    # Wide spread opportunity
                    # Buy at bid, sell at ask
                    mid_price = (best_bid + best_ask) / 2
                    
                    signal = self._create_signal(
                        market=market,
                        outcome=market.get("outcomes", [])[i] if i < len(market.get("outcomes", [])) else "Yes",
                        outcome_index=i,
                        entry_price=mid_price,
                        current_price=mid_price,
                        position_size=min(
                            settings.MAX_POSITION_SIZE,
                            liquidity * 0.05  # Small position relative to liquidity
                        ),
                        target_price=best_ask,  # Target is the ask price
                        stop_loss=best_bid  # Stop loss at bid price
                    )
                    signals.append(signal)
                    
                    logger.info(
                        f"💧 Low liquidity opportunity: {market['title']} | "
                        f"Outcome: {signal.outcome} | Spread: {spread_pct:.2f}% | "
                        f"Liquidity: ${liquidity:,.2f}"
                    )
                
                # Check for thin order book (few orders)
                if len(bids) < 3 or len(asks) < 3:
                    # Thin order book - can potentially manipulate price
                    signal = self._create_signal(
                        market=market,
                        outcome=market.get("outcomes", [])[i] if i < len(market.get("outcomes", [])) else "Yes",
                        outcome_index=i,
                        entry_price=mid_price,
                        current_price=mid_price,
                        position_size=min(
                            settings.MAX_POSITION_SIZE,
                            liquidity * 0.1
                        ),
                        target_price=best_ask * 1.05,  # Target 5% above ask
                        stop_loss=best_bid * 0.95  # Stop loss 5% below bid
                    )
                    signals.append(signal)
                    
                    logger.info(
                        f"📉 Thin order book: {market['title']} | "
                        f"Outcome: {signal.outcome} | Bids: {len(bids)} | Asks: {len(asks)}"
                    )
                
            except Exception as e:
                logger.error(f"❌ Error analyzing order book for {market['title']}: {e}")
        
        return signals
    
    async def find_illiquid_markets(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find all illiquid markets
        
        Args:
            markets: List of market dictionaries
            
        Returns:
            List of illiquid market dictionaries
        """
        return [
            m for m in markets 
            if m.get("liquidity", 0) <= self.max_liquidity
        ]
    
    async def find_wide_spread_markets(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find markets with wide spreads
        
        Args:
            markets: List of market dictionaries
            
        Returns:
            List of markets with wide spreads
        """
        wide_spread_markets = []
        
        for market in markets:
            clob_token_ids = market.get("clobTokenIds", [])
            if not clob_token_ids:
                continue
            
            for token_id in clob_token_ids:
                order_book = await self.polymarket.get_order_book(token_id)
                if not order_book:
                    continue
                
                bids = order_book.get("bids", [])
                asks = order_book.get("asks", [])
                
                if bids and asks:
                    best_bid = bids[0].get("price", 0)
                    best_ask = asks[0].get("price", 0)
                    spread_pct = ((best_ask - best_bid) / best_bid) * 100 if best_bid > 0 else 0
                    
                    if spread_pct >= self.min_spread:
                        market["spread_pct"] = spread_pct
                        market["token_id"] = token_id
                        wide_spread_markets.append(market)
                        break
        
        return wide_spread_markets
