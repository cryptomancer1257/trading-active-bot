#!/usr/bin/env python3
"""
Script to test and fix trial subscription logic
"""

import sys
import os
sys.path.append('.')

from database import SessionLocal
import models
import schemas
import crud
from datetime import datetime, timedelta

def test_trial_subscription_logic():
    """Test trial subscription logic"""
    print("=== Testing Trial Subscription Logic ===\n")
    
    db = SessionLocal()
    
    try:
        # Find user with existing trial subscriptions
        user_with_trials = db.query(models.User).join(models.Subscription).filter(
            models.Subscription.is_trial == True
        ).first()
        
        if not user_with_trials:
            print("No user with trial subscriptions found")
            return
        
        print(f"Testing with user ID: {user_with_trials.id}")
        
        # Check all trial subscriptions for this user
        all_trials = db.query(models.Subscription).filter(
            models.Subscription.user_id == user_with_trials.id,
            models.Subscription.is_trial == True
        ).all()
        
        print(f"Found {len(all_trials)} trial subscriptions:")
        for trial in all_trials:
            print(f"  - ID: {trial.id}, Bot: {trial.bot_id}, Status: {trial.status.value}, Name: '{trial.instance_name}'")
        
        # Check active trials only
        active_trials = db.query(models.Subscription).filter(
            models.Subscription.user_id == user_with_trials.id,
            models.Subscription.is_trial == True,
            models.Subscription.status == models.SubscriptionStatus.ACTIVE
        ).all()
        
        print(f"\nActive trials: {len(active_trials)}")
        for trial in active_trials:
            print(f"  - ID: {trial.id}, Bot: {trial.bot_id}, Status: {trial.status.value}")
        
        # Test creating new trial for same bot
        if all_trials:
            test_bot_id = all_trials[0].bot_id
            
            print(f"\nTesting new trial creation for bot {test_bot_id}...")
            
            # Check if there's an active trial for this bot
            active_trial_for_bot = db.query(models.Subscription).filter(
                models.Subscription.user_id == user_with_trials.id,
                models.Subscription.bot_id == test_bot_id,
                models.Subscription.is_trial == True,
                models.Subscription.status == models.SubscriptionStatus.ACTIVE
            ).first()
            
            if active_trial_for_bot:
                print(f"  ❌ Active trial exists for bot {test_bot_id} - cannot create new trial")
                print(f"     Active trial ID: {active_trial_for_bot.id}, Status: {active_trial_for_bot.status.value}")
            else:
                print(f"  ✅ No active trial for bot {test_bot_id} - can create new trial")
                
                # Try to create new trial
                try:
                    trial_data = schemas.SubscriptionTrialCreate(
                        instance_name=f"Test Trial {datetime.now().strftime('%H%M%S')}",
                        bot_id=test_bot_id,
                        exchange_type=schemas.ExchangeType.BINANCE,
                        trading_pair="BTC/USDT",
                        timeframe="1m",
                        trial_duration_hours=0.5
                    )
                    
                    new_trial = crud.create_trial_subscription(db, trial_data, user_with_trials.id)
                    print(f"  ✅ New trial created successfully: ID {new_trial.id}")
                    
                    # Clean up - cancel the test trial
                    new_trial.status = models.SubscriptionStatus.CANCELLED
                    db.commit()
                    print(f"  🧹 Test trial cancelled")
                    
                except Exception as e:
                    print(f"  ❌ Failed to create new trial: {e}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

def fix_trial_subscription_logic():
    """Show how to fix the trial subscription logic"""
    print("\n=== Fix for Trial Subscription Logic ===\n")
    
    print("The issue is in crud.py - create_trial_subscription function")
    print("Current logic (WRONG):")
    print("""
    existing_trial = db.query(models.Subscription).filter(
        models.Subscription.user_id == user_id,
        models.Subscription.bot_id == trial.bot_id,
        models.Subscription.is_trial == True  # Only checks is_trial, not status
    ).first()
    """)
    
    print("Fixed logic (CORRECT):")
    print("""
    existing_active_trial = db.query(models.Subscription).filter(
        models.Subscription.user_id == user_id,
        models.Subscription.bot_id == trial.bot_id,
        models.Subscription.is_trial == True,
        models.Subscription.status == models.SubscriptionStatus.ACTIVE  # Also check status
    ).first()
    """)
    
    print("Benefits of the fix:")
    print("✅ Allows creating new trial after cancelling previous trial")
    print("✅ Only prevents creating trial if there's an active trial")
    print("✅ Cancelled/expired trials don't block new trials")

def manual_cancel_trial():
    """Manually cancel trial subscription to test"""
    print("\n=== Manual Trial Cancellation ===\n")
    
    db = SessionLocal()
    
    try:
        # Find active trial subscriptions
        active_trials = db.query(models.Subscription).filter(
            models.Subscription.is_trial == True,
            models.Subscription.status == models.SubscriptionStatus.ACTIVE
        ).all()
        
        print(f"Found {len(active_trials)} active trial subscriptions:")
        
        for trial in active_trials:
            print(f"  ID: {trial.id}, User: {trial.user_id}, Bot: {trial.bot_id}, Name: '{trial.instance_name}'")
        
        if active_trials:
            print(f"\nTo manually cancel a trial, run:")
            print(f"UPDATE subscriptions SET status = 'CANCELLED' WHERE id = <trial_id>;")
            
            # Example: Cancel first trial
            if len(active_trials) > 0:
                trial_to_cancel = active_trials[0]
                print(f"\nExample - Cancel trial {trial_to_cancel.id}:")
                print(f"UPDATE subscriptions SET status = 'CANCELLED' WHERE id = {trial_to_cancel.id};")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_trial_subscription_logic()
    fix_trial_subscription_logic()
    manual_cancel_trial() 