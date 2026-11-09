"""
Notifier for Polymarket Crypto Lab
Sends notifications via Telegram, Discord, and Email
"""
import aiohttp
import logging
import json
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime

from config import settings
from ..models.schemas import Signal, Trade, PaperTrade, NotificationType
from ..data.database import Database
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Notifier:
    """
    Sends notifications via various channels
    """
    
    def __init__(
        self,
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        discord_webhook_url: Optional[str] = None
    ):
        """Initialize the notifier"""
        self.telegram_bot_token = telegram_bot_token or settings.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = telegram_chat_id or settings.TELEGRAM_CHAT_ID
        self.discord_webhook_url = discord_webhook_url or settings.DISCORD_WEBHOOK_URL
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.callbacks: List[Callable[[Dict[str, Any]], None]] = []
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add a callback to be called when a notification is sent"""
        self.callbacks.append(callback)
    
    async def send_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a notification via all enabled channels
        
        Args:
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            data: Additional data to include
            
        Returns:
            True if notification was sent successfully
        """
        success = False
        
        # Create notification object
        notification = {
            "type": notification_type.value,
            "title": title,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send via Telegram
        if self.telegram_bot_token and self.telegram_chat_id:
            telegram_success = await self._send_telegram(notification)
            success = success or telegram_success
        
        # Send via Discord
        if self.discord_webhook_url:
            discord_success = await self._send_discord(notification)
            success = success or discord_success
        
        # Save to database
        await self.database.save_notification({
            "id": f"notif_{datetime.utcnow().timestamp()}",
            "type": notification_type.value,
            "title": title,
            "message": message,
            "data": json.dumps(data) if data else None,
            "read": False
        })
        
        # Call callbacks
        for callback in self.callbacks:
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"Error in notification callback: {e}")
        
        return success
    
    async def _send_telegram(
        self,
        notification: Dict[str, Any]
    ) -> bool:
        """
        Send notification via Telegram
        
        Args:
            notification: Notification dictionary
            
        Returns:
            True if successful
        """
        if not self.telegram_bot_token or not self.telegram_chat_id:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            
            # Format message
            message = f"*{notification['title']}*\n\n{notification['message']}"
            
            if notification.get("data"):
                data = notification["data"]
                if "market_title" in data:
                    message += f"\n\n📌 *Market*: {data['market_title']}"
                if "pnl" in data:
                    pnl = data["pnl"]
                    pnl_color = "🟢" if pnl > 0 else "🔴"
                    message += f"\n{pnl_color} *PnL*: ${pnl:,.2f}"
                if "edge" in data:
                    message += f"\n📊 *Edge*: {data['edge']:.2%}"
            
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info("✅ Telegram notification sent")
                        return True
                    else:
                        logger.error(f"❌ Telegram API error: {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"❌ Error sending Telegram notification: {e}")
            return False
    
    async def _send_discord(
        self,
        notification: Dict[str, Any]
    ) -> bool:
        """
        Send notification via Discord webhook
        
        Args:
            notification: Notification dictionary
            
        Returns:
            True if successful
        """
        if not self.discord_webhook_url:
            return False
        
        try:
            # Format message for Discord
            embed = {
                "title": notification["title"],
                "description": notification["message"],
                "color": 0x3498db,  # Blue
                "timestamp": notification["timestamp"],
                "fields": []
            }
            
            # Add fields from data
            if notification.get("data"):
                data = notification["data"]
                
                if "market_title" in data:
                    embed["fields"].append({
                        "name": "Market",
                        "value": data["market_title"],
                        "inline": True
                    })
                
                if "pnl" in data:
                    pnl = data["pnl"]
                    embed["fields"].append({
                        "name": "PnL",
                        "value": f"${pnl:,.2f}",
                        "inline": True
                    })
                
                if "edge" in data:
                    embed["fields"].append({
                        "name": "Edge",
                        "value": f"{data['edge']:.2%}",
                        "inline": True
                    })
                
                if "type" in data:
                    embed["fields"].append({
                        "name": "Type",
                        "value": data["type"],
                        "inline": True
                    })
            
            payload = {
                "embeds": [embed]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.discord_webhook_url, json=payload) as response:
                    if response.status == 204:
                        logger.info("✅ Discord notification sent")
                        return True
                    else:
                        logger.error(f"❌ Discord API error: {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"❌ Error sending Discord notification: {e}")
            return False
    
    async def notify_signal(
        self,
        signal: Signal
    ) -> bool:
        """
        Send notification for a new signal
        
        Args:
            signal: Signal object
            
        Returns:
            True if successful
        """
        title = f"🚀 New {signal.type.value} Signal"
        message = f"Market: {signal.market_title}\nOutcome: {signal.outcome}\nEdge: {getattr(signal, 'edge', 0):.2%}"
        
        data = {
            "type": signal.type.value,
            "market_title": signal.market_title,
            "market_slug": signal.market_slug,
            "outcome": signal.outcome,
            "edge": getattr(signal, 'edge', 0),
            "arbitrage": getattr(signal, 'arbitrage', 0),
            "growth": getattr(signal, 'growth', 0)
        }
        
        return await self.send_notification(
            NotificationType.SIGNAL,
            title,
            message,
            data
        )
    
    async def notify_trade(
        self,
        trade: Trade,
        is_paper: bool = False
    ) -> bool:
        """
        Send notification for a trade
        
        Args:
            trade: Trade object
            is_paper: Whether it's a paper trade
            
        Returns:
            True if successful
        """
        trade_type = "Paper Trade" if is_paper else "Trade"
        title = f"💰 {trade_type} Executed"
        
        message = (
            f"Market: {trade.market_title}\n"
            f"Side: {trade.side.value}\n"
            f"Outcome: {trade.outcome}\n"
            f"Amount: ${trade.amount:,.2f}\n"
            f"Price: {trade.price:.2%}"
        )
        
        data = {
            "type": trade_type,
            "market_title": trade.market_title,
            "side": trade.side.value,
            "outcome": trade.outcome,
            "amount": trade.amount,
            "price": trade.price
        }
        
        return await self.send_notification(
            NotificationType.TRADE,
            title,
            message,
            data
        )
    
    async def notify_pnl(
        self,
        pnl: float,
        pnl_pct: float,
        description: str = ""
    ) -> bool:
        """
        Send notification for PnL update
        
        Args:
            pnl: PnL amount
            pnl_pct: PnL percentage
            description: Additional description
            
        Returns:
            True if successful
        """
        color = "🟢" if pnl > 0 else "🔴"
        title = f"{color} PnL Update"
        
        message = (
            f"PnL: ${pnl:,.2f} ({pnl_pct:+.2f}%)\n"
            f"{description}"
        )
        
        data = {
            "pnl": pnl,
            "pnl_pct": pnl_pct
        }
        
        return await self.send_notification(
            NotificationType.TRADE,
            title,
            message,
            data
        )
    
    async def notify_alert(
        self,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send an alert notification
        
        Args:
            title: Alert title
            message: Alert message
            data: Additional data
            
        Returns:
            True if successful
        """
        return await self.send_notification(
            NotificationType.ALERT,
            f"⚠️ {title}",
            message,
            data
        )
    
    async def notify_error(
        self,
        error: str,
        context: str = ""
    ) -> bool:
        """
        Send an error notification
        
        Args:
            error: Error message
            context: Additional context
            
        Returns:
            True if successful
        """
        title = "❌ Error"
        message = f"Error: {error}\nContext: {context}"
        
        return await self.send_notification(
            NotificationType.ERROR,
            title,
            message
        )
    
    async def send_daily_report(
        self,
        portfolio: Dict[str, Any],
        signals: List[Signal],
        trades: List[Dict[str, Any]]
    ) -> bool:
        """
        Send a daily report
        
        Args:
            portfolio: Portfolio data
            signals: List of active signals
            trades: List of recent trades
            
        Returns:
            True if successful
        """
        title = "📊 Daily Report"
        
        # Build message
        message = f"""
*Portfolio Status*
Balance: ${portfolio['balance']:,.2f}
PnL: ${portfolio['total_pnl']:,.2f} ({portfolio['total_pnl_pct']:+.2f}%)
Open Positions: {portfolio['open_positions']}

*Recent Activity*
New Signals: {len(signals)}
Recent Trades: {len(trades)}

*Performance*
Total Trades: {portfolio['stats']['total_trades']}
Winning Trades: {portfolio['stats']['winning_trades']}
Win Rate: {portfolio['stats']['win_rate']:.1f}%
"""
        
        data = {
            "portfolio": portfolio,
            "signals_count": len(signals),
            "trades_count": len(trades)
        }
        
        return await self.send_notification(
            NotificationType.SIGNAL,
            title,
            message,
            data
        )


# Create a global notifier instance
notifier = Notifier()
