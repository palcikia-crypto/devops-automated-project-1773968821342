"""
Paper Trading Engine for Polymarket Crypto Lab
Simulates trading with virtual money
"""
import asyncio
import logging
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from config import settings
from ..data.polymarket import PolymarketClient
from ..data.database import Database
from ..edge_finder.signals import signal_generator
from ..models.schemas import Signal, SignalStatus, TradeSide, TradeStatus, PaperTrade
from ..utils.logger import get_logger
from ..utils.helpers import generate_id

logger = get_logger(__name__)


class PaperTradeStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    CLOSED = "closed"


@dataclass
class PaperPosition:
    """Represents a paper trading position"""
    market_id: str
    market_title: str
    signal_id: Optional[str]
    outcome: str
    outcome_index: int
    side: TradeSide
    amount: float
    entry_price: float
    entry_timestamp: datetime
    current_price: float = 0.0
    
    @property
    def pnl(self) -> float:
        """Calculate current PnL"""
        if self.side == TradeSide.BUY:
            return self.amount * (self.current_price - self.entry_price)
        else:  # SELL
            return self.amount * (self.entry_price - self.current_price)
    
    @property
    def pnl_pct(self) -> float:
        """Calculate current PnL percentage"""
        if self.entry_price == 0:
            return 0.0
        return (self.pnl / (self.amount * self.entry_price)) * 100


