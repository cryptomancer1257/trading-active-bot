"""
Risk Management Service
Handles both DEFAULT (rule-based) and AI_PROMPT (LLM-based) risk management modes
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, time as dt_time
from dataclasses import dataclass
from core import schemas
from services.llm_integration import LLMIntegrationService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class RiskDecision:
    """Risk management decision output"""
    approved: bool
    reason: str
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    position_size_pct: Optional[float] = None
    max_leverage: Optional[int] = None
    risk_reward_ratio: Optional[float] = None
    trailing_stop_active: bool = False
    warnings: list = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class RiskManagementService:
    """
    Advanced Risk Management Service
    
    Supports two modes:
    1. DEFAULT: Rule-based risk management with human configuration
    2. AI_PROMPT: LLM-based dynamic risk analysis
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMIntegrationService()
    
    def evaluate_trade(
        self,
        risk_config: schemas.RiskConfig,
        subscription_id: int,
        signal_data: Dict[str, Any],
        market_data: Dict[str, Any],
        account_info: Dict[str, Any]
    ) -> RiskDecision:
        """
        Evaluate if a trade should be executed based on risk management rules
        
        Args:
            risk_config: Risk configuration (DEFAULT or AI_PROMPT mode)
            subscription_id: Subscription ID for tracking
            signal_data: Trading signal information (action, confidence, entry, sl, tp)
            market_data: Current market conditions
            account_info: Account balance and positions
            
        Returns:
            RiskDecision with approval status and parameters
        """
        try:
            if risk_config.mode == schemas.RiskManagementMode.AI_PROMPT:
                return self._evaluate_with_ai(
                    risk_config, subscription_id, signal_data, market_data, account_info
                )
            else:
                return self._evaluate_with_rules(
                    risk_config, subscription_id, signal_data, market_data, account_info
                )
        except Exception as e:
            logger.error(f"Risk evaluation error: {e}")
            return RiskDecision(
                approved=False,
                reason=f"Risk evaluation failed: {str(e)}"
            )
    
    def _evaluate_with_rules(
        self,
        risk_config: schemas.RiskConfig,
        subscription_id: int,
        signal_data: Dict[str, Any],
        market_data: Dict[str, Any],
        account_info: Dict[str, Any]
    ) -> RiskDecision:
        """
        Rule-based risk evaluation (DEFAULT mode)
        """
        warnings = []
        
        # 1. Check Trading Window
        if not self._is_within_trading_window(risk_config):
            return RiskDecision(
                approved=False,
                reason="Outside trading window hours"
            )
        
        # 2. Check Cooldown
        cooldown_check = self._check_cooldown(subscription_id, risk_config)
        if not cooldown_check['allowed']:
            return RiskDecision(
                approved=False,
                reason=f"In cooldown period: {cooldown_check['reason']}"
            )
        
        # 3. Check Daily Loss Limit
        daily_loss_check = self._check_daily_loss_limit(subscription_id, account_info, risk_config)
        if not daily_loss_check['allowed']:
            return RiskDecision(
                approved=False,
                reason=f"Daily loss limit exceeded: {daily_loss_check['reason']}"
            )
        
        # 4. Calculate Position Size
        entry_price = float(signal_data.get('entry_price', market_data.get('current_price', 0)))
        stop_loss = signal_data.get('stop_loss')
        take_profit = signal_data.get('take_profit')
        
        # Calculate position size based on risk per trade
        account_balance = float(account_info.get('totalWalletBalance', 0))
        position_size_pct = self._calculate_position_size(
            risk_config, account_balance, entry_price, stop_loss
        )
        
        # 5. Check Risk/Reward Ratio
        if risk_config.min_risk_reward_ratio and stop_loss and take_profit:
            rr_ratio = self._calculate_rr_ratio(entry_price, stop_loss, take_profit)
            if rr_ratio < risk_config.min_risk_reward_ratio:
                return RiskDecision(
                    approved=False,
                    reason=f"RR ratio {rr_ratio:.2f} below minimum {risk_config.min_risk_reward_ratio}"
                )
        else:
            rr_ratio = None
        
        # 6. Check Max Portfolio Exposure
        if risk_config.max_portfolio_exposure:
            exposure_check = self._check_portfolio_exposure(
                account_info, position_size_pct, risk_config.max_portfolio_exposure
            )
            if not exposure_check['allowed']:
                return RiskDecision(
                    approved=False,
                    reason=f"Portfolio exposure limit: {exposure_check['reason']}"
                )
            if exposure_check.get('warning'):
                warnings.append(exposure_check['warning'])
        
        # 7. Apply Leverage Limit
        max_leverage = risk_config.max_leverage or 10  # Default 10x if not specified
        
        # 8. Setup Trailing Stop if enabled
        trailing_active = False
        if risk_config.trailing_stop and risk_config.trailing_stop.enabled:
            trailing_active = True
            warnings.append(f"Trailing stop enabled: {risk_config.trailing_stop.activation_percent}% activation")
        
        # All checks passed
        return RiskDecision(
            approved=True,
            reason="All risk checks passed",
            stop_loss_price=stop_loss,
            take_profit_price=take_profit,
            position_size_pct=position_size_pct,
            max_leverage=max_leverage,
            risk_reward_ratio=rr_ratio,
            trailing_stop_active=trailing_active,
            warnings=warnings
        )
    
    def _evaluate_with_ai(
        self,
        risk_config: schemas.RiskConfig,
        subscription_id: int,
        signal_data: Dict[str, Any],
        market_data: Dict[str, Any],
        account_info: Dict[str, Any]
    ) -> RiskDecision:
        """
        AI-based risk evaluation (AI_PROMPT mode)
        """
        try:
            # Build context for AI
            context = {
                "signal": signal_data,
                "market": market_data,
                "account": {
                    "balance": account_info.get('totalWalletBalance'),
                    "available": account_info.get('availableBalance'),
                    "positions": len(account_info.get('positions', []))
                },
                "risk_bounds": {
                    "min_stop_loss": risk_config.ai_min_stop_loss,
                    "max_stop_loss": risk_config.ai_max_stop_loss,
                    "min_take_profit": risk_config.ai_min_take_profit,
                    "max_take_profit": risk_config.ai_max_take_profit
                }
            }
            
            # Get AI prompt
            if risk_config.ai_prompt_custom:
                prompt = risk_config.ai_prompt_custom
            elif risk_config.ai_prompt_id:
                # Load prompt from database
                from core import crud
                prompt_template = crud.get_prompt_template_by_id(self.db, risk_config.ai_prompt_id)
                prompt = prompt_template.content if prompt_template else self._get_default_ai_prompt()
            else:
                prompt = self._get_default_ai_prompt()
            
            # Call LLM for risk analysis
            ai_response = self._call_ai_for_risk_analysis(prompt, context)
            
            # Parse AI response
            decision = self._parse_ai_response(ai_response, risk_config)
            
            # Apply safety bounds even for AI
            if risk_config.ai_allow_override:
                decision = self._apply_ai_safety_bounds(decision, risk_config)
            
            return decision
            
        except Exception as e:
            logger.error(f"AI risk evaluation failed: {e}")
            # Fallback to rules-based if AI fails
            logger.info("Falling back to rule-based risk management")
            return self._evaluate_with_rules(
                risk_config, subscription_id, signal_data, market_data, account_info
            )
    
    def _is_within_trading_window(self, risk_config: schemas.RiskConfig) -> bool:
        """Check if current time is within allowed trading window"""
        if not risk_config.trading_window or not risk_config.trading_window.enabled:
            return True
        
        now = datetime.utcnow()
        current_hour = now.hour
        current_day = now.weekday()  # 0=Monday, 6=Sunday
        
        window = risk_config.trading_window
        
        # Check day of week
        if window.days_of_week and current_day not in window.days_of_week:
            return False
        
        # Check hour range
        if window.start_hour is not None and window.end_hour is not None:
            if window.start_hour <= window.end_hour:
                # Normal range (e.g., 9-17)
                if not (window.start_hour <= current_hour < window.end_hour):
                    return False
            else:
                # Overnight range (e.g., 22-6)
                if not (current_hour >= window.start_hour or current_hour < window.end_hour):
                    return False
        
        return True
    
    def _check_cooldown(
        self, 
        subscription_id: int, 
        risk_config: schemas.RiskConfig
    ) -> Dict[str, Any]:
        """Check if subscription is in cooldown period"""
        if not risk_config.cooldown or not risk_config.cooldown.enabled:
            return {'allowed': True}
        
        from core import crud
        subscription = crud.get_subscription_by_id(self.db, subscription_id)
        
        if subscription.cooldown_until:
            now = datetime.utcnow()
            if now < subscription.cooldown_until:
                remaining = (subscription.cooldown_until - now).total_seconds() / 60
                return {
                    'allowed': False,
                    'reason': f"Cooldown active for {remaining:.1f} more minutes"
                }
        
        return {'allowed': True}
    
    def _check_daily_loss_limit(
        self,
        subscription_id: int,
        account_info: Dict[str, Any],
        risk_config: schemas.RiskConfig
    ) -> Dict[str, Any]:
        """Check if daily loss limit has been exceeded"""
        if not risk_config.daily_loss_limit_percent:
            return {'allowed': True}
        
        from core import crud
        subscription = crud.get_subscription_by_id(self.db, subscription_id)
        
        today = datetime.utcnow().date()
        
        # Reset daily loss if it's a new day
        if subscription.last_loss_reset_date != today:
            subscription.daily_loss_amount = 0
            subscription.last_loss_reset_date = today
            self.db.commit()
        
        account_balance = float(account_info.get('totalWalletBalance', 0))
        max_daily_loss = account_balance * (risk_config.daily_loss_limit_percent / 100)
        
        if subscription.daily_loss_amount >= max_daily_loss:
            return {
                'allowed': False,
                'reason': f"Daily loss limit reached: ${subscription.daily_loss_amount:.2f} / ${max_daily_loss:.2f}"
            }
        
        return {'allowed': True}
    
    def _calculate_position_size(
        self,
        risk_config: schemas.RiskConfig,
        account_balance: float,
        entry_price: float,
        stop_loss: Optional[float]
    ) -> float:
        """Calculate position size based on risk parameters"""
        # Default to 2% if not specified
        risk_pct = risk_config.risk_per_trade_percent or 2.0
        
        if stop_loss and entry_price:
            # Calculate based on stop loss distance
            risk_distance = abs(entry_price - stop_loss) / entry_price
            if risk_distance > 0:
                # Position size = (Account * Risk%) / Risk Distance
                position_size = (account_balance * (risk_pct / 100)) / (entry_price * risk_distance)
                position_size_pct = (position_size * entry_price) / account_balance * 100
                
                # Cap at max position size
                if risk_config.max_position_size:
                    position_size_pct = min(position_size_pct, risk_config.max_position_size)
                
                return position_size_pct
        
        # Fallback to simple percentage
        return min(risk_pct, risk_config.max_position_size or 10.0)
    
    def _calculate_rr_ratio(
        self,
        entry: float,
        stop_loss: float,
        take_profit: float
    ) -> float:
        """Calculate Risk/Reward ratio"""
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        return reward / risk if risk > 0 else 0
    
    def _check_portfolio_exposure(
        self,
        account_info: Dict[str, Any],
        new_position_pct: float,
        max_exposure_pct: float
    ) -> Dict[str, Any]:
        """Check if adding new position would exceed max portfolio exposure"""
        positions = account_info.get('positions', [])
        account_balance = float(account_info.get('totalWalletBalance', 0))
        
        # Calculate current exposure
        current_exposure = 0
        for pos in positions:
            pos_value = abs(float(pos.get('positionAmt', 0)) * float(pos.get('markPrice', 0)))
            current_exposure += pos_value
        
        current_exposure_pct = (current_exposure / account_balance * 100) if account_balance > 0 else 0
        new_total_exposure = current_exposure_pct + new_position_pct
        
        if new_total_exposure > max_exposure_pct:
            return {
                'allowed': False,
                'reason': f"Would exceed max exposure: {new_total_exposure:.1f}% > {max_exposure_pct}%"
            }
        
        warning = None
        if new_total_exposure > max_exposure_pct * 0.8:  # 80% of limit
            warning = f"High exposure: {new_total_exposure:.1f}% of {max_exposure_pct}% limit"
        
        return {
            'allowed': True,
            'current_exposure': current_exposure_pct,
            'new_total': new_total_exposure,
            'warning': warning
        }
    
    def _call_ai_for_risk_analysis(
        self,
        prompt: str,
        context: Dict[str, Any]
    ) -> str:
        """Call LLM for risk analysis"""
        # Format prompt with context
        formatted_prompt = f"""{prompt}

CURRENT CONTEXT:
Signal: {context['signal']}
Market: {context['market']}
Account: {context['account']}
Risk Bounds: {context['risk_bounds']}

Provide your risk management decision in JSON format with these fields:
{{
    "approved": true/false,
    "reason": "explanation",
    "stop_loss_price": number or null,
    "take_profit_price": number or null,
    "position_size_pct": number or null,
    "risk_reward_ratio": number or null,
    "warnings": ["warning1", "warning2"]
}}
"""
        
        response = self.llm_service.generate_response(
            prompt=formatted_prompt,
            model_name="gpt-4o-mini",
            temperature=0.3
        )
        
        return response
    
    def _parse_ai_response(
        self,
        ai_response: str,
        risk_config: schemas.RiskConfig
    ) -> RiskDecision:
        """Parse AI response into RiskDecision"""
        import json
        try:
            # Extract JSON from response
            start = ai_response.find('{')
            end = ai_response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = ai_response[start:end]
                data = json.loads(json_str)
                
                return RiskDecision(
                    approved=data.get('approved', False),
                    reason=data.get('reason', 'AI decision'),
                    stop_loss_price=data.get('stop_loss_price'),
                    take_profit_price=data.get('take_profit_price'),
                    position_size_pct=data.get('position_size_pct'),
                    risk_reward_ratio=data.get('risk_reward_ratio'),
                    warnings=data.get('warnings', [])
                )
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
        
        # Fallback
        return RiskDecision(
            approved=False,
            reason="Failed to parse AI response"
        )
    
    def _apply_ai_safety_bounds(
        self,
        decision: RiskDecision,
        risk_config: schemas.RiskConfig
    ) -> RiskDecision:
        """Apply safety bounds to AI-generated decision"""
        warnings = list(decision.warnings) if decision.warnings else []
        
        # Check stop loss bounds
        if decision.stop_loss_price:
            if risk_config.ai_min_stop_loss and decision.stop_loss_price < risk_config.ai_min_stop_loss:
                decision.stop_loss_price = risk_config.ai_min_stop_loss
                warnings.append(f"Stop loss adjusted to minimum: {risk_config.ai_min_stop_loss}")
            
            if risk_config.ai_max_stop_loss and decision.stop_loss_price > risk_config.ai_max_stop_loss:
                decision.stop_loss_price = risk_config.ai_max_stop_loss
                warnings.append(f"Stop loss capped at maximum: {risk_config.ai_max_stop_loss}")
        
        # Check take profit bounds
        if decision.take_profit_price:
            if risk_config.ai_min_take_profit and decision.take_profit_price < risk_config.ai_min_take_profit:
                decision.take_profit_price = risk_config.ai_min_take_profit
                warnings.append(f"Take profit adjusted to minimum: {risk_config.ai_min_take_profit}")
            
            if risk_config.ai_max_take_profit and decision.take_profit_price > risk_config.ai_max_take_profit:
                decision.take_profit_price = risk_config.ai_max_take_profit
                warnings.append(f"Take profit capped at maximum: {risk_config.ai_max_take_profit}")
        
        decision.warnings = warnings
        return decision
    
    def _get_default_ai_prompt(self) -> str:
        """Get default AI prompt for risk management"""
        return """You are an expert risk management advisor for cryptocurrency futures trading.

Analyze the provided trading signal and market conditions to determine if the trade should be executed.

Consider:
1. Risk/Reward ratio
2. Current market volatility
3. Account exposure
4. Stop loss and take profit levels
5. Position sizing
6. Market trends and conditions

Provide a clear recommendation with reasoning."""
    
    def record_trade_result(
        self,
        subscription_id: int,
        profit_loss: float,
        was_win: bool
    ):
        """Record trade result for tracking consecutive losses and daily loss"""
        from core import crud
        subscription = crud.get_subscription_by_id(self.db, subscription_id)
        
        if not subscription:
            return
        
        # Update daily loss tracking
        today = datetime.utcnow().date()
        if subscription.last_loss_reset_date != today:
            subscription.daily_loss_amount = 0
            subscription.last_loss_reset_date = today
        
        if not was_win:
            subscription.daily_loss_amount = (subscription.daily_loss_amount or 0) + abs(profit_loss)
            subscription.consecutive_losses = (subscription.consecutive_losses or 0) + 1
            
            # Check if cooldown should be triggered
            risk_config_dict = subscription.risk_config or {}
            risk_config = schemas.RiskConfig(**risk_config_dict)
            
            if risk_config.cooldown and risk_config.cooldown.enabled:
                if subscription.consecutive_losses >= risk_config.cooldown.trigger_loss_count:
                    # Activate cooldown
                    cooldown_until = datetime.utcnow() + timedelta(
                        minutes=risk_config.cooldown.cooldown_minutes
                    )
                    subscription.cooldown_until = cooldown_until
                    logger.warning(
                        f"Cooldown activated for subscription {subscription_id} "
                        f"until {cooldown_until} after {subscription.consecutive_losses} consecutive losses"
                    )
        else:
            # Reset consecutive losses on win
            subscription.consecutive_losses = 0
            subscription.cooldown_until = None
        
        self.db.commit()
        logger.info(
            f"Trade result recorded for subscription {subscription_id}: "
            f"PnL=${profit_loss:.2f}, Win={was_win}, "
            f"Consecutive losses={subscription.consecutive_losses}"
        )

