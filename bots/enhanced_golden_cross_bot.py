"""
Enhanced Golden Cross Trading Bot
Uses the new CustomBot framework with complete data processing pipeline
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

from bot_sdk import CustomBot, Action

logger = logging.getLogger(__name__)

class EnhancedGoldenCrossBot(CustomBot):
    """
    Enhanced Golden Cross Trading Bot
    Uses moving average crossovers with advanced confirmation signals
    """
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str]):
        super().__init__(config, api_keys)
        
        # Bot metadata
        self.bot_name = "Enhanced Golden Cross Bot"
        self.description = "Golden Cross strategy with volume and momentum confirmation"
        self.version = "2.0.0"
        self.bot_type = "TECHNICAL"
        
        # Moving average configuration
        self.ma_short = config.get('ma_short', 50)
        self.ma_long = config.get('ma_long', 200)
        self.ma_signal = config.get('ma_signal', 20)  # For additional confirmation
        
        # Volume confirmation
        self.volume_threshold = config.get('volume_threshold', 1.5)
        self.volume_lookback = config.get('volume_lookback', 20)
        
        # Momentum confirmation
        self.momentum_threshold = config.get('momentum_threshold', 0.02)  # 2%
        self.momentum_period = config.get('momentum_period', 10)
        
        # Signal strength
        self.min_signal_strength = config.get('min_signal_strength', 0.6)
        self.confirmation_required = config.get('confirmation_required', True)
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """
        Execute Golden Cross algorithm with comprehensive analysis
        
        Args:
            data: Preprocessed market data with technical indicators
            timeframe: Trading timeframe
            subscription_config: Additional subscription configuration
            
        Returns:
            Action: Trading action (BUY/SELL/HOLD)
        """
        try:
            # Check if we have enough data
            if len(data) < self.ma_long + 10:
                return Action("HOLD", 0.0, "Insufficient data for Golden Cross analysis")
            
            # Get current market state
            current_price = float(data['close'].iloc[-1])
            
            # Calculate moving averages
            data[f'ma_{self.ma_short}'] = data['close'].rolling(window=self.ma_short).mean()
            data[f'ma_{self.ma_long}'] = data['close'].rolling(window=self.ma_long).mean()
            data[f'ma_{self.ma_signal}'] = data['close'].rolling(window=self.ma_signal).mean()
            
            # Get current MA values
            ma_short_current = data[f'ma_{self.ma_short}'].iloc[-1]
            ma_long_current = data[f'ma_{self.ma_long}'].iloc[-1]
            ma_signal_current = data[f'ma_{self.ma_signal}'].iloc[-1]
            
            # Get previous MA values
            ma_short_prev = data[f'ma_{self.ma_short}'].iloc[-2]
            ma_long_prev = data[f'ma_{self.ma_long}'].iloc[-2]
            
            # Detect crossovers
            golden_cross = self.detect_golden_cross(data, self.ma_short, self.ma_long)
            death_cross = self.detect_death_cross(data, self.ma_short, self.ma_long)
            
            # Analyze volume confirmation
            volume_confirmation = self.analyze_volume_confirmation(data)
            
            # Analyze momentum confirmation
            momentum_confirmation = self.analyze_momentum_confirmation(data)
            
            # Analyze trend strength
            trend_strength = self.analyze_trend_strength(data)
            
            # Generate primary signal
            primary_signal = self.generate_primary_signal(
                golden_cross, death_cross, ma_short_current, ma_long_current, 
                ma_signal_current, current_price
            )
            
            # Apply confirmations
            final_signal = self.apply_confirmations(
                primary_signal, volume_confirmation, momentum_confirmation, 
                trend_strength, current_price, timeframe
            )
            
            # Apply risk management
            final_signal = self.apply_risk_management(final_signal, data, subscription_config)
            
            logger.info(f"Golden Cross Analysis: MA{self.ma_short}={ma_short_current:.2f}, MA{self.ma_long}={ma_long_current:.2f}, Signal={final_signal.action}")
            
            return final_signal
            
        except Exception as e:
            logger.error(f"Error in Golden Cross algorithm: {e}")
            return Action("HOLD", 0.0, f"Algorithm error: {str(e)}")
    
    def detect_golden_cross(self, data: pd.DataFrame, short_period: int, long_period: int) -> Dict[str, Any]:
        """Detect golden cross pattern"""
        try:
            ma_short = data[f'ma_{short_period}']
            ma_long = data[f'ma_{long_period}']
            
            # Check recent crossover
            for i in range(min(5, len(data) - 1)):  # Check last 5 periods
                idx = -(i + 1)
                prev_idx = -(i + 2)
                
                if (ma_short.iloc[idx] > ma_long.iloc[idx] and 
                    ma_short.iloc[prev_idx] <= ma_long.iloc[prev_idx]):
                    
                    # Calculate crossover strength
                    crossover_strength = abs(ma_short.iloc[idx] - ma_long.iloc[idx]) / ma_long.iloc[idx]
                    
                    return {
                        "detected": True,
                        "periods_ago": i,
                        "strength": min(crossover_strength * 100, 1.0),
                        "ma_short_value": ma_short.iloc[idx],
                        "ma_long_value": ma_long.iloc[idx]
                    }
            
            return {"detected": False, "strength": 0.0}
            
        except Exception as e:
            logger.error(f"Error detecting golden cross: {e}")
            return {"detected": False, "strength": 0.0}
    
    def detect_death_cross(self, data: pd.DataFrame, short_period: int, long_period: int) -> Dict[str, Any]:
        """Detect death cross pattern"""
        try:
            ma_short = data[f'ma_{short_period}']
            ma_long = data[f'ma_{long_period}']
            
            # Check recent crossover
            for i in range(min(5, len(data) - 1)):  # Check last 5 periods
                idx = -(i + 1)
                prev_idx = -(i + 2)
                
                if (ma_short.iloc[idx] < ma_long.iloc[idx] and 
                    ma_short.iloc[prev_idx] >= ma_long.iloc[prev_idx]):
                    
                    # Calculate crossover strength
                    crossover_strength = abs(ma_short.iloc[idx] - ma_long.iloc[idx]) / ma_long.iloc[idx]
                    
                    return {
                        "detected": True,
                        "periods_ago": i,
                        "strength": min(crossover_strength * 100, 1.0),
                        "ma_short_value": ma_short.iloc[idx],
                        "ma_long_value": ma_long.iloc[idx]
                    }
            
            return {"detected": False, "strength": 0.0}
            
        except Exception as e:
            logger.error(f"Error detecting death cross: {e}")
            return {"detected": False, "strength": 0.0}
    
    def analyze_volume_confirmation(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume for signal confirmation"""
        try:
            current_volume = data['volume'].iloc[-1]
            avg_volume = data['volume'].rolling(window=self.volume_lookback).mean().iloc[-1]
            
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            if volume_ratio > self.volume_threshold:
                confirmation_strength = min(volume_ratio / self.volume_threshold, 2.0) * 0.3
                reason = f"High volume confirmation: {volume_ratio:.2f}x average"
            elif volume_ratio < 0.7:
                confirmation_strength = -0.2
                reason = f"Low volume warning: {volume_ratio:.2f}x average"
            else:
                confirmation_strength = 0.0
                reason = f"Normal volume: {volume_ratio:.2f}x average"
            
            return {
                "confirmation_strength": confirmation_strength,
                "volume_ratio": volume_ratio,
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volume confirmation: {e}")
            return {"confirmation_strength": 0.0, "reason": "Volume analysis error"}
    
    def analyze_momentum_confirmation(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price momentum for confirmation"""
        try:
            # Calculate momentum over specified period
            momentum = data['close'].pct_change(self.momentum_period).iloc[-1]
            
            if abs(momentum) > self.momentum_threshold:
                confirmation_strength = min(abs(momentum) / self.momentum_threshold, 2.0) * 0.2
                direction = "positive" if momentum > 0 else "negative"
                reason = f"Strong {direction} momentum: {momentum:.3f}"
            else:
                confirmation_strength = 0.0
                reason = f"Weak momentum: {momentum:.3f}"
            
            return {
                "confirmation_strength": confirmation_strength,
                "momentum_value": momentum,
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error analyzing momentum confirmation: {e}")
            return {"confirmation_strength": 0.0, "reason": "Momentum analysis error"}
    
    def analyze_trend_strength(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overall trend strength"""
        try:
            # Calculate trend strength using multiple timeframes
            short_trend = data['close'].iloc[-1] - data['close'].iloc[-10]
            medium_trend = data['close'].iloc[-1] - data['close'].iloc[-20]
            long_trend = data['close'].iloc[-1] - data['close'].iloc[-50]
            
            # Normalize by current price
            current_price = data['close'].iloc[-1]
            short_trend_pct = short_trend / current_price
            medium_trend_pct = medium_trend / current_price
            long_trend_pct = long_trend / current_price
            
            # Calculate weighted trend strength
            trend_strength = (short_trend_pct * 0.5 + medium_trend_pct * 0.3 + long_trend_pct * 0.2)
            
            if trend_strength > 0.02:  # 2% positive trend
                strength_score = min(trend_strength / 0.02, 2.0) * 0.3
                reason = f"Strong uptrend: {trend_strength:.3f}"
            elif trend_strength < -0.02:  # 2% negative trend
                strength_score = min(abs(trend_strength) / 0.02, 2.0) * 0.3
                reason = f"Strong downtrend: {trend_strength:.3f}"
            else:
                strength_score = 0.0
                reason = f"Sideways trend: {trend_strength:.3f}"
            
            return {
                "strength_score": strength_score,
                "trend_direction": "UP" if trend_strength > 0 else "DOWN",
                "trend_value": trend_strength,
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trend strength: {e}")
            return {"strength_score": 0.0, "reason": "Trend analysis error"}
    
    def generate_primary_signal(self, golden_cross: Dict[str, Any], death_cross: Dict[str, Any],
                               ma_short: float, ma_long: float, ma_signal: float, current_price: float) -> Dict[str, Any]:
        """Generate primary signal based on crossovers"""
        try:
            # Golden cross detected
            if golden_cross["detected"]:
                # Additional confirmation: price above signal MA
                if current_price > ma_signal:
                    strength = 0.8 + golden_cross["strength"] * 0.2
                    reason = f"Golden cross confirmed: MA{self.ma_short} > MA{self.ma_long}, price above signal MA"
                else:
                    strength = 0.6 + golden_cross["strength"] * 0.2
                    reason = f"Golden cross detected: MA{self.ma_short} > MA{self.ma_long}"
                
                return {
                    "action": "BUY",
                    "strength": strength,
                    "reason": reason,
                    "signal_type": "GOLDEN_CROSS"
                }
            
            # Death cross detected
            elif death_cross["detected"]:
                # Additional confirmation: price below signal MA
                if current_price < ma_signal:
                    strength = 0.8 + death_cross["strength"] * 0.2
                    reason = f"Death cross confirmed: MA{self.ma_short} < MA{self.ma_long}, price below signal MA"
                else:
                    strength = 0.6 + death_cross["strength"] * 0.2
                    reason = f"Death cross detected: MA{self.ma_short} < MA{self.ma_long}"
                
                return {
                    "action": "SELL",
                    "strength": strength,
                    "reason": reason,
                    "signal_type": "DEATH_CROSS"
                }
            
            # No crossover, check current MA relationship
            elif ma_short > ma_long * 1.01:  # 1% above for noise filtering
                strength = 0.3
                reason = f"MA{self.ma_short} above MA{self.ma_long} (bullish alignment)"
                return {
                    "action": "BUY",
                    "strength": strength,
                    "reason": reason,
                    "signal_type": "MA_ALIGNMENT"
                }
            
            elif ma_short < ma_long * 0.99:  # 1% below for noise filtering
                strength = 0.3
                reason = f"MA{self.ma_short} below MA{self.ma_long} (bearish alignment)"
                return {
                    "action": "SELL",
                    "strength": strength,
                    "reason": reason,
                    "signal_type": "MA_ALIGNMENT"
                }
            
            else:
                return {
                    "action": "HOLD",
                    "strength": 0.0,
                    "reason": "No clear MA signal",
                    "signal_type": "NO_SIGNAL"
                }
                
        except Exception as e:
            logger.error(f"Error generating primary signal: {e}")
            return {"action": "HOLD", "strength": 0.0, "reason": "Signal generation error"}
    
    def apply_confirmations(self, primary_signal: Dict[str, Any], volume_confirmation: Dict[str, Any],
                           momentum_confirmation: Dict[str, Any], trend_strength: Dict[str, Any],
                           current_price: float, timeframe: str) -> Action:
        """Apply confirmations to primary signal"""
        try:
            base_action = primary_signal["action"]
            base_strength = primary_signal["strength"]
            base_reason = primary_signal["reason"]
            
            # Apply volume confirmation
            if volume_confirmation["confirmation_strength"] > 0:
                base_strength += volume_confirmation["confirmation_strength"]
                base_reason += f" | {volume_confirmation['reason']}"
            elif volume_confirmation["confirmation_strength"] < 0:
                base_strength *= 0.8  # Reduce strength for low volume
                base_reason += f" | {volume_confirmation['reason']}"
            
            # Apply momentum confirmation
            if momentum_confirmation["confirmation_strength"] > 0:
                if ((base_action == "BUY" and momentum_confirmation["momentum_value"] > 0) or
                    (base_action == "SELL" and momentum_confirmation["momentum_value"] < 0)):
                    base_strength += momentum_confirmation["confirmation_strength"]
                    base_reason += f" | {momentum_confirmation['reason']}"
            
            # Apply trend strength
            if trend_strength["strength_score"] > 0:
                if ((base_action == "BUY" and trend_strength["trend_direction"] == "UP") or
                    (base_action == "SELL" and trend_strength["trend_direction"] == "DOWN")):
                    base_strength += trend_strength["strength_score"]
                    base_reason += f" | {trend_strength['reason']}"
            
            # Apply timeframe adjustments
            if timeframe in ["1m", "5m"]:
                base_strength *= 0.8  # Reduce strength for short timeframes
                base_reason += " | Short timeframe adjustment"
            elif timeframe in ["1d", "1w"]:
                base_strength *= 1.1  # Increase strength for long timeframes
                base_reason += " | Long timeframe adjustment"
            
            # Ensure strength is within bounds
            base_strength = max(0.0, min(1.0, base_strength))
            
            # Apply minimum signal strength threshold
            if base_strength < self.min_signal_strength and base_action != "HOLD":
                return Action("HOLD", current_price, f"Signal too weak: {base_strength:.2f} < {self.min_signal_strength}", "WEAK_SIGNAL", base_strength)
            
            return Action(base_action, current_price, base_reason, primary_signal["signal_type"], base_strength)
            
        except Exception as e:
            logger.error(f"Error applying confirmations: {e}")
            return Action("HOLD", current_price, f"Confirmation error: {str(e)}")
    
    def apply_risk_management(self, signal: Action, data: pd.DataFrame, 
                            subscription_config: Dict[str, Any] = None) -> Action:
        """Apply risk management rules"""
        try:
            # Check for extreme volatility
            if 'volatility' in data.columns:
                current_volatility = data['volatility'].iloc[-1]
                avg_volatility = data['volatility'].mean()
                
                if current_volatility > avg_volatility * 3:
                    return Action("HOLD", signal.value, "High volatility - trading suspended", "RISK_MGMT", 0.0)
            
            # Check for gap conditions
            if len(data) >= 2:
                price_gap = abs(data['close'].iloc[-1] - data['close'].iloc[-2]) / data['close'].iloc[-2]
                if price_gap > 0.05:  # 5% gap
                    return Action("HOLD", signal.value, f"Large price gap detected: {price_gap:.2%}", "RISK_MGMT", 0.0)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error applying risk management: {e}")
            return signal
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Return configuration schema for this bot"""
        return {
            "type": "object",
            "properties": {
                "ma_short": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 100,
                    "default": 50,
                    "description": "Short-term moving average period"
                },
                "ma_long": {
                    "type": "integer",
                    "minimum": 50,
                    "maximum": 500,
                    "default": 200,
                    "description": "Long-term moving average period"
                },
                "ma_signal": {
                    "type": "integer",
                    "minimum": 5,
                    "maximum": 50,
                    "default": 20,
                    "description": "Signal line moving average period"
                },
                "volume_threshold": {
                    "type": "number",
                    "minimum": 0.5,
                    "maximum": 5.0,
                    "default": 1.5,
                    "description": "Volume threshold for confirmation"
                },
                "momentum_threshold": {
                    "type": "number",
                    "minimum": 0.005,
                    "maximum": 0.1,
                    "default": 0.02,
                    "description": "Momentum threshold for confirmation"
                },
                "min_signal_strength": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 1.0,
                    "default": 0.6,
                    "description": "Minimum signal strength to execute trades"
                }
            },
            "required": ["ma_short", "ma_long"],
            "additionalProperties": False
        } 