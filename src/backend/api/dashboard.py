"""
Dashboard API endpoints for Polymarket Crypto Lab
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ..models.schemas import (
    Signal, Market, PaperTrade, Position, Portfolio,
    SignalType, SignalStatus, TradeSide
)
from ..data.database import Database
from ..data.cache import Cache
from ..data.polymarket import PolymarketClient
from ..edge_finder.scanner import MarketScanner
from ..edge_finder.signals import SignalGenerator
from ..automation.paper_trading import PaperTradingEngine
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


# Initialize clients
database = Database()
cache = Cache()
polymarket_client = PolymarketClient()
paper_trading_engine = PaperTradingEngine()


@router.get("/overview", response_model=Dict[str, Any])
async def get_dashboard_overview() -> Dict[str, Any]:
    """
    Get dashboard overview with key metrics.
    """
    try:
        # Get market stats
        markets = await polymarket_client.get_markets(tag_id=21, limit=100)
        
        # Get signal stats
        signals = await database.get_signals(limit=1000)
        active_signals = [s for s in signals if s.status == SignalStatus.ACTIVE]
        
        # Get paper trading stats
        portfolio = await paper_trading_engine.get_portfolio()
        trades = await database.get_paper_trades(limit=1000)
        
        # Get recent signals
        recent_signals = sorted(signals, key=lambda x: x.created_at, reverse=True)[:5]
        
        # Get top signals by edge
        top_signals = sorted(
            [s for s in active_signals if hasattr(s, 'edge')],
            key=lambda x: x.edge,
            reverse=True
        )[:5]
        
        return {
            "markets": {
                "total": len(markets),
                "active": len([m for m in markets if m.get('status') == 'active']),
                "volume_24hr": sum(m.get('volume_24hr', 0) for m in markets)
            },
            "signals": {
                "total": len(signals),
                "active": len(active_signals),
                "by_type": {
                    t.value: len([s for s in signals if s.type == t])
                    for t in SignalType
                }
            },
            "paper_trading": {
                "balance": portfolio.balance,
                "total_pnl": portfolio.total_pnl,
                "return_pct": portfolio.return_pct,
                "open_positions": len(portfolio.positions),
                "total_trades": len(trades)
            },
            "recent_signals": [
                {
                    "id": s.id,
                    "type": s.type.value,
                    "market_title": s.market_title,
                    "outcome": s.outcome,
                    "edge": getattr(s, 'edge', 0),
                    "created_at": s.created_at.isoformat()
                }
                for s in recent_signals
            ],
            "top_signals": [
                {
                    "id": s.id,
                    "type": s.type.value,
                    "market_title": s.market_title,
                    "outcome": s.outcome,
                    "edge": getattr(s, 'edge', 0),
                    "strategy": s.strategy
                }
                for s in top_signals
            ],
            "last_updated": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error fetching dashboard overview: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching overview: {str(e)}")


@router.get("/realtime", response_model=Dict[str, Any])
async def get_realtime_data() -> Dict[str, Any]:
    """
    Get real-time data for dashboard.
    """
    try:
        # Get latest markets
        markets = await polymarket_client.get_markets(tag_id=21, limit=20)
        
        # Get active signals
        signals = await database.get_signals(
            status=SignalStatus.ACTIVE,
            limit=20
        )
        
        # Get portfolio
        portfolio = await paper_trading_engine.get_portfolio()
        
        return {
            "markets": [
                {
                    "id": m.get('id'),
                    "title": m.get('title'),
                    "slug": m.get('slug'),
                    "outcome_prices": m.get('outcome_prices', []),
                    "volume_24hr": m.get('volume_24hr', 0),
                    "liquidity": m.get('liquidity', 0),
                    "end_date": m.get('end_date')
                }
                for m in markets
            ],
            "signals": [
                {
                    "id": s.id,
                    "type": s.type.value,
                    "market_title": s.market_title,
                    "outcome": s.outcome,
                    "edge": getattr(s, 'edge', 0),
                    "price": getattr(s, 'price', 0),
                    "strategy": s.strategy,
                    "created_at": s.created_at.isoformat()
                }
                for s in signals
            ],
            "portfolio": {
                "balance": portfolio.balance,
                "total_value": portfolio.total_value,
                "unrealized_pnl": portfolio.unrealized_pnl,
                "realized_pnl": portfolio.realized_pnl,
                "total_pnl": portfolio.total_pnl,
                "return_pct": portfolio.return_pct
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error fetching real-time data: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching real-time data: {str(e)}")


@router.get("/charts/markets", response_model=Dict[str, Any])
async def get_markets_chart_data(
    days: int = Query(7, ge=1, le=30, description="Number of days")
) -> Dict[str, Any]:
    """
    Get chart data for markets.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get markets with volume data
        markets = await polymarket_client.get_markets(tag_id=21, limit=50)
        
        # Group by date
        daily_data = {}
        for market in markets:
            market_date = market.get('start_date') or market.get('created_at')
            if market_date:
                date_str = datetime.fromisoformat(market_date.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                if date_str not in daily_data:
                    daily_data[date_str] = {"volume": 0, "markets": 0}
                daily_data[date_str]["volume"] += market.get('volume_24hr', 0)
                daily_data[date_str]["markets"] += 1
        
        # Sort by date
        sorted_dates = sorted(daily_data.keys())
        
        return {
            "labels": sorted_dates[-days:] if len(sorted_dates) >= days else sorted_dates,
            "volumes": [daily_data[d]["volume"] for d in sorted_dates[-days:]],
            "market_counts": [daily_data[d]["markets"] for d in sorted_dates[-days:]]
        }
    
    except Exception as e:
        logger.error(f"Error fetching markets chart data: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching chart data: {str(e)}")


@router.get("/charts/signals", response_model=Dict[str, Any])
async def get_signals_chart_data(
    days: int = Query(7, ge=1, le=30, description="Number of days")
) -> Dict[str, Any]:
    """
    Get chart data for signals.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        signals = await database.get_signals(limit=1000)
        
        # Group by date
        daily_data = {}
        for signal in signals:
            date_str = signal.created_at.strftime('%Y-%m-%d')
            if date_str not in daily_data:
                daily_data[date_str] = {
                    "count": 0,
                    "by_type": {t.value: 0 for t in SignalType}
                }
            daily_data[date_str]["count"] += 1
            daily_data[date_str]["by_type"][signal.type.value] += 1
        
        # Sort by date
        sorted_dates = sorted(daily_data.keys())
        
        return {
            "labels": sorted_dates[-days:] if len(sorted_dates) >= days else sorted_dates,
            "counts": [daily_data[d]["count"] for d in sorted_dates[-days:]],
            "by_type": {
                signal_type: [daily_data[d]["by_type"].get(signal_type, 0) for d in sorted_dates[-days:]]
                for signal_type in [t.value for t in SignalType]
            }
        }
    
    except Exception as e:
        logger.error(f"Error fetching signals chart data: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching chart data: {str(e)}")


@router.get("/charts/portfolio", response_model=Dict[str, Any])
async def get_portfolio_chart_data(
    days: int = Query(7, ge=1, le=30, description="Number of days")
) -> Dict[str, Any]:
    """
    Get chart data for portfolio.
    """
    try:
        portfolio = await paper_trading_engine.get_portfolio()
        trades = await database.get_paper_trades(limit=1000)
        
        # Get portfolio snapshots
        snapshots = await database.get_portfolio_snapshots(
            start_date=datetime.utcnow() - timedelta(days=days)
        )
        
        # Generate daily balance data
        daily_balances = {}
        current_balance = settings.PAPER_TRADING_INITIAL_BALANCE
        
        for snapshot in sorted(snapshots, key=lambda x: x.created_at):
            date_str = snapshot.created_at.strftime('%Y-%m-%d')
            daily_balances[date_str] = snapshot.balance
        
        # Fill in missing dates
        all_dates = [
            (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
            for i in range(days)
        ]
        
        balances = []
        for date_str in all_dates:
            if date_str in daily_balances:
                current_balance = daily_balances[date_str]
            balances.append(current_balance)
        
        return {
            "labels": all_dates,
            "balance": balances,
            "current_balance": portfolio.balance,
            "initial_balance": settings.PAPER_TRADING_INITIAL_BALANCE,
            "total_pnl": portfolio.total_pnl,
            "return_pct": portfolio.return_pct
        }
    
    except Exception as e:
        logger.error(f"Error fetching portfolio chart data: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching chart data: {str(e)}")


@router.get("/notifications", response_model=List[Dict[str, Any]])
async def get_notifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> List[Dict[str, Any]]:
    """
    Get recent notifications for dashboard.
    """
    try:
        notifications = await database.get_notifications(
            limit=limit,
            offset=offset
        )
        
        return [
            {
                "id": n.id,
                "type": n.notification_type.value,
                "title": n.title,
                "message": n.message,
                "data": n.data,
                "read": n.read,
                "created_at": n.created_at.isoformat()
            }
            for n in notifications
        ]
    
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching notifications: {str(e)}")


@router.get("/settings", response_model=Dict[str, Any])
async def get_dashboard_settings() -> Dict[str, Any]:
    """
    Get dashboard settings.
    """
    try:
        return {
            "theme": "dark",
            "refresh_interval": 30,
            "notifications_enabled": True,
            "sound_enabled": True,
            "auto_trade": settings.AUTO_TRADE,
            "paper_trading_enabled": settings.ENABLE_PAPER_TRADING,
            "real_trading_enabled": settings.ENABLE_REAL_TRADING
        }
    
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching settings: {str(e)}")


@router.post("/settings", response_model=Dict[str, Any])
async def update_dashboard_settings(settings_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update dashboard settings.
    """
    try:
        # Update settings in database
        for key, value in settings_data.items():
            await database.update_setting(key, value)
        
        return {
            "status": "success",
            "message": "Settings updated",
            "updated_settings": settings_data
        }
    
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating settings: {str(e)}")