class PaperTradingEngine:
    """
    Paper trading engine that simulates trading with virtual money
    """
    
    def __init__(
        self,
        initial_balance: float = 10000.0,
        polymarket_client: Optional[PolymarketClient] = None,
        fee_rate: float = 0.005  # 0.5% fee
    ):
        """Initialize the paper trading engine"""
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.available_balance = initial_balance
        self.fee_rate = fee_rate
        self.polymarket = polymarket_client or PolymarketClient()
        
        # Positions
        self.positions: Dict[str, PaperPosition] = {}
        
        # Trade history
        self.trades: List[PaperTrade] = []
        
        # Callbacks
        self.callbacks: List[Callable[[PaperTrade], None]] = []
        
        # Statistics
        self.stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
            "max_drawdown": 0.0,
            "max_balance": initial_balance
        }
    
    def add_callback(self, callback: Callable[[PaperTrade], None]):
        """Add a callback to be called when a trade is executed"""
        self.callbacks.append(callback)
    
    async def execute_trade(
        self,
        signal: Signal,
        amount: Optional[float] = None
    ) -> Optional[PaperTrade]:
        """
        Execute a paper trade based on a signal
        
        Args:
            signal: Signal to trade on
            amount: Amount to trade (overrides signal position size)
            
        Returns:
            PaperTrade object or None
        """
        if not settings.PAPER_TRADING_ENABLED:
            logger.warning("⚠️ Paper trading is disabled")
            return None
        
        # Check if we have enough balance
        position_size = amount or signal.position_size
        required_balance = position_size * (1 + self.fee_rate)
        
        if required_balance > self.available_balance:
            logger.warning(
                f"⚠️ Insufficient balance for trade: "
                f"Required: ${required_balance:,.2f}, Available: ${self.available_balance:,.2f}"
            )
            return None
        
        # Determine side (buy or sell)
        # For prediction markets, we always "buy" shares
        side = TradeSide.BUY
        
        # Create trade
        trade_id = generate_id()
        trade = PaperTrade(
            id=trade_id,
            market_id=signal.market_id,
            market_title=signal.market_title,
            signal_id=signal.id,
            side=side,
            outcome=signal.outcome,
            outcome_index=signal.outcome_index,
            amount=position_size,
            price=signal.entry_price,
            fee=position_size * self.fee_rate,
            status=TradeStatus.FILLED,
            filled_amount=position_size,
            avg_fill_price=signal.entry_price,
            current_price=signal.current_price,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Update balance
        self.balance -= position_size
        self.available_balance -= required_balance
        
        # Create position
        position = PaperPosition(
            market_id=signal.market_id,
            market_title=signal.market_title,
            signal_id=signal.id,
            outcome=signal.outcome,
            outcome_index=signal.outcome_index,
            side=side,
            amount=position_size,
            entry_price=signal.entry_price,
            entry_timestamp=datetime.utcnow(),
            current_price=signal.current_price
        )
        self.positions[trade_id] = position
        
        # Save to database
        await self.database.save_paper_trade(trade.model_dump())
        
        # Update statistics
        self.stats["total_trades"] += 1
        
        # Call callbacks
        for callback in self.callbacks:
            try:
                callback(trade)
            except Exception as e:
                logger.error(f"Error in trade callback: {e}")
        
        logger.info(
            f"💰 Paper trade executed: {signal.market_title} | "
            f"Outcome: {signal.outcome} | Amount: ${position_size:,.2f} | "
            f"Price: {signal.entry_price:.2%}"
        )
        
        return trade
    
    async def execute_signal(
        self,
        signal: Signal
    ) -> Optional[PaperTrade]:
        """
        Execute a trade based on a signal
        
        Args:
            signal: Signal to execute
            
        Returns:
            PaperTrade object or None
        """
        # Calculate position size based on risk management
        position_size = self._calculate_position_size(signal)
        
        return await self.execute_trade(signal, position_size)
    
    def _calculate_position_size(
        self,
        signal: Signal
    ) -> float:
        """
        Calculate position size based on risk management
        
        Args:
            signal: Signal to calculate position for
            
        Returns:
            Position size in pUSD
        """
        # Use signal's position size as base
        base_size = signal.position_size
        
        # Apply risk management constraints
        max_size = settings.MAX_POSITION_SIZE
        max_portfolio_risk = settings.MAX_PORTFOLIO_RISK
        
        # Calculate maximum position based on portfolio risk
        max_risk_size = self.balance * max_portfolio_risk
        
        # Use the minimum of all constraints
        position_size = min(base_size, max_size, max_risk_size)
        
        # Ensure we have enough balance
        required_balance = position_size * (1 + self.fee_rate)
        if required_balance > self.available_balance:
            position_size = self.available_balance / (1 + self.fee_rate)
        
        return position_size
    
    async def update_positions(self):
        """
        Update all positions with current market prices
        """
        for trade_id, position in self.positions.items():
            try:
                # Get current market data
                market = await self.polymarket.get_market_by_slug(position.market_title)
                if not market:
                    continue
                
                clob_token_ids = market.get("clobTokenIds", [])
                if not clob_token_ids or position.outcome_index >= len(clob_token_ids):
                    continue
                
                # Get current price for the outcome
                token_id = clob_token_ids[position.outcome_index]
                current_price = await self.polymarket.get_midprice(token_id)
                
                if current_price is not None:
                    # Update position
                    position.current_price = current_price
                    
                    # Update trade in database
                    await self.database.update_paper_trade(
                        trade_id,
                        {
                            "current_price": current_price,
                            "pnl": position.pnl,
                            "pnl_pct": position.pnl_pct,
                            "updated_at": datetime.utcnow()
                        }
                    )
                    
                    # Check for stop loss or take profit
                    await self._check_exit_conditions(trade_id, position, market)
            
            except Exception as e:
                logger.error(f"❌ Error updating position {trade_id}: {e}")
    
    async def _check_exit_conditions(
        self,
        trade_id: str,
        position: PaperPosition,
        market: Dict[str, Any]
    ):
        """
        Check if position should be closed due to stop loss or take profit
        
        Args:
            trade_id: Trade ID
            position: Position object
            market: Market dictionary
        """
        # Get stop loss and take profit from signal
        signal = await self.database.get_signal(position.signal_id) if position.signal_id else None
        
        if not signal:
            return
        
        # Check stop loss
        if signal.stop_loss and position.current_price <= signal.stop_loss:
            await self.close_position(trade_id, "stop_loss")
        
        # Check take profit
        elif signal.take_profit and position.current_price >= signal.take_profit:
            await self.close_position(trade_id, "take_profit")
        
        # Check if market has expired
        end_date = market.get("endDate")
        if end_date:
            end_datetime = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            if datetime.utcnow() > end_datetime:
                await self.close_position(trade_id, "expired")
    
    async def close_position(
        self,
        trade_id: str,
        reason: str = "manual"
    ) -> Optional[PaperTrade]:
        """
        Close a position
        
        Args:
            trade_id: Trade ID to close
            reason: Reason for closing
            
        Returns:
            Updated PaperTrade object or None
        """
        if trade_id not in self.positions:
            logger.warning(f"⚠️ Position {trade_id} not found")
            return None
        
        position = self.positions[trade_id]
        
        # Calculate PnL
        pnl = position.pnl
        pnl_pct = position.pnl_pct
        
        # Update available balance
        self.available_balance += position.amount
        
        # If it's a buy position, we "sell" to close
        # In prediction markets, closing means selling the shares
        self.balance += position.amount + pnl
        
        # Update statistics
        self.stats["total_pnl"] += pnl
        if pnl > 0:
            self.stats["winning_trades"] += 1
        else:
            self.stats["losing_trades"] += 1
        
        # Update max balance and drawdown
        if self.balance > self.stats["max_balance"]:
            self.stats["max_balance"] = self.balance
        
        drawdown = (self.stats["max_balance"] - self.balance) / self.stats["max_balance"]
        if drawdown > self.stats["max_drawdown"]:
            self.stats["max_drawdown"] = drawdown
        
        # Update trade in database
        await self.database.update_paper_trade(
            trade_id,
            {
                "status": TradeStatus.CLOSED,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "closed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        )
        
        # Remove from positions
        del self.positions[trade_id]
        
        logger.info(
            f"🔒 Position closed: {position.market_title} | "
            f"PnL: ${pnl:,.2f} ({pnl_pct:+.2f}%) | Reason: {reason}"
        )
        
        # Return the updated trade
        trade = await self.database.get_paper_trade(trade_id)
        return trade
    
    async def close_all_positions(self) -> int:
        """
        Close all open positions
        
        Returns:
            Number of positions closed
        """
        count = 0
        for trade_id in list(self.positions.keys()):
            await self.close_position(trade_id, "close_all")
            count += 1
        
        logger.info(f"🔒 Closed {count} positions")
        return count
    
    async def get_portfolio(self) -> Dict[str, Any]:
        """
        Get current portfolio status
        
        Returns:
            Dictionary with portfolio information
        """
        # Calculate total PnL
        total_pnl = sum(p.pnl for p in self.positions.values())
        total_pnl_pct = (total_pnl / self.initial_balance) * 100 if self.initial_balance > 0 else 0
        
        # Calculate positions by market
        positions_by_market = {}
        for trade_id, position in self.positions.items():
            if position.market_id not in positions_by_market:
                positions_by_market[position.market_id] = []
            positions_by_market[position.market_id].append(position)
        
        return {
            "balance": self.balance,
            "available_balance": self.available_balance,
            "initial_balance": self.initial_balance,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "open_positions": len(self.positions),
            "positions": [
                {
                    "trade_id": trade_id,
                    "market_title": position.market_title,
                    "outcome": position.outcome,
                    "side": position.side,
                    "amount": position.amount,
                    "entry_price": position.entry_price,
                    "current_price": position.current_price,
                    "pnl": position.pnl,
                    "pnl_pct": position.pnl_pct,
                    "entry_timestamp": position.entry_timestamp.isoformat()
                }
                for trade_id, position in self.positions.items()
            ],
            "positions_by_market": {
                market_id: [
                    {
                        "trade_id": trade_id,
                        "outcome": p.outcome,
                        "amount": p.amount,
                        "entry_price": p.entry_price,
                        "current_price": p.current_price,
                        "pnl": p.pnl
                    }
                    for trade_id, p in positions.items()
                ]
                for market_id, positions in positions_by_market.items()
            },
            "stats": self.stats
        }
    
    async def get_trade_history(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get trade history
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            List of trade dictionaries
        """
        trades = await self.database.get_paper_trades(limit=limit)
        return [trade.model_dump() for trade in trades]
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics
        
        Returns:
            Dictionary with performance metrics
        """
        trades = await self.database.get_paper_trades()
        
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "avg_pnl": 0.0,
                "max_pnl": 0.0,
                "min_pnl": 0.0,
                "total_pnl": 0.0
            }
        
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        
        total_pnl = sum(t.pnl for t in trades)
        avg_pnl = total_pnl / len(trades) if trades else 0.0
        max_pnl = max(t.pnl for t in trades) if trades else 0.0
        min_pnl = min(t.pnl for t in trades) if trades else 0.0
        win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0.0
        
        return {
            "total_trades": len(trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": win_rate,
            "avg_pnl": avg_pnl,
            "max_pnl": max_pnl,
            "min_pnl": min_pnl,
            "total_pnl": total_pnl,
            "profit_factor": abs(max_pnl / min_pnl) if min_pnl != 0 else 0.0
        }
    
    async def reset(self):
        """
        Reset the paper trading engine
        """
        self.balance = self.initial_balance
        self.available_balance = self.initial_balance
        self.positions = {}
        self.trades = []
        self.stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
            "max_drawdown": 0.0,
            "max_balance": self.initial_balance
        }
        
        # Clear database
        # Note: In production, you might want to keep historical data
        # await self.database.delete_all_paper_trades()
        
        logger.info("🔄 Paper trading engine reset")
    
    async def run(self, interval: int = 60):
        """
        Run the paper trading engine continuously
        
        Args:
            interval: Update interval in seconds
        """
        logger.info(f"🚀 Starting paper trading engine (update every {interval} seconds)")
        
        while True:
            try:
                # Update positions
                await self.update_positions()
                
                # Get new signals and execute trades
                markets = await self.polymarket.get_crypto_markets(limit=50)
                signals = await signal_generator.generate_signals(markets)
                
                # Execute top signals
                for signal in signals[:5]:  # Execute top 5 signals
                    await self.execute_signal(signal)
                
                # Wait for next update
                await asyncio.sleep(interval)
            
            except Exception as e:
                logger.error(f"❌ Error in paper trading engine: {e}")
                await asyncio.sleep(10)  # Wait before retrying


# Create a global paper trading engine instance
paper_trading_engine = PaperTradingEngine(
    initial_balance=settings.PAPER_TRADING_INITIAL_BALANCE
)
