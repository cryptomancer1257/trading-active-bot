import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from core import crud, models, schemas
from core.database import get_db
from core.tasks import run_bot_logic
from core.security import validate_marketplace_api_key

# Initialize logger
logger = logging.getLogger(__name__)

# Create router WITHOUT any security dependencies
router = APIRouter()

@router.post("/marketplace", 
             response_model=schemas.SubscriptionResponse, 
             status_code=status.HTTP_201_CREATED)
def create_marketplace_subscription(
    marketplace_sub: schemas.MarketplaceSubscriptionCreate,
    db: Session = Depends(get_db)
):
    """Create subscription from marketplace using user principal ID and bot API key authentication"""
    try:
        logger.info(f"Marketplace subscription request: user={marketplace_sub.user_principal_id}, bot_id={marketplace_sub.bot_id}, api_key={marketplace_sub.bot_api_key[:10]}...")
        
        # Authenticate using bot API key instead of marketplace API key
        bot_registration = crud.get_bot_registration_by_api_key(db, marketplace_sub.bot_api_key)
        logger.info(f"Bot registration found: {bot_registration is not None}")
        if not bot_registration:
            raise HTTPException(
                status_code=401, 
                detail="Invalid bot API key - authentication failed"
            )
        
        # Verify bot_id matches registration
        if bot_registration.bot_id != marketplace_sub.bot_id:
            raise HTTPException(
                status_code=400,
                detail="Bot ID does not match the provided API key"
            )
        
        # Check if bot exists and is approved
        bot = crud.get_bot_by_id(db, marketplace_sub.bot_id)
        logger.info(f"Bot found: {bot is not None}")
        if bot:
            logger.info(f"Bot status: {bot.status}, Expected: {models.BotStatus.APPROVED}")
            logger.info(f"Status comparison: {bot.status == models.BotStatus.APPROVED}")
            logger.info(f"Bot status value: {bot.status.value}")
        if not bot:
            logger.error(f"Bot not found with ID: {marketplace_sub.bot_id}")
            raise HTTPException(
                status_code=404, 
                detail="Bot not found"
            )
        if bot.status != models.BotStatus.APPROVED:
            logger.error(f"Bot not approved - status: {bot.status}")
            raise HTTPException(
                status_code=404, 
                detail="Bot not approved for use"
            )
        
        # Validate start_time and end_time
        now = datetime.now(timezone.utc)
        start_time = marketplace_sub.start_time or now
        
        if marketplace_sub.start_time and marketplace_sub.start_time < now:
            raise HTTPException(
                status_code=400,
                detail="Start time cannot be in the past"
            )
        
        if marketplace_sub.end_time and marketplace_sub.start_time:
            if marketplace_sub.end_time <= marketplace_sub.start_time:
                raise HTTPException(
                    status_code=400,
                    detail="End time must be after start time"
                )
        
        # Create internal user for the renter
        internal_user = crud.get_or_create_marketplace_user(db, marketplace_sub.user_principal_id)
        
        # Check for existing subscription with same instance name
        existing_sub = crud.get_user_subscription_by_name(
            db, user_id=internal_user.id, instance_name=marketplace_sub.instance_name
        )
        if existing_sub:
            raise HTTPException(
                status_code=400,
                detail="You already have a subscription with this instance name"
            )
        
        # Convert to standard SubscriptionCreate format
        sub_data = schemas.SubscriptionCreate(
            instance_name=marketplace_sub.instance_name,
            bot_id=marketplace_sub.bot_id,
            exchange_type=marketplace_sub.exchange_type,
            trading_pair=marketplace_sub.trading_pair,
            timeframe=marketplace_sub.timeframe,
            strategy_config=marketplace_sub.strategy_config,
            execution_config=marketplace_sub.execution_config,
            risk_config=marketplace_sub.risk_config,
            is_testnet=marketplace_sub.is_testnet,
            is_trial=False
        )
        
        # Create subscription
        subscription = crud.create_subscription(db, sub=sub_data, user_id=internal_user.id)
        
        # Set marketplace-controlled timing and user principal ID
        subscription.user_principal_id = marketplace_sub.user_principal_id
        subscription.started_at = start_time
        subscription.expires_at = marketplace_sub.end_time
        
        # Set status based on start time
        if start_time > now:
            subscription.status = models.SubscriptionStatus.PENDING  # Will start later
            subscription.next_run_at = start_time  # Schedule first run at start time
        else:
            subscription.status = models.SubscriptionStatus.ACTIVE  # Start immediately
            subscription.next_run_at = None  # Will be picked up by next Celery beat
        
        db.commit()
        
        # Only trigger immediate execution if starting now
        if start_time <= now:
            run_bot_logic.apply_async(args=[subscription.id], countdown=10)
        
        return schemas.SubscriptionResponse(
            subscription_id=subscription.id,
            status=subscription.status.value,
            message=f"Marketplace subscription created for user {marketplace_sub.user_principal_id}. Start: {start_time}, End: {marketplace_sub.end_time or 'No expiration'}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating marketplace subscription: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create marketplace subscription: {str(e)}"
        )

