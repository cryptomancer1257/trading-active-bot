"""
API Endpoints for Risk Management Configuration
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging

from core.database import get_db
from core import models, schemas, crud
from core.security import get_current_user
from services.risk_management_service import RiskManagementService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# BOT-LEVEL RISK CONFIGURATION (Default for all subscriptions)
# ============================================================================

@router.get("/bots/{bot_id}/risk-config", response_model=schemas.RiskConfig)
async def get_bot_risk_config(
    bot_id: int,
    db: Session = Depends(get_db)
    # TODO: Re-enable authentication: current_user: models.User = Depends(get_current_user)
):
    """Get default risk configuration for a bot"""
    bot = crud.get_bot_by_id(db, bot_id)
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    # TODO: Re-enable ownership check
    # Check ownership (only bot creator can view bot risk config)
    # if bot.developer_id != current_user.id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Not authorized to access this bot's configuration"
    #     )
    
    risk_config_dict = bot.risk_config or {}
    return schemas.RiskConfig(**risk_config_dict) if risk_config_dict else schemas.RiskConfig()


@router.put("/bots/{bot_id}/risk-config", response_model=schemas.RiskConfig)
async def update_bot_risk_config(
    bot_id: int,
    risk_config: schemas.RiskConfig,
    db: Session = Depends(get_db)
    # TODO: Re-enable authentication: current_user: models.User = Depends(get_current_user)
):
    """Update default risk configuration for a bot (used by all subscriptions unless overridden)"""
    bot = crud.get_bot_by_id(db, bot_id)
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    # TODO: Re-enable ownership check
    # Check ownership (only bot creator can modify bot risk config)
    # if bot.developer_id != current_user.id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Not authorized to modify this bot's configuration"
    #     )
    
    # Validate AI prompt if AI mode is selected
    if risk_config.mode == schemas.RiskManagementMode.AI_PROMPT:
        if risk_config.ai_prompt_id:
            prompt = crud.get_prompt_template_by_id(db, risk_config.ai_prompt_id)
            if not prompt or prompt.category != "RISK_MANAGEMENT":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid AI prompt template for risk management"
                )
        elif not risk_config.ai_prompt_custom:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="AI mode requires either ai_prompt_id or ai_prompt_custom"
            )
    
    # Update bot's default risk config
    bot.risk_config = risk_config.dict()
    bot.risk_management_mode = risk_config.mode  # Already a string due to use_enum_values
    
    db.commit()
    db.refresh(bot)
    
    logger.info(f"Updated default risk config for bot {bot_id} to {risk_config.mode} mode")
    
    return risk_config


# ============================================================================
# SUBSCRIPTION-LEVEL RISK CONFIGURATION (Overrides bot defaults)
# ============================================================================

@router.get("/subscriptions/{subscription_id}/risk-config", response_model=schemas.RiskConfig)
async def get_subscription_risk_config(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get risk configuration for a subscription"""
    subscription = crud.get_subscription_by_id(db, subscription_id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Check ownership
    if subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this subscription"
        )
    
    risk_config_dict = subscription.risk_config or {}
    return schemas.RiskConfig(**risk_config_dict)


