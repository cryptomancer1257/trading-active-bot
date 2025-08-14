#!/usr/bin/env python3
"""
PayPal integration service
Handles PayPal payment creation, execution, and webhook processing
"""

import paypalrestsdk
import os
import logging
import uuid
import hmac
import hashlib
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from core import models
from services.currency_service import get_currency_service

logger = logging.getLogger(__name__)

class PayPalService:
    """Service for handling PayPal payments and webhooks"""
    
    def __init__(self, db_session=None):
        self.db = db_session
        self.currency_service = get_currency_service()
        
        # PayPal configuration
        self.environment = os.getenv("PAYPAL_MODE", "sandbox")
        self.client_id = os.getenv("PAYPAL_CLIENT_ID")
        self.client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
        self.webhook_secret = os.getenv("PAYPAL_WEBHOOK_SECRET")
        
        if not self.client_id or not self.client_secret:
            logger.error("PayPal credentials not configured")
            raise ValueError("PayPal credentials missing")
        
        # Configure PayPal SDK
        paypalrestsdk.configure({
            "mode": self.environment,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        })
        
        logger.info(f"PayPal service initialized in {self.environment} mode")
    
    def calculate_pricing(self, bot: models.Bot, duration_days: int, pricing_tier: str) -> Dict[str, Decimal]:
        """Calculate pricing for bot rental in USD and ICP"""
        try:
            # Base daily price in ICP (assuming bot has daily price)
            base_daily_icp = Decimal(str(bot.price_per_month or 0)) / Decimal('30')
            if base_daily_icp <= 0:
                base_daily_icp = Decimal('2.5')  # Default daily price
            
            # Apply tier discounts
            tier_multiplier = {
                "daily": Decimal('1.0'),
                "quarterly": Decimal('0.85'),  # 15% discount
                "yearly": Decimal('0.70')      # 30% discount
            }.get(pricing_tier, Decimal('1.0'))
            
            # Calculate total ICP amount
            discounted_daily_icp = base_daily_icp * tier_multiplier
            total_icp = discounted_daily_icp * Decimal(str(duration_days))
            
            # Convert to USD
            total_usd = self.currency_service.icp_to_usd(total_icp)
            exchange_rate = self.currency_service.get_icp_usd_rate()
            
            return {
                "amount_usd": total_usd,
                "amount_icp_equivalent": total_icp,
                "exchange_rate_usd_to_icp": exchange_rate,
                "base_daily_icp": base_daily_icp,
                "tier_multiplier": tier_multiplier
            }
            
        except Exception as e:
            logger.error(f"Pricing calculation failed: {e}")
            raise ValueError(f"Pricing calculation error: {e}")
    
    def create_payment_order(self, 
                           user_principal_id: str,
                           bot: models.Bot,
                           duration_days: int,
                           pricing_tier: str,
                           frontend_url: str) -> Dict[str, Any]:
        """Create PayPal payment order"""
        try:
            # Calculate pricing
            pricing = self.calculate_pricing(bot, duration_days, pricing_tier)
            
            # Generate unique IDs
            payment_id = f"paypal_{uuid.uuid4().hex[:12]}"
            order_id = f"order_{int(datetime.now().timestamp())}"
            
            # Create PayPal payment
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "application_context": {
                    "brand_name": "AI Trading Bot Marketplace",
                    "landing_page": "BILLING",  # Start with billing for guest checkout
                    "user_action": "PAY_NOW",   # Show "Pay Now" button
                    "payment_method": {
                        "payer_selected": "PAYPAL",
                        "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED"
                    }
                },
                "redirect_urls": {
                    "return_url": f"{frontend_url}/payment/success?payment_id={payment_id}",
                    "cancel_url": f"{frontend_url}/payment/cancel?payment_id={payment_id}"
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": f"Bot Rental: {bot.name}",
                            "sku": f"bot_{bot.id}_{duration_days}d_{pricing_tier}",
                            "price": str(pricing["amount_usd"]),
                            "currency": "USD",
                            "quantity": 1,
                            "description": f"Rent {bot.name} for {duration_days} days ({pricing_tier} tier)"
                        }]
                    },
                    "amount": {
                        "total": str(pricing["amount_usd"]),
                        "currency": "USD"
                    },
                    "description": f"Bot rental payment for {bot.name}",
                    "custom": payment_id,  # Our internal reference
                    "invoice_number": order_id
                }],
                "note_to_payer": "You can pay with PayPal account or credit/debit card (no PayPal account required)"
            })
            
            if not payment.create():
                error_msg = f"PayPal payment creation failed: {payment.error}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # Get approval URL
            approval_url = None
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    break
            
            if not approval_url:
                raise Exception("No approval URL returned from PayPal")
            
            # Store payment in database
            if self.db:
                db_payment = models.PayPalPayment(
                    id=payment_id,
                    order_id=order_id,
                    user_principal_id=user_principal_id,
                    bot_id=bot.id,
                    duration_days=duration_days,
                    pricing_tier=pricing_tier,
                    amount_usd=pricing["amount_usd"],
                    amount_icp_equivalent=pricing["amount_icp_equivalent"],
                    exchange_rate_usd_to_icp=pricing["exchange_rate_usd_to_icp"],
                    status=models.PayPalPaymentStatus.PENDING,
                    paypal_order_id=payment.id,
                    paypal_approval_url=approval_url,
                    expires_at=datetime.utcnow() + timedelta(hours=1)
                )
                
                self.db.add(db_payment)
                self.db.commit()
                self.db.refresh(db_payment)
            
            return {
                "success": True,
                "payment_id": payment_id,
                "paypal_order_id": payment.id,
                "approval_url": approval_url,
                "amount_usd": pricing["amount_usd"],
                "amount_icp_equivalent": pricing["amount_icp_equivalent"],
                "expires_in_minutes": 60
            }
            
        except Exception as e:
            logger.error(f"PayPal order creation failed: {e}")
            raise
    
    def execute_payment(self, payment_id: str, payer_id: str) -> Dict[str, Any]:
        """Execute PayPal payment after user approval"""
        try:
            # Get payment from database
            if not self.db:
                raise Exception("Database session not available")
            
            db_payment = self.db.query(models.PayPalPayment).filter(
                models.PayPalPayment.id == payment_id
            ).first()
            
            if not db_payment:
                raise Exception("Payment not found")
            
            if db_payment.status != models.PayPalPaymentStatus.PENDING:
                raise Exception(f"Payment already processed. Status: {db_payment.status}")
            
            # Check expiration
            if datetime.utcnow() > db_payment.expires_at:
                db_payment.status = models.PayPalPaymentStatus.FAILED
                db_payment.error_message = "Payment expired"
                self.db.commit()
                raise Exception("Payment has expired")
            
            # Execute PayPal payment
            payment = paypalrestsdk.Payment.find(db_payment.paypal_order_id)
            
            if not payment.execute({"payer_id": payer_id}):
                error_msg = f"PayPal execution failed: {payment.error}"
                db_payment.status = models.PayPalPaymentStatus.FAILED
                db_payment.error_message = error_msg
                self.db.commit()
                raise Exception(error_msg)
            
            # Extract payer information
            payer_info = payment.payer.payer_info if payment.payer else {}
            
            # Update payment status
            db_payment.status = models.PayPalPaymentStatus.COMPLETED
            db_payment.paypal_payment_id = payment.id
            db_payment.paypal_payer_id = payer_id
            db_payment.completed_at = datetime.utcnow()
            db_payment.payer_email = payer_info.get('email')
            db_payment.payer_name = f"{payer_info.get('first_name', '')} {payer_info.get('last_name', '')}".strip()
            db_payment.payer_country_code = payer_info.get('country_code')
            
            self.db.commit()
            
            logger.info(f"PayPal payment executed successfully: {payment_id}")
            
            return {
                "success": True,
                "payment_id": payment_id,
                "paypal_payment_id": payment.id,
                "message": "Payment completed successfully",
                "rental_status": "processing"  # Rental creation will happen in background
            }
            
        except Exception as e:
            logger.error(f"PayPal execution failed for {payment_id}: {e}")
            raise
    
    def verify_webhook_signature(self, payload: bytes, headers: Dict[str, str]) -> bool:
        """Verify PayPal webhook signature"""
        if not self.webhook_secret:
            logger.warning("PayPal webhook secret not configured, skipping verification")
            return True  # Allow in development
        
        try:
            # Get signature headers
            auth_algo = headers.get('PAYPAL-AUTH-ALGO')
            transmission_id = headers.get('PAYPAL-TRANSMISSION-ID')
            cert_id = headers.get('PAYPAL-CERT-ID')
            timestamp = headers.get('PAYPAL-TRANSMISSION-TIME')
            signature = headers.get('PAYPAL-TRANSMISSION-SIG')
            
            if not all([auth_algo, transmission_id, cert_id, timestamp, signature]):
                logger.error("Missing required PayPal webhook headers")
                return False
            
            # For development, we'll implement basic HMAC verification
            # In production, use PayPal's webhook verification SDK
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature.lower(), expected_signature.lower())
            
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return False
    
    def process_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process PayPal webhook event"""
        try:
            event_type = event_data.get("event_type")
            resource = event_data.get("resource", {})
            
            # Store webhook event for audit
            if self.db:
                webhook_event = models.PayPalWebhookEvent(
                    id=event_data.get("id", str(uuid.uuid4())),
                    event_type=event_type,
                    event_data=event_data,
                    processed=False
                )
                self.db.add(webhook_event)
                self.db.commit()
            
            logger.info(f"Processing PayPal webhook event: {event_type}")
            
            # Process different event types
            if event_type == "PAYMENT.SALE.COMPLETED":
                return self._handle_payment_completed(resource)
            elif event_type == "PAYMENT.SALE.DENIED":
                return self._handle_payment_denied(resource)
            elif event_type == "PAYMENT.SALE.REFUNDED":
                return self._handle_payment_refunded(resource)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return {"status": "ignored", "event_type": event_type}
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            raise
    
    def _handle_payment_completed(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment webhook"""
        try:
            parent_payment = resource.get("parent_payment")
            if not parent_payment or not self.db:
                return {"status": "ignored", "reason": "No parent payment or database"}
            
            # Find payment by PayPal payment ID
            db_payment = self.db.query(models.PayPalPayment).filter(
                models.PayPalPayment.paypal_payment_id == parent_payment
            ).first()
            
            if not db_payment:
                logger.warning(f"Payment not found for PayPal ID: {parent_payment}")
                return {"status": "ignored", "reason": "Payment not found"}
            
            if db_payment.status == models.PayPalPaymentStatus.COMPLETED:
                return {"status": "already_processed"}
            
            # Update payment status
            db_payment.status = models.PayPalPaymentStatus.COMPLETED
            db_payment.completed_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Payment completed via webhook: {db_payment.id}")
            return {"status": "processed", "payment_id": db_payment.id}
            
        except Exception as e:
            logger.error(f"Failed to handle payment completed webhook: {e}")
            raise
    
    def _handle_payment_denied(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment webhook"""
        try:
            parent_payment = resource.get("parent_payment")
            if not parent_payment or not self.db:
                return {"status": "ignored"}
            
            db_payment = self.db.query(models.PayPalPayment).filter(
                models.PayPalPayment.paypal_payment_id == parent_payment
            ).first()
            
            if db_payment:
                db_payment.status = models.PayPalPaymentStatus.FAILED
                db_payment.error_message = "Payment denied by PayPal"
                self.db.commit()
                
                logger.info(f"Payment denied via webhook: {db_payment.id}")
                return {"status": "processed", "payment_id": db_payment.id}
            
            return {"status": "ignored", "reason": "Payment not found"}
            
        except Exception as e:
            logger.error(f"Failed to handle payment denied webhook: {e}")
            raise
    
    def _handle_payment_refunded(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Handle refunded payment webhook"""
        # TODO: Implement refund handling
        logger.info("Payment refund webhook received - manual review required")
        return {"status": "manual_review_required"}

    def sync_subscription_to_studio(self, payment_id: str) -> Dict[str, Any]:
        """Sync successful PayPal payment to Studio subscription API"""
        try:
            if not self.db:
                raise Exception("Database session not available")
            
            # Get payment details
            db_payment = self.db.query(models.PayPalPayment).filter(
                models.PayPalPayment.id == payment_id
            ).first()
            
            if not db_payment:
                raise Exception(f"Payment {payment_id} not found")
            
            if db_payment.status != models.PayPalPaymentStatus.COMPLETED:
                raise Exception(f"Payment {payment_id} not completed. Status: {db_payment.status}")
            
            # Get bot details
            from core.crud import get_bot_by_id
            bot = get_bot_by_id(self.db, db_payment.bot_id)
            if not bot:
                raise Exception(f"Bot {db_payment.bot_id} not found")
            
            # Prepare Studio API payload
            studio_payload = {
                "user_principal_id": db_payment.user_principal_id,
                "bot_id": str(db_payment.bot_id),
                "bot_studio_id": getattr(bot, 'ai_studio_bot_id', None) or str(db_payment.bot_id),
                "subscription_type": db_payment.pricing_tier,
                "duration_days": db_payment.duration_days,
                "payment_method": "PAYPAL",
                "payment_id": db_payment.id,
                "paypal_payment_id": db_payment.paypal_payment_id,
                "paypal_order_id": db_payment.paypal_order_id,
                "amount_usd": float(db_payment.amount_usd),
                "amount_icp_equivalent": float(db_payment.amount_icp_equivalent),
                "exchange_rate": float(db_payment.exchange_rate_usd_to_icp),
                "payment_completed_at": db_payment.completed_at.isoformat() if db_payment.completed_at else None,
                "rental_id": db_payment.rental_id,
                "payer_email": db_payment.payer_email,
                "payer_name": db_payment.payer_name
            }
            
            # Get Studio API configuration
            studio_api_base = os.getenv('STUDIO_API_BASE', 'http://localhost:3000')
            studio_api_key = os.getenv('STUDIO_API_KEY', '')
            
            if not studio_api_key:
                logger.warning("STUDIO_API_KEY not configured, skipping Studio sync")
                return {"status": "skipped", "reason": "No Studio API key"}
            
            # Call Studio subscription API
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {studio_api_key}',
                'X-API-Key': studio_api_key  # Some APIs might use this header instead
            }
            
            studio_url = f"{studio_api_base}/api/marketplace/subscription/paypal"
            
            logger.info(f"Syncing PayPal payment to Studio: {studio_url}")
            logger.debug(f"Studio payload: {studio_payload}")
            
            response = requests.post(
                studio_url,
                json=studio_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                studio_response = response.json()
                logger.info(f"Studio sync successful for payment {payment_id}")
                
                # Update payment with Studio sync info
                db_payment.error_message = f"Studio sync successful: {studio_response.get('message', 'OK')}"
                self.db.commit()
                
                return {
                    "status": "success",
                    "studio_response": studio_response,
                    "payment_id": payment_id
                }
            else:
                error_msg = f"Studio API returned {response.status_code}: {response.text}"
                logger.error(f"Studio sync failed for payment {payment_id}: {error_msg}")
                
                # Update payment with error info but don't fail the payment
                db_payment.error_message = f"Studio sync failed: {error_msg}"
                self.db.commit()
                
                return {
                    "status": "failed",
                    "error": error_msg,
                    "payment_id": payment_id
                }
                
        except Exception as e:
            logger.error(f"Failed to sync payment {payment_id} to Studio: {e}")
            return {
                "status": "error",
                "error": str(e),
                "payment_id": payment_id
            }

def get_paypal_service(db_session=None) -> PayPalService:
    """Get PayPal service instance"""
    return PayPalService(db_session)
