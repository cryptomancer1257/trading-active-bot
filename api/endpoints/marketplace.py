from io import BytesIO
import sys
import os
from PIL import Image
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import logging

from core.api_key_manager import api_key_manager
from core import crud, models, schemas, security
from core.database import get_db
from core.tasks import run_bot_logic, run_bot_signal_logic, run_bot_rpa_logic
from core.security import validate_marketplace_api_key

from typing import Dict, Any, List, Optional
from decimal import Decimal
from pydantic import BaseModel
import os
import time
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from google.cloud import storage

# Initialize logger
logger = logging.getLogger(__name__)

# Create router WITHOUT any security dependencies
router = APIRouter()

@router.post("/subscription", response_model=schemas.MarketplaceSubscriptionResponse)
async def create_marketplace_subscription_v2(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    """
    Create subscription for marketplace user (without studio account)
    
    This endpoint allows marketplace to create subscriptions for users who:
    - Only exist in marketplace, not in studio
    - Are identified by principal_id 
    - Have contact info stored for notifications
    """
    try:
        normalized_payload: Dict[str, Any]
        # Assume MarketplaceSubscriptionCreateV2 shape
        normalized_payload = dict(request)

        try:
            request = schemas.MarketplaceSubscriptionCreateV2(**normalized_payload)  # type: ignore[assignment]
        except Exception as e:
            logger.error(f"Failed to validate subscription request: {e}; payload={normalized_payload}")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid subscription payload")

        # Validate API key: allow either marketplace API key or a valid bot API key
        marketplace_key = os.getenv('MARKETPLACE_API_KEY', 'marketplace_dev_api_key_12345')
        if not x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is required",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        is_marketplace_key = x_api_key == marketplace_key
        bot_registration = None
        if not is_marketplace_key:
            bot_registration = crud.get_bot_registration_by_api_key(db, x_api_key)
            if not bot_registration:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid marketplace API key",
                    headers={"WWW-Authenticate": "ApiKey"},
                )

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
        
        # If authorized via bot API key, ensure the registration is for this bot
        if bot_registration and bot_registration.bot_id != request.bot_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key does not match the requested bot",
            )
        
        # Validate trading pairs against bot's configured pairs
        if request.trading_pair:  # Only validate if trading_pair is provided
            if bot.trading_pairs:
                # Primary trading pair must be in bot's trading_pairs
                if request.trading_pair not in bot.trading_pairs:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Primary trading pair '{request.trading_pair}' is not supported by this bot. "
                               f"Supported pairs: {', '.join(bot.trading_pairs)}"
                    )
                
                # Secondary trading pairs must also be in bot's trading_pairs
                if request.secondary_trading_pairs:
                    invalid_pairs = [pair for pair in request.secondary_trading_pairs if pair not in bot.trading_pairs]
                    if invalid_pairs:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Secondary trading pairs {invalid_pairs} are not supported by this bot. "
                                   f"Supported pairs: {', '.join(bot.trading_pairs)}"
                        )
                    
                    # Ensure primary pair is not in secondary pairs
                    if request.trading_pair in request.secondary_trading_pairs:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Primary trading pair '{request.trading_pair}' cannot be in secondary trading pairs"
                        )
            else:
                # Legacy bot without trading_pairs configured - use the bot's single trading_pair
                if bot.trading_pair and request.trading_pair != bot.trading_pair:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"This bot only supports trading pair: {bot.trading_pair}"
                    )

        # Auto-detect trade_mode from bot type (using string comparison)
        if bot.bot_type and bot.bot_type.upper() == "FUTURES":
            trade_mode = models.TradeMode.FUTURES.value
            logger.info(f"Bot {bot.id} is FUTURES bot, setting trade_mode to FUTURES")
        elif bot.bot_type and bot.bot_type.upper() == "SPOT":
            trade_mode = models.TradeMode.SPOT.value
            logger.info(f"Bot {bot.id} is SPOT bot, setting trade_mode to SPOT")
        else:
            # Default to SPOT for unknown types
            trade_mode = models.TradeMode.SPOT.value
            logger.info(f"Bot {bot.id} has bot_type={bot.bot_type}, defaulting to SPOT")
        
        # Check if user_principal_id has valid mapping (optional check)
        principal_mapping = db.query(models.UserPrincipal).filter(
            models.UserPrincipal.principal_id == request.user_principal_id,
            models.UserPrincipal.status == models.UserPrincipalStatus.ACTIVE
        ).first()
        
        # Set user_id from request or principal mapping, otherwise NULL
        user_id = request.user_id if request.user_id else (principal_mapping.user_id if principal_mapping else None)

        # ✅ Check subscription limit ONLY for Studio TRIAL subscriptions (not marketplace ICP/PayPal)
        if request.payment_method == 'TRIAL' and user_id:
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if user:
                from core.plan_checker import plan_checker
                plan_checker.check_user_subscription_limit(user, db)
                logger.info(f"User {user_id} has valid subscription limit for TRIAL payment method")

        # ✅ Check for trading pair conflicts with existing active subscriptions
        # Apply to both Studio users (user_id) and Marketplace users (user_principal_id)
        if request.trading_pair and (user_id or request.user_principal_id):
            from datetime import datetime
            
            # Get all active subscriptions for this user/principal and bot
            query = db.query(models.Subscription).filter(
                models.Subscription.bot_id == request.bot_id,
                models.Subscription.status == models.SubscriptionStatus.ACTIVE
            )
            
            if user_id:
                # Studio user: filter by user_id
                query = query.filter(models.Subscription.user_id == user_id)
                logger.info(f"Checking trading pair conflicts for Studio user {user_id}")
            else:
                # Marketplace user: filter by user_principal_id
                query = query.filter(models.Subscription.user_principal_id == request.user_principal_id)
                logger.info(f"Checking trading pair conflicts for Marketplace user {request.user_principal_id}")
            
            existing_subscriptions = query.all()
            
            # Filter only non-expired subscriptions
            now = datetime.now()
            active_subscriptions = []
            for sub in existing_subscriptions:
                end_date = sub.expires_at or sub.marketplace_subscription_end
                if end_date and end_date > now:
                    active_subscriptions.append(sub)
            
            # Check for trading pair conflicts (same network type)
            requested_pairs = [request.trading_pair] + (request.secondary_trading_pairs or [])
            conflicting_pairs = []
            
            for sub in active_subscriptions:
                # Check if same network type
                same_network = (
                    (sub.network_type == models.NetworkType.TESTNET and request.is_testnet) or
                    (sub.network_type == models.NetworkType.MAINNET and not request.is_testnet)
                )
                
                if same_network:
                    existing_pairs = [sub.trading_pair] + (sub.secondary_trading_pairs or [])
                    for pair in requested_pairs:
                        if pair in existing_pairs:
                            conflicting_pairs.append(f"{pair} ({sub.network_type.value})")
            
            if conflicting_pairs:
                unique_conflicts = list(set(conflicting_pairs))
                logger.warning(f"Trading pair conflict for user {user_id}, bot {request.bot_id}: {unique_conflicts}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Trading pair conflict! The following trading pair(s) are already in active subscriptions: {', '.join(unique_conflicts)}. Please choose different trading pairs or stop the existing subscription first."
                )

        # Create default configs if not provided
        execution_config = request.execution_config or schemas.ExecutionConfig(
            buy_order_type="PERCENTAGE",
            buy_order_value=100.0,
            sell_order_type="ALL",
            sell_order_value=100.0
        )
        
        risk_config = bot.risk_config or schemas.RiskConfig(
            stop_loss_percent=2.0,
            take_profit_percent=4.0,
            max_position_size=100.0
        ).dict()
        
        # Create marketplace subscription
        subscription = models.Subscription(
            instance_name= f"studio_{request.bot_id}_{int(time.time())}",  # SAI
            user_id=user_id,  # Can be NULL
            bot_id=request.bot_id,
            user_principal_id=request.user_principal_id,
            
            # Marketplace-specific fields
            is_marketplace_subscription=True,
            marketplace_subscription_start=request.subscription_start,
            marketplace_subscription_end=request.subscription_end,
            
            is_testnet=request.is_testnet,
            network_type=request.trading_network,
            trading_pair=request.trading_pair,
            exchange_type=bot.exchange_type,
            secondary_trading_pairs=request.secondary_trading_pairs or [],  # Multi-pair trading
            payment_method=request.payment_method,
            paypal_payment_id=request.paypal_payment_id,
            timeframe=bot.timeframe,
            timeframes=bot.timeframes,
            trade_mode=trade_mode,

            # configs
            execution_config=execution_config.dict(),
            risk_config=risk_config,
            
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
            # Safely get bot_type value (could be enum or string)
            bot_type_val = bot.bot_type.value if hasattr(bot.bot_type, 'value') else str(bot.bot_type)
            bot_mode_val = bot.bot_mode.value if hasattr(bot.bot_mode, 'value') else str(bot.bot_mode)
            
            if bot_mode_val == models.BotMode.ACTIVE.value and bot_type_val in [models.BotType.FUTURES.value, models.BotType.SPOT.value]:
                run_bot_logic.apply_async(args=[subscription.id], countdown=10)
                logger.info(f"✅ Triggered run_bot_logic for marketplace v2 {bot_type_val} bot (subscription {subscription.id})")
            elif bot_type_val == models.BotType.FUTURES_RPA.value:
                run_bot_rpa_logic.apply_async(args=[subscription.id], countdown=10)
                logger.info(f"✅ Triggered run_bot_rpa_logic for marketplace v2 RPA bot (subscription {subscription.id})")
            elif bot_type_val == models.BotType.SIGNALS_FUTURES.value:
                run_bot_logic.apply_async(args=[subscription.id], countdown=10)
                logger.info(
                    f"✅ Triggered run_bot_rpa_logic for marketplace v2 Signals bot (subscription {subscription.id})")
            else:
                run_bot_signal_logic.apply_async(args=[bot.id, subscription.id], countdown=10)
                logger.info(f"✅ Triggered run_bot_signal_logic for marketplace v2 PASSIVE bot (subscription {subscription.id})")
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
        elif bot.bot_type and str(bot.bot_type).upper() == 'FUTURES_RPA':
            return 'active_rpa'
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


@router.post("/store-by-principal/bulk", response_model=Dict[str, Any])
async def store_credentials_bulk_by_principal_id(
    request: schemas.ExchangeCredentialsBulkByPrincipalRequest,
    api_key: str = Depends(validate_marketplace_api_key),
    db: Session = Depends(get_db)
):
    """
    Bulk store credentials and optionally upsert user settings for a marketplace principal.
    - Upsert user_settings first if provided (keyed by principal_id)
    - Deduplicate per-request items by (exchange, is_testnet) – last one wins
    - Upsert credentials by pair (principal_id, exchange, is_testnet)
    """
    try:
        allowed = {"BINANCE", "BYBIT", "OKX", "BITGET", "HUOBI", "KRAKEN", "COINBASE"}
        def _norm_exchange(e: Any) -> str:
            try:
                return (e.value if hasattr(e, 'value') else str(e)).upper()
            except Exception:
                return str(e).upper()
        results: List[Dict[str, Any]] = []

        # Upsert user settings if provided
        if request.user_settings:
            # Convert payload (without principal_id) to full settings
            settings_full = schemas.MarketplaceUserSettings(
                principal_id=request.principal_id,
                **request.user_settings.dict()
            )
            rec = crud.upsert_user_settings_by_principal(db, settings=settings_full)
            results.append({
                "type": "user_settings",
                "status": "success",
                "principal_id": rec.principal_id,
                "message": "User settings upserted"
            })

        # Deduplicate credentials by (exchange, is_testnet): last one wins
        last_by_pair: Dict[tuple, schemas.ExchangeCredentialItemByPrincipal] = {}
        for item in request.credentials:
            exch = _norm_exchange(item.exchange)
            last_by_pair[(exch, bool(item.is_testnet))] = item

        success = 0
        failed = 0
        for (exch, is_testnet), item in last_by_pair.items():
            if exch not in allowed:
                failed += 1
                results.append({
                    "type": "credentials",
                    "exchange": exch,
                    "is_testnet": is_testnet,
                    "status": "failed",
                    "message": f"Unsupported exchange. Supported: {', '.join(sorted(allowed))}"
                })
                continue

            ok = api_key_manager.store_user_exchange_credentials_by_principal_id(
                db=db,
                principal_id=request.principal_id,
                exchange=exch,
                api_key=item.api_key,
                api_secret=item.api_secret,
                api_passphrase=item.api_passphrase,
                is_testnet=is_testnet,
                credential_type=item.trading_mode or 'SPOT',
            )

            if ok:
                success += 1
                results.append({
                    "type": "credentials",
                    "exchange": exch,
                    "is_testnet": is_testnet,
                    "status": "success",
                    "message": "Stored/updated credentials for principal/exchange/is_testnet pair"
                })
            else:
                failed += 1
                results.append({
                    "type": "credentials",
                    "exchange": exch,
                    "is_testnet": is_testnet,
                    "status": "failed",
                    "message": "Failed to store credentials"
                })

        return {
            "status": "ok",
            "principal_id": request.principal_id,
            "summary": {
                "total_received": len(request.credentials),
                "processed_pairs": len(last_by_pair),
                "success": success,
                "failed": failed
            },
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to bulk store credentials/settings by principal ID: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store credentials/settings (bulk)"
        )

@router.get("/user-settings/{principal_id}", response_model=schemas.MarketplaceUserSettingsInDB)
def get_user_settings(
    principal_id: str,
    db: Session = Depends(get_db),
):
    """
    Get marketplace user settings by ICP principal_id.
    """
    rec = crud.get_user_settings_by_principal(db, principal_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User settings not found")
    return rec

@router.post("/user-settings", response_model=schemas.MarketplaceUserSettingsInDB)
def upsert_user_settings(
    body: schemas.MarketplaceUserSettings,
    api_key: bool = Depends(validate_marketplace_api_key),
    db: Session = Depends(get_db),
):
    """
    Create/update marketplace user settings by principal_id (unique).
    Requires X-API-Key.
    """
    rec = crud.upsert_user_settings_by_principal(db, body)
    return rec

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
        # 🆕 Add full bot data to token
        'bot_data': {
            'name': bot.name,
            'description': bot.description,
            'image_url': bot.image_url,
            'bot_type': bot.bot_type,
            'timeframe': bot.timeframe,
            'timeframes': bot.timeframes or [],
            'exchange_type': bot.exchange_type.value if bot.exchange_type else None,
            'trading_pair': bot.trading_pair,
            'trading_pairs': bot.trading_pairs or [],
            'strategy_config': bot.strategy_config or {},
            'risk_config': bot.risk_config or {},
        }
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

    # 🆕 Get bot data from token and update bot record
    bot_data = payload.get('bot_data', {})
    if bot_data:
        # Update bot with full data from Studio
        bot.name = bot_data.get('name', bot.name)
        bot.description = bot_data.get('description', bot.description)
        bot.image_url = bot_data.get('image_url', bot.image_url)
        bot.bot_type = bot_data.get('bot_type', bot.bot_type)
        bot.timeframe = bot_data.get('timeframe', bot.timeframe)
        bot.timeframes = bot_data.get('timeframes', bot.timeframes or [])
        if bot_data.get('exchange_type'):
            bot.exchange_type = models.ExchangeType(bot_data['exchange_type'])
        bot.trading_pair = bot_data.get('trading_pair', bot.trading_pair)
        bot.trading_pairs = bot_data.get('trading_pairs', bot.trading_pairs or [])
        bot.strategy_config = bot_data.get('strategy_config', bot.strategy_config or {})
        bot.risk_config = bot_data.get('risk_config', bot.risk_config or {})
        
        db.commit()
        db.refresh(bot)

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
            # 🆕 Show synced bot data
            "synced_bot_data": {
                "name": bot.name,
                "bot_type": bot.bot_type,
                "exchange_type": bot.exchange_type.value if bot.exchange_type else None,
                "trading_pairs": bot.trading_pairs,
                "timeframes": bot.timeframes,
                "has_strategy_config": bool(bot.strategy_config),
                "has_risk_config": bool(bot.risk_config),
            } if bot_data else None,
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
    if trading_type == 'active':
        tags = ['Active Trading']
    elif trading_type == 'passive':
        tags = ['Signal Provider']
    elif trading_type == 'active_rpa':
        tags = ['Futures RPA']
    else:
        tags = []
    timeframes = _extract_timeframes(bot)

    base_url = os.getenv('STUDIO_BASE_URL', os.getenv('API_BASE_URL', 'https://quantumforge.cryptomancer.ai'))
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
        'supported_exchanges': [bot.exchange_type.value] if bot.exchange_type else ['BINANCE'],
        'supported_pairs': bot.trading_pairs or [bot.trading_pair] if bot.trading_pair else ['BTC/USDT'],
        'risk_level': 'medium',
        'bot_type': bot.bot_type,  # 🆕 Add bot_type (spot, futures, signals)
        'tags': tags,
        'performance': { 'roi': 15.0, 'winRate': 75, 'maxDrawdown': 10, 'sharpeRatio': 1.5 },
        'images': [],
        'aiStudioBotId': bot.id,
        'apiBaseUrl': api_base,
        'apiEndpoints': api_endpoints,
        'image_url': bot.image_url or ''
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
        
        # Trigger bot execution immediately upon resume based on bot type
        bot = subscription.bot
        # Safely get bot_type value (could be enum or string)
        bot_type_val = bot.bot_type.value if hasattr(bot.bot_type, 'value') else str(bot.bot_type)
        bot_mode_val = bot.bot_mode.value if hasattr(bot.bot_mode, 'value') else str(bot.bot_mode)
        
        if bot_mode_val != models.BotMode.PASSIVE.value and bot_type_val in [models.BotType.FUTURES.value, models.BotType.SPOT.value]:
            run_bot_logic.apply_async(args=[updated_subscription.id], countdown=10)
            logger.info(f"✅ Triggered run_bot_logic for resumed {bot_type_val} bot (subscription {updated_subscription.id})")
        elif bot_type_val == models.BotType.FUTURES_RPA.value:
            run_bot_rpa_logic.apply_async(args=[updated_subscription.id], countdown=10)
            logger.info(f"✅ Triggered run_bot_rpa_logic for resumed RPA bot (subscription {updated_subscription.id})")
        else:
            run_bot_signal_logic.apply_async(args=[bot.id, updated_subscription.id], countdown=10)
            logger.info(f"✅ Triggered run_bot_signal_logic for resumed PASSIVE bot (subscription {updated_subscription.id})")
        
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

@router.post("/subscription/paypal")
async def create_subscription_from_paypal(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    authorization: Optional[str] = Header(default=None)
):
    """Create subscription from PayPal payment data"""
    try:
        logger.info(f"Received PayPal subscription request: {request}")
        
        # Extract bot API key from headers
        bot_api_key = None
        if x_api_key:
            bot_api_key = x_api_key
        elif authorization and authorization.startswith("Bearer "):
            bot_api_key = authorization[7:]  # Remove "Bearer " prefix
        
        if not bot_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bot API key required (X-API-Key or Authorization header)"
            )
        
        # Extract required fields from PayPal payload
        user_principal_id = request.get("user_principal_id")
        bot_id = request.get("bot_id") or request.get("bot_studio_id")
        duration_days = request.get("duration_days", 30)
        payment_method = request.get("payment_method", "PAYPAL")
        payment_id = request.get("payment_id")
        subscription_type = request.get("subscription_type", "daily")
        
        if not user_principal_id or not bot_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: user_principal_id, bot_id"
            )
        
        logger.info(f"Creating subscription for user {user_principal_id}, bot {bot_id}, duration {duration_days} days")
        
        # Find bot registration by API key
        bot_registration = db.query(models.BotRegistration).filter(
            models.BotRegistration.api_key == bot_api_key
        ).first()
        
        if not bot_registration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot registration not found for provided API key"
            )
        
        # Get bot details
        bot = db.query(models.Bot).filter(models.Bot.id == bot_registration.bot_id).first()
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Calculate subscription dates
        now = datetime.utcnow()
        expires_at = now + timedelta(days=duration_days)
        
        # Create subscription
        subscription_data = {
            "user_principal_id": user_principal_id,
            "bot_id": bot.id,
            "status": models.SubscriptionStatus.ACTIVE,
            "pricing_plan_id": None,  # PayPal doesn't use pricing plans
            "started_at": now,
            "expires_at": expires_at,
            "is_marketplace_subscription": True,
            "trading_pair": "BTCUSDT",
            "timeframes": ["1h"],
            "instance_name": f"paypal_{payment_id}_{int(now.timestamp())}"
        }
        
        subscription = models.Subscription(**subscription_data)
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        logger.info(f"Created subscription {subscription.id} for PayPal payment {payment_id}")
        
        # Trigger bot execution based on bot type
        try:
            # Safely get bot_type value (could be enum or string)
            bot_type_val = bot.bot_type.value if hasattr(bot.bot_type, 'value') else str(bot.bot_type)
            bot_mode_val = bot.bot_mode.value if hasattr(bot.bot_mode, 'value') else str(bot.bot_mode)
            
            if bot_mode_val != models.BotMode.PASSIVE.value and bot_type_val in [models.BotType.FUTURES.value, models.BotType.SPOT.value]:
                run_bot_logic.apply_async(args=[subscription.id], countdown=30)
                logger.info(f"✅ Triggered run_bot_logic for PayPal {bot_type_val} bot (subscription {subscription.id})")
            elif bot_type_val == models.BotType.FUTURES_RPA.value:
                run_bot_rpa_logic.apply_async(args=[subscription.id], countdown=30)
                logger.info(f"✅ Triggered run_bot_rpa_logic for PayPal RPA bot (subscription {subscription.id})")
            else:
                run_bot_signal_logic.apply_async(args=[bot.id, subscription.id], countdown=30)
                logger.info(f"✅ Triggered run_bot_signal_logic for PayPal PASSIVE bot (subscription {subscription.id})")
        except Exception as e:
            logger.warning(f"Failed to schedule bot execution: {e}")
        
        return {
            "success": True,
            "message": "Subscription created successfully from PayPal payment",
            "subscription_id": subscription.id,
            "user_principal_id": user_principal_id,
            "bot_id": bot.id,
            "bot_name": bot.name,
            "status": subscription.status.value,
            "expires_at": expires_at.isoformat(),
            "payment_id": payment_id,
            "payment_method": payment_method
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create subscription from PayPal: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subscription: {str(e)}"
        )