@router.post("/subscription", response_model=schemas.MarketplaceSubscriptionResponse)
async def create_marketplace_subscription_v2(
    request: schemas.MarketplaceSubscriptionCreateV2,
    db: Session = Depends(get_db),
    _: bool = Depends(validate_marketplace_api_key)
):
    """
    Create subscription for marketplace user (without studio account)
    
    This endpoint allows marketplace to create subscriptions for users who:
    - Only exist in marketplace, not in studio
    - Are identified by principal_id 
    - Have contact info stored for notifications
    """
    try:
        # Validate bot exists and is approved
        bot = db.query(models.Bot).filter(
            models.Bot.id == request.bot_id,
            models.Bot.status == models.BotStatus.APPROVED
        ).first()
        
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found or not approved"
            )
        
        # Check if user_principal_id has valid mapping (optional check)
        principal_mapping = db.query(models.UserPrincipal).filter(
            models.UserPrincipal.principal_id == request.user_principal_id,
            models.UserPrincipal.status == models.UserPrincipalStatus.ACTIVE
        ).first()
        
        # Set user_id if principal mapping exists, otherwise NULL
        user_id = principal_mapping.user_id if principal_mapping else None
        
        # Create default configs if not provided
        execution_config = request.execution_config or schemas.ExecutionConfig(
            buy_order_type="PERCENTAGE",
            buy_order_value=100.0,
            sell_order_type="ALL",
            sell_order_value=100.0
        )
        
        risk_config = request.risk_config or schemas.RiskConfig(
            stop_loss_percent=2.0,
            take_profit_percent=4.0,
            max_position_size=100.0
        )
        
        # Create marketplace subscription
        subscription = models.Subscription(
            instance_name=request.instance_name,
            user_id=user_id,  # Can be NULL
            bot_id=request.bot_id,
            user_principal_id=request.user_principal_id,
            
            # Marketplace-specific fields
            is_marketplace_subscription=True,
            marketplace_user_email=request.marketplace_user_email,
            marketplace_user_telegram=request.marketplace_user_telegram,
            marketplace_user_discord=request.marketplace_user_discord,
            marketplace_subscription_start=request.subscription_start,
            marketplace_subscription_end=request.subscription_end,
            
            # Trading config
            exchange_type=request.exchange_type,
            trading_pair=request.trading_pair,
            timeframe=request.timeframe,
            is_testnet=request.is_testnet,
            
            # Strategy configs
            strategy_config=request.strategy_config,
            execution_config=execution_config.dict(),
            risk_config=risk_config.dict(),
            
            # Timing
            started_at=request.subscription_start or datetime.utcnow(),
            expires_at=request.subscription_end,
            
            status=models.SubscriptionStatus.ACTIVE
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        logger.info(f"Created marketplace subscription {subscription.id} for principal {request.user_principal_id}")
        
        # Return response
        return schemas.MarketplaceSubscriptionResponse(
            subscription_id=subscription.id,
            user_principal_id=subscription.user_principal_id,
            bot_id=subscription.bot_id,
            instance_name=subscription.instance_name,
            status=subscription.status,
            is_marketplace_subscription=subscription.is_marketplace_subscription,
            marketplace_user_email=subscription.marketplace_user_email,
            marketplace_user_telegram=subscription.marketplace_user_telegram,
            marketplace_user_discord=subscription.marketplace_user_discord,
            started_at=subscription.started_at,
            expires_at=subscription.expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create marketplace subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create marketplace subscription"
        )