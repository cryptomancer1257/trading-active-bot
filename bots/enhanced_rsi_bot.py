"""
Enhanced RSI Trading Bot
Uses the new CustomBot framework with complete data processing pipeline
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import logging

from bot_sdk import CustomBot, Action

logger = logging.getLogger(__name__)

class EnhancedRSIBot(CustomBot):
    """
    Enhanced RSI Trading Bot with complete data processing pipeline
    Implements the new execute_full_cycle method for comprehensive trading logic
    """
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str]):
        super().__init__(config, api_keys)
        
        # Bot metadata
        self.bot_name = "Enhanced RSI Bot"
        self.description = "RSI-based trading bot with advanced risk management and market analysis"
        self.version = "2.0.0"
        self.bot_type = "TECHNICAL"
        
        # RSI configuration
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.rsi_overbought = config.get('rsi_overbought', 70)
        self.rsi_extreme_oversold = config.get('rsi_extreme_oversold', 20)
        self.rsi_extreme_overbought = config.get('rsi_extreme_overbought', 80)
        
        # Moving average configuration
        self.sma_short = config.get('sma_short', 20)
        self.sma_long = config.get('sma_long', 50)
        
        # Volume configuration
        self.volume_threshold = config.get('volume_threshold', 1.5)
        self.volume_period = config.get('volume_period', 20)
        
        # Risk management
        self.max_rsi_divergence = config.get('max_rsi_divergence', 10)
        self.min_price_change = config.get('min_price_change', 0.005)  # 0.5%
        
        # Signal strength configuration
        self.signal_strength_multiplier = config.get('signal_strength_multiplier', 1.0)
        self.confirmation_required = config.get('confirmation_required', True)
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """
        Execute RSI trading algorithm with comprehensive analysis
        
        Args:
            data: Preprocessed market data with technical indicators
            timeframe: Trading timeframe (1m, 5m, 1h, 1d)
            subscription_config: Additional subscription configuration
            
        Returns:
            Action: Trading action (BUY/SELL/HOLD)
        """
        try:
            if len(data) < max(self.rsi_period, self.sma_long):
                return Action("HOLD", 0.0, "Insufficient data for RSI analysis")
            
            # Get current market state
            current_price = float(data['close'].iloc[-1])
            current_rsi = data['rsi'].iloc[-1]
            current_volume_ratio = data['volume_ratio'].iloc[-1]
            
            # Get moving averages
            sma_short = data['sma_20'].iloc[-1]
            sma_long = data['sma_50'].iloc[-1]
            
            # Calculate price momentum
            price_change = data['price_change'].iloc[-1]
            momentum_5 = data['momentum_5'].iloc[-1]
            
            # Analyze RSI signals
            rsi_signal = self.analyze_rsi_signals(data)
            
            # Analyze trend direction
            trend_signal = self.analyze_trend_signals(data)
            
            # Analyze volume confirmation
            volume_confirmation = self.analyze_volume_confirmation(data)
            
            # Check for RSI divergence
            divergence_signal = self.check_rsi_divergence(data)
            
            # Combine all signals
            final_signal = self.combine_signals(
                rsi_signal=rsi_signal,
                trend_signal=trend_signal,
                volume_confirmation=volume_confirmation,
                divergence_signal=divergence_signal,
                current_price=current_price,
                timeframe=timeframe
            )
            
            # Apply risk management
            final_signal = self.apply_risk_management(final_signal, data, subscription_config)
            
            logger.info(f"RSI Bot Analysis: RSI={current_rsi:.2f}, Price={current_price:.2f}, Signal={final_signal.action}")
            
            return final_signal
            
        except Exception as e:
            logger.error(f"Error in RSI algorithm execution: {e}")
            return Action("HOLD", 0.0, f"Algorithm error: {str(e)}")
    
    def analyze_rsi_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze RSI for trading signals"""
        try:
            current_rsi = data['rsi'].iloc[-1]
            prev_rsi = data['rsi'].iloc[-2]
            
            signal_strength = 0.0
            signal_type = "HOLD"
            reason = ""
            
            # Strong buy signals
            if current_rsi < self.rsi_extreme_oversold:
                signal_strength = 0.9
                signal_type = "BUY"
                reason = f"RSI extreme oversold: {current_rsi:.2f}"
            
            # Strong sell signals
            elif current_rsi > self.rsi_extreme_overbought:
                signal_strength = 0.9
                signal_type = "SELL"
                reason = f"RSI extreme overbought: {current_rsi:.2f}"
            
            # Moderate buy signals
            elif current_rsi < self.rsi_oversold and prev_rsi > current_rsi:
                signal_strength = 0.6
                signal_type = "BUY"
                reason = f"RSI oversold with downward momentum: {current_rsi:.2f}"
            
            # Moderate sell signals
            elif current_rsi > self.rsi_overbought and prev_rsi < current_rsi:
                signal_strength = 0.6
                signal_type = "SELL"
                reason = f"RSI overbought with upward momentum: {current_rsi:.2f}"
            
            # RSI recovery signals
            elif current_rsi > self.rsi_oversold and prev_rsi < self.rsi_oversold:
                signal_strength = 0.4
                signal_type = "BUY"
                reason = f"RSI recovery from oversold: {current_rsi:.2f}"
            
            elif current_rsi < self.rsi_overbought and prev_rsi > self.rsi_overbought:
                signal_strength = 0.4
                signal_type = "SELL"
                reason = f"RSI decline from overbought: {current_rsi:.2f}"
            
            return {
                "signal_type": signal_type,
                "signal_strength": signal_strength,
                "reason": reason,
                "rsi_value": current_rsi
            }
            
        except Exception as e:
            logger.error(f"Error analyzing RSI signals: {e}")
            return {"signal_type": "HOLD", "signal_strength": 0.0, "reason": "RSI analysis error"}
    
    def analyze_trend_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trend direction using moving averages"""
        try:
            current_price = data['close'].iloc[-1]
            sma_short = data['sma_20'].iloc[-1]
            sma_long = data['sma_50'].iloc[-1]
            
            signal_strength = 0.0
            signal_type = "HOLD"
            reason = ""
            
            # Strong uptrend
            if current_price > sma_short > sma_long:
                signal_strength = 0.7
                signal_type = "BUY"
                reason = "Strong uptrend: Price > SMA20 > SMA50"
            
            # Strong downtrend
            elif current_price < sma_short < sma_long:
                signal_strength = 0.7
                signal_type = "SELL"
                reason = "Strong downtrend: Price < SMA20 < SMA50"
            
            # Moderate uptrend
            elif current_price > sma_short and sma_short > sma_long * 0.995:
                signal_strength = 0.4
                signal_type = "BUY"
                reason = "Moderate uptrend: Price above SMA20"
            
            # Moderate downtrend
            elif current_price < sma_short and sma_short < sma_long * 1.005:
                signal_strength = 0.4
                signal_type = "SELL"
                reason = "Moderate downtrend: Price below SMA20"
            
            return {
                "signal_type": signal_type,
                "signal_strength": signal_strength,
                "reason": reason,
                "trend_direction": "UP" if sma_short > sma_long else "DOWN"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trend signals: {e}")
            return {"signal_type": "HOLD", "signal_strength": 0.0, "reason": "Trend analysis error"}
    
    def analyze_volume_confirmation(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume for signal confirmation"""
        try:
            current_volume_ratio = data['volume_ratio'].iloc[-1]
            
            confirmation_strength = 0.0
            reason = ""
            
            if current_volume_ratio > self.volume_threshold:
                confirmation_strength = min(current_volume_ratio / self.volume_threshold, 2.0) * 0.3
                reason = f"High volume confirmation: {current_volume_ratio:.2f}x average"
            elif current_volume_ratio < 0.5:
                confirmation_strength = -0.2
                reason = f"Low volume warning: {current_volume_ratio:.2f}x average"
            else:
                confirmation_strength = 0.1
                reason = f"Normal volume: {current_volume_ratio:.2f}x average"
            
            return {
                "confirmation_strength": confirmation_strength,
                "reason": reason,
                "volume_ratio": current_volume_ratio
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volume confirmation: {e}")
            return {"confirmation_strength": 0.0, "reason": "Volume analysis error"}
    
    def check_rsi_divergence(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Check for RSI divergence signals"""
        try:
            if len(data) < 20:
                return {"divergence_type": "NONE", "strength": 0.0, "reason": "Insufficient data"}
            
            # Get last 20 periods for divergence analysis
            recent_data = data.tail(20)
            
            # Find price peaks and RSI peaks
            price_peaks = self.find_peaks(recent_data['close'].values)
            rsi_peaks = self.find_peaks(recent_data['rsi'].values)
            
            # Find price troughs and RSI troughs
            price_troughs = self.find_troughs(recent_data['close'].values)
            rsi_troughs = self.find_troughs(recent_data['rsi'].values)
            
            # Check for bullish divergence (price makes lower low, RSI makes higher low)
            if len(price_troughs) >= 2 and len(rsi_troughs) >= 2:
                if (price_troughs[-1] < price_troughs[-2] and 
                    rsi_troughs[-1] > rsi_troughs[-2]):
                    return {
                        "divergence_type": "BULLISH",
                        "strength": 0.5,
                        "reason": "Bullish RSI divergence detected"
                    }
            
            # Check for bearish divergence (price makes higher high, RSI makes lower high)
            if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
                if (price_peaks[-1] > price_peaks[-2] and 
                    rsi_peaks[-1] < rsi_peaks[-2]):
                    return {
                        "divergence_type": "BEARISH",
                        "strength": 0.5,
                        "reason": "Bearish RSI divergence detected"
                    }
            
            return {"divergence_type": "NONE", "strength": 0.0, "reason": "No divergence detected"}
            
        except Exception as e:
            logger.error(f"Error checking RSI divergence: {e}")
            return {"divergence_type": "NONE", "strength": 0.0, "reason": "Divergence analysis error"}
    
    def find_peaks(self, values: np.ndarray) -> List[float]:
        """Find peaks in values array"""
        try:
            peaks = []
            for i in range(1, len(values) - 1):
                if values[i] > values[i-1] and values[i] > values[i+1]:
                    peaks.append(values[i])
            return peaks
        except:
            return []
    
    def find_troughs(self, values: np.ndarray) -> List[float]:
        """Find troughs in values array"""
        try:
            troughs = []
            for i in range(1, len(values) - 1):
                if values[i] < values[i-1] and values[i] < values[i+1]:
                    troughs.append(values[i])
            return troughs
        except:
            return []
    
    def combine_signals(self, rsi_signal: Dict[str, Any], trend_signal: Dict[str, Any],
                       volume_confirmation: Dict[str, Any], divergence_signal: Dict[str, Any],
                       current_price: float, timeframe: str) -> Action:
        """Combine all signals into final trading action"""
        try:
            # Base signal from RSI
            base_signal_type = rsi_signal["signal_type"]
            base_strength = rsi_signal["signal_strength"]
            
            # Adjust strength based on trend confirmation
            if trend_signal["signal_type"] == base_signal_type:
                base_strength += trend_signal["signal_strength"] * 0.5
            elif trend_signal["signal_type"] != "HOLD":
                base_strength *= 0.7  # Reduce strength if trend contradicts
            
            # Apply volume confirmation
            base_strength += volume_confirmation["confirmation_strength"]
            
            # Apply divergence signals
            if divergence_signal["divergence_type"] == "BULLISH" and base_signal_type == "BUY":
                base_strength += divergence_signal["strength"]
            elif divergence_signal["divergence_type"] == "BEARISH" and base_signal_type == "SELL":
                base_strength += divergence_signal["strength"]
            
            # Apply timeframe adjustments
            if timeframe in ["1m", "5m"]:
                base_strength *= 0.8  # Reduce strength for short timeframes
            elif timeframe in ["1d", "1w"]:
                base_strength *= 1.2  # Increase strength for long timeframes
            
            # Apply signal strength multiplier
            base_strength *= self.signal_strength_multiplier
            
            # Ensure strength is within bounds
            base_strength = max(0.0, min(1.0, base_strength))
            
            # Create reason string
            reasons = []
            if rsi_signal["reason"]:
                reasons.append(rsi_signal["reason"])
            if trend_signal["reason"]:
                reasons.append(trend_signal["reason"])
            if volume_confirmation["reason"]:
                reasons.append(volume_confirmation["reason"])
            if divergence_signal["reason"] and divergence_signal["divergence_type"] != "NONE":
                reasons.append(divergence_signal["reason"])
            
            combined_reason = " | ".join(reasons)
            
            # Determine final action
            if base_strength >= 0.6:
                return Action(base_signal_type, current_price, combined_reason, "RSI_SIGNAL", base_strength)
            elif base_strength >= 0.3:
                return Action(base_signal_type, current_price, f"Weak {combined_reason}", "RSI_WEAK", base_strength)
            else:
                return Action("HOLD", current_price, f"No strong signal: {combined_reason}", "RSI_HOLD", base_strength)
                
        except Exception as e:
            logger.error(f"Error combining signals: {e}")
            return Action("HOLD", current_price, f"Signal combination error: {str(e)}")
    
    def apply_risk_management(self, signal: Action, data: pd.DataFrame, 
                            subscription_config: Dict[str, Any] = None) -> Action:
        """Apply risk management rules to the signal"""
        try:
            # Check minimum price change requirement
            if len(data) >= 2:
                price_change = abs(data['close'].iloc[-1] - data['close'].iloc[-2]) / data['close'].iloc[-2]
                if price_change < self.min_price_change and signal.action != "HOLD":
                    return Action("HOLD", signal.value, f"Price change too small: {price_change:.4f}", "RISK_MGMT", 0.0)
            
            # Check volatility conditions
            if 'volatility' in data.columns:
                current_volatility = data['volatility'].iloc[-1]
                avg_volatility = data['volatility'].mean()
                
                if current_volatility > avg_volatility * 3:  # Very high volatility
                    signal.value *= 0.5  # Reduce signal strength
                    signal.reason += " (High volatility adjustment)"
            
            # Apply subscription-specific risk config
            if subscription_config and 'risk_config' in subscription_config:
                risk_config = subscription_config['risk_config']
                
                # Check if we should skip trading during certain conditions
                if risk_config.get('skip_high_volatility', False):
                    volatility_threshold = risk_config.get('volatility_threshold', 2.0)
                    if 'volatility_ratio' in data.columns:
                        if data['volatility_ratio'].iloc[-1] > volatility_threshold:
                            return Action("HOLD", signal.value, "Skipped due to high volatility", "RISK_MGMT", 0.0)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error applying risk management: {e}")
            return signal
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Return configuration schema for this bot"""
        return {
            "type": "object",
            "properties": {
                "rsi_period": {
                    "type": "integer",
                    "minimum": 5,
                    "maximum": 50,
                    "default": 14,
                    "description": "Period for RSI calculation"
                },
                "rsi_oversold": {
                    "type": "number",
                    "minimum": 10,
                    "maximum": 40,
                    "default": 30,
                    "description": "RSI oversold threshold"
                },
                "rsi_overbought": {
                    "type": "number",
                    "minimum": 60,
                    "maximum": 90,
                    "default": 70,
                    "description": "RSI overbought threshold"
                },
                "sma_short": {
                    "type": "integer",
                    "minimum": 5,
                    "maximum": 50,
                    "default": 20,
                    "description": "Short-term SMA period"
                },
                "sma_long": {
                    "type": "integer",
                    "minimum": 20,
                    "maximum": 200,
                    "default": 50,
                    "description": "Long-term SMA period"
                },
                "volume_threshold": {
                    "type": "number",
                    "minimum": 0.5,
                    "maximum": 5.0,
                    "default": 1.5,
                    "description": "Volume threshold for confirmation"
                },
                "signal_strength_multiplier": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 2.0,
                    "default": 1.0,
                    "description": "Multiplier for signal strength"
                }
            },
            "required": ["rsi_period", "rsi_oversold", "rsi_overbought"],
            "additionalProperties": False
        } 