"""
Dashboard API endpoints for activity feed and statistics
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from core.database import get_db
from core import models, schemas, security
from core.crud import get_subscription_by_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Dashboard"])


@router.get("/activity")
async def get_dashboard_activity(
    limit: int = Query(default=20, le=100),
    hours: int = Query(default=24, le=168),  # Max 7 days
    network_filter: Optional[str] = Query(None, description="Filter by network: 'mainnet' or 'testnet'"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """
    Get recent activity feed for dashboard
    Returns: trades, risk alerts, bot events
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        activities = []
        
        # 1. Get recent trades from transactions table
        query = db.query(models.Transaction).join(
            models.Subscription,
            models.Transaction.subscription_id == models.Subscription.id
        ).filter(
            models.Subscription.user_id == current_user.id,
            models.Transaction.created_at >= cutoff_time
        )
        
        # Apply network filter
        if network_filter == "mainnet":
            query = query.filter(models.Subscription.is_testnet == False)
        elif network_filter == "testnet":
            query = query.filter(models.Subscription.is_testnet == True)
        
        recent_transactions = query.order_by(desc(models.Transaction.created_at)).limit(limit).all()
        
        for tx in recent_transactions:
            # Get subscription and bot info
            subscription = get_subscription_by_id(db, tx.subscription_id)
            if not subscription or not subscription.bot:
                continue
            
            # Calculate P&L
            if tx.status == 'CLOSED':
                pnl = float(tx.realized_pnl or 0)
            else:  # OPEN
                pnl = float(tx.unrealized_pnl or 0)
            
            is_profit = pnl > 0
            
            # Format details
            position_info = f"{tx.position_side or 'SPOT'}" if tx.position_side else ""
            details = f"{tx.status} - {tx.action} {tx.symbol}"
            if position_info:
                details += f" ({position_info})"
            if tx.status == 'CLOSED':
                details += f" | Entry: ${float(tx.entry_price or 0):.2f} | Exit: ${float(tx.exit_price or 0):.2f}"
            else:
                current_price = tx.last_updated_price or tx.entry_price
                details += f" | Entry: ${float(tx.entry_price or 0):.2f} | Current: ${float(current_price or 0):.2f}"
            
            # Debug timestamp
            timestamp_str = tx.created_at.isoformat() if tx.created_at else None
            logger.info(f"Dashboard activity timestamp debug: tx_id={tx.id}, created_at={tx.created_at}, isoformat={timestamp_str}")
            
            activities.append({
                'id': f"trade_{tx.id}",
                'type': 'TRADE',
                'timestamp': timestamp_str,
                'bot_name': subscription.bot.name,
                'bot_id': subscription.bot.id,
                'subscription_id': subscription.id,
                'action': tx.action,  # BUY/SELL
                'symbol': tx.symbol,
                'price': float(tx.entry_price) if tx.entry_price else None,
                'quantity': float(tx.quantity) if tx.quantity else None,
                'stop_loss': float(tx.stop_loss) if tx.stop_loss else None,
                'take_profit': float(tx.take_profit) if tx.take_profit else None,
                'pnl': pnl,
                'is_profit': is_profit,
                'status': tx.status,
                'exchange': subscription.bot.exchange_type,
                'details': details
            })
        
        # 2. Get risk management events (from bot actions with risk alerts)
        # We can check for cooldown events or daily loss limit hits
        risk_query = db.query(models.Subscription).filter(
            models.Subscription.user_id == current_user.id,
            or_(
                models.Subscription.cooldown_until.isnot(None),
                models.Subscription.daily_loss_amount > 0
            )
        )
        
        # Apply network filter
        if network_filter == "mainnet":
            risk_query = risk_query.filter(models.Subscription.is_testnet == False)
        elif network_filter == "testnet":
            risk_query = risk_query.filter(models.Subscription.is_testnet == True)
        
        risk_events = risk_query.all()
        
        for sub in risk_events:
            if sub.cooldown_until and sub.cooldown_until > datetime.utcnow():
                activities.append({
                    'id': f"risk_cooldown_{sub.id}",
                    'type': 'RISK_ALERT',
                    'timestamp': sub.cooldown_until.isoformat(),
                    'bot_name': sub.bot.name if sub.bot else 'Unknown',
                    'bot_id': sub.bot.id if sub.bot else None,
                    'subscription_id': sub.id,
                    'alert_type': 'COOLDOWN',
                    'message': f"Trading paused until {sub.cooldown_until.strftime('%H:%M UTC')}",
                    'severity': 'WARNING'
                })
            
            if sub.daily_loss_amount and float(sub.daily_loss_amount) > 0:
                # Get risk config to check limit
                risk_config = sub.bot.risk_config if sub.bot else None
                if risk_config and 'daily_loss_limit_percent' in risk_config:
                    limit_pct = risk_config['daily_loss_limit_percent']
                    current_loss = float(sub.daily_loss_amount)
                    activities.append({
                        'id': f"risk_loss_{sub.id}",
                        'type': 'RISK_ALERT',
                        'timestamp': (sub.last_loss_reset_date or datetime.utcnow()).isoformat(),
                        'bot_name': sub.bot.name if sub.bot else 'Unknown',
                        'bot_id': sub.bot.id if sub.bot else None,
                        'subscription_id': sub.id,
                        'alert_type': 'DAILY_LOSS',
                        'message': f"Daily loss: ${current_loss:.2f} (Limit: {limit_pct}%)",
                        'severity': 'INFO' if current_loss < (limit_pct * 10) else 'WARNING'
                    })
        
        # 3. Get active subscriptions status
        active_subs_query = db.query(models.Subscription).filter(
            models.Subscription.user_id == current_user.id,
            models.Subscription.status == 'ACTIVE'
        )
        
        # Apply network filter
        if network_filter == "mainnet":
            active_subs_query = active_subs_query.filter(models.Subscription.is_testnet == False)
        elif network_filter == "testnet":
            active_subs_query = active_subs_query.filter(models.Subscription.is_testnet == True)
        
        active_subs = active_subs_query.all()
        
        for sub in active_subs[:5]:  # Top 5 most recent
            if sub.last_run_at and sub.last_run_at >= cutoff_time:
                activities.append({
                    'id': f"bot_run_{sub.id}_{sub.last_run_at.timestamp()}",
                    'type': 'BOT_EXECUTION',
                    'timestamp': sub.last_run_at.isoformat(),
                    'bot_name': sub.bot.name if sub.bot else 'Unknown',
                    'bot_id': sub.bot.id if sub.bot else None,
                    'subscription_id': sub.id,
                    'message': 'Bot execution completed',
                    'next_run': sub.next_run_at.isoformat() if sub.next_run_at else None
                })
        
        # Sort all activities by timestamp (most recent first)
        activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return {
            'activities': activities[:limit],
            'total': len(activities),
            'period_hours': hours
        }
        
    except Exception as e:
        logger.error(f"Error fetching dashboard activity: {e}")
        return {
            'activities': [],
            'total': 0,
            'period_hours': hours,
            'error': str(e)
        }


