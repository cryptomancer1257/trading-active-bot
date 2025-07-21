import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# file: api/endpoints/subscriptions_simple.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from core import models, schemas, security
from core.database import get_db
from tasks_simple_no_s3 import run_bot_logic_simple

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/trial", response_model=schemas.SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_trial_subscription_simple(
    trial_in: schemas.SubscriptionTrialCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Create a trial subscription for testing a bot without S3 dependencies"""
    try:
        # Check if bot exists and is approved
        bot = db.query(models.Bot).filter(models.Bot.id == trial_in.bot_id).first()
        
        if not bot or bot.status != models.BotStatus.APPROVED:
            raise HTTPException(status_code=404, detail="Bot not found or not approved for trial")

        # Create a simplified subscription entry
        db_subscription = models.Subscription(
            instance_name=trial_in.instance_name,
            user_id=current_user.id,
            bot_id=trial_in.bot_id,
            status=models.SubscriptionStatus.ACTIVE,
            is_testnet=True,  # Always testnet for trials
            is_trial=True,
            exchange_type=trial_in.exchange_type,
            trading_pair=trial_in.trading_pair,
            timeframe=trial_in.timeframe or "1h",
            strategy_config=trial_in.strategy_config or {},
            execution_config={"order_type": "market", "initial_balance": 1000.0, "max_position_size": 0.1},
            risk_config={"trailing_stop": False, "max_daily_loss": 0.05, "max_loss_per_trade": 0.02}
        )
        
        # Set trial expiration
        from datetime import datetime, timedelta
        trial_duration = trial_in.trial_duration_hours or 0.5
        db_subscription.trial_expires_at = datetime.utcnow() + timedelta(hours=trial_duration)
        db_subscription.expires_at = db_subscription.trial_expires_at
        
        db.add(db_subscription)
        db.commit()
        db.refresh(db_subscription)
        
        # Start the simplified bot execution cycle
        run_bot_logic_simple.apply_async(args=[db_subscription.id], countdown=30)
        
        return schemas.SubscriptionResponse(
            subscription_id=db_subscription.id,
            status=db_subscription.status.value,
            message=f"Trial subscription created! Bot will run on testnet for {trial_duration} hours with safe defaults (simplified mode)."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create trial subscription: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create trial subscription: {str(e)}"
        )

@router.post("/{subscription_id}/force-run-simple")
def force_run_subscription_simple(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Force run a subscription immediately using simplified logic"""
    subscription = db.query(models.Subscription).filter(
        models.Subscription.id == subscription_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if subscription.user_id != current_user.id and current_user.role != schemas.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if subscription.status != models.SubscriptionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Can only force run active subscriptions")
    
    # Trigger immediate execution with simplified logic
    task = run_bot_logic_simple.apply_async(args=[subscription_id])
    
    return {"message": "Simplified bot execution triggered", "task_id": task.id} 