#!/usr/bin/env python3
"""
Debug script for bot scheduling issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from core import crud, models
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_scheduling(subscription_id: int = None):
    """Debug bot scheduling issues"""
    
    db = SessionLocal()
    try:
        print(f"🔍 Debugging bot scheduling...")
        print(f"   Current time: {datetime.utcnow()}")
        
        # Get all active subscriptions
        active_subscriptions = crud.get_active_subscriptions(db)
        print(f"\n📊 Active Subscriptions ({len(active_subscriptions)}):")
        
        for sub in active_subscriptions:
            print(f"\n   Subscription {sub.id}:")
            print(f"      Bot: {sub.bot.name}")
            print(f"      User: {sub.user.email}")
            print(f"      Status: {sub.status}")
            print(f"      Timeframe: {sub.timeframe}")
            print(f"      Trading Pair: {sub.trading_pair}")
            print(f"      Testnet: {sub.is_testnet}")
            print(f"      Last Run: {sub.last_run_at}")
            print(f"      Next Run: {sub.next_run_at}")
            print(f"      Created: {sub.started_at}")
            
            # Check if it should run now
            should_run = False
            if sub.next_run_at:
                should_run = sub.next_run_at <= datetime.utcnow()
                print(f"      Should Run Now: {'✅ YES' if should_run else '❌ NO'}")
                if not should_run:
                    time_diff = sub.next_run_at - datetime.utcnow()
                    print(f"      Time Until Next Run: {time_diff}")
            else:
                print(f"      Should Run Now: ❌ NO (no next_run_at)")
            
            # Check trial status
            if sub.is_trial:
                print(f"      Trial: YES")
                if sub.trial_expires_at:
                    trial_expired = sub.trial_expires_at <= datetime.utcnow()
                    print(f"      Trial Expired: {'✅ YES' if trial_expired else '❌ NO'}")
                    if not trial_expired:
                        trial_time_left = sub.trial_expires_at - datetime.utcnow()
                        print(f"      Trial Time Left: {trial_time_left}")
                else:
                    print(f"      Trial Expired: ❓ UNKNOWN (no trial_expires_at)")
        
        # Check specific subscription if provided
        if subscription_id:
            print(f"\n🎯 Checking specific subscription {subscription_id}:")
            sub = crud.get_subscription_by_id(db, subscription_id)
            if sub:
                print(f"   Found subscription {sub.id}")
                print(f"   Status: {sub.status}")
                print(f"   Next Run: {sub.next_run_at}")
                print(f"   Should Run: {sub.next_run_at <= datetime.utcnow() if sub.next_run_at else False}")
            else:
                print(f"   ❌ Subscription {subscription_id} not found")
        
        # Check recent bot actions
        print(f"\n📝 Recent Bot Actions:")
        for sub in active_subscriptions[:3]:  # Check first 3 subscriptions
            logs = crud.get_subscription_logs(db, sub.id, limit=3)
            print(f"\n   Subscription {sub.id} ({sub.bot.name}):")
            for log in logs:
                print(f"      {log.timestamp}: {log.action} - {log.details}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def test_schedule_active_bots():
    """Test the schedule_active_bots function"""
    
    print(f"\n🧪 Testing schedule_active_bots function...")
    
    try:
        from core.tasks import schedule_active_bots
        from celery import current_app
        
        # Manually call the function
        result = schedule_active_bots()
        print(f"   Function result: {result}")
        
    except Exception as e:
        print(f"   ❌ Error testing schedule_active_bots: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    subscription_id = None
    if len(sys.argv) > 1:
        subscription_id = int(sys.argv[1])
    
    debug_scheduling(subscription_id)
    test_schedule_active_bots() 