@router.post("/upload/image-bot")
async def upload_image_bot(
    file: UploadFile = File(...),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'bot_bucket')
    client = storage.Client.from_service_account_json(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
    storage_client = client.bucket(GCS_BUCKET_NAME)
    
    try:
        marketplace_key = os.getenv('MARKETPLACE_API_KEY', 'marketplace_dev_api_key_12345')
        if not x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is required",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Chỉ hỗ trợ JPEG, PNG, WebP")
        
        is_marketplace_key = x_api_key == marketplace_key
        bot_registration = None
        if not is_marketplace_key:
            bot_registration = crud.get_bot_registration_by_api_key(db, x_api_key)
            if not bot_registration:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid marketplace API key",
                    headers={"WWW-Authenticate": "ApiKey"},
                )
        if file.size and file.size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 5MB)")
        image = Image.open(BytesIO(await file.read()))

        max_width = 1024
        if image.width > max_width:
            ratio = max_width / float(image.width)
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height), Image.LANCZOS)

        output_buffer = BytesIO()
        image = image.convert("RGB") 
        image.save(output_buffer, format="JPEG", quality=95, optimize=True)
        output_buffer.seek(0)

        file_name = f"uploads/{uuid.uuid4()}.jpg"
        blob = storage_client.blob(file_name)
        blob.upload_from_file(output_buffer, content_type="image/jpeg")
        # blob.make_public()

        GCS_PUBLIC_URL = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}"

        public_url = f"{GCS_PUBLIC_URL}/{file_name}"
        logger.info(f"Uploaded image to {public_url}")

        return {"url": public_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscription/update", response_model=schemas.SubscriptionResponse)
async def update_marketplace_subscription(
        request: schemas.SubscriptionUpdate,
        db: Session = Depends(get_db)
):
    """Resume a paused marketplace subscription - restarts bot execution"""
    try:
        # Validate subscription access with enhanced security
        subscription, bot_registration = crud.validate_marketplace_subscription_access(
            db, request.subscription_id, request.principal_id, request.api_key
        )

        # Check if subscription is paused (only PAUSED subscriptions can be resumed)
        if subscription.status != models.SubscriptionStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update subscription with status: {subscription.status}. Only ACTIVE subscriptions can be updated."
            )

        # Check if subscription hasn't expired
        now = datetime.utcnow()
        if subscription.expires_at and subscription.expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot resume expired subscription"
            )
        # data_need_update = schemas.SubscriptionUpdate(trading_pair=request.trading_pair)
        # Update subscription status to ACTIVE
        updated_subscription = crud.update_subscription(
            db, request.subscription_id, request
        )

        logger.info(f"Update marketplace subscription {request.subscription_id} for principal {request.principal_id}")

        return schemas.SubscriptionResponse(
            subscription_id=updated_subscription.id,
            status=updated_subscription.status,
            message="Subscription updated successfully. Bot execution will restart shortly."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update marketplace subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subscription"
        )