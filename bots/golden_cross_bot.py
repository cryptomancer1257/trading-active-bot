"""
Golden Cross Strategy Bot - Version 1.2.0
Classic trend-following strategy using 50/200 day moving average crossover. 
Ideal for catching major market trends with reduced false signals.
"""

from bots.bot_sdk.CustomBot import CustomBot
from bots.bot_sdk.Action import Action
import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class GoldenCrossBot(CustomBot):
    """
    Golden Cross Strategy Bot
    - Buy when short MA (50) crosses above long MA (200) - Golden Cross
    - Sell when short MA (50) crosses below long MA (200) - Death Cross
    - Uses 50/200 day moving averages for reduced false signals
    """
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str]):
        super().__init__(config, api_keys)
        
        # Bot metadata
        self.bot_name = "Golden Cross Strategy"
        self.description = "Classic trend-following strategy using 50/200 day moving average crossover"
        self.version = "1.2.0"
        self.bot_type = "TECHNICAL"
        
        # Strategy parameters from config
        self.short_window = config.get('short_window', 50)
        self.long_window = config.get('long_window', 200)
        self.position_size = config.get('position_size', 0.3)  # 30% of balance
        self.min_volume_threshold = config.get('min_volume_threshold', 1000000)  # Minimum volume
        self.volatility_threshold = config.get('volatility_threshold', 0.05)  # 5% volatility threshold
        
        logger.info(f"GoldenCrossBot v{self.version} initialized: short_window={self.short_window}, long_window={self.long_window}")
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """
        Golden Cross Strategy Implementation with enhanced signal validation
        
        Args:
            data: Preprocessed market data with OHLCV and technical indicators
            timeframe: Trading timeframe 
            subscription_config: Additional configuration from subscription
            
        Returns:
            Action: Trading decision with confidence level
        """
        try:
            # Check if we have enough data for long MA
            if len(data) < self.long_window:
                return Action("HOLD", 0.0, f"Insufficient data: {len(data)} < {self.long_window} periods required")
            
            # Use existing SMA columns if available, otherwise calculate
            short_ma_col = f'sma_{self.short_window}'
            long_ma_col = f'sma_{self.long_window}'
            
            # Calculate moving averages if not already present
            if short_ma_col not in data.columns:
                data[short_ma_col] = data['close'].rolling(window=self.short_window).mean()
            if long_ma_col not in data.columns:
                data[long_ma_col] = data['close'].rolling(window=self.long_window).mean()
            
            # Remove NaN values
            data = data.dropna()
            
            if len(data) < 2:
                return Action("HOLD", 0.0, "Not enough data after removing NaN values")
            
            # Get current and previous MA values
            current_short_ma = data[short_ma_col].iloc[-1]
            current_long_ma = data[long_ma_col].iloc[-1]
            prev_short_ma = data[short_ma_col].iloc[-2]
            prev_long_ma = data[long_ma_col].iloc[-2]
            
            current_price = data['close'].iloc[-1]
            current_volume = data['volume'].iloc[-1]
            
            # Calculate signal strength and market conditions
            ma_spread = abs(current_short_ma - current_long_ma) / current_price
            signal_strength = min(ma_spread * 10, 1.0)  # Normalize to 0-1 scale
            
            # Volume validation
            avg_volume = data['volume'].tail(20).mean()
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            # Volatility check
            volatility = data['close'].pct_change().tail(20).std()
            
            # Enhanced Golden Cross detection
            if prev_short_ma <= prev_long_ma and current_short_ma > current_long_ma:
                # Golden Cross detected
                confidence = signal_strength
                
                # Apply volume filter
                if volume_ratio < 0.8:
                    confidence *= 0.5  # Reduce confidence if volume is low
                
                # Apply volatility filter
                if volatility > self.volatility_threshold:
                    confidence *= 0.7  # Reduce confidence in high volatility
                
                # Additional confirmation: ensure trend strength
                ma_slope = (current_short_ma - data[short_ma_col].iloc[-5]) / current_short_ma
                if ma_slope > 0.002:  # Positive slope indicates strong trend
                    confidence *= 1.2  # Boost confidence
                
                confidence = min(confidence, 1.0)  # Cap at 100%
                position_size = self.position_size * confidence
                
                reason = f"Golden Cross: MA{self.short_window}({current_short_ma:.2f}) > MA{self.long_window}({current_long_ma:.2f}), confidence={confidence:.2f}, volume_ratio={volume_ratio:.2f}"
                
                logger.info(f"Golden Cross signal: {reason}")
                return Action.buy("PERCENTAGE", position_size, reason)
            
            # Enhanced Death Cross detection
            elif prev_short_ma >= prev_long_ma and current_short_ma < current_long_ma:
                # Death Cross detected
                confidence = signal_strength
                
                # Apply volume filter
                if volume_ratio < 0.8:
                    confidence *= 0.5
                
                # Apply volatility filter  
                if volatility > self.volatility_threshold:
                    confidence *= 0.7
                
                # Additional confirmation: ensure downward trend
                ma_slope = (current_short_ma - data[short_ma_col].iloc[-5]) / current_short_ma
                if ma_slope < -0.002:  # Negative slope indicates strong downward trend
                    confidence *= 1.2
                
                confidence = min(confidence, 1.0)
                
                reason = f"Death Cross: MA{self.short_window}({current_short_ma:.2f}) < MA{self.long_window}({current_long_ma:.2f}), confidence={confidence:.2f}, volume_ratio={volume_ratio:.2f}"
                
                logger.info(f"Death Cross signal: {reason}")
                return Action.sell("PERCENTAGE", confidence, reason)  # Sell with confidence-based amount
            
            # No cross signal - trend continuation check
            else:
                # Check if we're in a strong trend
                ma_distance = (current_short_ma - current_long_ma) / current_price
                
                if abs(ma_distance) > 0.02:  # 2% separation indicates strong trend
                    trend_direction = "bullish" if ma_distance > 0 else "bearish"
                    reason = f"Strong {trend_direction} trend: MA distance {ma_distance:.3f}, holding position"
                else:
                    reason = f"No cross signal: MA{self.short_window}({current_short_ma:.2f}) vs MA{self.long_window}({current_long_ma:.2f})"
                
                return Action("HOLD", 0.0, reason)
                
        except Exception as e:
            logger.error(f"Error in Golden Cross algorithm: {e}")
            return Action("HOLD", 0.0, f"Algorithm error: {str(e)}")
    
    def add_custom_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add custom features specific to Golden Cross strategy"""
        try:
            # Add trend strength indicators
            data['trend_strength'] = abs(data['sma_50'] - data['sma_20']) / data['close']
            
            # Add MA convergence indicator
            data['ma_convergence'] = (data['sma_50'] - data['sma_20']).rolling(window=5).std()
            
            # Add volume-price trend
            data['volume_price_trend'] = data['volume'] * data['close'].pct_change()
            
            # Add momentum confirmation
            data['momentum_5'] = data['close'].pct_change(5)
            data['momentum_10'] = data['close'].pct_change(10)
            
            return data
            
        except Exception as e:
            logger.error(f"Error adding custom features: {e}")
            return data
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this bot"""
        return {
            "type": "object",
            "properties": {
                "short_window": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 100,
                    "default": 50,
                    "description": "Short-term moving average period (default: 50)"
                },
                "long_window": {
                    "type": "integer", 
                    "minimum": 100,
                    "maximum": 500,
                    "default": 200,
                    "description": "Long-term moving average period (default: 200)"
                },
                "position_size": {
                    "type": "number",
                    "minimum": 0.01,
                    "maximum": 1.0,
                    "default": 0.3,
                    "description": "Position size as fraction of balance (0.3 = 30%)"
                },
                "min_volume_threshold": {
                    "type": "number",
                    "minimum": 100000,
                    "maximum": 10000000,
                    "default": 1000000,
                    "description": "Minimum volume threshold for signal validation"
                },
                "volatility_threshold": {
                    "type": "number",
                    "minimum": 0.01,
                    "maximum": 0.2,
                    "default": 0.05,
                    "description": "Volatility threshold for signal filtering (5%)"
                },
                "timeframe": {
                    "type": "string",
                    "enum": ["1m", "5m", "15m", "1h", "4h", "1d"],
                    "default": "1h",
                    "description": "Trading timeframe"
                }
            },
            "required": ["short_window", "long_window", "position_size"],
            "additionalProperties": True
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get detailed strategy information"""
        return {
            "name": self.bot_name,
            "version": self.version,
            "description": self.description,
            "strategy_type": "Trend Following",
            "indicators_used": ["SMA-50", "SMA-200", "Volume", "Volatility"],
            "suitable_for": ["Bitcoin", "Major Altcoins", "Trending Markets"],
            "risk_level": "Medium",
            "recommended_timeframes": ["1h", "4h", "1d"],
            "features": [
                "Classic Golden Cross/Death Cross detection",
                "Volume-based signal validation",
                "Volatility filtering",
                "Trend strength confirmation",
                "Position sizing based on signal confidence"
            ]
        }