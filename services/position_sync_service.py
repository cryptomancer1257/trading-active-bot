#!/usr/bin/env python3
"""
Real-Time Position Sync Service
Syncs open positions from exchanges and updates transaction records

Features:
- Multi-exchange support (Bybit, Binance, OKX, Bitget, Huobi, Kraken)
- Real-time P&L calculation
- Auto-detect position closures
- Update transaction records with exchange data
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import or_

from core import models
from core.api_key_manager import APIKeyManager
from services.exchange_integrations.exchange_factory import create_futures_exchange
from services.exchange_integrations.base_futures_exchange import FuturesPosition

logger = logging.getLogger(__name__)


class PositionSyncService:
    """Service for syncing positions from exchanges to database"""
    
    def __init__(self, db: Session):
        self.db = db
        self.exchange_clients = {}  # Cache exchange clients
        self.api_key_manager = APIKeyManager()  # For decrypting API keys
        
    def get_exchange_client(self, exchange_type: str, api_key: str, api_secret: str, network: str = "TESTNET", passphrase: str = ""):
        """
        Get or create exchange client (with caching)
        """
        cache_key = f"{exchange_type}:{network}:{api_key[:10]}"
        
        if cache_key not in self.exchange_clients:
            try:
                # Convert network to testnet boolean
                testnet = (network == "TESTNET")
                
                client = create_futures_exchange(
                    exchange_name=exchange_type,
                    api_key=api_key,
                    api_secret=api_secret,
                    passphrase=passphrase,
                    testnet=testnet
                )
                self.exchange_clients[cache_key] = client
                logger.debug(f"Created new exchange client for {exchange_type} ({network})")
            except Exception as e:
                logger.error(f"Failed to create exchange client for {exchange_type}: {e}")
                return None
                
        return self.exchange_clients[cache_key]
    
    def sync_transaction_with_exchange(self, transaction: models.Transaction) -> Dict[str, Any]:
        """
        Sync a single transaction with exchange API
        
        Returns:
            dict with status and updated fields
        """
        try:
            # Get subscription to access API keys
            subscription = self.db.query(models.Subscription).filter(
                models.Subscription.id == transaction.subscription_id
            ).first()
            
            if not subscription:
                logger.warning(f"Transaction {transaction.id} has no subscription")
                return {"status": "error", "message": "No subscription found"}
            
            # Get bot to access exchange type
            bot = subscription.bot
            if not bot:
                logger.warning(f"Subscription {subscription.id} has no bot")
                return {"status": "error", "message": "No bot found"}
            
            # Determine network type
            network_type = subscription.network_type if subscription.network_type else models.NetworkType.TESTNET
            is_testnet = (network_type == models.NetworkType.TESTNET)
            
            # Get exchange credentials based on user type
            api_key = None
            api_secret = None
            api_passphrase = None
            
            # Case 1: Developer testing their own bot
            # Check if subscription belongs to bot developer
            is_developer_testing = (subscription.user_id == bot.developer_id) if subscription.user_id and bot.developer_id else False
            
            if is_developer_testing:
                logger.debug(f"Developer {subscription.user_id} testing bot {bot.id}")
                # Query developer_exchange_credentials
                dev_credentials = self.db.query(models.DeveloperExchangeCredentials).filter(
                    models.DeveloperExchangeCredentials.user_id == subscription.user_id,
                    models.DeveloperExchangeCredentials.exchange_type == bot.exchange_type,
                    models.DeveloperExchangeCredentials.credential_type == models.CredentialType.FUTURES,
                    models.DeveloperExchangeCredentials.network_type == network_type,
                    models.DeveloperExchangeCredentials.is_active == True
                ).first()
                
                if dev_credentials:
                    # Decrypt API keys
                    api_key = self.api_key_manager.decrypt_api_key(dev_credentials.api_key)
                    api_secret = self.api_key_manager.decrypt_api_key(dev_credentials.api_secret)
                    api_passphrase = self.api_key_manager.decrypt_api_key(dev_credentials.passphrase) if dev_credentials.passphrase else None
                    logger.debug(f"Using developer credentials: {dev_credentials.name}")
                else:
                    logger.warning(f"No developer credentials found for user {subscription.user_id}, exchange: {bot.exchange_type.value}, network: {network_type.value}")
                    return {"status": "error", "message": "No developer credentials"}
            
            # Case 2: Marketplace user renting bot
            elif subscription.user_principal_id:
                logger.debug(f"Marketplace user {subscription.user_principal_id} using bot {bot.id}")
                # Query exchange_credentials by principal_id
                marketplace_credentials = self.db.query(models.ExchangeCredentials).filter(
                    models.ExchangeCredentials.principal_id == subscription.user_principal_id,
                    models.ExchangeCredentials.exchange == bot.exchange_type,
                    models.ExchangeCredentials.is_testnet == is_testnet,
                    models.ExchangeCredentials.is_active == True
                ).first()
                
                if marketplace_credentials:
                    # Decrypt API keys
                    api_key = self.api_key_manager.decrypt_api_key(marketplace_credentials.api_key)
                    api_secret = self.api_key_manager.decrypt_api_key(marketplace_credentials.api_secret)
                    api_passphrase = self.api_key_manager.decrypt_api_key(marketplace_credentials.api_passphrase) if marketplace_credentials.api_passphrase else None
                    logger.debug(f"Using marketplace credentials for principal: {subscription.user_principal_id}")
                else:
                    logger.warning(f"No marketplace credentials found for principal {subscription.user_principal_id}, exchange: {bot.exchange_type.value}, testnet: {is_testnet}")
                    return {"status": "error", "message": "No marketplace credentials"}
            
            # Case 3: Regular studio user (legacy - fallback to exchange_credentials by user_id)
            elif subscription.user_id:
                logger.debug(f"Regular user {subscription.user_id} using bot {bot.id}")
                regular_credentials = self.db.query(models.ExchangeCredentials).filter(
                    models.ExchangeCredentials.user_id == subscription.user_id,
                    models.ExchangeCredentials.exchange == bot.exchange_type,
                    models.ExchangeCredentials.is_testnet == is_testnet,
                    models.ExchangeCredentials.is_active == True
                ).first()
                
                if regular_credentials:
                    # Decrypt API keys
                    api_key = self.api_key_manager.decrypt_api_key(regular_credentials.api_key)
                    api_secret = self.api_key_manager.decrypt_api_key(regular_credentials.api_secret)
                    api_passphrase = self.api_key_manager.decrypt_api_key(regular_credentials.api_passphrase) if regular_credentials.api_passphrase else None
                    logger.debug(f"Using regular user credentials for user: {subscription.user_id}")
                else:
                    logger.warning(f"No credentials found for user {subscription.user_id}, exchange: {bot.exchange_type.value}, testnet: {is_testnet}")
                    return {"status": "error", "message": "No user credentials"}
            else:
                logger.error(f"Cannot determine credentials source for subscription {subscription.id}")
                return {"status": "error", "message": "Invalid subscription configuration"}
            
            # Get exchange client with credentials
            network_str = "TESTNET" if is_testnet else "MAINNET"
            exchange_client = self.get_exchange_client(
                exchange_type=bot.exchange_type.value,
                api_key=api_key,
                api_secret=api_secret,
                network=network_str,
                passphrase=api_passphrase or ""
            )
            
            if not exchange_client:
                return {"status": "error", "message": "Failed to create exchange client"}
            
            # Get position info from exchange
            symbol = transaction.symbol.replace('/', '')  # Normalize symbol
            positions = exchange_client.get_position_info(symbol=symbol)
            
            # Find matching position
            matching_position = None
            for position in positions:
                # Check if position matches our transaction
                if position.symbol == symbol and float(position.size) != 0:
                    matching_position = position
                    break
            
            if not matching_position:
                # Position is closed (no longer exists on exchange)
                logger.info(f"Position {transaction.id} ({transaction.symbol}) is closed on exchange")
                return self._handle_closed_position(transaction, exchange_client)
            
            # Position still open - update with real-time data
            return self._update_open_position(transaction, matching_position)
            
        except Exception as e:
            logger.error(f"Error syncing transaction {transaction.id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"status": "error", "message": str(e)}
    
    def _update_open_position(self, transaction: models.Transaction, position: FuturesPosition) -> Dict[str, Any]:
        """
        Update transaction with real-time position data from exchange
        """
        try:
            updated_fields = []
            
            # Get current market price
            current_price = float(position.mark_price)
            
            # Calculate unrealized P&L
            entry_price = float(transaction.entry_price)
            quantity = abs(float(position.size))
            position_side = transaction.position_side or position.side  # Use exchange's side
            
            if position_side == 'LONG':
                unrealized_pnl = (current_price - entry_price) * quantity
            else:  # SHORT
                unrealized_pnl = (entry_price - current_price) * quantity
            
            # Calculate percentage
            position_value = entry_price * quantity * transaction.leverage
            unrealized_pnl_pct = (unrealized_pnl / position_value * 100) if position_value > 0 else 0
            
            # Update transaction fields
            if transaction.last_updated_price != current_price:
                transaction.last_updated_price = current_price
                updated_fields.append('last_updated_price')
            
            if transaction.unrealized_pnl != unrealized_pnl:
                transaction.unrealized_pnl = unrealized_pnl
                updated_fields.append('unrealized_pnl')
            
            if transaction.pnl_percentage != unrealized_pnl_pct:
                transaction.pnl_percentage = unrealized_pnl_pct
                updated_fields.append('pnl_percentage')
            
            # Update leverage if different
            exchange_leverage = int(position.leverage) if hasattr(position, 'leverage') else transaction.leverage
            if transaction.leverage != exchange_leverage:
                transaction.leverage = exchange_leverage
                updated_fields.append('leverage')
            
            # Update liquidation price if available
            if hasattr(position, 'liquidation_price') and position.liquidation_price:
                liq_price = float(position.liquidation_price)
                # Store in transaction.reason as JSON metadata (if needed later)
                # For now, just log it
                logger.debug(f"Liquidation price for {transaction.symbol}: {liq_price}")
            
            # Update timestamp
            transaction.updated_at = datetime.utcnow()
            
            # Commit changes
            if updated_fields:
                self.db.commit()
                logger.info(f"✅ Updated transaction {transaction.id} ({transaction.symbol}): {', '.join(updated_fields)}")
                logger.info(f"   Current Price: ${current_price:.2f} | Unrealized P&L: ${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.2f}%)")
            
            return {
                "status": "success",
                "transaction_id": transaction.id,
                "updated_fields": updated_fields,
                "current_price": current_price,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct
            }
            
        except Exception as e:
            logger.error(f"Error updating open position {transaction.id}: {e}")
            self.db.rollback()
            return {"status": "error", "message": str(e)}
    
    def _handle_closed_position(self, transaction: models.Transaction, exchange_client) -> Dict[str, Any]:
        """
        Handle position that is closed on exchange but still marked as OPEN in database
        """
        try:
            # Try to get order details to determine exit reason
            order_id = transaction.order_id
            exit_reason = "UNKNOWN"
            exit_price = None
            exit_time = datetime.utcnow()
            
            # Try to fetch order history (if supported by exchange)
            try:
                # Note: This requires exchange-specific implementation
                # For now, we'll mark it as closed with unknown reason
                logger.info(f"Checking order history for {transaction.symbol} order_id: {order_id}")
                
                # Get current market price as best estimate for exit price
                account_info = exchange_client.get_account_info()
                # Find recent trades or use mark price
                exit_price = transaction.last_updated_price or transaction.entry_price
                
            except Exception as e:
                logger.warning(f"Could not fetch order details for {order_id}: {e}")
                exit_price = transaction.last_updated_price or transaction.entry_price
            
            # Calculate realized P&L
            entry_price = float(transaction.entry_price)
            quantity = float(transaction.quantity)
            position_side = transaction.position_side or 'LONG'
            
            if position_side == 'LONG':
                realized_pnl = (exit_price - entry_price) * quantity
            else:  # SHORT
                realized_pnl = (entry_price - exit_price) * quantity
            
            # Subtract fees (estimate 0.05% for taker)
            position_value = exit_price * quantity
            estimated_fees = position_value * 0.0005
            realized_pnl -= estimated_fees
            
            # Calculate percentage
            cost_basis = entry_price * quantity * transaction.leverage
            realized_pnl_pct = (realized_pnl / cost_basis * 100) if cost_basis > 0 else 0
            
            # Calculate trade duration
            entry_time = transaction.entry_time or transaction.created_at
            duration_minutes = int((exit_time - entry_time).total_seconds() / 60)
            
            # Determine exit reason (heuristic)
            if transaction.take_profit and exit_price >= transaction.take_profit * 0.99:  # Within 1% of TP
                exit_reason = "TP_HIT"
            elif transaction.stop_loss and exit_price <= transaction.stop_loss * 1.01:  # Within 1% of SL
                exit_reason = "SL_HIT"
            else:
                exit_reason = "MANUAL"  # Or market close
            
            # Update transaction
            transaction.status = 'CLOSED'
            transaction.exit_price = exit_price
            transaction.exit_time = exit_time
            transaction.exit_reason = exit_reason
            transaction.pnl_usd = realized_pnl
            transaction.realized_pnl = realized_pnl
            transaction.pnl_percentage = realized_pnl_pct
            transaction.is_winning = realized_pnl > 0
            transaction.fees_paid = estimated_fees
            transaction.trade_duration_minutes = duration_minutes
            transaction.unrealized_pnl = 0  # Clear unrealized P&L
            transaction.updated_at = exit_time
            
            self.db.commit()
            
            logger.info(f"✅ Closed transaction {transaction.id} ({transaction.symbol})")
            logger.info(f"   Exit: ${exit_price:.2f} | Reason: {exit_reason}")
            logger.info(f"   Realized P&L: ${realized_pnl:.2f} ({realized_pnl_pct:+.2f}%)")
            logger.info(f"   Duration: {duration_minutes} minutes")
            
            # 🧹 Cancel remaining SL/TP orders
            try:
                from services.order_cleanup_service import OrderCleanupService
                cleanup_service = OrderCleanupService(self.db)
                cleanup_result = cleanup_service.cancel_position_orders(
                    transaction=transaction,
                    exchange_client=exchange_client,
                    force_cancel_all=False  # Try specific orders first
                )
                
                if cleanup_result.get('success'):
                    logger.info(f"🧹 Cleanup: {cleanup_result['cancelled_count']} orders cancelled")
                else:
                    logger.warning(f"⚠️ Order cleanup had issues: {cleanup_result.get('error', 'Unknown')}")
            except Exception as e:
                logger.error(f"❌ Failed to cleanup orders: {e}")
                # Don't fail the transaction close if cleanup fails
            
            # Trigger performance metrics update
            try:
                from core.tasks import update_bot_performance_metrics
                if transaction.bot_id:
                    update_bot_performance_metrics.delay(transaction.bot_id)
            except Exception as e:
                logger.warning(f"Could not trigger performance update: {e}")
            
            return {
                "status": "closed",
                "transaction_id": transaction.id,
                "exit_price": exit_price,
                "exit_reason": exit_reason,
                "realized_pnl": realized_pnl,
                "realized_pnl_pct": realized_pnl_pct,
                "duration_minutes": duration_minutes
            }
            
        except Exception as e:
            logger.error(f"Error handling closed position {transaction.id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.db.rollback()
            return {"status": "error", "message": str(e)}
    
    def sync_all_open_positions(self) -> Dict[str, Any]:
        """
        Sync all open positions across all exchanges
        
        Returns summary statistics
        """
        try:
            # Get all open transactions
            open_transactions = self.db.query(models.Transaction).filter(
                models.Transaction.status == 'OPEN'
            ).all()
            
            if not open_transactions:
                logger.debug("No open transactions to sync")
                return {
                    "status": "success",
                    "total": 0,
                    "updated": 0,
                    "closed": 0,
                    "errors": 0
                }
            
            logger.info(f"📊 Syncing {len(open_transactions)} open positions...")
            
            # Sync each transaction
            results = {
                "total": len(open_transactions),
                "updated": 0,
                "closed": 0,
                "errors": 0,
                "details": []
            }
            
            for transaction in open_transactions:
                try:
                    result = self.sync_transaction_with_exchange(transaction)
                    
                    if result["status"] == "success":
                        results["updated"] += 1
                    elif result["status"] == "closed":
                        results["closed"] += 1
                    else:
                        results["errors"] += 1
                    
                    results["details"].append({
                        "transaction_id": transaction.id,
                        "symbol": transaction.symbol,
                        "result": result
                    })
                    
                except Exception as e:
                    logger.error(f"Error syncing transaction {transaction.id}: {e}")
                    results["errors"] += 1
                    results["details"].append({
                        "transaction_id": transaction.id,
                        "error": str(e)
                    })
            
            logger.info(f"✅ Sync complete: {results['updated']} updated, {results['closed']} closed, {results['errors']} errors")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in sync_all_open_positions: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "message": str(e)
            }

