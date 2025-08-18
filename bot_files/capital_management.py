"""
Advanced Capital Management System for Crypto Futures Trading
Integrates multiple position sizing strategies with LLM-based risk assessment
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)

@dataclass
class RiskMetrics:
    """Risk assessment metrics for position sizing"""
    account_balance: float
    available_balance: float
    current_drawdown: float
    max_drawdown: float
    portfolio_exposure: float
    volatility: float
    var_95: float  # Value at Risk 95%
    sharpe_ratio: float
    win_rate: float
    avg_win_loss_ratio: float

@dataclass
class PositionSizeRecommendation:
    """Position size recommendation with rationale"""
    recommended_size_pct: float  # % of account balance
    max_size_pct: float  # Maximum allowed size
    risk_level: str  # LOW, MEDIUM, HIGH
    sizing_method: str  # Method used for calculation
    confidence_adjustment: float  # Adjustment based on signal confidence
    volatility_adjustment: float  # Adjustment based on market volatility
    drawdown_adjustment: float  # Adjustment based on current drawdown
    llm_recommendation: Optional[Dict[str, Any]] = None
    reasoning: str = ""

class CapitalManagement:
    """Advanced Capital Management System"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize capital management system"""
        # Base configuration
        self.base_position_size_pct = config.get('base_position_size_pct', 0.02)  # 2% base
        self.max_position_size_pct = config.get('max_position_size_pct', 0.10)   # 10% max
        self.max_portfolio_exposure = config.get('max_portfolio_exposure', 0.30) # 30% total
        
        # Risk management thresholds
        self.max_drawdown_threshold = config.get('max_drawdown_threshold', 0.15)  # 15%
        self.volatility_threshold_low = config.get('volatility_threshold_low', 0.02)   # 2%
        self.volatility_threshold_high = config.get('volatility_threshold_high', 0.08)  # 8%
        
        # Kelly Criterion parameters
        self.kelly_multiplier = config.get('kelly_multiplier', 0.25)  # Use 25% of Kelly
        self.min_win_rate = config.get('min_win_rate', 0.35)  # Minimum 35% win rate
        
        # LLM integration
        self.use_llm_capital_management = config.get('use_llm_capital_management', True)
        self.llm_weight = config.get('llm_capital_weight', 0.40)  # 40% weight to LLM advice
        
        # Position sizing methods
        self.sizing_methods = {
            'fixed': self._fixed_percentage_sizing,
            'kelly': self._kelly_criterion_sizing,
            'volatility': self._volatility_based_sizing,
            'atr': self._atr_based_sizing,
            'confidence': self._confidence_based_sizing,
            'llm_hybrid': self._llm_hybrid_sizing
        }
        
        self.default_method = config.get('sizing_method', 'llm_hybrid')
        
        logger.info(f"Capital Management initialized - Base: {self.base_position_size_pct*100:.1f}%, Max: {self.max_position_size_pct*100:.1f}%")
        
    def calculate_position_size(self, 
                              signal_confidence: float,
                              risk_metrics: RiskMetrics,
                              market_data: Dict[str, Any],
                              llm_service: Optional[Any] = None) -> PositionSizeRecommendation:
        """Calculate optimal position size using multiple strategies"""
        try:
            # Get base calculations from different methods
            sizing_results = {}
            
            for method_name, method_func in self.sizing_methods.items():
                if method_name == 'llm_hybrid' and not llm_service:
                    continue  # Skip LLM method if service unavailable
                    
                try:
                    size_pct = method_func(signal_confidence, risk_metrics, market_data, llm_service)
                    sizing_results[method_name] = size_pct
                except Exception as e:
                    logger.warning(f"Error in {method_name} sizing method: {e}")
                    sizing_results[method_name] = self.base_position_size_pct
            
            # Combine results intelligently
            final_recommendation = self._combine_sizing_recommendations(
                sizing_results, signal_confidence, risk_metrics, market_data
            )
            
            # Apply safety constraints
            final_recommendation = self._apply_safety_constraints(final_recommendation, risk_metrics)
            
            logger.info(f"Position Size Recommendation: {final_recommendation.recommended_size_pct*100:.2f}% "
                       f"(Method: {final_recommendation.sizing_method}, Risk: {final_recommendation.risk_level})")
            
            return final_recommendation
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            # Return conservative fallback
            return PositionSizeRecommendation(
                recommended_size_pct=self.base_position_size_pct * 0.5,
                max_size_pct=self.base_position_size_pct,
                risk_level="LOW",
                sizing_method="fallback",
                confidence_adjustment=0.0,
                volatility_adjustment=0.0,
                drawdown_adjustment=0.0,
                reasoning="Error in calculation - using conservative fallback"
            )
    
    def _fixed_percentage_sizing(self, confidence: float, risk_metrics: RiskMetrics, 
                               market_data: Dict[str, Any], llm_service: Any) -> float:
        """Fixed percentage of account balance"""
        base_size = self.base_position_size_pct
        
        # Adjust based on confidence
        confidence_multiplier = 0.5 + (confidence * 1.5)  # 0.5x to 2.0x based on confidence
        
        return base_size * confidence_multiplier
    
    def _kelly_criterion_sizing(self, confidence: float, risk_metrics: RiskMetrics,
                              market_data: Dict[str, Any], llm_service: Any) -> float:
        """Kelly Criterion based position sizing"""
        try:
            win_rate = max(risk_metrics.win_rate, self.min_win_rate)
            avg_win_loss = max(risk_metrics.avg_win_loss_ratio, 1.0)
            
            # Kelly formula: f = (bp - q) / b
            # where b = odds (avg_win_loss), p = win_rate, q = loss_rate
            loss_rate = 1 - win_rate
            kelly_fraction = (avg_win_loss * win_rate - loss_rate) / avg_win_loss
            
            # Apply safety multiplier and confidence adjustment
            kelly_size = max(0, kelly_fraction * self.kelly_multiplier * confidence)
            
            return min(kelly_size, self.max_position_size_pct)
            
        except Exception as e:
            logger.warning(f"Kelly criterion calculation error: {e}")
            return self.base_position_size_pct
    
    def _volatility_based_sizing(self, confidence: float, risk_metrics: RiskMetrics,
                               market_data: Dict[str, Any], llm_service: Any) -> float:
        """Volatility-adjusted position sizing"""
        volatility = risk_metrics.volatility
        
        # Inverse relationship with volatility
        if volatility <= self.volatility_threshold_low:
            vol_multiplier = 1.5  # Low volatility - increase size
        elif volatility >= self.volatility_threshold_high:
            vol_multiplier = 0.5  # High volatility - decrease size
        else:
            # Linear interpolation between thresholds
            vol_range = self.volatility_threshold_high - self.volatility_threshold_low
            vol_position = (volatility - self.volatility_threshold_low) / vol_range
            vol_multiplier = 1.5 - (vol_position * 1.0)  # 1.5 to 0.5
        
        base_size = self.base_position_size_pct * vol_multiplier * confidence
        return min(base_size, self.max_position_size_pct)
    
    def _atr_based_sizing(self, confidence: float, risk_metrics: RiskMetrics,
                        market_data: Dict[str, Any], llm_service: Any) -> float:
        """ATR (Average True Range) based position sizing"""
        try:
            atr = market_data.get('atr', 0)
            current_price = market_data.get('current_price', 0)
            
            if atr <= 0 or current_price <= 0:
                return self.base_position_size_pct
            
            # Calculate position size based on fixed risk amount
            risk_amount = risk_metrics.available_balance * 0.01  # Risk 1% of balance
            atr_percentage = atr / current_price
            
            # Position size = Risk Amount / (ATR * Price)
            position_value = risk_amount / atr_percentage if atr_percentage > 0 else 0
            position_size_pct = position_value / risk_metrics.available_balance
            
            # Apply confidence adjustment
            adjusted_size = position_size_pct * confidence
            
            return min(adjusted_size, self.max_position_size_pct)
            
        except Exception as e:
            logger.warning(f"ATR sizing calculation error: {e}")
            return self.base_position_size_pct
    
    def _confidence_based_sizing(self, confidence: float, risk_metrics: RiskMetrics,
                               market_data: Dict[str, Any], llm_service: Any) -> float:
        """Confidence-based dynamic position sizing"""
        # Base size scales directly with confidence
        confidence_size = self.base_position_size_pct * (confidence ** 0.8)  # Slightly dampen extreme confidence
        
        # Adjust for current drawdown
        drawdown_multiplier = max(0.3, 1 - risk_metrics.current_drawdown * 2)  # Reduce size during drawdown
        
        # Adjust for Sharpe ratio
        sharpe_multiplier = min(1.5, max(0.5, 0.5 + risk_metrics.sharpe_ratio * 0.3))
        
        final_size = confidence_size * drawdown_multiplier * sharpe_multiplier
        
        return min(final_size, self.max_position_size_pct)
    
    def _llm_hybrid_sizing(self, confidence: float, risk_metrics: RiskMetrics,
                               market_data: Dict[str, Any], llm_service: Any) -> float:
        """LLM-enhanced position sizing with hybrid approach"""
        try:
            if not llm_service:
                return self.base_position_size_pct
            
            # Prepare data for LLM
            capital_context = {
                "account_balance": risk_metrics.account_balance,
                "available_balance": risk_metrics.available_balance,
                "current_drawdown": f"{risk_metrics.current_drawdown*100:.1f}%",
                "portfolio_exposure": f"{risk_metrics.portfolio_exposure*100:.1f}%",
                "market_volatility": f"{risk_metrics.volatility*100:.1f}%",
                "signal_confidence": f"{confidence*100:.1f}%",
                "win_rate": f"{risk_metrics.win_rate*100:.1f}%",
                "sharpe_ratio": f"{risk_metrics.sharpe_ratio:.2f}",
                "var_95": f"{risk_metrics.var_95*100:.1f}%",
                "current_price": market_data.get('current_price', 0),
                "atr": market_data.get('atr', 0)
            }
            
            # Get LLM recommendation for capital allocation (run synchronously)
            import asyncio
            try:
                # Try to get existing event loop first
                try:
                    loop = asyncio.get_running_loop()
                    # If we're in an existing loop, use create_task
                    if loop.is_running():
                        logger.info("Using existing event loop for LLM capital management")
                        # For now, skip LLM call if we're in another event loop
                        # This prevents the "loop already running" error
                        logger.warning("Skipping LLM call due to event loop conflict - using traditional methods")
                        return self._confidence_based_sizing(confidence, risk_metrics, market_data, None)
                except RuntimeError:
                    # No event loop running, create new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    llm_response = loop.run_until_complete(
                        llm_service.get_capital_management_advice(
                            capital_context=capital_context,
                            base_position_size=self.base_position_size_pct,
                            max_position_size=self.max_position_size_pct
                        )
                    )
                    loop.close()
            except Exception as e:
                logger.warning(f"LLM capital management call failed: {e}")
                return self._confidence_based_sizing(confidence, risk_metrics, market_data, None)
            
            if llm_response and 'recommended_size_pct' in llm_response:
                llm_size = float(llm_response['recommended_size_pct']) / 100.0
                
                # Combine LLM recommendation with traditional methods
                traditional_size = self._confidence_based_sizing(confidence, risk_metrics, market_data, None)
                
                # Weighted combination
                combined_size = (llm_size * self.llm_weight + 
                               traditional_size * (1 - self.llm_weight))
                
                return min(combined_size, self.max_position_size_pct)
            else:
                # Fallback to confidence-based if LLM fails
                return self._confidence_based_sizing(confidence, risk_metrics, market_data, None)
                
        except Exception as e:
            logger.warning(f"LLM hybrid sizing error: {e}")
            return self._confidence_based_sizing(confidence, risk_metrics, market_data, None)
    
    def _combine_sizing_recommendations(self, sizing_results: Dict[str, float],
                                      confidence: float, risk_metrics: RiskMetrics,
                                      market_data: Dict[str, Any]) -> PositionSizeRecommendation:
        """Intelligently combine different sizing method results"""
        
        if not sizing_results:
            return PositionSizeRecommendation(
                recommended_size_pct=self.base_position_size_pct,
                max_size_pct=self.max_position_size_pct,
                risk_level="MEDIUM",
                sizing_method="default",
                confidence_adjustment=0.0,
                volatility_adjustment=0.0,
                drawdown_adjustment=0.0,
                reasoning="No sizing methods available"
            )
        
        # Weight different methods based on market conditions
        weights = {
            'fixed': 0.10,
            'kelly': 0.20,
            'volatility': 0.15,
            'atr': 0.15,
            'confidence': 0.20,
            'llm_hybrid': 0.20
        }
        
        # Adjust weights based on market conditions
        if risk_metrics.volatility > self.volatility_threshold_high:
            weights['volatility'] += 0.10
            weights['atr'] += 0.10
            weights['confidence'] -= 0.10
            weights['fixed'] -= 0.10
        
        if risk_metrics.current_drawdown > 0.05:  # If in drawdown
            weights['fixed'] += 0.15  # Be more conservative
            weights['kelly'] -= 0.10
            weights['confidence'] -= 0.05
        
        # Calculate weighted average
        weighted_sum = 0
        total_weight = 0
        used_methods = []
        
        for method, size in sizing_results.items():
            if method in weights:
                weight = weights[method]
                weighted_sum += size * weight
                total_weight += weight
                used_methods.append(method)
        
        if total_weight > 0:
            recommended_size = weighted_sum / total_weight
        else:
            recommended_size = self.base_position_size_pct
        
        # Determine risk level
        if recommended_size <= self.base_position_size_pct * 0.7:
            risk_level = "LOW"
        elif recommended_size >= self.base_position_size_pct * 1.5:
            risk_level = "HIGH"
        else:
            risk_level = "MEDIUM"
        
        # Calculate adjustments
        confidence_adj = (confidence - 0.5) * 2  # -1 to 1 range
        volatility_adj = -(risk_metrics.volatility - 0.05) * 10  # Negative for high volatility
        drawdown_adj = -risk_metrics.current_drawdown * 5  # Negative for drawdown
        
        return PositionSizeRecommendation(
            recommended_size_pct=recommended_size,
            max_size_pct=self.max_position_size_pct,
            risk_level=risk_level,
            sizing_method=f"weighted_combination_{'+'.join(used_methods)}",
            confidence_adjustment=confidence_adj,
            volatility_adjustment=volatility_adj,
            drawdown_adjustment=drawdown_adj,
            reasoning=f"Combined {len(used_methods)} methods with market-adaptive weights"
        )
    
    def _apply_safety_constraints(self, recommendation: PositionSizeRecommendation,
                                risk_metrics: RiskMetrics) -> PositionSizeRecommendation:
        """Apply final safety constraints to position size"""
        
        original_size = recommendation.recommended_size_pct
        constrained_size = original_size
        
        # Constraint 1: Maximum position size
        if constrained_size > self.max_position_size_pct:
            constrained_size = self.max_position_size_pct
            recommendation.reasoning += f" | Capped at max size {self.max_position_size_pct*100:.1f}%"
        
        # Constraint 2: Portfolio exposure limit
        if risk_metrics.portfolio_exposure + constrained_size > self.max_portfolio_exposure:
            max_allowed = self.max_portfolio_exposure - risk_metrics.portfolio_exposure
            constrained_size = max(0, max_allowed)
            recommendation.reasoning += f" | Portfolio exposure limit applied"
        
        # Constraint 3: Drawdown protection
        if risk_metrics.current_drawdown > 0.10:  # 10% drawdown
            drawdown_multiplier = max(0.2, 1 - risk_metrics.current_drawdown * 2)
            constrained_size *= drawdown_multiplier
            recommendation.reasoning += f" | Drawdown protection applied ({drawdown_multiplier:.2f}x)"
        
        # Constraint 4: Minimum viable size
        min_size = 0.001  # 0.1% minimum
        if constrained_size < min_size:
            constrained_size = 0
            recommendation.reasoning += f" | Below minimum threshold - no position"
        
        # Update recommendation
        recommendation.recommended_size_pct = constrained_size
        
        # Update risk level if size was significantly reduced
        if constrained_size < original_size * 0.5:
            recommendation.risk_level = "LOW"
        
        return recommendation
    
    def calculate_risk_metrics(self, account_info: Dict[str, Any], 
                             historical_performance: List[Dict[str, Any]] = None) -> RiskMetrics:
        """Calculate comprehensive risk metrics for position sizing"""
        try:
            account_balance = float(account_info.get('totalWalletBalance', 0))
            available_balance = float(account_info.get('availableBalance', 0))
            
            # Calculate current portfolio exposure
            total_position_value = 0
            for position in account_info.get('positions', []):
                if float(position.get('positionAmt', 0)) != 0:
                    position_value = abs(float(position.get('positionAmt', 0)) * float(position.get('markPrice', 0)))
                    total_position_value += position_value
            
            portfolio_exposure = total_position_value / account_balance if account_balance > 0 else 0
            
            # Calculate drawdown
            total_unrealized_pnl = sum(float(pos.get('unrealizedProfit', 0)) for pos in account_info.get('positions', []))
            current_equity = account_balance + total_unrealized_pnl
            peak_balance = account_balance  # This should be tracked over time
            current_drawdown = max(0, (peak_balance - current_equity) / peak_balance) if peak_balance > 0 else 0
            
            # Default values if no historical performance
            volatility = 0.05  # 5% default
            var_95 = 0.02      # 2% VaR
            sharpe_ratio = 0.0
            win_rate = 0.5
            avg_win_loss_ratio = 1.0
            max_drawdown = current_drawdown
            
            # Calculate from historical performance if available
            if historical_performance:
                returns = [float(trade.get('pnl_pct', 0)) for trade in historical_performance]
                if returns:
                    volatility = np.std(returns) if len(returns) > 1 else 0.05
                    var_95 = np.percentile(returns, 5) if len(returns) >= 20 else 0.02
                    
                    if len(returns) > 1:
                        avg_return = np.mean(returns)
                        sharpe_ratio = avg_return / volatility if volatility > 0 else 0
                    
                    winning_trades = [r for r in returns if r > 0]
                    losing_trades = [r for r in returns if r < 0]
                    
                    win_rate = len(winning_trades) / len(returns) if returns else 0.5
                    
                    if winning_trades and losing_trades:
                        avg_win = np.mean(winning_trades)
                        avg_loss = abs(np.mean(losing_trades))
                        avg_win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 1.0
                    
                    # Calculate maximum drawdown
                    cumulative_returns = np.cumprod(1 + np.array(returns))
                    running_max = np.maximum.accumulate(cumulative_returns)
                    drawdowns = (running_max - cumulative_returns) / running_max
                    max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else current_drawdown
            
            return RiskMetrics(
                account_balance=account_balance,
                available_balance=available_balance,
                current_drawdown=current_drawdown,
                max_drawdown=max_drawdown,
                portfolio_exposure=portfolio_exposure,
                volatility=volatility,
                var_95=var_95,
                sharpe_ratio=sharpe_ratio,
                win_rate=win_rate,
                avg_win_loss_ratio=avg_win_loss_ratio
            )
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            # Return safe defaults
            return RiskMetrics(
                account_balance=10000,
                available_balance=10000,
                current_drawdown=0.0,
                max_drawdown=0.0,
                portfolio_exposure=0.0,
                volatility=0.05,
                var_95=0.02,
                sharpe_ratio=0.0,
                win_rate=0.5,
                avg_win_loss_ratio=1.0
            )