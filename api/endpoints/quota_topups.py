"""
Quota Top-up API Endpoints
Handles LLM quota top-up purchases for PRO and ULTRA plan users
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core import models, schemas
from core.database import get_db
from core import security
from datetime import datetime
import logging
import os
import requests
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["quota-topups"])

# Request/Response schemas
class CreatePayPalOrderRequest(BaseModel):
    package: str

class CreatePayPalOrderResponse(BaseModel):
    order_id: str
    approve_url: str
    package: dict
    amount: float

# PayPal configuration
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")  # sandbox or live
PAYPAL_API_BASE = "https://api-m.sandbox.paypal.com" if PAYPAL_MODE == "sandbox" else "https://api-m.paypal.com"

# Quota top-up packages
QUOTA_PACKAGES = {
    "small": {
        "name": "Small Pack",
        "quota": 300,
        "price": 20.00,
        "description": "300 additional LLM API calls",
        "icon": "📦"
    },
    "medium": {
        "name": "Medium Pack", 
        "quota": 700,
        "price": 50.00,
        "description": "700 additional LLM API calls",
        "icon": "📦📦"
    },
    "large": {
        "name": "Large Pack",
        "quota": 1500,
        "price": 100.00,
        "description": "1500 additional LLM API calls", 
        "icon": "📦📦📦"
    }
}

def get_paypal_access_token():
    """Get PayPal access token for API calls"""
    try:
        logger.info(f"🔑 Getting PayPal access token - Mode: {PAYPAL_MODE}")
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
        raise HTTPException(status_code=500, detail="PayPal authentication failed")

def verify_paypal_payment(payment_id: str):
    """Verify PayPal payment and get details"""
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
        
        if payment_data.get('status') != 'COMPLETED':
            raise HTTPException(
                status_code=400, 
                detail=f"Payment not completed. Status: {payment_data.get('status')}"
            )
        
        # Extract amount and currency
        purchase_units = payment_data.get('purchase_units', [])
        if not purchase_units:
            raise HTTPException(status_code=400, detail="No purchase units found")
        
        amount = purchase_units[0].get('amount', {})
        return {
            "status": payment_data.get('status'),
            "amount": float(amount.get('value', 0)),
            "currency": amount.get('currency_code', 'USD')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to verify PayPal payment: {e}")
        raise HTTPException(status_code=500, detail="Payment verification failed")

@router.get("/packages")
def get_quota_packages():
    """Get available quota top-up packages"""
    return {
        "packages": QUOTA_PACKAGES,
        "currency": "USD"
    }

@router.get("/usage")
def get_quota_usage(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Get current quota usage for the user"""
    try:
        # Get user's plan
        user_plan = db.query(models.UserPlan).filter(
            models.UserPlan.user_id == current_user.id,
            models.UserPlan.status == models.PlanStatus.ACTIVE
        ).first()
        
        if not user_plan:
            raise HTTPException(
                status_code=404, 
                detail="No active plan found"
            )
        
        # Calculate remaining quota
        remaining = user_plan.llm_quota_total - user_plan.llm_quota_used
        percentage = (user_plan.llm_quota_used / user_plan.llm_quota_total * 100) if user_plan.llm_quota_total > 0 else 0
        
        return {
            "total": user_plan.llm_quota_total,
            "used": user_plan.llm_quota_used,
            "remaining": remaining,
            "percentage": round(percentage, 1),
            "reset_at": user_plan.llm_quota_reset_at.isoformat() if user_plan.llm_quota_reset_at else None,
            "plan_name": user_plan.plan_name.value,
            "can_purchase": user_plan.plan_name in [models.PlanName.PRO, models.PlanName.ULTRA]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting quota usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quota usage")

@router.post("/purchase")
def purchase_quota_topup(
    package: str,
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Purchase additional LLM quota"""
    try:
        # Validate package
        if package not in QUOTA_PACKAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid package. Available: {list(QUOTA_PACKAGES.keys())}"
            )
        
        package_info = QUOTA_PACKAGES[package]
        
        # Check if user has an active plan
        user_plan = db.query(models.UserPlan).filter(
            models.UserPlan.user_id == current_user.id,
            models.UserPlan.status == models.PlanStatus.ACTIVE
        ).first()
        
        if not user_plan:
            raise HTTPException(
                status_code=404,
                detail="No active plan found"
            )
        
        # Check if user can purchase top-ups (PRO or ULTRA only)
        if user_plan.plan_name not in [models.PlanName.PRO, models.PlanName.ULTRA]:
            raise HTTPException(
                status_code=403,
                detail="Quota top-ups are only available for PRO and ULTRA plans"
            )
        
        # Verify PayPal payment
        payment_details = verify_paypal_payment(payment_id)
        
        # Check if payment amount matches package price
        if abs(payment_details["amount"] - package_info["price"]) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Payment amount mismatch. Expected: ${package_info['price']}, Received: ${payment_details['amount']}"
            )
        
        # Create quota top-up record
        quota_topup = models.QuotaTopUp(
            user_id=current_user.id,
            quota_amount=package_info["quota"],
            price_usd=package_info["price"],
            payment_method=models.PaymentMethod.PAYPAL,
            payment_id=payment_id,
            payment_status="completed",
            applied_at=datetime.now()
        )
        
        db.add(quota_topup)
        
        # Add quota to user's plan
        user_plan.llm_quota_total += package_info["quota"]
        
        # Commit changes
        db.commit()
        
        logger.info(f"✅ Quota top-up purchased: User {current_user.id}, Package: {package}, Quota: +{package_info['quota']}")
        
        return {
            "success": True,
            "message": f"Successfully purchased {package_info['quota']} additional LLM calls",
            "quota_added": package_info["quota"],
            "new_total": user_plan.llm_quota_total,
            "remaining": user_plan.llm_quota_total - user_plan.llm_quota_used
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error purchasing quota top-up: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to purchase quota top-up")

@router.get("/history")
def get_quota_topup_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Get user's quota top-up purchase history"""
    try:
        topups = db.query(models.QuotaTopUp).filter(
            models.QuotaTopUp.user_id == current_user.id
        ).order_by(models.QuotaTopUp.created_at.desc()).all()
        
        return {
            "topups": [
                {
                    "id": topup.id,
                    "quota_amount": topup.quota_amount,
                    "price_usd": float(topup.price_usd),
                    "payment_method": topup.payment_method.value,
                    "payment_status": topup.payment_status,
                    "created_at": topup.created_at.isoformat(),
                    "applied_at": topup.applied_at.isoformat() if topup.applied_at else None
                }
                for topup in topups
            ],
            "total_purchased": sum(topup.quota_amount for topup in topups),
            "total_spent": sum(float(topup.price_usd) for topup in topups)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting quota top-up history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quota top-up history")

@router.post("/create-paypal-order-demo", response_model=CreatePayPalOrderResponse)
def create_paypal_order_demo(request: CreatePayPalOrderRequest):
    """Create PayPal order for quota top-up purchase (DEMO MODE - No auth required)"""
    try:
        package = request.package
        # Validate package
        if package not in QUOTA_PACKAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid package. Available: {list(QUOTA_PACKAGES.keys())}"
            )
        
        package_info = QUOTA_PACKAGES[package]
        
        # For demo mode, return a fake PayPal order
        logger.info(f"🎭 DEMO MODE: Creating fake PayPal order for package: {package}")
        
        # Create demo PayPal URL with proper redirect
        # Use clean URL to avoid DEVELOPMENT_MODE issues
        clean_frontend_url = 'http://localhost:3001'
        demo_token = f"demo_{package}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # URL encode the redirect URLs
        import urllib.parse
        return_url = urllib.parse.quote(f"{clean_frontend_url}/quota-success", safe='')
        cancel_url = urllib.parse.quote(f"{clean_frontend_url}/quota-cancel", safe='')
        
        return CreatePayPalOrderResponse(
            order_id=demo_token,
            approve_url=f"https://www.sandbox.paypal.com/checkoutnow?token={demo_token}&return_url={return_url}&cancel_url={cancel_url}",
            package=package_info,
            amount=package_info["price"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating demo PayPal order: {e}")
        raise HTTPException(status_code=500, detail="Failed to create demo PayPal order")

@router.post("/create-paypal-order", response_model=CreatePayPalOrderResponse)
def create_paypal_order(
    request: CreatePayPalOrderRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Create PayPal order for quota top-up purchase"""
    try:
        package = request.package
        # Validate package
        if package not in QUOTA_PACKAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid package. Available: {list(QUOTA_PACKAGES.keys())}"
            )
        
        package_info = QUOTA_PACKAGES[package]
        
        # Check if user can purchase top-ups
        user_plan = db.query(models.UserPlan).filter(
            models.UserPlan.user_id == current_user.id,
            models.UserPlan.status == models.PlanStatus.ACTIVE
        ).first()
        
        if not user_plan or user_plan.plan_name not in [models.PlanName.PRO, models.PlanName.ULTRA]:
            raise HTTPException(
                status_code=403,
                detail="Quota top-ups are only available for PRO and ULTRA plans"
            )
        
        # Create PayPal order
        access_token = get_paypal_access_token()
        
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "USD",
                        "value": str(package_info["price"])
                    },
                    "description": f"LLM Quota Top-up: {package_info['name']} - {package_info['quota']} calls"
                }
            ],
            "application_context": {
                "return_url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3001')}/quota-success",
                "cancel_url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3001')}/quota-cancel"
            }
        }
        
        response = requests.post(
            f"{PAYPAL_API_BASE}/v2/checkout/orders",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=order_data
        )
        response.raise_for_status()
        
        order_result = response.json()
        
        logger.info(f"✅ PayPal order created: {order_result.get('id')}")
        
        return {
            "order_id": order_result.get("id"),
            "approve_url": next(
                (link["href"] for link in order_result.get("links", []) if link["rel"] == "approve"),
                None
            ),
            "package": package_info,
            "amount": package_info["price"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating PayPal order: {e}")
        raise HTTPException(status_code=500, detail="Failed to create PayPal order")
