#!/usr/bin/env python3
"""
PayPal payment API endpoints
Handles PayPal payment creation, execution, and webhooks
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging
import json
import uuid
from datetime import datetime

from core import crud, models, schemas
from core.database import get_db
from services.paypal_service import get_paypal_service
from services.currency_service import get_currency_service

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/paypal/create-order", response_model=schemas.PayPalOrderResponse)
async def create_paypal_order(
    order_data: schemas.PayPalOrderRequest,
    db: Session = Depends(get_db)
):
    """
    Create PayPal order for bot rental
    Supports both PayPal account and guest checkout (credit/debit cards)
    """
    try:
        logger.info(f"Creating PayPal order for user: {order_data.user_principal_id}, bot: {order_data.bot_id}")
        
        # Validate bot exists and is approved
        bot = crud.get_bot_by_id(db, order_data.bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        if bot.status != models.BotStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot is not available for rental"
            )
        
        # Validate pricing tier
        valid_tiers = ["daily", "quarterly", "yearly"]
        if order_data.pricing_tier not in valid_tiers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid pricing tier. Must be one of: {valid_tiers}"
            )
        
        # Validate duration
        if order_data.duration_days < 1 or order_data.duration_days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duration must be between 1 and 365 days"
            )
        
        # Get frontend URL for redirects
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        # Create PayPal payment
        paypal_service = get_paypal_service(db)
        result = paypal_service.create_payment_order(
            user_principal_id=order_data.user_principal_id,
            bot=bot,
            duration_days=order_data.duration_days,
            pricing_tier=order_data.pricing_tier,
            frontend_url=frontend_url
        )
        
        logger.info(f"PayPal order created successfully: {result['payment_id']}")
        
        return schemas.PayPalOrderResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PayPal order creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment creation failed: {str(e)}"
        )

@router.post("/paypal/execute-payment", response_model=schemas.PayPalExecutionResponse)
async def execute_paypal_payment(
    execution_data: schemas.PayPalExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Execute PayPal payment after user approval
    Creates rental in IC canister as background task
    """
    try:
        logger.info(f"Executing PayPal payment: {execution_data.payment_id}")
        
        # Execute payment
        paypal_service = get_paypal_service(db)
        result = paypal_service.execute_payment(
            payment_id=execution_data.payment_id,
            payer_id=execution_data.payer_id
        )
        
        # Schedule rental creation and Studio sync in background
        background_tasks.add_task(
            create_rental_in_canister,
            execution_data.payment_id,
            db
        )
        
        # Schedule Studio subscription sync
        background_tasks.add_task(
            sync_payment_to_studio,
            execution_data.payment_id,
            db
        )
        
        logger.info(f"PayPal payment executed successfully: {execution_data.payment_id}")
        
        return schemas.PayPalExecutionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PayPal execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment execution failed: {str(e)}"
        )

