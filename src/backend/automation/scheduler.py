"""
Scheduler for Polymarket Crypto Lab
Coordinates automated market scanning, signal generation, and trading
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable, List
import traceback

from ..data.polymarket import PolymarketClient
from ..data.database import Database
from ..data.cache import Cache
from ..edge_finder.scanner import MarketScanner
from ..edge_finder.signals import SignalGenerator
from ..automation.paper_trading import PaperTradingEngine
from ..automation.notifier import Notifier
from config import settings

logger = logging.getLogger(__name__)


class Scheduler:
    """
    Main scheduler that coordinates all automated tasks.
    
    Responsibilities:
    - Schedule market scanning at regular intervals
    - Schedule signal generation at regular intervals
    - Schedule position updates at regular intervals
    - Schedule portfolio snapshots at regular intervals
    - Handle errors and retries
    - Manage task lifecycle
    """
    
    def __init__(
        self,
        scan_interval: int = 300,  # 5 minutes
        signal_interval: int = 900,  # 15 minutes
        position_update_interval: int = 60,  # 1 minute
        portfolio_snapshot_interval: int = 3600,  # 1 hour
        auto_trade: bool = True
    ):
        """
        Initialize the scheduler.
        
        Args:
            scan_interval: Seconds between market scans
            signal_interval: Seconds between signal generation
            position_update_interval: Seconds between position updates
            portfolio_snapshot_interval: Seconds between portfolio snapshots
            auto_trade: Whether to automatically execute trades from signals
        """
        self.scan_interval = scan_interval
        self.signal_interval = signal_interval
        self.position_update_interval = position_update_interval
        self.portfolio_snapshot_interval = portfolio_snapshot_interval
        self.auto_trade = auto_trade
        self.running = False
        
        # Initialize components
        self.polymarket_client = PolymarketClient()
        self.database = Database()
        self.cache = Cache()
        self.scanner = MarketScanner()
        self.signal_generator = SignalGenerator()
        self.paper_trading_engine = PaperTradingEngine()
        self.notifier = Notifier()
        
        # Task tracking
        self.tasks: Dict[str, asyncio.Task] = {}
        self.last_run: Dict[str, datetime] = {}
        self.stats: Dict[str, Any] = {
            "markets_scanned": 0,
            "signals_generated": 0,
            "positions_updated": 0,
            "portfolio_snapshots": 0,
            "trades_executed": 0,
            "errors": 0,
            "started_at": None,
            "last_error": None
        }
    
    async def start(self) -> None:
        """
        Start all scheduled tasks.
        """
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info("Starting Polymarket Crypto Lab Scheduler")
        self.running = True
        self.stats["started_at"] = datetime.utcnow()
        
        # Start all tasks
        self.tasks["market_scan"] = asyncio.create_task(
            self._market_scan_loop()
        )
        self.tasks["signal_generation"] = asyncio.create_task(
            self._signal_generation_loop()
        )
        self.tasks["position_update"] = asyncio.create_task(
            self._position_update_loop()
        )
        self.tasks["portfolio_snapshot"] = asyncio.create_task(
            self._portfolio_snapshot_loop()
        )
        
        logger.info("All scheduler tasks started")
    
    async def stop(self) -> None:
        """
        Stop all scheduled tasks.
        """
        if not self.running:
            logger.warning("Scheduler is not running")
            return
        
        logger.info("Stopping Polymarket Crypto Lab Scheduler")
        self.running = False
        
        # Cancel all tasks
        for task_name, task in self.tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Task '{task_name}' cancelled")
        
        logger.info("All scheduler tasks stopped")
    
    async def restart(self) -> None:
        """
        Restart all scheduled tasks.
        """
        await self.stop()
        await asyncio.sleep(1)
        await self.start()
    
    async def _market_scan_loop(self) -> None:
        """
        Market scanning loop.
        """
        logger.info(f"Market scan loop started (interval: {self.scan_interval}s)")
        
        while self.running:
            try:
                start_time = datetime.utcnow()
                logger.info("Starting market scan...")
                
                # Scan markets
                result = await self.scanner.scan_markets(
                    tag_id=settings.CRYPTO_TAG_ID,
                    force=False
                )
                
                self.stats["markets_scanned"] += result.get("markets_scanned", 0)
                self.last_run["market_scan"] = datetime.utcnow()
                
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"Market scan completed in {elapsed:.2f}s. Found {result.get('new_markets', 0)} new markets, {result.get('updated_markets', 0)} updated")
                
            except Exception as e:
                self.stats["errors"] += 1
                self.stats["last_error"] = str(e)
                logger.error(f"Error in market scan loop: {e}\n{traceback.format_exc()}")
                
                # Wait before retrying
                await asyncio.sleep(60)
            
            # Wait for next interval
            await asyncio.sleep(self.scan_interval)
    
    async def _signal_generation_loop(self) -> None:
        """
        Signal generation loop.
        """
        logger.info(f"Signal generation loop started (interval: {self.signal_interval}s)")
        
        while self.running:
            try:
                start_time = datetime.utcnow()
                logger.info("Starting signal generation...")
                
                # Generate signals
                result = await self.signal_generator.generate_signals(force=False)
                
                self.stats["signals_generated"] += result.get("signals_generated", 0)
                self.last_run["signal_generation"] = datetime.utcnow()
                
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"Signal generation completed in {elapsed:.2f}s. Generated {result.get('signals_generated', 0)} signals")
                
                # Optionally auto-trade signals
                if self.auto_trade and settings.AUTO_TRADE:
                    await self._auto_trade_signals()
                
            except Exception as e:
                self.stats["errors"] += 1
                self.stats["last_error"] = str(e)
                logger.error(f"Error in signal generation loop: {e}\n{traceback.format_exc()}")
                
                # Wait before retrying
                await asyncio.sleep(60)
            
            # Wait for next interval
            await asyncio.sleep(self.signal_interval)
    
    async def _position_update_loop(self) -> None:
        """
        Position update loop.
        """
        logger.info(f"Position update loop started (interval: {self.position_update_interval}s)")
        
        while self.running:
            try:
                start_time = datetime.utcnow()
                logger.debug("Starting position update...")
                
                # Update positions with current prices
                updated_positions = await self.paper_trading_engine.update_positions()
                
                self.stats["positions_updated"] += updated_positions
                self.last_run["position_update"] = datetime.utcnow()
                
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                logger.debug(f"Position update completed in {elapsed:.2f}s. Updated {updated_positions} positions")
                
            except Exception as e:
                self.stats["errors"] += 1
                self.stats["last_error"] = str(e)
                logger.error(f"Error in position update loop: {e}\n{traceback.format_exc()}")
                
                # Wait before retrying
                await asyncio.sleep(10)
            
            # Wait for next interval
            await asyncio.sleep(self.position_update_interval)
    
    async def _portfolio_snapshot_loop(self) -> None:
        """
        Portfolio snapshot loop.
        """
        logger.info(f"Portfolio snapshot loop started (interval: {self.portfolio_snapshot_interval}s)")
        
        while self.running:
            try:
                start_time = datetime.utcnow()
                logger.info("Starting portfolio snapshot...")
                
                # Take portfolio snapshot
                portfolio = await self.paper_trading_engine.get_portfolio()
                await self.database.save_portfolio_snapshot(portfolio)
                
                self.stats["portfolio_snapshots"] += 1
                self.last_run["portfolio_snapshot"] = datetime.utcnow()
                
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"Portfolio snapshot completed in {elapsed:.2f}s. Balance: {portfolio.balance:.2f} pUSD, PnL: {portfolio.total_pnl:.2f} pUSD")
                
            except Exception as e:
                self.stats["errors"] += 1
                self.stats["last_error"] = str(e)
                logger.error(f"Error in portfolio snapshot loop: {e}\n{traceback.format_exc()}")
                
                # Wait before retrying
                await asyncio.sleep(60)
            
            # Wait for next interval
            await asyncio.sleep(self.portfolio_snapshot_interval)
    
    async def _auto_trade_signals(self) -> None:
        """
        Automatically execute trades from active signals.
        """
        try:
            logger.info("Starting auto-trading from signals...")
            
            # Get active signals
            signals = await self.database.get_signals(
                status="active",
                limit=100
            )
            
            # Sort by edge (highest first)
            signals = sorted(
                [s for s in signals if hasattr(s, 'edge')],
                key=lambda x: x.edge,
                reverse=True
            )
            
            # Execute trades for top signals
            for signal in signals[:settings.MAX_AUTO_TRADES]:
                try:
                    # Check if we already have a position for this signal
                    existing_positions = await self.database.get_positions(
                        market_id=signal.market_id,
                        outcome=signal.outcome
                    )
                    
                    if existing_positions:
                        logger.debug(f"Already have position for signal {signal.id}, skipping")
                        continue
                    
                    # Execute trade
                    trade = await self.paper_trading_engine.execute_signal(signal)
                    
                    if trade:
                        self.stats["trades_executed"] += 1
                        logger.info(f"Auto-traded signal {signal.id}: {signal.market_title} - {signal.outcome} (edge: {getattr(signal, 'edge', 0):.2%})")
                        
                        # Notify
                        await self.notifier.notify_trade(trade)
                    
                except Exception as e:
                    logger.error(f"Error auto-trading signal {signal.id}: {e}")
            
            logger.info(f"Auto-trading completed. Executed trades for {min(len(signals), settings.MAX_AUTO_TRADES)} signals")
            
        except Exception as e:
            logger.error(f"Error in auto-trading: {e}\n{traceback.format_exc()}")
    
    async def run_once(self) -> Dict[str, Any]:
        """
        Run all tasks once (for manual triggering).
        
        Returns:
            Statistics from the run
        """
        logger.info("Running scheduler tasks once...")
        
        try:
            # Market scan
            result = await self.scanner.scan_markets(
                tag_id=settings.CRYPTO_TAG_ID,
                force=True
            )
            self.stats["markets_scanned"] += result.get("markets_scanned", 0)
            
            # Signal generation
            result = await self.signal_generator.generate_signals(force=True)
            self.stats["signals_generated"] += result.get("signals_generated", 0)
            
            # Position update
            updated = await self.paper_trading_engine.update_positions()
            self.stats["positions_updated"] += updated
            
            # Portfolio snapshot
            portfolio = await self.paper_trading_engine.get_portfolio()
            await self.database.save_portfolio_snapshot(portfolio)
            self.stats["portfolio_snapshots"] += 1
            
            # Auto-trade if enabled
            if self.auto_trade and settings.AUTO_TRADE:
                await self._auto_trade_signals()
            
            logger.info("Scheduler tasks completed")
            
        except Exception as e:
            self.stats["errors"] += 1
            self.stats["last_error"] = str(e)
            logger.error(f"Error in run_once: {e}\n{traceback.format_exc()}")
        
        return self.stats
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get scheduler statistics.
        """
        return {
            **self.stats,
            "running": self.running,
            "last_run": self.last_run,
            "tasks": {
                name: {
                    "running": not task.done(),
                    "done": task.done()
                }
                for name, task in self.tasks.items()
            },
            "uptime": (datetime.utcnow() - self.stats.get("started_at")).total_seconds() if self.stats.get("started_at") else 0
        }
    
    async def trigger_market_scan(self) -> Dict[str, Any]:
        """
        Manually trigger a market scan.
        """
        logger.info("Manual market scan triggered")
        result = await self.scanner.scan_markets(
            tag_id=settings.CRYPTO_TAG_ID,
            force=True
        )
        return result
    
    async def trigger_signal_generation(self) -> Dict[str, Any]:
        """
        Manually trigger signal generation.
        """
        logger.info("Manual signal generation triggered")
        result = await self.signal_generator.generate_signals(force=True)
        return result
    
    async def trigger_position_update(self) -> Dict[str, Any]:
        """
        Manually trigger position update.
        """
        logger.info("Manual position update triggered")
        updated = await self.paper_trading_engine.update_positions()
        return {"positions_updated": updated}
    
    async def trigger_portfolio_snapshot(self) -> Dict[str, Any]:
        """
        Manually trigger portfolio snapshot.
        """
        logger.info("Manual portfolio snapshot triggered")
        portfolio = await self.paper_trading_engine.get_portfolio()
        await self.database.save_portfolio_snapshot(portfolio)
        return {"snapshot_saved": True, "balance": portfolio.balance}


# Global scheduler instance
scheduler = Scheduler(
    scan_interval=settings.MARKET_SCAN_INTERVAL,
    signal_interval=settings.SIGNAL_GENERATION_INTERVAL,
    position_update_interval=settings.POSITION_UPDATE_INTERVAL,
    portfolio_snapshot_interval=settings.PORTFOLIO_SNAPSHOT_INTERVAL,
    auto_trade=settings.AUTO_TRADE
)
