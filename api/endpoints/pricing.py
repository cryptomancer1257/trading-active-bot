#!/usr/bin/env python3
"""
Pricing management API endpoints
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from core import crud, models, schemas, security
from core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Pricing Plans ---
@router.get("/bots/{bot_id}/pricing-plans", response_model=List[schemas.PricingPlanInDB])
def get_bot_pricing_plans(
    bot_id: int,
    active_only: bool = Query(True, description="Show only active plans"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get all pricing plans for a bot"""
    # Check if bot exists
    bot = crud.get_bot_by_id(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    plans = crud.get_bot_pricing_plans(db, bot_id, active_only)
    return plans

@router.post("/bots/{bot_id}/pricing-plans", response_model=schemas.PricingPlanInDB)
def create_pricing_plan(
    bot_id: int,
    plan_data: schemas.PricingPlanCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Create a new pricing plan for a bot (Developer only)"""
    # Check if bot exists and belongs to developer
    bot = crud.get_bot_by_id(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if bot.developer_id != current_user.id and current_user.role.value != "ADMIN":
        raise HTTPException(status_code=403, detail="Not authorized to modify this bot")
    
    plan = crud.create_pricing_plan(db, plan_data, bot_id)
    return plan

@router.put("/pricing-plans/{plan_id}", response_model=schemas.PricingPlanInDB)
def update_pricing_plan(
    plan_id: int,
    plan_data: schemas.PricingPlanUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Update a pricing plan (Developer only)"""
    plan = crud.get_pricing_plan_by_id(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Pricing plan not found")
    
    # Check if user can modify this plan
    bot = crud.get_bot_by_id(db, plan.bot_id)
    if bot.developer_id != current_user.id and current_user.role.value != "ADMIN":
        raise HTTPException(status_code=403, detail="Not authorized to modify this plan")
    
    updated_plan = crud.update_pricing_plan(db, plan_id, plan_data)
    return updated_plan

@router.delete("/pricing-plans/{plan_id}")
def delete_pricing_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Delete a pricing plan (soft delete)"""
    plan = crud.get_pricing_plan_by_id(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Pricing plan not found")
    
    # Check if user can modify this plan
    bot = crud.get_bot_by_id(db, plan.bot_id)
    if bot.developer_id != current_user.id and current_user.role.value != "ADMIN":
        raise HTTPException(status_code=403, detail="Not authorized to delete this plan")
    
    success = crud.delete_pricing_plan(db, plan_id)
    if success:
        return {"message": "Pricing plan deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete pricing plan")

# --- Promotions ---
@router.get("/bots/{bot_id}/promotions", response_model=List[schemas.PromotionInDB])
def get_bot_promotions(
    bot_id: int,
    active_only: bool = Query(True, description="Show only active promotions"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get all promotions for a bot"""
    bot = crud.get_bot_by_id(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    promotions = crud.get_bot_promotions(db, bot_id, active_only)
    return promotions

@router.post("/bots/{bot_id}/promotions", response_model=schemas.PromotionInDB)
def create_promotion(
    bot_id: int,
    promotion_data: schemas.PromotionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Create a new promotion for a bot (Developer only)"""
    bot = crud.get_bot_by_id(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if bot.developer_id != current_user.id and current_user.role.value != "ADMIN":
        raise HTTPException(status_code=403, detail="Not authorized to create promotions for this bot")
    
    promotion = crud.create_promotion(db, promotion_data, bot_id, current_user.id)
    return promotion

@router.post("/promotions/validate")
def validate_promotion_code(
    promotion_code: str,
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Validate a promotion code"""
    promotion, error = crud.validate_promotion(db, promotion_code, bot_id, current_user.id)
    
    if error:
        return {
            "valid": False,
            "error": error
        }
    
    return {
        "valid": True,
        "promotion": {
            "code": promotion.promotion_code,
            "name": promotion.promotion_name,
            "discount_type": promotion.discount_type,
            "discount_value": promotion.discount_value,
            "description": promotion.promotion_description
        }
    }

# --- Invoices ---
@router.get("/invoices", response_model=List[schemas.InvoiceInDB])
def get_user_invoices(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get user's invoices"""
    invoices = crud.get_user_invoices(db, current_user.id, skip, limit)
    return invoices

@router.get("/subscriptions/{subscription_id}/invoices", response_model=List[schemas.InvoiceInDB])
def get_subscription_invoices(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get invoices for a specific subscription"""
    # Check if subscription belongs to user
    subscription = crud.get_subscription_by_id(db, subscription_id)
    if not subscription or subscription.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    invoices = crud.get_subscription_invoices(db, subscription_id)
    return invoices

# --- Enhanced Subscription Creation ---
@router.post("/subscriptions/with-plan", response_model=schemas.SubscriptionResponse)
def create_subscription_with_plan(
    subscription_data: schemas.SubscriptionCreate,
    pricing_plan_id: int,
    promotion_code: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Create subscription with specific pricing plan and optional promotion"""
    try:
        subscription = crud.create_subscription_with_plan(
            db, subscription_data, current_user.id, pricing_plan_id, promotion_code
        )
        
        return schemas.SubscriptionResponse(
            subscription_id=subscription.id,
            status=subscription.status.value,
            message="Subscription created successfully with pricing plan"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create subscription: {str(e)}")

# --- Pricing Calculator ---
@router.get("/calculate-price")
def calculate_subscription_price(
    pricing_plan_id: int,
    billing_cycle: str = Query("MONTHLY", description="MONTHLY, QUARTERLY, YEARLY"),
    promotion_code: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Calculate subscription price with discounts"""
    pricing_plan = crud.get_pricing_plan_by_id(db, pricing_plan_id)
    if not pricing_plan:
        raise HTTPException(status_code=404, detail="Pricing plan not found")
    
    promotion = None
    if promotion_code:
        promotion, error = crud.validate_promotion(db, promotion_code, pricing_plan.bot_id, current_user.id)
        if error:
            return {
                "valid": False,
                "error": error,
                "pricing": None
            }
    
    pricing = crud.calculate_subscription_price(pricing_plan, billing_cycle, promotion)
    
    return {
        "valid": True,
        "pricing": pricing,
        "plan": {
            "name": pricing_plan.plan_name,
            "description": pricing_plan.plan_description,
            "features": pricing_plan.advanced_features
        },
        "promotion": {
            "code": promotion.promotion_code if promotion else None,
            "name": promotion.promotion_name if promotion else None,
            "discount_type": promotion.discount_type if promotion else None,
            "discount_value": promotion.discount_value if promotion else None
        }
    } 