@router.get("/paypal/payment/{payment_id}", response_model=schemas.PayPalPaymentInDB)
async def get_paypal_payment(
    payment_id: str,
    db: Session = Depends(get_db)
):
    """Get PayPal payment details"""
    payment = crud.get_paypal_payment(db, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return payment

@router.get("/paypal/payments/user/{user_principal_id}", response_model=List[schemas.PayPalPaymentInDB])
async def get_user_paypal_payments(
    user_principal_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get PayPal payments for a specific user"""
    payments = crud.get_paypal_payments_by_user(
        db=db,
        user_principal_id=user_principal_id,
        skip=skip,
        limit=limit
    )
    return payments

@router.get("/paypal/payments/summary", response_model=List[schemas.PayPalPaymentSummary])
async def get_paypal_payment_summaries(
    skip: int = 0,
    limit: int = 50,
    status_filter: str = None,
    db: Session = Depends(get_db)
):
    """Get PayPal payment summaries (admin endpoint)"""
    summaries = crud.get_paypal_payment_summaries(
        db=db,
        skip=skip,
        limit=limit,
        status_filter=status_filter
    )
    
    # Convert to proper schema format
    result = []
    for summary in summaries:
        overall_status = "PENDING"
        if summary.status == "COMPLETED" and summary.rental_id:
            overall_status = "SUCCESS"
        elif summary.status == "COMPLETED_PENDING_RENTAL":
            overall_status = "NEEDS_MANUAL_REVIEW"
        elif summary.status in ["FAILED", "CANCELLED"]:
            overall_status = "FAILED"
        
        result.append(schemas.PayPalPaymentSummary(
            id=summary.id,
            user_principal_id=summary.user_principal_id,
            bot_name=summary.bot_name,
            amount_usd=summary.amount_usd,
            status=summary.status,
            overall_status=overall_status,
            created_at=summary.created_at,
            completed_at=summary.completed_at,
            rental_id=summary.rental_id
        ))
    
    return result

@router.post("/paypal/retry-rental/{payment_id}")
async def retry_rental_creation(
    payment_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Retry rental creation for failed PayPal payment (admin endpoint)"""
    payment = crud.get_paypal_payment(db, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    if payment.status != models.PayPalPaymentStatus.COMPLETED_PENDING_RENTAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment is not in pending rental status"
        )
    
    # Schedule retry in background
    background_tasks.add_task(create_rental_in_canister, payment_id, db)
    
    return {
        "success": True,
        "message": "Rental creation retry scheduled",
        "payment_id": payment_id
    }

@router.post("/paypal/webhook")
async def paypal_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle PayPal webhook notifications
    Processes payment status updates automatically
    """
    try:
        # Get raw body and headers
        body = await request.body()
        headers = dict(request.headers)
        
        # Parse JSON data
        try:
            event_data = json.loads(body.decode())
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON in webhook payload"
            )
        
        # Verify webhook signature
        paypal_service = get_paypal_service(db)
        if not paypal_service.verify_webhook_signature(body, headers):
            logger.warning("PayPal webhook signature verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Process webhook in background
        background_tasks.add_task(
            process_webhook_event,
            event_data,
            db
        )
        
        logger.info(f"PayPal webhook received: {event_data.get('event_type')}")
        
        return {"status": "received"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )

@router.get("/paypal/config", response_model=schemas.PayPalConfigInDB)
async def get_paypal_config(db: Session = Depends(get_db)):
    """Get current PayPal configuration (admin endpoint)"""
    config = crud.get_paypal_config(db)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PayPal configuration not found"
        )
    return config

@router.post("/paypal/config", response_model=schemas.PayPalConfigInDB)
async def create_paypal_config(
    config_data: schemas.PayPalConfigCreate,
    db: Session = Depends(get_db)
):
    """Create or update PayPal configuration (admin endpoint)"""
    try:
        config = crud.create_paypal_config(db, config_data)
        logger.info(f"PayPal configuration created: {config.environment}")
        return config
    except Exception as e:
        logger.error(f"PayPal configuration creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuration creation failed"
        )

@router.post("/paypal/sync-to-studio/{payment_id}")
async def sync_payment_to_studio_endpoint(
    payment_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Manually sync PayPal payment to Studio (admin endpoint)"""
    try:
        # Verify payment exists
        payment = crud.get_paypal_payment(db, payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        if payment.status != models.PayPalPaymentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment must be completed to sync. Current status: {payment.status}"
            )
        
        # Schedule sync
        background_tasks.add_task(sync_payment_to_studio, payment_id, db)
        
        return {
            "success": True,
            "message": f"Studio sync scheduled for payment {payment_id}",
            "payment_id": payment_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Studio sync scheduling failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule Studio sync: {str(e)}"
        )

@router.get("/paypal/currency-rate")
async def get_currency_rate():
    """Get current ICP/USD exchange rate"""
    try:
        currency_service = get_currency_service()
        rate = currency_service.get_icp_usd_rate()
        cache_info = currency_service.get_cached_rate_info()
        
        return {
            "icp_usd_rate": float(rate),
            "cache_info": cache_info,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Currency rate fetch failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Currency rate fetch failed"
        )

# Background Tasks
async def create_rental_in_canister(payment_id: str, db: Session):
    """Background task to create rental in IC canister"""
    try:
        # Get fresh database session
        from core.database import SessionLocal
        db = SessionLocal()
        
        try:
            payment = crud.get_paypal_payment(db, payment_id)
            if not payment:
                logger.error(f"Payment {payment_id} not found for rental creation")
                return
            
            # Implement IC canister integration for PayPal
            logger.info(f"Creating rental in IC canister for PayPal payment: {payment_id}")
            
            # Get bot details
            bot = crud.get_bot_by_id(db, payment.bot_id)
            if not bot:
                raise Exception(f"Bot {payment.bot_id} not found")
            
            # Call IC canister to create PayPal rental
            rental_result = await create_paypal_rental_in_canister(
                payment=payment,
                bot=bot
            )
            
            if rental_result["success"]:
                # Update payment with rental ID
                crud.update_paypal_payment_status(
                    db=db,
                    payment_id=payment_id,
                    status=models.PayPalPaymentStatus.COMPLETED,
                    rental_id=rental_result["rental_id"]
                )
                logger.info(f"Rental created successfully: {rental_result['rental_id']}")
            else:
                raise Exception(f"Rental creation failed: {rental_result.get('error', 'Unknown error')}")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Rental creation failed for payment {payment_id}: {e}")
        
        # Update payment status to require manual intervention
        try:
            from core.database import SessionLocal
            db = SessionLocal()
            try:
                crud.update_paypal_payment_status(
                    db=db,
                    payment_id=payment_id,
                    status=models.PayPalPaymentStatus.COMPLETED_PENDING_RENTAL,
                    error_message=f"Rental creation failed: {str(e)}",
                    retry_count=models.PayPalPayment.retry_count + 1
                )
            finally:
                db.close()
        except Exception as update_error:
            logger.error(f"Failed to update payment status: {update_error}")

async def sync_payment_to_studio(payment_id: str, db_session: Session):
    """Background task to sync PayPal payment to Studio subscription API"""
    try:
        # Get fresh database session
        from core.database import SessionLocal
        db = SessionLocal()
        
        try:
            paypal_service = get_paypal_service(db)
            result = paypal_service.sync_subscription_to_studio(payment_id)
            
            if result["status"] == "success":
                logger.info(f"Studio sync successful for payment {payment_id}")
            elif result["status"] == "skipped":
                logger.info(f"Studio sync skipped for payment {payment_id}: {result.get('reason')}")
            else:
                logger.warning(f"Studio sync failed for payment {payment_id}: {result.get('error')}")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Studio sync failed for payment {payment_id}: {e}")

async def create_paypal_rental_in_canister(payment, bot) -> Dict[str, Any]:
    """Create rental record in IC canister for PayPal payment"""
    try:
        # Import IC canister interaction modules
        # This would typically use dfx or agent-py to call IC canisters
        # For now, we'll simulate the call structure
        
        logger.info(f"Calling IC rental_service canister for PayPal payment {payment.id}")
        
        # Prepare rental request data
        rental_request = {
            "bot_id": str(payment.bot_id),
            "user_principal_id": payment.user_principal_id,
            "duration_days": payment.duration_days,
            "pricing_tier": payment.pricing_tier,
            "payment_method": "PAYPAL",
            "payment_amount_usd": float(payment.amount_usd),
            "payment_amount_icp_equivalent": float(payment.amount_icp_equivalent),
            "exchange_rate": float(payment.exchange_rate_usd_to_icp),
            "paypal_payment_id": payment.paypal_payment_id,
            "paypal_order_id": payment.paypal_order_id,
            "timestamp": int(payment.completed_at.timestamp() * 1_000_000_000) if payment.completed_at else int(datetime.now().timestamp() * 1_000_000_000)
        }
        
        # TODO: Replace with actual IC canister call
        # Example structure for future implementation:
        # from ic_agent import ICAgent
        # agent = ICAgent(url="http://localhost:4944")
        # rental_service_id = get_rental_service_canister_id()
        # result = await agent.call(rental_service_id, "create_paypal_rental", rental_request)
        
        # For now, simulate successful rental creation
        rental_id = f"paypal_rental_{payment.id}_{int(datetime.now().timestamp())}"
        
        logger.info(f"✅ [SIMULATED] PayPal rental created in IC canister: {rental_id}")
        logger.info(f"  Bot: {bot.name} (ID: {payment.bot_id})")
        logger.info(f"  User: {payment.user_principal_id}")
        logger.info(f"  Duration: {payment.duration_days} days")
        logger.info(f"  Amount: ${payment.amount_usd} USD ({payment.amount_icp_equivalent} ICP equivalent)")
        
        return {
            "success": True,
            "rental_id": rental_id,
            "message": "PayPal rental created in IC canister"
        }
        
    except Exception as e:
        logger.error(f"Failed to create PayPal rental in IC canister: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create rental in IC canister"
        }

async def process_webhook_event(event_data: Dict[str, Any], db: Session):
    """Background task to process PayPal webhook event"""
    try:
        # Get fresh database session
        from core.database import SessionLocal
        db = SessionLocal()
        
        try:
            paypal_service = get_paypal_service(db)
            result = paypal_service.process_webhook_event(event_data)
            
            logger.info(f"Webhook event processed: {result}")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Webhook event processing failed: {e}")
