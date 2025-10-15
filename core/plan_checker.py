"""
Plan validation dependency for API endpoints
Checks if user's plan allows the requested action
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from core import models
from typing import Optional


class PlanChecker:
    """Check if user's plan allows specific actions"""
    
    @staticmethod
    def check_bot_creation_limit(user: models.User, db: Session) -> None:
        """
        Check if user can create a new bot based on their plan
        Raises HTTPException if limit exceeded
        """
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
        
        # Count user's existing bots
        bot_count = db.query(models.Bot).filter(
            models.Bot.developer_id == user.id
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


# Global instance
plan_checker = PlanChecker()

