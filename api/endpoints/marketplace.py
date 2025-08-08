import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from core.api_key_manager import api_key_manager
from core import crud, models, schemas, security
from core.database import get_db
from core.tasks import run_bot_logic
from core.security import validate_marketplace_api_key

from typing import Dict, Any, List, Optional
from decimal import Decimal
from pydantic import BaseModel
import os
import time
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError

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
        
        # Auto-detect trade_mode from bot type (using string comparison)
        if bot.bot_type and bot.bot_type.upper() == "FUTURES":
            trade_mode = models.TradeMode.FUTURES
            logger.info(f"Bot {bot.id} is FUTURES bot, setting trade_mode to FUTURES")
        elif bot.bot_type and bot.bot_type.upper() == "SPOT":
            trade_mode = models.TradeMode.SPOT
            logger.info(f"Bot {bot.id} is SPOT bot, setting trade_mode to SPOT")
        else:
            # Default to SPOT for unknown types
            trade_mode = models.TradeMode.SPOT
            logger.info(f"Bot {bot.id} has bot_type={bot.bot_type}, defaulting to SPOT")
        
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
            trade_mode=trade_mode,  # Auto-detected from bot type
            
            # Strategy configs
            strategy_config=request.strategy_config,
            execution_config=execution_config.dict(),
            risk_config=risk_config.dict(),
            
            # Timing - both are now required
            started_at=request.subscription_start,
            expires_at=request.subscription_end,
            
            status=models.SubscriptionStatus.ACTIVE
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        logger.info(f"Created marketplace subscription {subscription.id} for principal {request.user_principal_id}")
        
        # Trigger bot execution based on start and end time
        now = datetime.utcnow()
        if subscription.started_at <= now <= subscription.expires_at:
            logger.info(f"Triggering immediate bot execution for marketplace subscription {subscription.id}")
            run_bot_logic.apply_async(args=[subscription.id], countdown=10)
        elif subscription.started_at > now:
            logger.info(f"Marketplace subscription {subscription.id} will start later at {subscription.started_at}")
        else:
            logger.info(f"Marketplace subscription {subscription.id} has expired (ended at {subscription.expires_at})")
        
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


# Marketplace endpoint for storing credentials by principal ID
@router.post("/store-by-principal", response_model=Dict[str, Any])
async def store_credentials_by_principal_id(
        request: schemas.ExchangeCredentialsByPrincipalRequest,
        api_key: str = Depends(validate_marketplace_api_key),
        db: Session = Depends(get_db)
):
    """
    Marketplace: Store exchange credentials by ICP Principal ID
    Allows marketplace users to provide their exchange API keys
    Requires valid marketplace API key
    """
    try:
        # Verify marketplace API key
        # if api_key != security.MARKETPLACE_API_KEY:
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="Invalid marketplace API key"
        #     )

        # Validate exchange
        if request.exchange.upper() not in ["BINANCE", "COINBASE", "KRAKEN"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported exchange. Supported: BINANCE, COINBASE, KRAKEN"
            )

        # Store credentials using principal ID
        success = api_key_manager.store_user_exchange_credentials_by_principal_id(
            db=db,
            principal_id=request.principal_id,
            exchange=request.exchange.upper(),
            api_key=request.api_key,
            api_secret=request.api_secret,
            api_passphrase=request.api_passphrase,
            is_testnet=request.is_testnet
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to store credentials. Check if user exists and credentials are valid."
            )

        logger.info(f"Stored {request.exchange} credentials for principal ID: {request.principal_id}")

        return {
            "status": "success",
            "message": "Exchange credentials stored successfully",
            "principal_id": request.principal_id,
            "exchange": request.exchange.upper(),
            "is_testnet": request.is_testnet,
            "created_at": "2025-08-03T12:00:00Z"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store credentials by principal ID: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store credentials"
        )


# Marketplace Subscription Control Endpoints

@router.post("/subscription/pause", response_model=schemas.MarketplaceSubscriptionControlResponse)
async def pause_marketplace_subscription(
    request: schemas.MarketplaceSubscriptionControlRequest,
    db: Session = Depends(get_db)
):
    """Pause a marketplace subscription - temporarily stops bot execution"""
    try:
        # Validate subscription access with enhanced security
        subscription, bot_registration = crud.validate_marketplace_subscription_access(
            db, request.subscription_id, request.principal_id, request.api_key
        )
        
        # Check if subscription is already paused
        if subscription.status == models.SubscriptionStatus.PAUSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription is already paused"
            )
        
        # Check if subscription can be paused (only ACTIVE subscriptions)
        if subscription.status != models.SubscriptionStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot pause subscription with status: {subscription.status}"
            )
        
        # Update subscription status to PAUSED
        updated_subscription = crud.update_subscription_status_by_principal(
            db, request.subscription_id, request.principal_id, models.SubscriptionStatus.PAUSED
        )
        
        logger.info(f"Paused marketplace subscription {request.subscription_id} for principal {request.principal_id}")
        
        return schemas.MarketplaceSubscriptionControlResponse(
            subscription_id=updated_subscription.id,
            principal_id=updated_subscription.user_principal_id,
            action="paused",
            status=updated_subscription.status,
            message="Subscription paused successfully",
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause marketplace subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pause subscription"
        )


