"""
Plan validation dependency for API endpoints
Checks if user's plan allows the requested action
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from core import models
from typing import Optional
from datetime import datetime


class PlanChecker:
    """Check if user's plan allows specific actions"""
    
    @staticmethod
    def is_plan_package_enabled(db: Session) -> bool:
        """
        Check if plan package feature is currently enabled
        Returns True if enabled, False if disabled
        """
        try:
            flag = db.query(models.FeatureFlag).filter(
                models.FeatureFlag.feature_type == models.FeatureFlagType.PLAN_PACKAGE
            ).first()
            
            if not flag:
                # Default to enabled if flag doesn't exist
                return True
            
            current_time = datetime.utcnow()
            
            # Check if currently in disabled period
            if (flag.disabled_from and flag.disabled_until and 
                flag.disabled_from <= current_time <= flag.disabled_until):
                return False
            
            return flag.is_enabled
            
        except Exception:
            # Default to enabled on error
            return True
    
    @staticmethod
    def check_plan_package_enabled(db: Session) -> None:
        """
        Check if plan package is enabled, raise exception if disabled
        """
        if not PlanChecker.is_plan_package_enabled(db):
            flag = db.query(models.FeatureFlag).filter(
                models.FeatureFlag.feature_type == models.FeatureFlagType.PLAN_PACKAGE
            ).first()
            
            reason = flag.reason if flag else "Plan package is temporarily disabled"
            disabled_until = flag.disabled_until if flag else None
            
            detail = reason
            if disabled_until:
                detail += f" (until {disabled_until.strftime('%Y-%m-%d %H:%M')})"
            
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=detail
            )
    
    @staticmethod
    def check_bot_creation_limit(user: models.User, db: Session) -> None:
        """
        Check if user can create a new bot based on their plan
        Raises HTTPException if limit exceeded
        """
        # First check if plan package is enabled
        if PlanChecker.is_plan_package_enabled(db):
            # Plan package is enabled, check limits normally
            pass
        else:
            # Plan package is disabled, allow unlimited bot creation
            return
        
        # Get user's plan
        user_plan = db.query(models.UserPlan).filter(
            models.UserPlan.user_id == user.id
        ).first()
        
        if not user_plan:
            # No plan found - create default free plan
            user_plan = models.UserPlan(
                user_id=user.id,
                plan_name=models.PlanName.FREE,
                max_bots=5,
                status=models.PlanStatus.ACTIVE
            )
            db.add(user_plan)
            db.commit()
            db.refresh(user_plan)
        
        # Check if plan is active
        if user_plan.status != models.PlanStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your plan is {user_plan.status.value}. Please activate or upgrade your plan."
            )
        
        # Count user's existing APPROVED bots only
        bot_count = db.query(models.Bot).filter(
            models.Bot.developer_id == user.id,
            models.Bot.status == models.BotStatus.APPROVED
        ).count()
        
        # Pro plan has unlimited bots (set to 999999)
        if user_plan.max_bots == 999999:
            return  # Pro plan - unlimited
        
        # Check limit
        if bot_count >= user_plan.max_bots:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Bot creation limit reached ({bot_count}/{user_plan.max_bots}). Upgrade to Pro for unlimited bots."
            )
    
    @staticmethod
    def check_marketplace_publish(user: models.User, db: Session) -> None:
        """
        Check if user's plan allows publishing to marketplace
        Raises HTTPException if not allowed
        """
        user_plan = db.query(models.UserPlan).filter(
            models.UserPlan.user_id == user.id
        ).first()
        
        if not user_plan or not user_plan.publish_marketplace:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Marketplace publishing requires a Pro plan. Upgrade to publish your bots."
            )
    
    @staticmethod
    def check_mainnet_access(user: models.User, db: Session, network_type: str) -> None:
        """
        Check if user's plan allows mainnet access
        Raises HTTPException if attempting to use mainnet on free plan
        """
        if network_type.lower() != "mainnet":
            return  # Testnet is always allowed
        
        user_plan = db.query(models.UserPlan).filter(
            models.UserPlan.user_id == user.id
        ).first()
        
        if not user_plan or user_plan.allowed_environment != models.NetworkType.MAINNET:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Mainnet access requires a Pro plan. Upgrade to trade on mainnet."
            )
    
    @staticmethod
    def check_subscription_limit(bot_id: int, db: Session) -> None:
        """
        Check if bot has reached subscription limit based on owner's plan
        Raises HTTPException if limit exceeded
        """
        # Get bot and owner
        bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
        if not bot:
            return  # Bot not found - will be handled by other logic
        
        user_plan = db.query(models.UserPlan).filter(
            models.UserPlan.user_id == bot.developer_id
        ).first()
        
        if not user_plan:
            return  # No plan - create default (handled elsewhere)
        
        # Count active subscriptions for this bot
        subscription_count = db.query(models.Subscription).filter(
            models.Subscription.bot_id == bot_id,
            models.Subscription.status == models.SubscriptionStatus.ACTIVE
        ).count()
        
        # Pro plan has unlimited subscriptions (set to 999999)
        if user_plan.max_subscriptions_per_bot == 999999:
            return  # Pro plan - unlimited
        
        # Check limit
        if subscription_count >= user_plan.max_subscriptions_per_bot:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This bot has reached its subscription limit ({subscription_count}/{user_plan.max_subscriptions_per_bot}). Owner needs to upgrade to Pro."
            )
    
    @staticmethod
    def check_user_subscription_limit(user: models.User, db: Session) -> None:
        """
        Check if user has reached their total subscription limit across all bots
        Free plan: 5 subscriptions total
        Pro plan: unlimited
        Raises HTTPException if limit exceeded
        """
        # First check if plan package is enabled
        if not PlanChecker.is_plan_package_enabled(db):
            # Plan package is disabled, allow unlimited subscriptions
            return
        
        # Get user's plan
        user_plan = db.query(models.UserPlan).filter(
            models.UserPlan.user_id == user.id
        ).first()
        
        if not user_plan:
            # No plan found - create default free plan
            user_plan = models.UserPlan(
                user_id=user.id,
                plan_name=models.PlanName.FREE,
                max_subscriptions_per_bot=5,  # Free plan: 5 total subscriptions
                status=models.PlanStatus.ACTIVE
            )
            db.add(user_plan)
            db.commit()
            db.refresh(user_plan)
        
        # Check if plan is active
        if user_plan.status != models.PlanStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your plan is {user_plan.status.value}. Please activate or upgrade your plan."
            )
        
        # Pro plan has unlimited subscriptions (set to 999999)
        if user_plan.max_subscriptions_per_bot == 999999:
            return  # Pro plan - unlimited
        
        # Count user's total active subscriptions across ALL bots
        total_subscriptions = db.query(models.Subscription).filter(
            models.Subscription.user_id == user.id,
            models.Subscription.status == models.SubscriptionStatus.ACTIVE
        ).count()
        
        # Check limit (Free plan: 5 total subscriptions)
        if total_subscriptions >= user_plan.max_subscriptions_per_bot:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Subscription limit reached ({total_subscriptions}/{user_plan.max_subscriptions_per_bot}). Upgrade to Pro for unlimited subscriptions."
            )


# Global instance
plan_checker = PlanChecker()

