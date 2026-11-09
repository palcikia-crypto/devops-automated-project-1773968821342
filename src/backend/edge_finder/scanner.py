"""
Market Scanner for Polymarket Crypto Lab
Scans Polymarket for crypto markets and collects data
"""
import asyncio
import logging
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
import time

from config import settings
from ..data.polymarket import PolymarketClient
from ..data.database import Database
from ..data.cache import Cache
from ..models.schemas import Market
from ..utils.logger import get_logger
from ..utils.helpers import generate_id

logger = get_logger(__name__)


class MarketScanner:
    """
    Scans Polymarket for crypto markets and collects relevant data
    """
    
    def __init__(
        self,
        polymarket_client: Optional[PolymarketClient] = None,
        scan_interval: int = 300,  # 5 minutes
        crypto_tag_id: int = 21
    ):
        """Initialize the market scanner"""
        self.polymarket = polymarket_client or PolymarketClient()
        self.database = Database()
        self.cache = Cache()
        self.scan_interval = scan_interval
        self.crypto_tag_id = crypto_tag_id
        self.is_running = False
        self.callbacks: List[Callable[[List[Dict[str, Any]]], None]] = []
    
    def add_callback(self, callback: Callable[[List[Dict[str, Any]]], None]):
        """Add a callback to be called when new market data is available"""
        self.callbacks.append(callback)
    
    async def scan_markets(self) -> List[Dict[str, Any]]:
        """
        Scan for crypto markets and return the data
        
        Returns:
            List of market dictionaries
        """
        logger.info("🔍 Scanning for crypto markets...")
        
        try:
            # Get markets from Gamma API
            markets = await self.polymarket.get_crypto_markets(limit=200)
            
            if not markets:
                logger.warning("⚠️ No markets found")
                return []
            
            logger.info(f"✅ Found {len(markets)} crypto markets")
            
            # Filter and enrich market data
            filtered_markets = []
            for market in markets:
                # Skip markets that are not accepting orders
                if not market.get("acceptingOrders", True):
                    continue
                
                # Skip markets with low liquidity (configurable)
                liquidity = market.get("liquidity", 0)
                if liquidity < settings.MIN_LIQUIDITY:
                    logger.debug(f"Skipping market {market['title']} - low liquidity: ${liquidity:,.2f}")
                    continue
                
                # Skip markets with low volume
                volume_24hr = market.get("volume24hr", 0)
                if volume_24hr < settings.MIN_VOLUME_24HR:
                    logger.debug(f"Skipping market {market['title']} - low volume: ${volume_24hr:,.2f}")
                    continue
                
                # Add metadata
                market["scanned_at"] = datetime.utcnow().isoformat()
                market["source"] = "polymarket"
                
                filtered_markets.append(market)
            
            logger.info(f"✅ Filtered to {len(filtered_markets)} high-quality markets")
            
            # Save to database
            await self.database.save_markets(filtered_markets)
            
            # Cache markets
            await self.cache.set_markets(f"markets:all", filtered_markets, ttl=300)
            
            # Call callbacks
            for callback in self.callbacks:
                try:
                    callback(filtered_markets)
                except Exception as e:
                    logger.error(f"Error in callback: {e}")
            
            return filtered_markets
            
        except Exception as e:
            logger.error(f"❌ Error scanning markets: {e}")
            return []
    
    async def scan_market_details(self, market_slug: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific market
        
        Args:
            market_slug: Market slug
            
        Returns:
            Market dictionary with order book and price data
        """
        try:
            # Get market from Gamma API
            market = await self.polymarket.get_market_by_slug(market_slug)
            if not market:
                return None
            
            # Get order book for each outcome
            clob_token_ids = market.get("clobTokenIds", [])
            if clob_token_ids:
                order_books = []
                prices = {}
                
                for token_id in clob_token_ids:
                    # Get order book
                    order_book = await self.polymarket.get_order_book(token_id)
                    if order_book:
                        order_books.append(order_book)
                    
                    # Get price
                    price = await self.polymarket.get_midprice(token_id)
                    if price is not None:
                        prices[token_id] = price
                
                market["order_books"] = order_books
                market["prices"] = prices
            
            return market
            
        except Exception as e:
            logger.error(f"❌ Error scanning market details for {market_slug}: {e}")
            return None
    
    async def scan_all_market_details(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get detailed information for all crypto markets
        
        Args:
            limit: Maximum number of markets to scan
            
        Returns:
            List of market dictionaries with details
        """
        # Get markets first
        markets = await self.scan_markets()
        
        detailed_markets = []
        for market in markets[:limit]:
            # Add small delay to avoid rate limiting
            await asyncio.sleep(0.1)
            
            detailed_market = await self.scan_market_details(market["slug"])
            if detailed_market:
                detailed_markets.append(detailed_market)
        
        return detailed_markets
    
    async def scan_order_books(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Scan order books for top markets
        
        Args:
            limit: Number of markets to scan
            
        Returns:
            List of order book dictionaries
        """
        markets = await self.scan_markets()
        
        order_books = []
        for market in markets[:limit]:
            clob_token_ids = market.get("clobTokenIds", [])
            if clob_token_ids:
                for token_id in clob_token_ids:
                    order_book = await self.polymarket.get_order_book(token_id)
                    if order_book:
                        order_book["market_id"] = market["id"]
                        order_book["market_title"] = market["title"]
                        order_books.append(order_book)
        
        return order_books
    
    async def continuous_scan(self):
        """
        Continuously scan markets at the specified interval
        """
        self.is_running = True
        logger.info(f"🚀 Starting continuous market scanning (every {self.scan_interval} seconds)")
        
        while self.is_running:
            start_time = time.time()
            
            try:
                markets = await self.scan_markets()
                logger.info(f"📊 Scanned {len(markets)} markets")
            except Exception as e:
                logger.error(f"❌ Error in continuous scan: {e}")
            
            # Calculate sleep time to maintain interval
            elapsed = time.time() - start_time
            sleep_time = max(0, self.scan_interval - elapsed)
            await asyncio.sleep(sleep_time)
        
        logger.info("⏹️ Stopped continuous market scanning")
    
    def stop(self):
        """Stop the continuous scanning"""
        self.is_running = False
    
    async def get_historical_data(
        self,
        market_slug: str,
        hours: int = 24,
        interval: int = 15
    ) -> Dict[str, Any]:
        """
        Get historical data for a market
        
        Args:
            market_slug: Market slug
            hours: Number of hours to look back
            interval: Interval in minutes between data points
            
        Returns:
            Dictionary with historical data
        """
        market = await self.polymarket.get_market_by_slug(market_slug)
        if not market:
            return {}
        
        clob_token_ids = market.get("clobTokenIds", [])
        if not clob_token_ids:
            return {}
        
        historical_data = {
            "market": market,
            "prices": {},
            "volumes": {},
            "liquidity": []
        }
        
        # Get price history for each token
        for token_id in clob_token_ids:
            price_history = await self.polymarket.get_price_history(
                token_id,
                limit=(hours * 60) // interval
            )
            historical_data["prices"][token_id] = price_history
        
        return historical_data


# Create a global scanner instance
scanner = MarketScanner()
