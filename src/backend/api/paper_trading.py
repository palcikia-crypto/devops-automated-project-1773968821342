"""
Paper Trading API endpoints for Polymarket Crypto Lab
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..models.schemas import (
    PaperTrade, PaperTradeCreate, Position, Portfolio, 
    TradeSide, TradeStatus
)
from ..data.database import Database
from ..automation.paper_trading import PaperTradingEngine
from ..edge_finder.signals import SignalGenerator
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


# Initialize clients
database = Database()
paper_trading_engine = PaperTradingEngine()


@router.get("/balance", response_model=Dict[str, Any])
async def get_paper_balance() -> Dict[str, Any]:
    """
    Get current paper trading balance.
    """
    try:
        balance = paper_trading_engine.get_balance()
        
        return {
            "balance": balance,
            "currency": "pUSD",
            "last_updated": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error fetching paper balance: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching balance: {str(e)}")


@router.get("/positions", response_model=List[Position])
async def get_paper_positions(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    market_id: Optional[str] = Query(None, description="Filter by market ID"),
    outcome: Optional[str] = Query(None, description="Filter by outcome")
) -> List[Position]:
    """
    Get all open positions in paper trading.
    """
    try:
        positions = await database.get_positions(
            limit=limit,
            offset=offset,
            market_id=market_id,
            outcome=outcome
        )
        
        return positions
    
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching positions: {str(e)}")


@router.get("/positions/{position_id}", response_model=Position)
async def get_paper_position(position_id: str) -> Position:
    """
    Get a specific position by ID.
    """
    try:
        position = await database.get_position_by_id(position_id)
        
        if not position:
            raise HTTPException(status_code=404, detail=f"Position with ID '{position_id}' not found")
        
        return position
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching position {position_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching position: {str(e)}")


@router.get("/trades", response_model=List[PaperTrade])
async def get_paper_trades(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    market_id: Optional[str] = Query(None, description="Filter by market ID"),
    signal_id: Optional[str] = Query(None, description="Filter by signal ID"),
    side: Optional[TradeSide] = Query(None, description="Filter by trade side"),
    status: Optional[TradeStatus] = Query(None, description="Filter by trade status")
) -> List[PaperTrade]:
    """
    Get paper trading history.
    """
    try:
        trades = await database.get_paper_trades(
            limit=limit,
            offset=offset,
            market_id=market_id,
            signal_id=signal_id,
            side=side,
            status=status
        )
        
        return trades
    
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching trades: {str(e)}")


@router.get("/trades/{trade_id}", response_model=PaperTrade)
async def get_paper_trade(trade_id: str) -> PaperTrade:
    """
    Get a specific paper trade by ID.
    """
    try:
        trade = await database.get_paper_trade_by_id(trade_id)
        
        if not trade:
            raise HTTPException(status_code=404, detail=f"Trade with ID '{trade_id}' not found")
        
        return trade
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trade {trade_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching trade: {str(e)}")


@router.post("/trade", response_model=PaperTrade)
async def execute_paper_trade(trade_data: PaperTradeCreate) -> PaperTrade:
    """
    Execute a paper trade.
    """
    try:
        # Get the signal if provided
        signal = None
        if trade_data.signal_id:
            signal = await database.get_signal_by_id(trade_data.signal_id)
        
        # Execute the trade
        trade = await paper_trading_engine.execute_trade(
            market_id=trade_data.market_id,
            outcome=trade_data.outcome,
            side=trade_data.side,
            amount=trade_data.amount,
            price=trade_data.price,
            signal=signal,
            position_size=trade_data.position_size,
            stop_loss=trade_data.stop_loss,
            take_profit=trade_data.take_profit
        )
        
        return trade
    
    except Exception as e:
        logger.error(f"Error executing paper trade: {e}")
        raise HTTPException(status_code=500, detail=f"Error executing trade: {str(e)}")


@router.post("/trade/signal/{signal_id}", response_model=PaperTrade)
async def execute_paper_trade_from_signal(signal_id: str) -> PaperTrade:
    """
    Execute a paper trade from a signal.
    """
    try:
        signal = await database.get_signal_by_id(signal_id)
        
        if not signal:
            raise HTTPException(status_code=404, detail=f"Signal with ID '{signal_id}' not found")
        
        # Execute the trade based on the signal
        trade = await paper_trading_engine.execute_signal(signal)
        
        return trade
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing trade from signal {signal_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error executing trade: {str(e)}")


@router.post("/close-position/{position_id}", response_model=PaperTrade)
async def close_paper_position(position_id: str) -> PaperTrade:
    """
    Close a paper trading position.
    """
    try:
        position = await database.get_position_by_id(position_id)
        
        if not position:
            raise HTTPException(status_code=404, detail=f"Position with ID '{position_id}' not found")
        
        # Close the position
        trade = await paper_trading_engine.close_position(position)
        
        return trade
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing position {position_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error closing position: {str(e)}")


@router.get("/portfolio", response_model=Portfolio)
async def get_paper_portfolio() -> Portfolio:
    """
    Get current paper trading portfolio.
    """
    try:
        portfolio = await paper_trading_engine.get_portfolio()
        return portfolio
    
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching portfolio: {str(e)}")


@router.get("/portfolio/snapshot", response_model=Dict[str, Any])
async def get_portfolio_snapshot() -> Dict[str, Any]:
    """
    Get a snapshot of the current portfolio.
    """
    try:
        portfolio = await paper_trading_engine.get_portfolio()
        
        snapshot = {
            "balance": portfolio.balance,
            "positions": len(portfolio.positions),
            "total_value": portfolio.total_value,
            "unrealized_pnl": portfolio.unrealized_pnl,
            "realized_pnl": portfolio.realized_pnl,
            "total_pnl": portfolio.total_pnl,
            "return_pct": portfolio.return_pct,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return snapshot
    
    except Exception as e:
        logger.error(f"Error fetching portfolio snapshot: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching snapshot: {str(e)}")


@router.post("/reset", response_model=Dict[str, Any])
async def reset_paper_trading() -> Dict[str, Any]:
    """
    Reset paper trading (clear all positions and trades, reset balance).
    """
    try:
        await paper_trading_engine.reset()
        
        return {
            "status": "success",
            "message": "Paper trading reset",
            "balance": settings.PAPER_TRADING_INITIAL_BALANCE,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error resetting paper trading: {e}")
        raise HTTPException(status_code=500, detail=f"Error resetting: {str(e)}")


@router.get("/performance", response_model=Dict[str, Any])
async def get_paper_performance(
    days: int = Query(30, ge=1, le=365, description="Number of days to calculate performance")
) -> Dict[str, Any]:
    """
    Get paper trading performance metrics.
    """
    try:
        performance = await paper_trading_engine.get_performance(days=days)
        
        return {
            "total_trades": performance.get("total_trades", 0),
            "winning_trades": performance.get("winning_trades", 0),
            "losing_trades": performance.get("losing_trades", 0),
            "win_rate": performance.get("win_rate", 0),
            "total_pnl": performance.get("total_pnl", 0),
            "avg_pnl": performance.get("avg_pnl", 0),
            "max_pnl": performance.get("max_pnl", 0),
            "max_loss": performance.get("max_loss", 0),
            "sharpe_ratio": performance.get("sharpe_ratio", 0),
            "sortino_ratio": performance.get("sortino_ratio", 0),
            "max_drawdown": performance.get("max_drawdown", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error fetching performance: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching performance: {str(e)}")


@router.get("/stats", response_model=Dict[str, Any])
async def get_paper_stats() -> Dict[str, Any]:
    """
    Get paper trading statistics.
    """
    try:
        trades = await database.get_paper_trades(limit=1000)
        positions = await database.get_positions(limit=1000)
        
        return {
            "total_trades": len(trades),
            "open_positions": len(positions),
            "balance": paper_trading_engine.get_balance(),
            "initial_balance": settings.PAPER_TRADING_INITIAL_BALANCE,
            "total_pnl": sum(t.pnl for t in trades if t.pnl is not None),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error fetching paper stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")
