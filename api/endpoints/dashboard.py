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
        
        # 1. Get recent trades from performance_logs
        recent_trades = db.query(models.PerformanceLog).join(
            models.Subscription,
            models.PerformanceLog.subscription_id == models.Subscription.id
        ).filter(
            models.Subscription.user_id == current_user.id,
            models.PerformanceLog.timestamp >= cutoff_time
        ).order_by(desc(models.PerformanceLog.timestamp)).limit(limit).all()
        
        for trade in recent_trades:
            # Get subscription and bot info
            subscription = get_subscription_by_id(db, trade.subscription_id)
            if not subscription or not subscription.bot:
                continue
            
            # Parse signal data
            signal_data = trade.signal_data or {}
            details = signal_data.get('details', '')
            
            # Determine if profitable
            pnl = float(trade.balance or 0) - float(trade.price or 0)
            is_profit = pnl > 0
            
            activities.append({
                'id': f"trade_{trade.id}",
                'type': 'TRADE',
                'timestamp': trade.timestamp.isoformat() if trade.timestamp else None,
                'bot_name': subscription.bot.name,
                'bot_id': subscription.bot.id,
                'subscription_id': subscription.id,
                'action': trade.action,
                'symbol': subscription.trading_pair,
                'price': float(trade.price) if trade.price else None,
                'quantity': float(trade.quantity) if trade.quantity else None,
                'balance': float(trade.balance) if trade.balance else None,
                'pnl': pnl,
                'is_profit': is_profit,
                'exchange': subscription.bot.exchange_type,
                'details': details[:100] if details else None
            })
        
        # 2. Get risk management events (from bot actions with risk alerts)
        # We can check for cooldown events or daily loss limit hits
        risk_events = db.query(models.Subscription).filter(
            models.Subscription.user_id == current_user.id,
            or_(
                models.Subscription.cooldown_until.isnot(None),
                models.Subscription.daily_loss_amount > 0
            )
        ).all()
        
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
        active_subs = db.query(models.Subscription).filter(
            models.Subscription.user_id == current_user.id,
            models.Subscription.status == 'ACTIVE'
        ).all()
        
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """
    Get summary statistics for dashboard
    """
    try:
        # Active subscriptions
        active_subs = db.query(models.Subscription).filter(
            models.Subscription.user_id == current_user.id,
            models.Subscription.status == 'ACTIVE'
        ).count()
        
        # Trades today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        trades_today = db.query(models.PerformanceLog).join(
            models.Subscription
        ).filter(
            models.Subscription.user_id == current_user.id,
            models.PerformanceLog.timestamp >= today_start
        ).count()
        
        # Total P&L (rough estimate from recent trades)
        recent_trades = db.query(models.PerformanceLog).join(
            models.Subscription
        ).filter(
            models.Subscription.user_id == current_user.id,
            models.PerformanceLog.timestamp >= today_start
        ).all()
        
        total_pnl = sum(
            float(trade.balance or 0) - float(trade.price or 0)
            for trade in recent_trades
        )
        
        # Win rate (today)
        winning_trades = sum(1 for trade in recent_trades 
                           if (float(trade.balance or 0) - float(trade.price or 0)) > 0)
        win_rate = (winning_trades / len(recent_trades) * 100) if recent_trades else 0
        
        return {
            'active_subscriptions': active_subs,
            'trades_today': trades_today,
            'total_pnl_today': round(total_pnl, 2),
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

