"""
Plan Management API Endpoints
Handles Free and Pro plan subscriptions, upgrades, and billing
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core import models, schemas
from core.database import get_db
from core import security
from datetime import datetime, timedelta
import logging
import os
import requests

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plans", tags=["plans"])

# PayPal configuration
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")  # sandbox or live
PAYPAL_API_BASE = "https://api-m.sandbox.paypal.com" if PAYPAL_MODE == "sandbox" else "https://api-m.paypal.com"

# Plan constants
FREE_PLAN_CONFIG = {
    "plan_name": "free",
    "price_usd": 0.00,
    "max_bots": 5,
    "max_subscriptions_per_bot": 5,
    "allowed_environment": "testnet",
    "publish_marketplace": False,
    "subscription_expiry_days": 3,
    "compute_quota_per_day": 1000,
    "revenue_share_percentage": 0.00
}

PRO_PLAN_CONFIG = {
    "plan_name": "pro",
    "price_usd": 10.00,
    "max_bots": 999999,  # Unlimited
    "max_subscriptions_per_bot": 999999,  # Unlimited
    "allowed_environment": "mainnet",
    "publish_marketplace": True,
    "subscription_expiry_days": 999999,  # Unlimited
    "compute_quota_per_day": 999999,  # Unlimited
    "revenue_share_percentage": 90.00
}


def get_paypal_access_token():
    """Get PayPal access token for API calls"""
    try:
        logger.info(f"🔑 Attempting PayPal auth - Client ID: {PAYPAL_CLIENT_ID[:20]}..., Mode: {PAYPAL_MODE}")
        response = requests.post(
            f"{PAYPAL_API_BASE}/v1/oauth2/token",
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials"}
        )
        response.raise_for_status()
        logger.info("✅ PayPal authentication successful")
        return response.json()["access_token"]
    except Exception as e:
        logger.error(f"❌ Failed to get PayPal access token: {e}")
        logger.error(f"Response: {response.text if 'response' in locals() else 'No response'}")
        raise HTTPException(status_code=500, detail="PayPal authentication failed")


def verify_paypal_payment(payment_id: str):
    """Verify PayPal payment and get details. If APPROVED, capture it first."""
    try:
        logger.info(f"🔍 Verifying PayPal order: {payment_id}")
        access_token = get_paypal_access_token()
        
        # Get order details
        response = requests.get(
            f"{PAYPAL_API_BASE}/v2/checkout/orders/{payment_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        response.raise_for_status()
        payment_data = response.json()
        
        logger.info(f"📦 PayPal order status: {payment_data.get('status')}")
        
        # If APPROVED, capture the payment
        if payment_data.get("status") == "APPROVED":
            logger.info(f"💰 Order is APPROVED, capturing payment...")
            capture_response = requests.post(
                f"{PAYPAL_API_BASE}/v2/checkout/orders/{payment_id}/capture",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
            )
            capture_response.raise_for_status()
            payment_data = capture_response.json()
            logger.info(f"✅ Payment captured! New status: {payment_data.get('status')}")
        
        # Check if payment is completed
        if payment_data.get("status") != "COMPLETED":
            logger.warning(f"⚠️ Payment not completed. Status: {payment_data.get('status')}")
            raise HTTPException(status_code=400, detail=f"Payment not completed. Status: {payment_data.get('status')}")
        
        # Get amount from capture
        amount = float(payment_data["purchase_units"][0]["payments"]["captures"][0]["amount"]["value"])
        payer_email = payment_data["payer"]["email_address"]
        
        logger.info(f"✅ Payment verified: ${amount} from {payer_email}")
        
        return {
            "status": payment_data["status"],
            "amount_usd": amount,
            "payer_email": payer_email,
            "payment_id": payment_id
        }
    except HTTPException:
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ PayPal API error for order {payment_id}: {e}")
        logger.error(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
        raise HTTPException(status_code=500, detail=f"Payment verification failed: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Failed to verify PayPal payment {payment_id}: {e}")
        raise HTTPException(status_code=500, detail="Payment verification failed")


@router.get("/current", response_model=schemas.UserPlanInDB)
def get_current_plan(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get current user's plan"""
    plan = db.query(models.UserPlan).filter(
        models.UserPlan.user_id == current_user.id
    ).first()
    
    if not plan:
        # Create default Free plan if doesn't exist
        plan = models.UserPlan(
            user_id=current_user.id,
            **FREE_PLAN_CONFIG,
            status=models.PlanStatus.ACTIVE
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
    
    return plan


@router.get("/config")
def get_plan_configs():
    """Get available plan configurations"""
    return {
        "free": FREE_PLAN_CONFIG,
        "pro": PRO_PLAN_CONFIG
    }


@router.post("/upgrade", response_model=schemas.PlanUpgradeResponse)
def upgrade_to_pro(
    request: schemas.PlanUpgradeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """
    Upgrade user to Pro plan after PayPal payment verification
    """
    try:
        # Verify PayPal payment
        payment_info = verify_paypal_payment(request.payment_id)
        
        # Check payment amount (should be $10)
        if payment_info["amount_usd"] < 10.00:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient payment amount: ${payment_info['amount_usd']}"
            )
        
        # Get or create user plan
        plan = db.query(models.UserPlan).filter(
            models.UserPlan.user_id == current_user.id
        ).first()
        
        if not plan:
            plan = models.UserPlan(user_id=current_user.id)
            db.add(plan)
        
        # Update to Pro plan
        plan.plan_name = models.PlanName.PRO
        plan.price_usd = PRO_PLAN_CONFIG["price_usd"]
        plan.max_bots = PRO_PLAN_CONFIG["max_bots"]
        plan.max_subscriptions_per_bot = PRO_PLAN_CONFIG["max_subscriptions_per_bot"]
        plan.allowed_environment = models.NetworkType.MAINNET
        plan.publish_marketplace = PRO_PLAN_CONFIG["publish_marketplace"]
        plan.subscription_expiry_days = PRO_PLAN_CONFIG["subscription_expiry_days"]
        plan.compute_quota_per_day = PRO_PLAN_CONFIG["compute_quota_per_day"]
        plan.revenue_share_percentage = PRO_PLAN_CONFIG["revenue_share_percentage"]
        plan.status = models.PlanStatus.ACTIVE
        plan.expiry_date = datetime.now() + timedelta(days=30)
        plan.auto_renew = request.auto_renew
        plan.payment_method = models.PaymentMethod.PAYPAL
        plan.last_payment_id = request.payment_id
        plan.last_payment_date = datetime.now()
        plan.next_billing_date = datetime.now() + timedelta(days=30)
        
        db.commit()
        db.refresh(plan)
        
        # Log plan history
        history = models.PlanHistory(
            user_id=current_user.id,
            plan_name=models.PlanName.PRO,
            action=models.PlanAction.UPGRADE,
            payment_id=request.payment_id,
            amount_usd=payment_info["amount_usd"],
            reason="Upgraded to Pro plan via PayPal"
        )
        db.add(history)
        db.commit()
        
        logger.info(f"User {current_user.id} upgraded to Pro plan with payment {request.payment_id}")
        
        return schemas.PlanUpgradeResponse(
            success=True,
            message="Successfully upgraded to Pro plan",
            plan=plan
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upgrade plan for user {current_user.id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upgrade plan: {str(e)}"
        )


@router.post("/cancel")
def cancel_pro_plan(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Cancel Pro plan and downgrade to Free"""
    plan = db.query(models.UserPlan).filter(
        models.UserPlan.user_id == current_user.id
    ).first()
    
    if not plan or plan.plan_name != models.PlanName.PRO:
        raise HTTPException(status_code=400, detail="Not on Pro plan")
    
    # Downgrade to Free
    plan.plan_name = models.PlanName.FREE
    plan.price_usd = FREE_PLAN_CONFIG["price_usd"]
    plan.max_bots = FREE_PLAN_CONFIG["max_bots"]
    plan.max_subscriptions_per_bot = FREE_PLAN_CONFIG["max_subscriptions_per_bot"]
    plan.allowed_environment = models.NetworkType.TESTNET
    plan.publish_marketplace = FREE_PLAN_CONFIG["publish_marketplace"]
    plan.subscription_expiry_days = FREE_PLAN_CONFIG["subscription_expiry_days"]
    plan.compute_quota_per_day = FREE_PLAN_CONFIG["compute_quota_per_day"]
    plan.revenue_share_percentage = FREE_PLAN_CONFIG["revenue_share_percentage"]
    plan.status = models.PlanStatus.ACTIVE
    plan.expiry_date = None
    plan.auto_renew = False
    plan.next_billing_date = None
    
    db.commit()
    db.refresh(plan)
    
    # Log plan history
    history = models.PlanHistory(
        user_id=current_user.id,
        plan_name=models.PlanName.FREE,
        action=models.PlanAction.DOWNGRADE,
        reason="Cancelled Pro plan"
    )
    db.add(history)
    db.commit()
    
    logger.info(f"User {current_user.id} cancelled Pro plan")
    
    return {"success": True, "message": "Pro plan cancelled", "plan": plan}


@router.get("/history", response_model=list[schemas.PlanHistoryInDB])
def get_plan_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get user's plan history"""
    history = db.query(models.PlanHistory).filter(
        models.PlanHistory.user_id == current_user.id
    ).order_by(models.PlanHistory.created_at.desc()).limit(50).all()
    
    return history


@router.get("/limits")
def get_current_limits(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get current usage vs limits for the user"""
    plan = db.query(models.UserPlan).filter(
        models.UserPlan.user_id == current_user.id
    ).first()
    
    if not plan:
        plan = models.UserPlan(user_id=current_user.id, **FREE_PLAN_CONFIG)
        db.add(plan)
        db.commit()
        db.refresh(plan)
    
    # Count current usage
    total_bots = db.query(models.Bot).filter(
        models.Bot.developer_id == current_user.id
    ).count()
    
    total_subscriptions = db.query(models.Subscription).join(
        models.Bot, models.Bot.id == models.Subscription.bot_id
    ).filter(
        models.Bot.developer_id == current_user.id,
        models.Subscription.status == models.SubscriptionStatus.ACTIVE
    ).count()
    
    return {
        "plan": {
            "name": plan.plan_name.value,
            "max_bots": plan.max_bots,
            "max_subscriptions_per_bot": plan.max_subscriptions_per_bot,
            "allowed_environment": plan.allowed_environment.value,
            "publish_marketplace": plan.publish_marketplace,
            "compute_quota_per_day": plan.compute_quota_per_day,
            "revenue_share_percentage": float(plan.revenue_share_percentage)
        },
        "usage": {
            "total_bots": total_bots,
            "total_subscriptions": total_subscriptions,
            "bots_remaining": max(0, plan.max_bots - total_bots),
            "can_create_bot": total_bots < plan.max_bots,
            "can_publish_marketplace": plan.publish_marketplace
        },
        "status": {
            "is_pro": plan.plan_name == models.PlanName.PRO,
            "is_active": plan.status == models.PlanStatus.ACTIVE,
            "expiry_date": plan.expiry_date.isoformat() if plan.expiry_date else None,
            "auto_renew": plan.auto_renew
        }
    }