# ============================
# Studio → Marketplace Publish
# ============================

def _derive_trading_type(bot: models.Bot) -> str:
    try:
        if bot.bot_type and str(bot.bot_type).upper() == 'LLM':
            return 'passive'
        return 'active'
    except Exception:
        return 'active'

def _extract_timeframes(bot: models.Bot) -> List[str]:
    try:
        cfg = bot.default_config or {}
        tfs = cfg.get('timeframes') or cfg.get('timeframe')
        if isinstance(tfs, list) and tfs:
            return [str(x) for x in tfs]
        if isinstance(tfs, str) and tfs:
            return [tfs]
    except Exception:
        pass
    return ['1H']


@router.post("/publish-token", status_code=status.HTTP_200_OK)
def create_publish_token(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    """Issue one-time JWT for marketplace publish redirect."""
    bot = crud.get_bot_by_id(db, bot_id)
    if not bot or bot.developer_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bot not found or not owned by current user")

    secret = os.getenv('STUDIO_JWT_SECRET', 'dev-secret')
    ttl_seconds = int(os.getenv('PUBLISH_TOKEN_TTL', '600'))
    payload = {
        'bot_id': bot_id,
        'owner_id': current_user.id,
        'aud': 'ai-marketplace',
        'iss': 'studio',
        'exp': int(time.time()) + ttl_seconds,
        'nonce': os.urandom(8).hex(),
    }
    token = jwt.encode(payload, secret, algorithm='HS256')

    marketplace_url = os.getenv('MARKETPLACE_WEB_URL', 'http://localhost:3000/submit')
    return {
        'publish_url': f"{marketplace_url}?token={token}",
        'expires_in': ttl_seconds,
    }


class RegisterByTokenRequest(BaseModel):
    token: str
    user_principal_id: str
    marketplace_name: Optional[str] = None
    marketplace_description: Optional[str] = None
    price_on_marketplace: Optional[Decimal] = None


@router.post("/register-by-token", response_model=schemas.BotMarketplaceRegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_by_token(body: RegisterByTokenRequest, db: Session = Depends(get_db)):
    """Register bot for marketplace using short-lived JWT token (no X-API-Key).

    - Verifies token (audience, expiry)
    - Ensures caller owns the bot in token
    - Creates registration and returns generated api_key
    """
    secret = os.getenv('STUDIO_JWT_SECRET', 'dev-secret')
    try:
        payload = jwt.decode(body.token, secret, algorithms=['HS256'], audience='ai-marketplace')
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token expired')
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f'Invalid token: {e}')

    bot_id = int(payload.get('bot_id') or 0)
    owner_id = int(payload.get('owner_id') or 0)
    if not bot_id or not owner_id:
        raise HTTPException(status_code=400, detail='Invalid token payload')

    bot = crud.get_bot_by_id(db, bot_id)
    if not bot or bot.developer_id != owner_id:
        raise HTTPException(status_code=404, detail='Bot not found or not owned by token owner')

    reg_req = schemas.BotMarketplaceRegistrationRequest(
        user_principal_id=body.user_principal_id,
        bot_id=bot_id,
        marketplace_name=body.marketplace_name,
        marketplace_description=body.marketplace_description,
        price_on_marketplace=body.price_on_marketplace,
    )

    registration_record = crud.create_bot_marketplace_registration(db=db, registration=reg_req)
    db.refresh(registration_record)

    return schemas.BotMarketplaceRegistrationResponse(
        registration_id=registration_record.id,
        user_principal_id=registration_record.user_principal_id,
        bot_id=registration_record.bot_id,
        api_key=registration_record.api_key,
        status="approved",
        message="Bot registered successfully for marketplace with auto-generated API key",
        registration_details={
            "marketplace_name": registration_record.marketplace_name,
            "marketplace_description": registration_record.marketplace_description,
            "price_on_marketplace": str(registration_record.price_on_marketplace),
            "commission_rate": registration_record.commission_rate,
            "registered_at": registration_record.registered_at.isoformat() if registration_record.registered_at else None,
            "status": registration_record.status.value if hasattr(registration_record.status, 'value') else str(registration_record.status),
            "api_key": registration_record.api_key,
        },
    )

@router.get("/bot-by-token/{token}")
def bot_by_token(token: str, db: Session = Depends(get_db)):
    """Return bot metadata for marketplace to submit to canisters."""
    secret = os.getenv('STUDIO_JWT_SECRET', 'dev-secret')
    try:
        # Validate token audience to match issuance in create_publish_token
        payload = jwt.decode(token, secret, algorithms=['HS256'], audience='ai-marketplace')
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token expired')
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f'Invalid token: {e}')

    bot_id = payload.get('bot_id')
    bot = crud.get_bot_by_id(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail='Bot not found')

    price_month = float(bot.price_per_month or 0.0)
    price_daily_icp = round(price_month / 30.0, 8) if price_month > 0 else 2.5
    trading_type = _derive_trading_type(bot)
    tags = ['Active Trading'] if trading_type == 'active' else ['Signal Provider']
    timeframes = _extract_timeframes(bot)

    base_url = os.getenv('STUDIO_BASE_URL', 'http://localhost:8000')
    api_base = base_url
    api_endpoints = {
        'pause': '/marketplace/subscription/pause',
        'cancel': '/marketplace/subscription/cancel',
        'resume': '/marketplace/subscription/resume',
    }

    return {
        'id_hint': f'studio_{bot.id}',
        'name': bot.name,
        'description': bot.description,
        'price_daily_icp': price_daily_icp,
        'trading_type': trading_type,
        'timeframes': timeframes,
        'strategies': [],
        'supported_exchanges': ['Binance'],
        'supported_pairs': ['BTC/USDT'],
        'risk_level': 'medium',
        'tags': tags,
        'performance': { 'roi': 15.0, 'winRate': 75, 'maxDrawdown': 10, 'sharpeRatio': 1.5 },
        'images': [],
        'aiStudioBotId': bot.id,
        'apiBaseUrl': api_base,
        'apiEndpoints': api_endpoints,
    }


