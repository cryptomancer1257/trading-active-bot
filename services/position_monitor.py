#!/usr/bin/env python3
"""
Position Monitor Service
Monitors open positions, checks TP/SL, updates P&L, and triggers close events
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from binance.client import Client
from binance.exceptions import BinanceAPIException

from core import models, crud
from core.database import get_db

logger = logging.getLogger(__name__)


class PositionMonitor:
    """Monitor and manage open trading positions"""
    
    def __init__(self, db: Session, futures_client: Client):
        self.db = db
        self.futures_client = futures_client
    
    def get_open_transactions(self, bot_id: Optional[int] = None) -> List[models.Transaction]:
        """Get all open transactions, optionally filtered by bot_id"""
        query = self.db.query(models.Transaction).filter(
            models.Transaction.status == 'OPEN'
        )
        
        if bot_id:
            query = query.filter(models.Transaction.bot_id == bot_id)
        
        return query.all()
    
    def check_order_status_from_exchange(self, symbol: str, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Check order status from Binance Futures API
        Returns order info or None if not found
        """
        try:
            # Normalize symbol (remove '/' if present)
            normalized_symbol = symbol.replace('/', '')
            
            # Query order status
            order = self.futures_client.futures_get_order(
                symbol=normalized_symbol,
                orderId=int(order_id)
            )
            
            logger.info(f"Order status for {order_id}: {order.get('status')}")
            return order
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error checking order {order_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error checking order status for {order_id}: {e}")
            return None
    
    def get_current_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current position from Binance Futures
        Returns position info or None if no position
        """
        try:
            # Normalize symbol
            normalized_symbol = symbol.replace('/', '')
            
            # Get all positions
            positions = self.futures_client.futures_position_information(symbol=normalized_symbol)
            
            # Find non-zero position
            for position in positions:
                position_amt = float(position.get('positionAmt', 0))
                if position_amt != 0:
                    return position
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting position for {symbol}: {e}")
            return None
    
    def calculate_pnl(
        self,
        entry_price: float,
        current_price: float,
        quantity: float,
        position_side: str
    ) -> Dict[str, float]:
        """
        Calculate P&L for a position
        Returns dict with pnl_usd and pnl_percentage
        """
        if position_side == 'LONG':
            pnl_usd = (current_price - entry_price) * quantity
        else:  # SHORT
            pnl_usd = (entry_price - current_price) * quantity
        
        pnl_percentage = (pnl_usd / (entry_price * quantity)) * 100
        
        return {
            'pnl_usd': round(pnl_usd, 8),
            'pnl_percentage': round(pnl_percentage, 4)
        }
    
    def check_tp_sl_hit(
        self,
        transaction: models.Transaction,
        current_price: float
    ) -> Optional[str]:
        """
        Check if TP or SL has been hit
        Returns 'TP_HIT', 'SL_HIT', or None
        """
        position_side = transaction.position_side or 'LONG'
        
        if position_side == 'LONG':
            # Long position: TP above entry, SL below entry
            if transaction.take_profit and current_price >= transaction.take_profit:
                return 'TP_HIT'
            if transaction.stop_loss and current_price <= transaction.stop_loss:
                return 'SL_HIT'
        else:
            # Short position: TP below entry, SL above entry
            if transaction.take_profit and current_price <= transaction.take_profit:
                return 'TP_HIT'
            if transaction.stop_loss and current_price >= transaction.stop_loss:
                return 'SL_HIT'
        
        return None
    
    def update_transaction_on_close(
        self,
        transaction: models.Transaction,
        exit_price: float,
        exit_reason: str,
        current_time: datetime,
        exchange_client = None
    ):
        """
        Update transaction when position is closed
        Calculate final P&L and metrics
        Also cancels any remaining SL/TP orders
        """
        # Calculate P&L
        pnl_data = self.calculate_pnl(
            entry_price=float(transaction.entry_price),
            current_price=exit_price,
            quantity=float(transaction.quantity),
            position_side=transaction.position_side or 'LONG'
        )
        
        # Calculate trade duration
        entry_time = transaction.entry_time or transaction.created_at
        trade_duration = (current_time - entry_time).total_seconds() / 60
        
        # Calculate actual RR ratio
        risk = abs(float(transaction.entry_price) - float(transaction.stop_loss or transaction.entry_price))
        actual_gain = abs(exit_price - float(transaction.entry_price))
        actual_rr_ratio = (actual_gain / risk) if risk > 0 else 0
        
        # Update transaction
        transaction.status = 'CLOSED'
        transaction.exit_price = Decimal(str(exit_price))
        transaction.exit_time = current_time
        transaction.exit_reason = exit_reason
        transaction.pnl_usd = Decimal(str(pnl_data['pnl_usd']))
        transaction.pnl_percentage = Decimal(str(pnl_data['pnl_percentage']))
        transaction.is_winning = pnl_data['pnl_usd'] > 0
        transaction.realized_pnl = Decimal(str(pnl_data['pnl_usd']))  # Same as pnl_usd for closed
        transaction.trade_duration_minutes = int(trade_duration)
        transaction.actual_rr_ratio = Decimal(str(round(actual_rr_ratio, 4)))
        transaction.updated_at = current_time
        
        self.db.commit()
        
        logger.info(f"✅ Transaction {transaction.id} closed: {exit_reason}, P&L: ${pnl_data['pnl_usd']:.2f}")
        
        # 🧹 Cancel remaining SL/TP orders
        if exchange_client:
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
        else:
            logger.warning(f"⚠️ No exchange_client provided, skipping order cleanup")
        
        return transaction
    
    def update_unrealized_pnl(
        self,
        transaction: models.Transaction,
        current_price: float
    ):
        """
        Update unrealized P&L for open position
        """
        pnl_data = self.calculate_pnl(
            entry_price=float(transaction.entry_price),
            current_price=current_price,
            quantity=float(transaction.quantity),
            position_side=transaction.position_side or 'LONG'
        )
        
        transaction.unrealized_pnl = Decimal(str(pnl_data['pnl_usd']))
        transaction.last_updated_price = Decimal(str(current_price))
        transaction.updated_at = datetime.now()
        
        self.db.commit()
    
    def monitor_open_positions(self, bot_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Main monitoring function: Check all open positions
        - Update unrealized P&L
        - Check if TP/SL hit
        - Close positions if needed
        
        Returns summary of monitoring results
        """
        results = {
            'total_checked': 0,
            'positions_closed': 0,
            'positions_updated': 0,
            'errors': []
        }
        
        try:
            open_transactions = self.get_open_transactions(bot_id)
            results['total_checked'] = len(open_transactions)
            
            logger.info(f"📊 Monitoring {len(open_transactions)} open positions...")
            
            for transaction in open_transactions:
                try:
                    # Get current position from exchange
                    position = self.get_current_position(transaction.symbol)
                    
                    if not position:
                        # Position no longer exists on exchange
                        logger.warning(f"Position for transaction {transaction.id} not found on exchange")
                        # Could be closed manually or by exchange
                        # Check order status to determine
                        order_info = self.check_order_status_from_exchange(
                            transaction.symbol,
                            str(transaction.order_id)
                        )
                        
                        if order_info and order_info.get('status') in ['FILLED', 'CLOSED']:
                            # Position was closed
                            self.update_transaction_on_close(
                                transaction=transaction,
                                exit_price=float(order_info.get('avgPrice', transaction.entry_price)),
                                exit_reason='MANUAL',  # Assume manual close
                                current_time=datetime.now(),
                                exchange_client=self.futures_client
                            )
                            results['positions_closed'] += 1
                        continue
                    
                    # Get current market price
                    current_price = float(position.get('markPrice', 0))
                    
                    if current_price <= 0:
                        logger.warning(f"Invalid price for {transaction.symbol}")
                        continue
                    
                    # Check if TP/SL hit
                    hit_reason = self.check_tp_sl_hit(transaction, current_price)
                    
                    if hit_reason:
                        # TP or SL hit - close position
                        logger.info(f"🎯 {hit_reason} for transaction {transaction.id}")
                        self.update_transaction_on_close(
                            transaction=transaction,
                            exit_price=current_price,
                            exit_reason=hit_reason,
                            current_time=datetime.now(),
                            exchange_client=self.futures_client
                        )
                        results['positions_closed'] += 1
                        
                        # Trigger performance update (async)
                        from core.tasks import update_bot_performance_metrics
                        update_bot_performance_metrics.delay(transaction.bot_id)
                        
                    else:
                        # Update unrealized P&L
                        self.update_unrealized_pnl(transaction, current_price)
                        results['positions_updated'] += 1
                
                except Exception as e:
                    error_msg = f"Error monitoring transaction {transaction.id}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            logger.info(f"✅ Monitoring complete: {results['positions_closed']} closed, {results['positions_updated']} updated")
            
        except Exception as e:
            error_msg = f"Error in monitor_open_positions: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results


def monitor_positions_for_bot(bot_id: int, futures_client: Client) -> Dict[str, Any]:
    """
    Convenience function to monitor positions for a specific bot
    """
    db = next(get_db())
    try:
        monitor = PositionMonitor(db, futures_client)
        return monitor.monitor_open_positions(bot_id=bot_id)
    finally:
        db.close()


def monitor_all_positions(futures_client: Client) -> Dict[str, Any]:
    """
    Convenience function to monitor all open positions
    """
    db = next(get_db())
    try:
        monitor = PositionMonitor(db, futures_client)
        return monitor.monitor_open_positions()
    finally:
        db.close()

