"""
Signal Generator for Polymarket Crypto Lab
Generates trading signals based on various strategies
"""
import asyncio
import logging
import numpy as np
from typing import List, Dict, Optional, Any, Callable, Type
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from config import settings
from ..data.polymarket import PolymarketClient
from ..data.database import Database
from ..models.schemas import Signal, SignalType, SignalStatus
from ..utils.logger import get_logger
from ..utils.helpers import generate_id
from .strategies import (
    UndervaluedStrategy,
    ArbitrageStrategy,
    TrendingStrategy,
    CorrelationStrategy,
    LiquidityStrategy,
    SentimentStrategy,
    SeasonalityStrategy,
    MeanReversionStrategy,
    BreakoutStrategy,
    VolumeSpikeStrategy,
)

logger = get_logger(__name__)


@dataclass
class StrategyConfig:
    """Configuration for a strategy"""
    name: str
    strategy_class: Type
    enabled: bool = True
    weight: float = 1.0
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class SignalGenerator:
    """
    Generates trading signals using multiple strategies
    """
    
    # Available strategies
    STRATEGIES = {
        SignalType.UNDERVALUED: StrategyConfig(
            name="Undervalued",
            strategy_class=UndervaluedStrategy,
            enabled=True,
            weight=1.0,
            parameters={}
        ),
        SignalType.ARBITRAGE: StrategyConfig(
            name="Arbitrage",
            strategy_class=ArbitrageStrategy,
            enabled=True,
            weight=1.5,  # Higher weight for arbitrage
            parameters={}
        ),
        SignalType.TRENDING: StrategyConfig(
            name="Trending",
            strategy_class=TrendingStrategy,
            enabled=True,
            weight=1.0,
            parameters={"min_growth": 0.05}
        ),
        SignalType.CORRELATION: StrategyConfig(
            name="Correlation",
            strategy_class=CorrelationStrategy,
            enabled=True,
            weight=0.8,
            parameters={"min_correlation": 0.8}
        ),
        SignalType.LIQUIDITY: StrategyConfig(
            name="Liquidity",
            strategy_class=LiquidityStrategy,
            enabled=True,
            weight=0.5,
            parameters={"max_liquidity": 10000}
        ),
        SignalType.SENTIMENT: StrategyConfig(
            name="Sentiment",
            strategy_class=SentimentStrategy,
            enabled=False,  # Disabled by default (requires external APIs)
            weight=0.7,
            parameters={}
        ),
        SignalType.SEASONALITY: StrategyConfig(
            name="Seasonality",
            strategy_class=SeasonalityStrategy,
            enabled=True,
            weight=0.6,
            parameters={}
        ),
        SignalType.MEAN_REVERSION: StrategyConfig(
            name="Mean Reversion",
            strategy_class=MeanReversionStrategy,
            enabled=True,
            weight=0.9,
            parameters={"threshold": 0.2}
        ),
        SignalType.BREAKOUT: StrategyConfig(
            name="Breakout",
            strategy_class=BreakoutStrategy,
            enabled=True,
            weight=0.8,
            parameters={}
        ),
        SignalType.VOLUME_SPIKE: StrategyConfig(
            name="Volume Spike",
            strategy_class=VolumeSpikeStrategy,
            enabled=True,
            weight=0.7,
            parameters={"min_ratio": 2.0}
        ),
    }
    
    def __init__(
        self,
        polymarket_client: Optional[PolymarketClient] = None,
        signal_generation_interval: int = 900,  # 15 minutes
        callbacks: Optional[List[Callable[[List[Signal]], None]]] = None
    ):
        """Initialize the signal generator"""
        self.polymarket = polymarket_client or PolymarketClient()
        self.database = Database()
        self.signal_generation_interval = signal_generation_interval
        self.callbacks = callbacks or []
        self.is_running = False
        self.historical_data: Dict[str, List[float]] = {}
    
    def add_callback(self, callback: Callable[[List[Signal]], None]):
        """Add a callback to be called when new signals are generated"""
        self.callbacks.append(callback)
    
    async def generate_signals(self, markets: List[Dict[str, Any]]) -> List[Signal]:
        """
        Generate signals for a list of markets
        
        Args:
            markets: List of market dictionaries
            
        Returns:
            List of Signal objects
        """
        if not markets:
            logger.warning("⚠️ No markets provided for signal generation")
            return []
        
        logger.info(f"🎯 Generating signals for {len(markets)} markets...")
        
        all_signals = []
        
        # Initialize strategies
        strategies = {}
        for signal_type, config in self.STRATEGIES.items():
            if config.enabled:
                try:
                    strategy = config.strategy_class(
                        polymarket_client=self.polymarket,
                        **config.parameters
                    )
                    strategies[signal_type] = strategy
                    logger.debug(f"✅ Initialized strategy: {config.name}")
                except Exception as e:
                    logger.error(f"❌ Error initializing strategy {config.name}: {e}")
        
        # Generate signals using each strategy
        for signal_type, strategy in strategies.items():
            try:
                signals = await strategy.generate_signals(markets)
                if signals:
                    logger.info(f"📊 {config.name} generated {len(signals)} signals")
                    all_signals.extend(signals)
            except Exception as e:
                logger.error(f"❌ Error in {config.name} strategy: {e}")
        
        # Sort signals by potential (edge, arbitrage, etc.)
        all_signals.sort(key=lambda s: abs(getattr(s, "edge", 0) or 
                                            getattr(s, "arbitrage", 0) or 
                                            getattr(s, "growth", 0) or 0), 
                         reverse=True)
        
        logger.info(f"✅ Generated {len(all_signals)} signals total")
        
        # Save signals to database
        signal_dicts = [signal.model_dump() for signal in all_signals]
        await self.database.save_signals(signal_dicts)
        
        # Call callbacks
        for callback in self.callbacks:
            try:
                callback(all_signals)
            except Exception as e:
                logger.error(f"Error in signal callback: {e}")
        
        return all_signals
    
    async def generate_signals_for_market(self, market: Dict[str, Any]) -> List[Signal]:
        """
        Generate signals for a specific market
        
        Args:
            market: Market dictionary
            
        Returns:
            List of Signal objects
        """
        return await self.generate_signals([market])
    
    async def update_signals(self, signals: List[Signal]):
        """
        Update existing signals with current market data
        
        Args:
            signals: List of Signal objects to update
        """
        if not signals:
            return
        
        for signal in signals:
            try:
                # Get current market data
                market = await self.polymarket.get_market_by_slug(signal.market_slug)
                if not market:
                    continue
                
                # Update signal with current price
                clob_token_ids = market.get("clobTokenIds", [])
                if clob_token_ids and signal.outcome_index < len(clob_token_ids):
                    token_id = clob_token_ids[signal.outcome_index]
                    current_price = await self.polymarket.get_midprice(token_id)
                    if current_price is not None:
                        signal.current_price = current_price
                        signal.updated_at = datetime.utcnow()
                        
                        # Update in database
                        await self.database.update_signal(
                            signal.id,
                            {
                                "current_price": current_price,
                                "updated_at": signal.updated_at
                            }
                        )
                
                # Check if signal should be closed
                if signal.status == SignalStatus.PENDING:
                    # Check for stop loss or take profit
                    if signal.stop_loss and signal.current_price <= signal.stop_loss:
                        pnl = signal.position_size * (signal.stop_loss - signal.entry_price)
                        pnl_pct = (pnl / signal.position_size) * 100
                        await self.database.close_signal(signal.id, pnl, pnl_pct)
                        signal.status = SignalStatus.CLOSED
                        signal.pnl = pnl
                        signal.pnl_pct = pnl_pct
                        signal.closed_at = datetime.utcnow()
                    
                    elif signal.take_profit and signal.current_price >= signal.take_profit:
                        pnl = signal.position_size * (signal.take_profit - signal.entry_price)
                        pnl_pct = (pnl / signal.position_size) * 100
                        await self.database.close_signal(signal.id, pnl, pnl_pct)
                        signal.status = SignalStatus.CLOSED
                        signal.pnl = pnl
                        signal.pnl_pct = pnl_pct
                        signal.closed_at = datetime.utcnow()
            
            except Exception as e:
                logger.error(f"❌ Error updating signal {signal.id}: {e}")
    
    async def close_expired_signals(self):
        """Close signals for markets that have expired"""
        # Get all active signals
        signals = await self.database.get_signals(status="pending")
        
        for signal in signals:
            try:
                market = await self.polymarket.get_market_by_slug(signal.market_slug)
                if market and market.get("endDate"):
                    end_date = datetime.fromisoformat(market["endDate"].replace("Z", "+00:00"))
                    if datetime.utcnow() > end_date:
                        # Market has expired, close the signal
                        pnl = signal.position_size * (signal.current_price - signal.entry_price)
                        pnl_pct = (pnl / signal.position_size) * 100
                        await self.database.close_signal(signal.id, pnl, pnl_pct)
            except Exception as e:
                logger.error(f"❌ Error closing expired signal {signal.id}: {e}")
    
    async def continuous_signal_generation(self):
        """
        Continuously generate signals at the specified interval
        """
        self.is_running = True
        logger.info(f"🚀 Starting continuous signal generation (every {self.signal_generation_interval} seconds)")
        
        while self.is_running:
            start_time = datetime.utcnow()
            
            try:
                # Get markets
                markets = await self.polymarket.get_crypto_markets(limit=100)
                
                # Generate signals
                signals = await self.generate_signals(markets)
                
                # Update existing signals
                existing_signals = await self.database.get_signals(status="pending")
                await self.update_signals(existing_signals)
                
                # Close expired signals
                await self.close_expired_signals()
                
                logger.info(f"📊 Generated {len(signals)} new signals")
                
            except Exception as e:
                logger.error(f"❌ Error in continuous signal generation: {e}")
            
            # Calculate sleep time
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            sleep_time = max(0, self.signal_generation_interval - elapsed)
            await asyncio.sleep(sleep_time)
        
        logger.info("⏹️ Stopped continuous signal generation")
    
    def stop(self):
        """Stop the continuous signal generation"""
        self.is_running = False
    
    async def get_top_signals(self, limit: int = 10) -> List[Signal]:
        """
        Get top signals by potential
        
        Args:
            limit: Maximum number of signals to return
            
        Returns:
            List of top Signal objects
        """
        signals = await self.database.get_signals(status="pending", limit=limit * 2)
        
        # Sort by potential
        signals.sort(
            key=lambda s: abs(getattr(s, "edge", 0) or 
                               getattr(s, "arbitrage", 0) or 
                               getattr(s, "growth", 0) or 0),
            reverse=True
        )
        
        return signals[:limit]
    
    async def get_signals_by_type(self, signal_type: SignalType, limit: int = 10) -> List[Signal]:
        """
        Get signals by type
        
        Args:
            signal_type: Type of signals to filter by
            limit: Maximum number of signals to return
            
        Returns:
            List of Signal objects
        """
        signals = await self.database.get_signals(type=signal_type.value, limit=limit)
        return signals
    
    async def get_signal_stats(self) -> Dict[str, Any]:
        """
        Get statistics about generated signals
        
        Returns:
            Dictionary with signal statistics
        """
        signals = await self.database.get_signals(limit=1000)
        
        if not signals:
            return {"total": 0}
        
        stats = {
            "total": len(signals),
            "active": len([s for s in signals if s.status == SignalStatus.PENDING]),
            "closed": len([s for s in signals if s.status == SignalStatus.CLOSED]),
            "by_type": {},
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "avg_pnl": 0.0
        }
        
        # Group by type
        for signal in signals:
            signal_type = signal.type.value
            if signal_type not in stats["by_type"]:
                stats["by_type"][signal_type] = {"count": 0, "pnl": 0.0}
            stats["by_type"][signal_type]["count"] += 1
            
            if signal.pnl:
                stats["by_type"][signal_type]["pnl"] += signal.pnl
                stats["total_pnl"] += signal.pnl
        
        # Calculate win rate
        closed_signals = [s for s in signals if s.status == SignalStatus.CLOSED and s.pnl is not None]
        if closed_signals:
            winning_signals = [s for s in closed_signals if s.pnl > 0]
            stats["win_rate"] = (len(winning_signals) / len(closed_signals)) * 100
            stats["avg_pnl"] = stats["total_pnl"] / len(closed_signals)
        
        return stats


# Create a global signal generator instance
signal_generator = SignalGenerator()
