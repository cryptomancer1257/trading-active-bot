"""
Quota Top-up API Endpoints
Handles LLM quota top-up purchases for PRO and ULTRA plan users
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
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
        "quota": 500,
        "price": 20.00,
        "description": "500 additional Trade times",
        "icon": "📦"
    },
    "medium": {
        "name": "Medium Pack", 
        "quota": 1300,
        "price": 50.00,
        "description": "1300 additional Trade times",
        "icon": "📦📦"
    },
    "large": {
        "name": "Large Pack",
        "quota": 2800,
        "price": 100.00,
        "description": "2800 additional Trade times", 
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
        
        # If no active plan, return default FREE plan values
        if not user_plan:
            return {
                "total": 0,
                "used": 0,
                "remaining": 0,
                "percentage": 0,
                "reset_at": None,
                "plan_name": "free",
                "can_purchase": False
            }
        
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
        logger.info(f"🎭 Demo PayPal order requested - PAYPAL_MODE: {PAYPAL_MODE}")
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
        
        # Use correct PayPal domain based on PAYPAL_MODE
        paypal_checkout_domain = "www.sandbox.paypal.com" if PAYPAL_MODE == "sandbox" else "www.paypal.com"
        
        return CreatePayPalOrderResponse(
            order_id=demo_token,
            approve_url=f"https://{paypal_checkout_domain}/checkoutnow?token={demo_token}&return_url={return_url}&cancel_url={cancel_url}",
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
        logger.info(f"🔐 Real PayPal order requested - PAYPAL_MODE: {PAYPAL_MODE}, API Base: {PAYPAL_API_BASE}")
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

@router.post("/complete-paypal-purchase")
def complete_paypal_purchase(
    token: str = Body(...),
    payer_id: str = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Complete PayPal purchase and add quota to user"""
    try:
        logger.info(f"🔄 Completing PayPal purchase for user {current_user.id}, token: {token}, payer_id: {payer_id}")
        
        # Check if this is a demo/test token
        is_demo = token.startswith("demo_") or "DEVELOPMENT" in token
        
        if is_demo:
            logger.info(f"🎭 Demo mode detected, using default small package")
            # For demo mode, assume small package ($20)
            package_key = "small"
            package_info = QUOTA_PACKAGES["small"]
        else:
            # Real PayPal flow
            # Check if this order was already processed
            existing_topup = db.query(models.QuotaTopUp).filter(
                models.QuotaTopUp.payment_id == token
            ).first()
            
            if existing_topup:
                logger.info(f"⚠️ Order {token} already processed, returning existing purchase info")
                # Get user plan for current quota
                user_plan = db.query(models.UserPlan).filter(
                    models.UserPlan.user_id == current_user.id,
                    models.UserPlan.status == models.PlanStatus.ACTIVE
                ).first()
                
                return {
                    "success": True,
                    "message": f"Payment already processed. {existing_topup.quota_amount} calls were added to your account.",
                    "quota_added": existing_topup.quota_amount,
                    "new_total": user_plan.llm_quota_total if user_plan else 0,
                    "remaining": (user_plan.llm_quota_total - user_plan.llm_quota_used) if user_plan else 0
                }
            
            # Get PayPal access token
            access_token = get_paypal_access_token()
            
            # Capture the PayPal order
            capture_url = f"{PAYPAL_API_BASE}/v2/checkout/orders/{token}/capture"
            capture_response = requests.post(
                capture_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
            )
            
            if capture_response.status_code != 201:
                # Check if order was already captured
                response_data = capture_response.json()
                if "ORDER_ALREADY_CAPTURED" in str(response_data):
                    logger.warning(f"⚠️ Order {token} already captured by PayPal")
                    # Try to get order details instead
                    order_url = f"{PAYPAL_API_BASE}/v2/checkout/orders/{token}"
                    order_response = requests.get(
                        order_url,
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    if order_response.status_code == 200:
                        capture_result = order_response.json()
                        logger.info(f"✅ Retrieved order details for already captured order")
                    else:
                        logger.error(f"❌ PayPal capture failed: {capture_response.text}")
                        raise HTTPException(
                            status_code=400,
                            detail="Payment was already processed. Please check your quota or contact support."
                        )
                else:
                    logger.error(f"❌ PayPal capture failed: {capture_response.text}")
                    raise HTTPException(
                        status_code=400,
                        detail="Payment capture failed. Please contact support."
                    )
            else:
                capture_result = capture_response.json()
                logger.info(f"✅ PayPal capture successful: {capture_result.get('id')}")
            
            # Extract purchase details
            purchase_units = capture_result.get("purchase_units", [])
            if not purchase_units:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid PayPal response"
                )
            
            # Try to get amount from different possible locations in PayPal response
            amount = None
            try:
                # Try from purchase_units[0].amount.value
                if "amount" in purchase_units[0] and "value" in purchase_units[0]["amount"]:
                    amount = float(purchase_units[0]["amount"]["value"])
                # Try from purchase_units[0].payments.captures[0].amount.value
                elif "payments" in purchase_units[0] and "captures" in purchase_units[0]["payments"]:
                    captures = purchase_units[0]["payments"]["captures"]
                    if captures and "amount" in captures[0] and "value" in captures[0]["amount"]:
                        amount = float(captures[0]["amount"]["value"])
            except (KeyError, IndexError, ValueError) as e:
                logger.error(f"❌ Error parsing amount from PayPal response: {e}")
                logger.error(f"PayPal response: {capture_result}")
                raise HTTPException(
                    status_code=400,
                    detail="Failed to parse payment amount from PayPal"
                )
            
            if amount is None:
                raise HTTPException(
                    status_code=400,
                    detail="Could not find payment amount in PayPal response"
                )
            
            # Determine which package was purchased based on amount
            package_key = None
            package_info = None
            for key, pkg in QUOTA_PACKAGES.items():
                if abs(pkg["price"] - amount) < 0.01:
                    package_key = key
                    package_info = pkg
                    break
            
            if not package_info:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid purchase amount: ${amount}"
                )
        
        # Get user plan
        user_plan = db.query(models.UserPlan).filter(
            models.UserPlan.user_id == current_user.id,
            models.UserPlan.status == models.PlanStatus.ACTIVE
        ).first()
        
        if not user_plan:
            raise HTTPException(
                status_code=404,
                detail="No active plan found"
            )
        
        # Create quota top-up record
        quota_topup = models.QuotaTopUp(
            user_id=current_user.id,
            quota_amount=package_info["quota"],
            price_usd=package_info["price"],
            payment_method=models.PaymentMethod.PAYPAL,
            payment_id=token,
            payment_status="completed",
            applied_at=datetime.now()
        )
        
        db.add(quota_topup)
        
        # Add quota to user's plan
        old_total = user_plan.llm_quota_total
        user_plan.llm_quota_total += package_info["quota"]
        
        # Commit changes
        db.commit()
        
        logger.info(f"✅ Quota top-up completed: User {current_user.id}, Package: {package_key}, Quota: +{package_info['quota']}")
        
        return {
            "success": True,
            "message": f"Successfully purchased {package_info['quota']} additional LLM calls",
            "quota_added": package_info["quota"],
            "old_total": old_total,
            "new_total": user_plan.llm_quota_total,
            "remaining": user_plan.llm_quota_total - user_plan.llm_quota_used
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error completing PayPal purchase: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to complete purchase")
