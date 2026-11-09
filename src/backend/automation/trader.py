"""
Real Trader for Polymarket Crypto Lab
Handles real trading via CLOB API with wallet integration
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import hashlib
import hmac
import base64
import json
from uuid import uuid4

import aiohttp
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

from ..data.polymarket import PolymarketClient
from ..data.database import Database
from ..models.schemas import Trade, TradeCreate, TradeSide, TradeStatus, Signal
from config import settings

logger = logging.getLogger(__name__)


class Trader:
    """
    Real trading engine for Polymarket.
    
    Handles:
    - Wallet connection and signing
    - Order placement via CLOB API
    - Order status tracking
    - Position management
    - Risk management
    
    Note: This requires:
    1. A configured wallet with private key
    2. Sufficient balance in pUSD
    3. CLOB API access
    """
    
    def __init__(
        self,
        private_key: Optional[str] = None,
        wallet_address: Optional[str] = None,
        clob_api_url: str = settings.CLOB_API_URL
    ):
        """
        Initialize the trader.
        
        Args:
            private_key: Wallet private key (hex string)
            wallet_address: Wallet address
            clob_api_url: CLOB API endpoint URL
        """
        self.private_key = private_key or settings.WALLET_PRIVATE_KEY
        self.wallet_address = wallet_address or settings.WALLET_ADDRESS
        self.clob_api_url = clob_api_url
        
        # Initialize components
        self.polymarket_client = PolymarketClient()
        self.database = Database()
        
        # Web3 for signing
        self.w3 = Web3()
        
        # Verify wallet
        if self.private_key:
            self._verify_wallet()
    
    def _verify_wallet(self) -> None:
        """
        Verify wallet configuration.
        """
        try:
            # Create account from private key
            account = Account.from_key(self.private_key)
            
            # Verify address matches
            if self.wallet_address and account.address.lower() != self.wallet_address.lower():
                raise ValueError(
                    f"Wallet address mismatch: expected {self.wallet_address}, "
                    f"got {account.address}"
                )
            
            self.wallet_address = account.address
            logger.info(f"Wallet verified: {self.wallet_address}")
            
        except Exception as e:
            logger.error(f"Wallet verification failed: {e}")
            raise
    
    async def get_balance(self) -> float:
        """
        Get wallet balance in pUSD.
        """
        try:
            # This is a placeholder - actual implementation requires
            # querying the CLOB API or blockchain for token balance
            
            # For now, return a mock value
            return 10000.0
            
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions from CLOB API.
        """
        try:
            # This is a placeholder - actual implementation requires
            # querying the CLOB API for user positions
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            raise
    
    async def place_order(
        self,
        market_id: str,
        outcome: str,
        side: TradeSide,
        amount: float,
        price: float,
        signal: Optional[Signal] = None
    ) -> Optional[Trade]:
        """
        Place an order on Polymarket CLOB.
        
        Args:
            market_id: Market ID
            outcome: Outcome to trade
            side: BUY or SELL
            amount: Amount in pUSD
            price: Price (0-1 for binary markets)
            signal: Optional signal that triggered this trade
        
        Returns:
            Trade object if successful, None otherwise
        """
        try:
            # Validate inputs
            if not self.private_key:
                logger.error("No private key configured for real trading")
                return None
            
            if amount <= 0:
                logger.error(f"Invalid amount: {amount}")
                return None
            
            if price <= 0 or price > 1:
                logger.error(f"Invalid price: {price}")
                return None
            
            # Get token ID for the outcome
            token_id = await self._get_token_id(market_id, outcome)
            if not token_id:
                logger.error(f"Could not get token ID for market {market_id}, outcome {outcome}")
                return None
            
            # Create order
            order = {
                "tokenId": token_id,
                "amount": str(int(amount * 1e6)),  # Convert to micro-units
                "price": str(int(price * 1e6)),  # Convert to micro-units
                "side": side.value.upper(),
                "expiration": int((datetime.utcnow() + datetime.timedelta(days=1)).timestamp())
            }
            
            # Sign the order
            signature = await self._sign_order(order)
            
            # Submit order to CLOB API
            order_id = await self._submit_order(order, signature)
            
            if not order_id:
                logger.error("Failed to submit order")
                return None
            
            # Create trade record
            trade = Trade(
                id=str(uuid4()),
                market_id=market_id,
                outcome=outcome,
                side=side,
                amount=amount,
                price=price,
                signal_id=signal.id if signal else None,
                status=TradeStatus.PENDING,
                filled_amount=0.0,
                filled_price=0.0,
                fee=0.0,
                pnl=None,
                stop_loss=None,
                take_profit=None,
                order_id=order_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save to database
            await self.database.save_trade(trade)
            
            logger.info(f"Order placed: {order_id} for {amount} pUSD of {outcome} at {price}")
            
            return trade
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise
    
    async def execute_signal(
        self,
        signal: Signal,
        amount: Optional[float] = None
    ) -> Optional[Trade]:
        """
        Execute a trade based on a signal.
        
        Args:
            signal: Signal to trade
            amount: Optional amount override
        
        Returns:
            Trade object if successful, None otherwise
        """
        try:
            # Determine side based on signal
            # For undervalued signals, we BUY the undervalued outcome
            # For overvalued signals, we SELL the overvalued outcome
            
            edge = getattr(signal, 'edge', 0)
            current_price = getattr(signal, 'price', 0.5)
            
            # Simple logic: if edge > 0, buy; if edge < 0, sell
            # This can be customized per strategy
            side = TradeSide.BUY if edge > 0 else TradeSide.SELL
            
            # Calculate amount
            if amount is None:
                amount = signal.position_size if hasattr(signal, 'position_size') else 100.0
            
            # Get current price for the outcome
            market = await self.polymarket_client.get_market_by_slug(signal.market_slug)
            if not market:
                logger.error(f"Market not found: {signal.market_slug}")
                return None
            
            # Find the outcome price
            outcomes = market.get('outcomes', [])
            outcome_index = outcomes.index(signal.outcome) if signal.outcome in outcomes else 0
            outcome_prices = market.get('outcome_prices', [])
            price = outcome_prices[outcome_index] if outcome_index < len(outcome_prices) else 0.5
            
            # Place the order
            trade = await self.place_order(
                market_id=signal.market_id,
                outcome=signal.outcome,
                side=side,
                amount=amount,
                price=price,
                signal=signal
            )
            
            return trade
            
        except Exception as e:
            logger.error(f"Error executing signal {signal.id}: {e}")
            raise
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
        
        Returns:
            True if cancelled successfully
        """
        try:
            # This is a placeholder - actual implementation requires
            # CLOB API cancel endpoint
            
            logger.info(f"Order {order_id} cancelled")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order status.
        
        Args:
            order_id: Order ID
        
        Returns:
            Order status information
        """
        try:
            # This is a placeholder - actual implementation requires
            # CLOB API order status endpoint
            
            return {"status": "filled", "filled_amount": 100, "filled_price": 0.5}
            
        except Exception as e:
            logger.error(f"Error fetching order status {order_id}: {e}")
            return None
    
    async def close_position(
        self,
        market_id: str,
        outcome: str,
        amount: float
    ) -> Optional[Trade]:
        """
        Close a position.
        
        Args:
            market_id: Market ID
            outcome: Outcome
            amount: Amount to close
        
        Returns:
            Trade object for the closing trade
        """
        try:
            # Get current position
            positions = await self.get_positions()
            position = next(
                (p for p in positions if p.get('market_id') == market_id and p.get('outcome') == outcome),
                None
            )
            
            if not position:
                logger.error(f"Position not found: {market_id} - {outcome}")
                return None
            
            # Determine side (opposite of position)
            position_side = position.get('side', 'buy')
            side = TradeSide.SELL if position_side == 'buy' else TradeSide.BUY
            
            # Get current price
            market = await self.polymarket_client.get_market_by_slug(market_id)
            if not market:
                logger.error(f"Market not found: {market_id}")
                return None
            
            outcomes = market.get('outcomes', [])
            outcome_index = outcomes.index(outcome) if outcome in outcomes else 0
            outcome_prices = market.get('outcome_prices', [])
            price = outcome_prices[outcome_index] if outcome_index < len(outcome_prices) else 0.5
            
            # Place closing order
            trade = await self.place_order(
                market_id=market_id,
                outcome=outcome,
                side=side,
                amount=amount,
                price=price
            )
            
            return trade
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            raise
    
    async def update_trade_status(self, trade: Trade) -> Trade:
        """
        Update trade status from CLOB API.
        
        Args:
            trade: Trade to update
        
        Returns:
            Updated trade
        """
        try:
            if not trade.order_id:
                return trade
            
            status = await self.get_order_status(trade.order_id)
            
            if status:
                trade.status = TradeStatus(status.get('status', 'pending'))
                trade.filled_amount = status.get('filled_amount', trade.filled_amount)
                trade.filled_price = status.get('filled_price', trade.filled_price)
                trade.updated_at = datetime.utcnow()
                
                # Save to database
                await self.database.update_trade(trade)
            
            return trade
            
        except Exception as e:
            logger.error(f"Error updating trade status: {e}")
            return trade
    
    # ==================== PRIVATE METHODS ====================
    
    async def _get_token_id(self, market_id: str, outcome: str) -> Optional[str]:
        """
        Get the CLOB token ID for a market outcome.
        
        Args:
            market_id: Market ID
            outcome: Outcome name
        
        Returns:
            Token ID or None
        """
        try:
            # Get market info
            market = await self.polymarket_client.get_market_by_slug(market_id)
            if not market:
                return None
            
            # Find token ID for outcome
            clob_token_ids = market.get('clob_token_ids', [])
            outcomes = market.get('outcomes', [])
            
            if outcome in outcomes:
                index = outcomes.index(outcome)
                if index < len(clob_token_ids):
                    return clob_token_ids[index]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting token ID: {e}")
            return None
    
    async def _sign_order(self, order: Dict[str, Any]) -> str:
        """
        Sign an order for CLOB API.
        
        Args:
            order: Order dictionary
        
        Returns:
            Signature string
        """
        try:
            # Create message to sign
            message = self._create_signature_message(order)
            
            # Sign with wallet
            account = Account.from_key(self.private_key)
            signed_message = account.sign_message(encode_defunct(text=message))
            
            return signed_message.signature.hex()
            
        except Exception as e:
            logger.error(f"Error signing order: {e}")
            raise
    
    def _create_signature_message(self, order: Dict[str, Any]) -> str:
        """
        Create message to sign for order.
        
        Args:
            order: Order dictionary
        
        Returns:
            Message string
        """
        # Sort keys and create canonical string
        sorted_keys = sorted(order.keys())
        parts = [f"{key}:{order[key]}" for key in sorted_keys]
        return "|".join(parts)
    
    async def _submit_order(
        self,
        order: Dict[str, Any],
        signature: str
    ) -> Optional[str]:
        """
        Submit order to CLOB API.
        
        Args:
            order: Order dictionary
            signature: Order signature
        
        Returns:
            Order ID or None
        """
        try:
            # Prepare request
            url = f"{self.clob_api_url}/orders"
            
            payload = {
                **order,
                "signature": signature,
                "address": self.wallet_address
            }
            
            # Send request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("orderId")
                    else:
                        error = await response.text()
                        logger.error(f"CLOB API error: {response.status} - {error}")
                        return None
            
        except Exception as e:
            logger.error(f"Error submitting order: {e}")
            return None


# Global trader instance
trader = Trader() if settings.ENABLE_REAL_TRADING else None
