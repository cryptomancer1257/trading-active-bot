"""
Risk Management Integration Helper
Provides easy integration of risk management into bot execution flows
"""

import logging
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from core import schemas, crud
from services.risk_management_service import RiskManagementService, RiskDecision

logger = logging.getLogger(__name__)


class RiskIntegration:
    """
    Helper class to integrate risk management into existing bot flows
    Simplifies the process of applying risk rules to trade signals
    """
    
    @staticmethod
    def apply_risk_management(
        db: Session,
        subscription_id: int,
        signal: Dict[str, Any],
        market_data: Dict[str, Any],
        account_info: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Apply risk management to a trading signal
        
        Args:
            db: Database session
            subscription_id: Subscription ID
            signal: Trading signal with action, entry_price, stop_loss, take_profit, confidence
            market_data: Current market data
            account_info: Account balance and positions
            
        Returns:
            Tuple of (approved, enhanced_signal, reason)
            - approved: Whether trade is approved
            - enhanced_signal: Signal enhanced with risk parameters (or None if rejected)
            - reason: Approval/rejection reason
        """
        try:
            # Get subscription and risk config
            subscription = crud.get_subscription_by_id(db, subscription_id)
            if not subscription or not subscription.risk_config:
                logger.warning(f"No risk config for subscription {subscription_id}, using defaults")
                return True, signal, "No risk management configured"
            
            # Parse risk config
            risk_config_dict = subscription.risk_config
            risk_config = schemas.RiskConfig(**risk_config_dict)
            
            # Initialize risk service
            risk_service = RiskManagementService(db)
            
            # Evaluate trade
            decision = risk_service.evaluate_trade(
                risk_config=risk_config,
                subscription_id=subscription_id,
                signal_data=signal,
                market_data=market_data,
                account_info=account_info
            )
            
            if not decision.approved:
                logger.warning(
                    f"Trade rejected by risk management for subscription {subscription_id}: "
                    f"{decision.reason}"
                )
                return False, None, decision.reason
            
            # Enhance signal with risk management parameters
            enhanced_signal = signal.copy()
            
            if decision.stop_loss_price:
                enhanced_signal['stop_loss'] = decision.stop_loss_price
                
            if decision.take_profit_price:
                enhanced_signal['take_profit'] = decision.take_profit_price
                
            if decision.position_size_pct:
                enhanced_signal['position_size_pct'] = decision.position_size_pct
                
            if decision.max_leverage:
                enhanced_signal['max_leverage'] = decision.max_leverage
                
            if decision.risk_reward_ratio:
                enhanced_signal['risk_reward_ratio'] = decision.risk_reward_ratio
                
            enhanced_signal['trailing_stop_enabled'] = decision.trailing_stop_active
            enhanced_signal['risk_warnings'] = decision.warnings or []
            enhanced_signal['risk_approved_at'] = str(logger.handlers[0].formatter.formatTime(logger.makeRecord('', 0, '', 0, '', (), None)))
            
            # Log approval with warnings
            log_msg = f"Trade approved by risk management ({risk_config.mode.value} mode)"
            if decision.warnings:
                log_msg += f" with warnings: {', '.join(decision.warnings)}"
            logger.info(log_msg)
            
            return True, enhanced_signal, decision.reason
            
        except Exception as e:
            logger.error(f"Error applying risk management: {e}", exc_info=True)
            # Fail-safe: approve but log error
            return True, signal, f"Risk management error (approved by default): {str(e)}"
    
    @staticmethod
    def record_trade_outcome(
        db: Session,
        subscription_id: int,
        profit_loss: float,
        was_successful: bool
    ):
        """
        Record trade outcome for risk tracking
        
        Args:
            db: Database session
            subscription_id: Subscription ID
            profit_loss: Profit or loss amount
            was_successful: Whether trade was profitable
        """
        try:
            risk_service = RiskManagementService(db)
            risk_service.record_trade_result(
                subscription_id=subscription_id,
                profit_loss=profit_loss,
                was_win=was_successful
            )
            logger.info(
                f"Recorded trade outcome for subscription {subscription_id}: "
                f"PnL=${profit_loss:.2f}, Success={was_successful}"
            )
        except Exception as e:
            logger.error(f"Error recording trade outcome: {e}", exc_info=True)
    
    @staticmethod
    def check_trading_allowed(
        db: Session,
        subscription_id: int
    ) -> Tuple[bool, str]:
        """
        Quick check if trading is currently allowed
        (without evaluating a specific trade)
        
        Returns:
            Tuple of (allowed, reason)
        """
        try:
            subscription = crud.get_subscription_by_id(db, subscription_id)
            if not subscription or not subscription.risk_config:
                return True, "No risk restrictions"
            
            risk_config = schemas.RiskConfig(**subscription.risk_config)
            risk_service = RiskManagementService(db)
            
            # Check trading window
            if not risk_service._is_within_trading_window(risk_config):
                return False, "Outside trading window"
            
            # Check cooldown
            cooldown_check = risk_service._check_cooldown(subscription_id, risk_config)
            if not cooldown_check['allowed']:
                return False, cooldown_check['reason']
            
            # Check daily loss (needs account info for accurate check)
            # This is a preliminary check
            from datetime import datetime
            today = datetime.utcnow().date()
            if subscription.last_loss_reset_date != today:
                subscription.daily_loss_amount = 0
                subscription.last_loss_reset_date = today
                db.commit()
            
            if risk_config.daily_loss_limit_percent:
                # We can't check exact limit without account balance,
                # but we can check if there's accumulated loss
                if subscription.daily_loss_amount and subscription.daily_loss_amount > 0:
                    logger.warning(
                        f"Daily loss amount: ${subscription.daily_loss_amount:.2f} "
                        f"(limit: {risk_config.daily_loss_limit_percent}%)"
                    )
            
            return True, "Trading allowed"
            
        except Exception as e:
            logger.error(f"Error checking trading allowed: {e}", exc_info=True)
            return True, "Check failed (allowed by default)"


# Convenience functions for quick integration

def apply_risk_to_signal(
    db: Session,
    subscription_id: int,
    signal: Dict[str, Any],
    market_data: Dict[str, Any],
    account_info: Dict[str, Any]
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Convenience function to apply risk management
    
    Usage:
        approved, enhanced_signal, reason = apply_risk_to_signal(
            db, subscription_id, signal, market_data, account_info
        )
        
        if not approved:
            logger.warning(f"Trade rejected: {reason}")
            return
            
        # Use enhanced_signal for trading
        entry = enhanced_signal['entry_price']
        sl = enhanced_signal['stop_loss']
        tp = enhanced_signal['take_profit']
    """
    return RiskIntegration.apply_risk_management(
        db, subscription_id, signal, market_data, account_info
    )


def record_trade(
    db: Session,
    subscription_id: int,
    pnl: float,
    is_win: bool
):
    """
    Convenience function to record trade outcome
    
    Usage:
        record_trade(db, subscription_id, profit_loss, was_profitable)
    """
    RiskIntegration.record_trade_outcome(db, subscription_id, pnl, is_win)


def is_trading_allowed(
    db: Session,
    subscription_id: int
) -> Tuple[bool, str]:
    """
    Convenience function to check if trading is allowed
    
    Usage:
        allowed, reason = is_trading_allowed(db, subscription_id)
        if not allowed:
            logger.info(f"Trading not allowed: {reason}")
            return
    """
    return RiskIntegration.check_trading_allowed(db, subscription_id)