@router.post('/published', status_code=status.HTTP_200_OK)
def published_callback(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """Optional callback from marketplace to store mapping aiStudioBotId ↔ marketplaceBotId."""
    studio_id = body.get('aiStudioBotId')
    marketplace_bot_id = body.get('marketplaceBotId')
    if not studio_id or not marketplace_bot_id:
        raise HTTPException(status_code=400, detail='Missing ids')

    try:
        reg = db.query(models.BotRegistration).filter(models.BotRegistration.bot_id == studio_id).first()
        if reg:
            if hasattr(reg, 'marketplace_bot_id'):
                setattr(reg, 'marketplace_bot_id', str(marketplace_bot_id))
            if hasattr(reg, 'is_published'):
                setattr(reg, 'is_published', True)
            if hasattr(reg, 'published_at'):
                setattr(reg, 'published_at', datetime.utcnow())
            db.commit()
    except Exception:
        db.rollback()
    return { 'ok': True }
@router.post("/subscription/cancel", response_model=schemas.MarketplaceSubscriptionControlResponse)
async def cancel_marketplace_subscription(
    request: schemas.MarketplaceSubscriptionControlRequest,
    db: Session = Depends(get_db)
):
    """Cancel a marketplace subscription - permanently stops bot and closes all trades"""
    try:
        # Validate subscription access with enhanced security
        subscription, bot_registration = crud.validate_marketplace_subscription_access(
            db, request.subscription_id, request.principal_id, request.api_key
        )
        
        # Check if subscription is already cancelled
        if subscription.status == models.SubscriptionStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription is already cancelled"
            )
        
        # Close any open trades before cancelling
        crud.close_open_trades_for_subscription(db, request.subscription_id)
        
        # Update subscription status to CANCELLED
        updated_subscription = crud.update_subscription_status_by_principal(
            db, request.subscription_id, request.principal_id, models.SubscriptionStatus.CANCELLED
        )
        
        logger.info(f"Cancelled marketplace subscription {request.subscription_id} for principal {request.principal_id}")
        
        return schemas.MarketplaceSubscriptionControlResponse(
            subscription_id=updated_subscription.id,
            principal_id=updated_subscription.user_principal_id,
            action="cancelled",
            status=updated_subscription.status,
            message="Subscription cancelled successfully. All open trades have been closed.",
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel marketplace subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )


@router.post("/subscription/resume", response_model=schemas.MarketplaceSubscriptionControlResponse)
async def resume_marketplace_subscription(
    request: schemas.MarketplaceSubscriptionControlRequest,
    db: Session = Depends(get_db)
):
    """Resume a paused marketplace subscription - restarts bot execution"""
    try:
        # Validate subscription access with enhanced security
        subscription, bot_registration = crud.validate_marketplace_subscription_access(
            db, request.subscription_id, request.principal_id, request.api_key
        )
        
        # Check if subscription is paused (only PAUSED subscriptions can be resumed)
        if subscription.status != models.SubscriptionStatus.PAUSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot resume subscription with status: {subscription.status}. Only PAUSED subscriptions can be resumed."
            )
        
        # Check if subscription hasn't expired
        now = datetime.utcnow()
        if subscription.expires_at and subscription.expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot resume expired subscription"
            )
        
        # Update subscription status to ACTIVE
        updated_subscription = crud.update_subscription_status_by_principal(
            db, request.subscription_id, request.principal_id, models.SubscriptionStatus.ACTIVE
        )
        
        # Trigger bot execution immediately upon resume
        run_bot_logic.apply_async(args=[updated_subscription.id], countdown=10)
        
        logger.info(f"Resumed marketplace subscription {request.subscription_id} for principal {request.principal_id}")
        
        return schemas.MarketplaceSubscriptionControlResponse(
            subscription_id=updated_subscription.id,
            principal_id=updated_subscription.user_principal_id,
            action="resumed",
            status=updated_subscription.status,
            message="Subscription resumed successfully. Bot execution will restart shortly.",
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume marketplace subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resume subscription"
        )