@router.get("/stats")
async def get_dashboard_stats(
    network_filter: Optional[str] = Query(None, description="Filter by network: 'mainnet' or 'testnet'"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """
    Get summary statistics for dashboard
    """
    try:
        # Active subscriptions
        active_subs_query = db.query(models.Subscription).filter(
            models.Subscription.user_id == current_user.id,
            models.Subscription.status == 'ACTIVE'
        )
        
        # Apply network filter
        if network_filter == "mainnet":
            active_subs_query = active_subs_query.filter(models.Subscription.is_testnet == False)
        elif network_filter == "testnet":
            active_subs_query = active_subs_query.filter(models.Subscription.is_testnet == True)
        
        active_subs = active_subs_query.count()
        
        # Trades today - from Transaction table
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get today's transactions
        today_tx_query = db.query(models.Transaction).join(
            models.Subscription
        ).filter(
            models.Subscription.user_id == current_user.id,
            models.Transaction.created_at >= today_start
        )
        
        # Apply network filter
        if network_filter == "mainnet":
            today_tx_query = today_tx_query.filter(models.Subscription.is_testnet == False)
        elif network_filter == "testnet":
            today_tx_query = today_tx_query.filter(models.Subscription.is_testnet == True)
        
        today_transactions = today_tx_query.all()
        
        trades_today = len(today_transactions)
        
        # Calculate Today's P&L from transactions
        total_realized_pnl = 0.0
        total_unrealized_pnl = 0.0
        winning_trades = 0
        closed_trades = 0
        
        for tx in today_transactions:
            if tx.status == 'CLOSED':
                closed_trades += 1
                realized = float(tx.realized_pnl or 0)
                total_realized_pnl += realized
                if realized > 0:
                    winning_trades += 1
            else:  # OPEN
                unrealized = float(tx.unrealized_pnl or 0)
                total_unrealized_pnl += unrealized
        
        # Total P&L = Realized + Unrealized
        total_pnl_today = total_realized_pnl + total_unrealized_pnl
        
        # Win rate (only from closed trades)
        win_rate = (winning_trades / closed_trades * 100) if closed_trades > 0 else 0
        
        return {
            'active_subscriptions': active_subs,
            'trades_today': trades_today,
            'total_pnl_today': round(total_pnl_today, 2),
            'win_rate_today': round(win_rate, 1),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        return {
            'active_subscriptions': 0,
            'trades_today': 0,
            'total_pnl_today': 0,
            'win_rate_today': 0,
            'error': str(e)
        }

