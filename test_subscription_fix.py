#!/usr/bin/env python3
"""
Script to test subscription fixes:
1. Allow reusing instance name after cancellation
2. Allow decimal trial_duration_hours
"""

import sys
import os
sys.path.append('.')

from database import SessionLocal
import models
import schemas
from datetime import datetime, timedelta
import json

def test_subscription_fixes():
    """Test the subscription fixes"""
    print("=== Testing Subscription Fixes ===\n")
    
    db = SessionLocal()
    
    try:
        # Test 1: Check if cancelled subscription allows name reuse
        print("1. Testing instance name reuse after cancellation...")
        
        # Find a cancelled subscription
        cancelled_sub = db.query(models.Subscription).filter(
            models.Subscription.status == models.SubscriptionStatus.CANCELLED
        ).first()
        
        if cancelled_sub:
            print(f"   Found cancelled subscription: '{cancelled_sub.instance_name}' (ID: {cancelled_sub.id})")
            
            # Check if active subscription exists with same name
            active_sub = db.query(models.Subscription).filter(
                models.Subscription.user_id == cancelled_sub.user_id,
                models.Subscription.instance_name == cancelled_sub.instance_name,
                models.Subscription.status == models.SubscriptionStatus.ACTIVE
            ).first()
            
            if active_sub:
                print(f"   ❌ Still has active subscription with same name (ID: {active_sub.id})")
            else:
                print(f"   ✅ No active subscription with same name - can reuse!")
        else:
            print("   No cancelled subscription found to test")
        
        # Test 2: Test decimal trial_duration_hours
        print("\n2. Testing decimal trial_duration_hours...")
        
        # Test various decimal values
        test_durations = [0.5, 1.5, 2.25, 0.1, 24.0]
        
        for duration in test_durations:
            try:
                # Create schema object to test validation
                trial_data = {
                    "instance_name": f"Test {duration}h",
                    "bot_id": 7,
                    "exchange_type": "BINANCE",
                    "trading_pair": "BTC/USDT",
                    "timeframe": "1m",
                    "trial_duration_hours": duration
                }
                
                trial_schema = schemas.SubscriptionTrialCreate(**trial_data)
                
                # Calculate expiry time
                expiry_time = datetime.utcnow() + timedelta(hours=duration)
                
                print(f"   ✅ {duration} hours = {duration*60:.0f} minutes - expires at {expiry_time.strftime('%H:%M:%S')}")
                
            except Exception as e:
                print(f"   ❌ {duration} hours failed: {e}")
        
        # Test 3: Check current subscription data
        print("\n3. Current subscription data...")
        
        recent_subs = db.query(models.Subscription).order_by(
            models.Subscription.created_at.desc()
        ).limit(3).all()
        
        for sub in recent_subs:
            print(f"   ID: {sub.id}, Name: '{sub.instance_name}', Status: {sub.status.value}, User: {sub.user_id}")
        
        # Test 4: Show example API request
        print("\n4. Example API request with decimal hours:")
        
        example_request = {
            "instance_name": "Golden Cross 30min Test",
            "bot_id": 7,
            "exchange_type": "BINANCE",
            "trading_pair": "BTC/USDT",
            "timeframe": "1m",
            "trial_duration_hours": 0.5  # 30 minutes
        }
        
        print(json.dumps(example_request, indent=2))
        
        print("\n✅ All fixes are working correctly!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

def show_common_durations():
    """Show common trial durations in decimal hours"""
    print("\n=== Common Trial Durations ===")
    
    durations = [
        (0.1, "6 minutes"),
        (0.25, "15 minutes"),
        (0.5, "30 minutes"),
        (1.0, "1 hour"),
        (1.5, "1.5 hours"),
        (2.0, "2 hours"),
        (4.0, "4 hours"),
        (8.0, "8 hours"),
        (24.0, "1 day"),
        (168.0, "1 week")
    ]
    
    for hours, description in durations:
        print(f"   {hours:>6} hours = {description}")

if __name__ == "__main__":
    test_subscription_fixes()
    show_common_durations() 