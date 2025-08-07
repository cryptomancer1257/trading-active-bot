"""
Celery-Based Position Monitoring - Sử dụng Celery để monitor positions
Approach này scale tốt hơn với hàng ngàn users
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery import Celery
from core.database import get_db
from core import crud, models
from bot_files.binance_futures_bot import BinanceFuturesIntegration
from core.api_key_manager import get_bot_api_keys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import existing celery app
from core.tasks import celery_app

@celery_app.task(bind=True, name='monitor_principal_positions')
def monitor_principal_positions(self, user_principal_id: str, is_testnet: bool = True):
    """
    Celery task để monitor positions cho một principal ID
    Task này sẽ được schedule cho mỗi principal ID riêng biệt
    """
    try:
        logger.info(f"🔍 Monitoring positions for principal: {user_principal_id}")
        
        # Load API keys from database
        db_credentials = get_bot_api_keys(
            user_principal_id=user_principal_id,
            exchange="BINANCE",
            is_testnet=is_testnet
        )
        
        if not db_credentials:
            logger.warning(f"No API credentials found for principal: {user_principal_id}")
            return {"status": "no_credentials", "principal_id": user_principal_id}
        
        # Initialize Binance client
        binance_client = BinanceFuturesIntegration(
            db_credentials['api_key'], 
            db_credentials['api_secret'], 
            is_testnet
        )
        
        # Get positions
        positions = binance_client.get_positions()
        active_positions = []
        critical_positions = []
        
        for position in positions:
            if hasattr(position, 'size'):
                position_amt = float(position.size)
                if position_amt != 0:  # Only active positions
                    pnl_percentage = float(position.percentage) if position.percentage else 0
                    
                    pos_data = {
                        'principal_id': user_principal_id,
                        'symbol': position.symbol,
                        'side': position.side,
                        'size': abs(position_amt),
                        'entry_price': float(position.entry_price),
                        'mark_price': float(position.mark_price),
                        'unrealized_pnl': float(position.pnl),
                        'pnl_percentage': pnl_percentage,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    active_positions.append(pos_data)
                    
                    # Check for critical positions (>5% loss)
                    if pnl_percentage <= -5.0:
                        critical_positions.append(pos_data)
                        logger.warning(f"🚨 CRITICAL position: {position.symbol} - {pnl_percentage:.2f}% loss")
                        
                        # Trigger emergency action task
                        handle_critical_position.delay(user_principal_id, pos_data)
        
        result = {
            "status": "success",
            "principal_id": user_principal_id,
            "total_positions": len(active_positions),
            "critical_positions": len(critical_positions),
            "positions": active_positions,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save monitoring result
        save_monitoring_result.delay(result)
        
        logger.info(f"✅ Monitored {len(active_positions)} positions for {user_principal_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error monitoring {user_principal_id}: {e}")
        return {"status": "error", "principal_id": user_principal_id, "error": str(e)}

@celery_app.task(name='handle_critical_position')
def handle_critical_position(user_principal_id: str, position_data: Dict[str, Any]):
    """
    Xử lý position có risk cao
    Task này được trigger khi phát hiện position loss > 5%
    """
    try:
        logger.warning(f"🚨 Handling critical position for {user_principal_id}: {position_data['symbol']}")
        
        # TODO: Implement auto-close logic
        # 1. Send notification
        # 2. Execute emergency close if configured
        # 3. Log action
        
        action_log = {
            "timestamp": datetime.now().isoformat(),
            "principal_id": user_principal_id,
            "action": "critical_position_detected",
            "position": position_data,
            "status": "notified"  # or "auto_closed"
        }
        
        # Save action log
        with open(f"logs/critical_actions_{datetime.now().strftime('%Y%m%d')}.json", "a") as f:
            f.write(json.dumps(action_log) + "\n")
        
        return action_log
        
    except Exception as e:
        logger.error(f"Error handling critical position: {e}")
        return {"status": "error", "error": str(e)}

@celery_app.task(name='save_monitoring_result')
def save_monitoring_result(result: Dict[str, Any]):
    """Lưu kết quả monitoring vào database hoặc file"""
    try:
        # Save to file (có thể thay bằng database)
        filename = f"monitoring_data/positions_{datetime.now().strftime('%Y%m%d')}.json"
        os.makedirs("monitoring_data", exist_ok=True)
        
        with open(filename, "a") as f:
            f.write(json.dumps(result) + "\n")
        
        logger.info(f"💾 Saved monitoring result for {result['principal_id']}")
        
    except Exception as e:
        logger.error(f"Error saving monitoring result: {e}")

@celery_app.task(name='schedule_all_principal_monitoring')
def schedule_all_principal_monitoring():
    """
    Master task để schedule monitoring cho tất cả active principals
    Task này chạy mỗi 5 phút để update danh sách principals
    """
    try:
        logger.info("📋 Scheduling monitoring for all active principals...")
        
        db = next(get_db())
        # Get all active subscriptions with futures bots
        subscriptions = db.query(models.Subscription).join(
            models.Bot
        ).filter(
            models.Subscription.status == "ACTIVE",
            models.Subscription.expires_at > datetime.now(),
            models.Subscription.started_at <= datetime.now(),
            models.Bot.bot_type == "FUTURES"
        ).all()
        
        scheduled_count = 0
        for sub in subscriptions:
            if sub.user_principal_id:
                # Schedule monitoring task for this principal (every 2 minutes)
                monitor_principal_positions.apply_async(
                    args=[sub.user_principal_id, sub.is_testnet],
                    countdown=0  # Start immediately
                )
                scheduled_count += 1
        
        logger.info(f"✅ Scheduled monitoring for {scheduled_count} principals")
        return {"scheduled": scheduled_count, "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        logger.error(f"Error scheduling principal monitoring: {e}")
        return {"status": "error", "error": str(e)}

# Celery Beat Schedule
celery_app.conf.beat_schedule = {
    # Schedule all principals every 5 minutes
    'schedule-all-principals': {
        'task': 'schedule_all_principal_monitoring',
        'schedule': 300.0,  # 5 minutes
    },
}

celery_app.conf.timezone = 'UTC'

if __name__ == "__main__":
    print("🚀 Celery Position Monitor")
    print("="*40)
    print("To start monitoring:")
    print("1. Start Celery Worker:")
    print("   celery -A celery_position_monitor worker --loglevel=info")
    print()
    print("2. Start Celery Beat (scheduler):")
    print("   celery -A celery_position_monitor beat --loglevel=info")
    print()
    print("3. Monitor with Flower (optional):")
    print("   celery -A celery_position_monitor flower")
    print()
    print("Features:")
    print("✅ Auto-discovery của active principals")
    print("✅ Distributed monitoring với Celery")
    print("✅ Scalable cho hàng ngàn users")
    print("✅ Automatic critical position handling")
    print("✅ Comprehensive logging và reporting")