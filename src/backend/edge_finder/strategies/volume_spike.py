"""
Volume Spike Strategy for Polymarket Crypto Lab
Identifies markets with unusual volume spikes
"""
from typing import List, Dict, Optional, Any, Tuple
import logging
import numpy as np

from config import settings
from ...models.schemas import Signal, SignalType
from .base import BaseStrategy
from ...utils.logger import get_logger

logger = get_logger(__name__)


class VolumeSpikeStrategy(BaseStrategy):
    """
    Strategy that identifies volume spikes
    
    A volume spike can indicate:
    1. Increased interest in a market
    2. News or events affecting the market
    3. Potential price movements
    
    Looks for:
    1. Volume significantly higher than average
    2. Sudden increases in trading activity
    3. Volume spikes with price movements
    """
    
    @property
    def signal_type(self) -> SignalType:
        return SignalType.VOLUME_SPIKE
    
    @property
    def name(self) -> str:
        return "Volume Spike"
    
    @property
    def description(self) -> str:
        return "Identifies markets with unusual volume spikes that may indicate future price movements"
    
    def __init__(
        self,
        polymarket_client: Optional[Any] = None,
        min_ratio: float = 2.0,  # Minimum 2x volume increase
        lookback_period: int = 10,
        **kwargs
    ):
        """Initialize the strategy"""
        super().__init__(polymarket_client, **kwargs)
        self.min_ratio = min_ratio
        self.lookback_period = lookback_period
    
    async def generate_signals(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[Signal]:
        """
        Generate volume spike signals
        
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
        Analyze a single market for volume spikes
        
        Args:
            market: Market dictionary
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        volume_24hr = market.get("volume24hr", 0)
        volume_1wk = market.get("volume1wk", 0)
        volume_1mo = market.get("volume1mo", 0)
        current_price = market.get("outcomePrices", [0.5])[0]
        outcomes = market.get("outcomes", [])
        
        # Calculate volume ratios
        ratio_24hr_1wk = (volume_24hr / (volume_1wk / 7)) if volume_1wk > 0 else 0
        ratio_24hr_1mo = (volume_24hr / (volume_1mo / 30)) if volume_1mo > 0 else 0
        
        # Check for 24-hour volume spike
        if ratio_24hr_1wk >= self.min_ratio:
            # Volume is at least 2x the weekly average
            for i, outcome in enumerate(outcomes):
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
                    target_price=min(0.99, current_price * 1.1),  # 10% target
                    stop_loss=max(0.01, current_price * 0.95)  # 5% stop loss
                )
                signal.volume_ratio = ratio_24hr_1wk
                signals.append(signal)
                
                logger.info(
                    f"📈 Volume spike (24h): {market['title']} | "
                    f"Volume: ${volume_24hr:,.2f} | Ratio: {ratio_24hr_1wk:.2f}x"
                )
        
        # Check for 24-hour volume spike compared to monthly average
        elif ratio_24hr_1mo >= self.min_ratio * 1.5:  # Higher threshold for monthly
            for i, outcome in enumerate(outcomes):
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
                    target_price=min(0.99, current_price * 1.15),  # 15% target
                    stop_loss=max(0.01, current_price * 0.9)  # 10% stop loss
                )
                signal.volume_ratio = ratio_24hr_1mo
                signals.append(signal)
                
                logger.info(
                    f"📈 Volume spike (24h vs 1mo): {market['title']} | "
                    f"Volume: ${volume_24hr:,.2f} | Ratio: {ratio_24hr_1mo:.2f}x"
                )
        
        return signals
    
    async def find_volume_spikes(
        self,
        markets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find all markets with volume spikes
        
        Args:
            markets: List of market dictionaries
            
        Returns:
            List of markets with volume spikes
        """
        spiking_markets = []
        
        for market in markets:
            volume_24hr = market.get("volume24hr", 0)
            volume_1wk = market.get("volume1wk", 0)
            
            if volume_1wk > 0:
                ratio = (volume_24hr / (volume_1wk / 7))
                if ratio >= self.min_ratio:
                    market["volume_ratio"] = ratio
                    spiking_markets.append(market)
        
        return spiking_markets
    
    async def analyze_volume_trends(
        self,
        markets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze volume trends across markets
        
        Args:
            markets: List of market dictionaries
            
        Returns:
            Dictionary with volume trend analysis
        """
        analysis = {
            "total_markets": len(markets),
            "spiking_markets": [],
            "declining_markets": [],
            "stable_markets": [],
            "avg_volume_ratio": 0.0
        }
        
        ratios = []
        
        for market in markets:
            volume_24hr = market.get("volume24hr", 0)
            volume_1wk = market.get("volume1wk", 0)
            
            if volume_1wk > 0:
                ratio = (volume_24hr / (volume_1wk / 7))
                ratios.append(ratio)
                
                if ratio >= self.min_ratio:
                    analysis["spiking_markets"].append(market)
                elif ratio <= 0.5:
                    analysis["declining_markets"].append(market)
                else:
                    analysis["stable_markets"].append(market)
        
        if ratios:
            analysis["avg_volume_ratio"] = np.mean(ratios)
        
        return analysis
