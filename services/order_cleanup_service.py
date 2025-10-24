"""
Order Cleanup Service
Handles cancellation of SL/TP orders when positions are closed
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from core import models

logger = logging.getLogger(__name__)


class OrderCleanupService:
    """Service to cleanup SL/TP orders when position closes"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def cancel_position_orders(
        self, 
        transaction: models.Transaction, 
        exchange_client,
        force_cancel_all: bool = False
    ) -> Dict[str, Any]:
        """
        Cancel all SL/TP orders associated with a position
        
        Args:
            transaction: Transaction record
            exchange_client: Exchange client (Bybit, Binance, etc.)
            force_cancel_all: If True, cancel ALL orders for symbol (fallback)
        
        Returns:
            Dict with cancellation results
        """
        symbol = transaction.symbol
        cancelled_orders = []
        failed_orders = []
        
        logger.info(f"🧹 Starting order cleanup for transaction {transaction.id} ({symbol})")
        
        try:
            # Method 1: Cancel specific orders by ID (preferred)
            if transaction.sl_order_ids or transaction.tp_order_ids:
                order_ids = []
                
                # Collect all order IDs
                if transaction.sl_order_ids:
                    if isinstance(transaction.sl_order_ids, list):
                        order_ids.extend(transaction.sl_order_ids)
                    else:
                        order_ids.append(transaction.sl_order_ids)
                
                if transaction.tp_order_ids:
                    if isinstance(transaction.tp_order_ids, list):
                        order_ids.extend(transaction.tp_order_ids)
                    else:
                        order_ids.append(transaction.tp_order_ids)
                
                logger.info(f"📋 Found {len(order_ids)} order IDs to cancel: {order_ids}")
                
                # Cancel each order
                for order_id in order_ids:
                    if not order_id or order_id == 'N/A' or order_id == '':
                        continue
                    
                    try:
                        result = exchange_client.cancel_order(symbol, str(order_id))
                        cancelled_orders.append({
                            'order_id': order_id,
                            'status': 'cancelled',
                            'result': result
                        })
                        logger.info(f"   ✅ Cancelled order: {order_id}")
                    except Exception as e:
                        error_msg = str(e)
                        failed_orders.append({
                            'order_id': order_id,
                            'error': error_msg
                        })
                        # Don't fail if order already cancelled or doesn't exist
                        if 'not found' in error_msg.lower() or 'does not exist' in error_msg.lower():
                            logger.info(f"   ℹ️ Order {order_id} already cancelled or doesn't exist")
                        else:
                            logger.warning(f"   ⚠️ Failed to cancel order {order_id}: {e}")
            
            # Method 2: Fallback - Cancel all SL/TP orders for symbol
            elif force_cancel_all or (not transaction.sl_order_ids and not transaction.tp_order_ids):
                logger.info(f"📋 No order IDs found, using fallback method (cancel all SL/TP for {symbol})")
                
                try:
                    # Get all open orders for symbol
                    open_orders = exchange_client.get_open_orders(symbol)
                    
                    for order in open_orders:
                        order_type = order.get('type', order.get('orderType', ''))
                        
                        # Only cancel SL/TP orders
                        if order_type in ['STOP_MARKET', 'TAKE_PROFIT_MARKET', 'STOP', 'TAKE_PROFIT', 'Stop', 'TakeProfit']:
                            order_id = str(order.get('orderId', order.get('order_id', order.get('orderLinkId', ''))))
                            
                            if not order_id:
                                continue
                            
                            try:
                                result = exchange_client.cancel_order(symbol, order_id)
                                cancelled_orders.append({
                                    'order_id': order_id,
                                    'type': order_type,
                                    'status': 'cancelled',
                                    'result': result
                                })
                                logger.info(f"   ✅ Cancelled {order_type} order: {order_id}")
                            except Exception as e:
                                failed_orders.append({
                                    'order_id': order_id,
                                    'type': order_type,
                                    'error': str(e)
                                })
                                logger.warning(f"   ⚠️ Failed to cancel {order_type} {order_id}: {e}")
                
                except Exception as e:
                    logger.error(f"❌ Failed to get open orders for {symbol}: {e}")
                    failed_orders.append({
                        'error': f"Failed to get open orders: {str(e)}"
                    })
            
            # Summary
            total_cancelled = len(cancelled_orders)
            total_failed = len(failed_orders)
            
            if total_cancelled > 0:
                logger.info(f"✅ Order cleanup complete: {total_cancelled} cancelled, {total_failed} failed")
            elif total_failed > 0:
                logger.warning(f"⚠️ Order cleanup partial: {total_cancelled} cancelled, {total_failed} failed")
            else:
                logger.info(f"ℹ️ No orders to cancel for {symbol}")
            
            return {
                'success': total_cancelled > 0 or total_failed == 0,
                'cancelled_count': total_cancelled,
                'failed_count': total_failed,
                'cancelled_orders': cancelled_orders,
                'failed_orders': failed_orders
            }
        
        except Exception as e:
            logger.error(f"❌ Critical error in order cleanup: {e}")
            return {
                'success': False,
                'error': str(e),
                'cancelled_count': len(cancelled_orders),
                'failed_count': len(failed_orders)
            }
    
    def cleanup_orphaned_orders(self, exchange_name: str = None) -> Dict[str, Any]:
        """
        Periodic cleanup: Find closed positions with potentially orphaned orders
        
        Args:
            exchange_name: Optional filter by exchange
        
        Returns:
            Summary of cleanup results
        """
        logger.info("🔍 Starting orphaned order cleanup scan...")
        
        try:
            # Find recently closed transactions (last 24 hours) that might have orphaned orders
            from datetime import datetime, timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            query = self.db.query(models.Transaction).filter(
                models.Transaction.status == 'CLOSED',
                models.Transaction.exit_time >= cutoff_time
            )
            
            # Filter by exchange if specified
            if exchange_name:
                # Get bots for this exchange
                bot_ids = self.db.query(models.Bot.id).filter(
                    models.Bot.exchange_type == exchange_name
                ).all()
                bot_ids = [b[0] for b in bot_ids]
                query = query.filter(models.Transaction.bot_id.in_(bot_ids))
            
            closed_transactions = query.all()
            
            logger.info(f"📊 Found {len(closed_transactions)} recently closed transactions to check")
            
            results = {
                'total_checked': len(closed_transactions),
                'orders_cancelled': 0,
                'errors': []
            }
            
            # For each closed transaction, check if it has order IDs that need cleanup
            for transaction in closed_transactions:
                if transaction.sl_order_ids or transaction.tp_order_ids:
                    # This transaction has order IDs - might need cleanup
                    # Note: In production, you'd need to get the appropriate exchange client
                    logger.info(f"   Transaction {transaction.id} has order IDs but position is closed")
                    # TODO: Implement actual cleanup with exchange client
            
            return results
        
        except Exception as e:
            logger.error(f"❌ Error in orphaned order cleanup: {e}")
            return {
                'success': False,
                'error': str(e)
            }

