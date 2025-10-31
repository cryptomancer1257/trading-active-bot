#!/usr/bin/env python3
"""
Transaction Service
Handles transaction queries and data formatting, including historical learning
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from core.database import get_db
from core import models

logger = logging.getLogger(__name__)


class TransactionService:
    """Service for transaction-related operations"""
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize Transaction Service
        
        Args:
            db: SQLAlchemy Session instance (optional, will create if not provided)
        """
        self.db = db
    
    def get_recent_transactions_for_learning(
        self, 
        bot_id: int, 
        limit: int = 25,
        include_failed: bool = True,
        mode: str = 'recent'
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent transactions for LLM learning
        
        Args:
            bot_id: Bot ID
            limit: Number of transactions (10, 25, or 50)
            include_failed: Include losing trades
            mode: 'recent', 'best_performance', or 'mixed'
        
        Returns:
            List of transaction summaries formatted for LLM
        """
        try:
            # Validate limit
            if limit not in [10, 25, 50]:
                logger.warning(f"Invalid limit {limit}, using default 25")
                limit = 25
            
            # Get or create db session
            db = self.db
            if db is None:
                db = next(get_db())
            
            # Base query using SQLAlchemy ORM
            query = db.query(models.Transaction).join(
                models.Subscription,
                models.Transaction.subscription_id == models.Subscription.id
            ).filter(
                models.Subscription.bot_id == bot_id,
                models.Transaction.exit_price.isnot(None),  # Only closed trades
                models.Transaction.status == 'CLOSED'
            )
            
            # Filter by performance if needed
            if not include_failed:
                query = query.filter(models.Transaction.profit_loss > 0)
            
            # Order by mode
            if mode == 'recent':
                query = query.order_by(desc(models.Transaction.exit_time))
            elif mode == 'best_performance':
                query = query.order_by(desc(models.Transaction.profit_loss_percentage))
            elif mode == 'mixed':
                # For mixed mode, get recent and best separately then combine
                # Simplified: just use recent ordering for now
                logger.info(f"Mixed mode - using recent ordering (simplified)")
                query = query.order_by(desc(models.Transaction.exit_time))
            else:
                logger.warning(f"Invalid mode {mode}, using 'recent'")
                query = query.order_by(desc(models.Transaction.exit_time))
            
            # Apply limit and fetch
            transactions = query.limit(limit).all()
            
            # Format for LLM
            return self._format_transactions_for_llm(transactions)
        
        except Exception as e:
            logger.error(f"Error fetching transactions for learning (bot_id={bot_id}): {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _format_transactions_for_llm(self, transactions) -> List[Dict]:
        """
        Format transactions into LLM-friendly structure
        
        Args:
            transactions: SQLAlchemy Transaction model objects
            
        Returns:
            Formatted transactions with relevant fields
        """
        formatted = []
        
        for t in transactions:
            # Calculate duration
            duration = None
            if hasattr(t, 'exit_time') and hasattr(t, 'entry_time') and t.exit_time and t.entry_time:
                try:
                    delta = t.exit_time - t.entry_time
                    hours = delta.total_seconds() / 3600
                    if hours < 1:
                        duration = f"{delta.total_seconds() / 60:.0f}m"
                    else:
                        duration = f"{hours:.1f}h"
                except Exception as e:
                    logger.debug(f"Error calculating duration: {e}")
                    duration = "N/A"
            
            # Determine result (use pnl_percentage or realized_pnl)
            profit_loss_pct = float(t.pnl_percentage) if t.pnl_percentage else 0.0
            profit_loss_usd = float(t.realized_pnl) if t.realized_pnl else (float(t.pnl_usd) if t.pnl_usd else 0.0)
            result = 'WIN' if profit_loss_pct > 0 else 'LOSS' if profit_loss_pct < 0 else 'BREAKEVEN'
            
            # Format indicators_used (strategy_used field in model)
            indicators_used = []
            if t.strategy_used:
                if isinstance(t.strategy_used, list):
                    indicators_used = t.strategy_used
                elif isinstance(t.strategy_used, str):
                    # Try to parse if it's a comma-separated string
                    indicators_used = [ind.strip() for ind in t.strategy_used.split(',') if ind.strip()]
            
            formatted_transaction = {
                'trade_id': t.id,
                'symbol': t.symbol,
                'side': t.action,  # Use 'action' field from model (BUY/SELL)
                'entry_price': float(t.entry_price) if t.entry_price else None,
                'exit_price': float(t.exit_price) if t.exit_price else None,
                'profit_loss_pct': profit_loss_pct,
                'profit_loss': profit_loss_usd,
                'result': result,
                'strategy': t.strategy_used if t.strategy_used else 'N/A',
                'timeframe': 'N/A',  # Not stored in Transaction model
                'duration': duration,
                'stop_loss': float(t.stop_loss) if t.stop_loss else None,
                'take_profit': float(t.take_profit) if t.take_profit else None,
                'indicators_used': indicators_used,
                'market_conditions': None  # Not stored in Transaction model
            }
            
            formatted.append(formatted_transaction)
        
        return formatted
    
    def get_transaction_summary_stats(self, bot_id: int, limit: int = 25) -> Dict[str, Any]:
        """
        Get summary statistics for recent transactions
        
        Args:
            bot_id: Bot ID
            limit: Number of recent transactions to analyze
            
        Returns:
            Dict with win rate, avg profit, avg loss, etc.
        """
        try:
            transactions = self.get_recent_transactions_for_learning(
                bot_id=bot_id,
                limit=limit,
                include_failed=True,
                mode='recent'
            )
            
            if not transactions:
                return {
                    'total_trades': 0,
                    'win_count': 0,
                    'loss_count': 0,
                    'win_rate': 0.0,
                    'avg_win': 0.0,
                    'avg_loss': 0.0,
                    'risk_reward_ratio': 0.0,
                    'total_pnl': 0.0
                }
            
            total = len(transactions)
            wins = [t for t in transactions if t['result'] == 'WIN']
            losses = [t for t in transactions if t['result'] == 'LOSS']
            
            win_count = len(wins)
            loss_count = len(losses)
            win_rate = (win_count / total * 100) if total > 0 else 0.0
            
            avg_win = sum(t['profit_loss_pct'] for t in wins) / win_count if win_count > 0 else 0.0
            avg_loss = sum(t['profit_loss_pct'] for t in losses) / loss_count if loss_count > 0 else 0.0
            
            risk_reward = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0
            
            total_pnl = sum(t['profit_loss'] for t in transactions)
            
            return {
                'total_trades': total,
                'win_count': win_count,
                'loss_count': loss_count,
                'win_rate': round(win_rate, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'risk_reward_ratio': round(risk_reward, 2),
                'total_pnl': round(total_pnl, 2)
            }
        
        except Exception as e:
            logger.error(f"Error calculating transaction stats (bot_id={bot_id}): {e}")
            return {
                'total_trades': 0,
                'win_count': 0,
                'loss_count': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'risk_reward_ratio': 0.0,
                'total_pnl': 0.0
            }