@router.put("/subscriptions/{subscription_id}/risk-config", response_model=schemas.RiskConfig)
async def update_subscription_risk_config(
    subscription_id: int,
    risk_config: schemas.RiskConfig,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update risk configuration for a subscription"""
    subscription = crud.get_subscription_by_id(db, subscription_id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Check ownership
    if subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this subscription"
        )
    
    # Validate AI prompt if AI mode is selected
    if risk_config.mode == schemas.RiskManagementMode.AI_PROMPT:
        if risk_config.ai_prompt_id:
            prompt = crud.get_prompt_template_by_id(db, risk_config.ai_prompt_id)
            if not prompt or prompt.category != "RISK_MANAGEMENT":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid AI prompt template for risk management"
                )
        elif not risk_config.ai_prompt_custom:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="AI mode requires either ai_prompt_id or ai_prompt_custom"
            )
    
    # Update risk config
    subscription.risk_config = risk_config.dict()
    subscription.risk_management_mode = risk_config.mode  # Already a string due to use_enum_values
    
    db.commit()
    db.refresh(subscription)
    
    logger.info(f"Updated risk config for subscription {subscription_id} to {risk_config.mode} mode")
    
    return risk_config


@router.post("/subscriptions/{subscription_id}/risk-config/test", response_model=Dict[str, Any])
async def test_risk_config(
    subscription_id: int,
    test_scenario: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Test risk configuration with a hypothetical scenario
    
    Example test_scenario:
    {
        "signal": {
            "action": "BUY",
            "entry_price": 50000,
            "stop_loss": 49000,
            "take_profit": 52000,
            "confidence": 0.75
        },
        "market": {
            "current_price": 50000,
            "volatility": 0.05
        },
        "account": {
            "totalWalletBalance": 10000,
            "availableBalance": 8000,
            "positions": []
        }
    }
    """
    subscription = crud.get_subscription_by_id(db, subscription_id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Check ownership
    if subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to test this subscription"
        )
    
    # Get risk config
    risk_config_dict = subscription.risk_config or {}
    risk_config = schemas.RiskConfig(**risk_config_dict)
    
    # Run risk evaluation
    risk_service = RiskManagementService(db)
    
    decision = risk_service.evaluate_trade(
        risk_config=risk_config,
        subscription_id=subscription_id,
        signal_data=test_scenario.get('signal', {}),
        market_data=test_scenario.get('market', {}),
        account_info=test_scenario.get('account', {})
    )
    
    return {
        "approved": decision.approved,
        "reason": decision.reason,
        "stop_loss_price": decision.stop_loss_price,
        "take_profit_price": decision.take_profit_price,
        "position_size_pct": decision.position_size_pct,
        "max_leverage": decision.max_leverage,
        "risk_reward_ratio": decision.risk_reward_ratio,
        "trailing_stop_active": decision.trailing_stop_active,
        "warnings": decision.warnings
    }


@router.get("/subscriptions/{subscription_id}/risk-status", response_model=Dict[str, Any])
async def get_risk_status(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get current risk management status for a subscription"""
    subscription = crud.get_subscription_by_id(db, subscription_id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Check ownership
    if subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this subscription"
        )
    
    from datetime import datetime
    
    status_info = {
        "subscription_id": subscription_id,
        "risk_mode": subscription.risk_management_mode,
        "daily_loss_amount": float(subscription.daily_loss_amount or 0),
        "consecutive_losses": subscription.consecutive_losses or 0,
        "cooldown_active": False,
        "cooldown_remaining_minutes": 0,
        "trading_allowed": True,
        "restrictions": []
    }
    
    # Check cooldown status
    if subscription.cooldown_until:
        now = datetime.utcnow()
        if now < subscription.cooldown_until:
            remaining = (subscription.cooldown_until - now).total_seconds() / 60
            status_info["cooldown_active"] = True
            status_info["cooldown_remaining_minutes"] = round(remaining, 1)
            status_info["trading_allowed"] = False
            status_info["restrictions"].append(f"In cooldown for {remaining:.1f} more minutes")
    
    # Check daily loss limit
    risk_config_dict = subscription.risk_config or {}
    risk_config = schemas.RiskConfig(**risk_config_dict)
    
    if risk_config.daily_loss_limit_percent:
        # Need account balance to calculate
        status_info["daily_loss_limit_enabled"] = True
        status_info["daily_loss_limit_percent"] = risk_config.daily_loss_limit_percent
    
    # Check trading window
    if risk_config.trading_window and risk_config.trading_window.enabled:
        now = datetime.utcnow()
        current_hour = now.hour
        window = risk_config.trading_window
        
        is_allowed = True
        if window.start_hour is not None and window.end_hour is not None:
            if window.start_hour <= window.end_hour:
                is_allowed = window.start_hour <= current_hour < window.end_hour
            else:
                is_allowed = current_hour >= window.start_hour or current_hour < window.end_hour
        
        status_info["trading_window_enabled"] = True
        status_info["trading_window_hours"] = f"{window.start_hour}:00-{window.end_hour}:00 UTC"
        
        if not is_allowed:
            status_info["trading_allowed"] = False
            status_info["restrictions"].append("Outside trading window hours")
    
    return status_info


@router.post("/subscriptions/{subscription_id}/risk-config/reset-cooldown")
async def reset_cooldown(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Manually reset cooldown period (admin override)"""
    subscription = crud.get_subscription_by_id(db, subscription_id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Check ownership
    if subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this subscription"
        )
    
    subscription.cooldown_until = None
    subscription.consecutive_losses = 0
    db.commit()
    
    logger.info(f"Cooldown reset for subscription {subscription_id} by user {current_user.id}")
    
    return {"message": "Cooldown reset successfully"}


@router.post("/subscriptions/{subscription_id}/risk-config/reset-daily-loss")
async def reset_daily_loss(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Manually reset daily loss counter"""
    subscription = crud.get_subscription_by_id(db, subscription_id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Check ownership
    if subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this subscription"
        )
    
    from datetime import datetime
    subscription.daily_loss_amount = 0
    subscription.last_loss_reset_date = datetime.utcnow().date()
    db.commit()
    
    logger.info(f"Daily loss reset for subscription {subscription_id} by user {current_user.id}")
    
    return {"message": "Daily loss counter reset successfully"}


@router.get("/risk-management/prompts", response_model=List[Dict[str, Any]])
async def get_risk_management_prompts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get available risk management prompt templates"""
    prompts = db.query(models.LLMPromptTemplate).filter(
        models.LLMPromptTemplate.category == "RISK_MANAGEMENT",
        models.LLMPromptTemplate.is_active == True
    ).all()
    
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "content_preview": p.content[:200] + "..." if len(p.content) > 200 else p.content,
            "created_at": p.created_at,
            "win_rate": p.win_rate
        }
        for p in prompts
    ]

