"""
Plan Expiry Notification Service
Sends notifications to users whose Pro plans are about to expire or have expired
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from core import models
from core.database import SessionLocal
from services.email_service import send_email
from typing import List

logger = logging.getLogger(__name__)


class PlanExpiryNotifier:
    """Service to notify users about plan expiry"""
    
    def __init__(self):
        self.db: Session = SessionLocal()
    
    def check_and_notify_expiring_plans(self, days_before: int = 7) -> int:
        """
        Check for plans expiring in N days and send notifications
        Returns number of notifications sent
        """
        try:
            notification_count = 0
            expiry_date_threshold = datetime.now() + timedelta(days=days_before)
            
            # Find Pro plans expiring soon (within days_before days)
            expiring_plans = self.db.query(models.UserPlan).filter(
                and_(
                    models.UserPlan.plan_name == models.PlanName.PRO,
                    models.UserPlan.status == models.PlanStatus.ACTIVE,
                    models.UserPlan.expiry_date <= expiry_date_threshold,
                    models.UserPlan.expiry_date > datetime.now()
                )
            ).all()
            
            logger.info(f"Found {len(expiring_plans)} plans expiring in {days_before} days")
            
            for plan in expiring_plans:
                try:
                    self._send_expiry_reminder(plan, days_before)
                    notification_count += 1
                except Exception as e:
                    logger.error(f"Failed to send expiry notification for user {plan.user_id}: {e}")
            
            return notification_count
        except Exception as e:
            logger.error(f"Error in check_and_notify_expiring_plans: {e}")
            return 0
        finally:
            self.db.close()
    
    def check_and_downgrade_expired_plans(self) -> int:
        """
        Check for expired plans and downgrade them to Free
        Returns number of plans downgraded
        """
        try:
            downgrade_count = 0
            
            # Find expired Pro plans
            expired_plans = self.db.query(models.UserPlan).filter(
                and_(
                    models.UserPlan.plan_name == models.PlanName.PRO,
                    models.UserPlan.status == models.PlanStatus.ACTIVE,
                    models.UserPlan.expiry_date <= datetime.now()
                )
            ).all()
            
            logger.info(f"Found {len(expired_plans)} expired plans to downgrade")
            
            for plan in expired_plans:
                try:
                    self._downgrade_to_free(plan)
                    downgrade_count += 1
                except Exception as e:
                    logger.error(f"Failed to downgrade plan for user {plan.user_id}: {e}")
            
            self.db.commit()
            return downgrade_count
        except Exception as e:
            logger.error(f"Error in check_and_downgrade_expired_plans: {e}")
            self.db.rollback()
            return 0
        finally:
            self.db.close()
    
    def _send_expiry_reminder(self, plan: models.UserPlan, days_remaining: int) -> None:
        """Send expiry reminder email to user"""
        user = self.db.query(models.User).filter(models.User.id == plan.user_id).first()
        
        if not user or not user.email:
            logger.warning(f"No email found for user {plan.user_id}")
            return
        
        subject = f"⚠️ Your QuantumForge Pro Plan Expires in {days_remaining} Days"
        
        body = f"""
        <html>
        <body>
            <h2>Pro Plan Expiry Reminder</h2>
            <p>Hi {user.username},</p>
            
            <p>Your <strong>QuantumForge Pro Plan</strong> will expire in <strong>{days_remaining} days</strong> on <strong>{plan.expiry_date.strftime('%B %d, %Y')}</strong>.</p>
            
            <h3>What happens when your plan expires?</h3>
            <ul>
                <li>Your account will be downgraded to the <strong>Free Plan</strong></li>
                <li>Bot limit: <strong>5 bots maximum</strong></li>
                <li>Environment: <strong>Testnet only</strong></li>
                <li>Marketplace: <strong>Not allowed</strong></li>
                <li>Revenue share: <strong>0%</strong></li>
            </ul>
            
            <h3>Keep Your Pro Benefits</h3>
            <p>To continue enjoying unlimited bots, mainnet access, and 90% revenue share, please renew your subscription before it expires.</p>
            
            <p style="margin: 30px 0;">
                <a href="https://quantumforge.ai/plans" style="background: linear-gradient(to right, #9333ea, #ec4899); color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                    Renew Pro Plan - $10/month
                </a>
            </p>
            
            <p>If you have any questions, please contact our support team.</p>
            
            <p>Best regards,<br>
            QuantumForge Team</p>
        </body>
        </html>
        """
        
        send_email(
            to_email=user.email,
            subject=subject,
            body=body
        )
        
        logger.info(f"Sent expiry reminder to {user.email} (User ID: {user.id})")
    
    def _downgrade_to_free(self, plan: models.UserPlan) -> None:
        """Downgrade Pro plan to Free"""
        user = self.db.query(models.User).filter(models.User.id == plan.user_id).first()
        
        # Update plan to Free
        plan.plan_name = models.PlanName.FREE
        plan.price_usd = 0.00
        plan.max_bots = 5
        plan.max_subscriptions_per_bot = 5
        plan.allowed_environment = models.NetworkType.TESTNET
        plan.publish_marketplace = False
        plan.subscription_expiry_days = 3
        plan.compute_quota_per_day = 1000
        plan.revenue_share_percentage = 0.00
        plan.status = models.PlanStatus.ACTIVE
        plan.expiry_date = None
        plan.auto_renew = False
        plan.payment_method = None
        plan.paypal_subscription_id = None
        
        # Add to history
        history = models.PlanHistory(
            user_id=plan.user_id,
            plan_name=models.PlanName.FREE,
            action=models.PlanAction.DOWNGRADE,
            details={
                "reason": "Plan expired",
                "previous_plan": "pro",
                "new_plan": "free",
                "downgraded_at": datetime.now().isoformat()
            }
        )
        self.db.add(history)
        
        logger.info(f"Downgraded user {plan.user_id} from Pro to Free")
        
        # Send downgrade notification email
        if user and user.email:
            self._send_downgrade_notification(user)
    
    def _send_downgrade_notification(self, user: models.User) -> None:
        """Send downgrade notification email"""
        subject = "Your QuantumForge Plan Has Been Downgraded to Free"
        
        body = f"""
        <html>
        <body>
            <h2>Plan Downgrade Notification</h2>
            <p>Hi {user.username},</p>
            
            <p>Your <strong>Pro Plan</strong> has expired and your account has been downgraded to the <strong>Free Plan</strong>.</p>
            
            <h3>Current Plan Limits:</h3>
            <ul>
                <li>Bot limit: <strong>5 bots maximum</strong></li>
                <li>Environment: <strong>Testnet only</strong></li>
                <li>Marketplace: <strong>Not allowed</strong></li>
                <li>Revenue share: <strong>0%</strong></li>
            </ul>
            
            <h3>Upgrade to Pro Again</h3>
            <p>To restore unlimited bots, mainnet access, and 90% revenue share, upgrade to Pro anytime.</p>
            
            <p style="margin: 30px 0;">
                <a href="https://quantumforge.ai/plans" style="background: linear-gradient(to right, #9333ea, #ec4899); color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                    Upgrade to Pro - $10/month
                </a>
            </p>
            
            <p>Thank you for using QuantumForge!</p>
            
            <p>Best regards,<br>
            QuantumForge Team</p>
        </body>
        </html>
        """
        
        send_email(
            to_email=user.email,
            subject=subject,
            body=body
        )
        
        logger.info(f"Sent downgrade notification to {user.email} (User ID: {user.id})")


# Global instance
plan_expiry_notifier = PlanExpiryNotifier()


if __name__ == "__main__":
    # Manual run for testing
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        # Downgrade expired plans
        count = plan_expiry_notifier.check_and_downgrade_expired_plans()
        print(f"Downgraded {count} expired plans")
    else:
        # Send expiry reminders (7 days before)
        count = plan_expiry_notifier.check_and_notify_expiring_plans(days_before=7)
        print(f"Sent {count} expiry reminders")

