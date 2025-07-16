"""
Golden Cross Trading Bot - Fixed Version
Buys when 50-day MA crosses above 200-day MA, sells when opposite occurs.
Compatible with new CustomBot framework.
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
    - Buy when short MA crosses above long MA (Golden Cross)
    - Sell when short MA crosses below long MA (Death Cross)
    """
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str]):
        super().__init__(config, api_keys)
        
        # Bot metadata
        self.bot_name = "Golden Cross Bot"
        self.description = "Trades based on moving average crossovers"
        self.version = "1.0.0"
        self.bot_type = "TECHNICAL"
        
        # Strategy parameters
        self.short_window = config.get('short_window', 50)
        self.long_window = config.get('long_window', 200)
        self.position_size = config.get('position_size', 0.2)  # 20% of balance
        
        logger.info(f"GoldenCrossBot initialized: short_window={self.short_window}, long_window={self.long_window}")
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """
        Golden Cross Strategy Implementation
        
        Args:
            data: Preprocessed market data with OHLCV
            timeframe: Trading timeframe (not used in this strategy)
            subscription_config: Additional configuration
            
        Returns:
            Action: Trading decision
        """
        try:
            # Check if we have enough data
            if len(data) < self.long_window:
                return Action("HOLD", 0.0, f"Insufficient data: {len(data)} < {self.long_window}")
            
            # Calculate moving averages (they might already be calculated in preprocessing)
            if 'ma_short' not in data.columns:
                data[f'ma_{self.short_window}'] = data['close'].rolling(window=self.short_window).mean()
            if 'ma_long' not in data.columns:
                data[f'ma_{self.long_window}'] = data['close'].rolling(window=self.long_window).mean()
            
            # Use calculated MAs or use our custom names
            ma_short_col = f'ma_{self.short_window}' if f'ma_{self.short_window}' in data.columns else 'sma_50'
            ma_long_col = f'ma_{self.long_window}' if f'ma_{self.long_window}' in data.columns else 'sma_20'
            
            # If standard MA columns don't exist, calculate them
            if ma_short_col not in data.columns:
                data[ma_short_col] = data['close'].rolling(window=self.short_window).mean()
            if ma_long_col not in data.columns:
                data[ma_long_col] = data['close'].rolling(window=self.long_window).mean()
            
            # Remove NaN values
            data = data.dropna()
            
            if len(data) < 2:
                return Action("HOLD", 0.0, "Not enough data after removing NaN")
            
            # Get current and previous values
            current_short_ma = data[ma_short_col].iloc[-1]
            current_long_ma = data[ma_long_col].iloc[-1]
            prev_short_ma = data[ma_short_col].iloc[-2]
            prev_long_ma = data[ma_long_col].iloc[-2]
            current_price = data['close'].iloc[-1]
            
            # Calculate signal strength
            ma_diff_current = current_short_ma - current_long_ma
            ma_diff_prev = prev_short_ma - prev_long_ma
            signal_strength = abs(ma_diff_current) / current_price  # Normalize by price
            
            # Golden Cross: short MA crosses above long MA
            if prev_short_ma <= prev_long_ma and current_short_ma > current_long_ma:
                confidence = min(signal_strength * 100, 1.0)  # Cap at 100%
                reason = f"Golden Cross detected: MA{self.short_window}({current_short_ma:.2f}) > MA{self.long_window}({current_long_ma:.2f})"
                logger.info(f"Golden Cross signal: {reason}")
                return Action("BUY", self.position_size * confidence, reason)
            
            # Death Cross: short MA crosses below long MA  
            elif prev_short_ma >= prev_long_ma and current_short_ma < current_long_ma:
                confidence = min(signal_strength * 100, 1.0)  # Cap at 100%
                reason = f"Death Cross detected: MA{self.short_window}({current_short_ma:.2f}) < MA{self.long_window}({current_long_ma:.2f})"
                logger.info(f"Death Cross signal: {reason}")
                return Action("SELL", confidence, reason)  # Sell all position
            
            # No cross detected
            else:
                reason = f"No cross signal: MA{self.short_window}({current_short_ma:.2f}) vs MA{self.long_window}({current_long_ma:.2f})"
                return Action("HOLD", 0.0, reason)
                
        except Exception as e:
            logger.error(f"Error in Golden Cross algorithm: {e}")
            return Action("HOLD", 0.0, f"Algorithm error: {str(e)}")
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this bot"""
        return {
            "type": "object",
            "properties": {
                "short_window": {
                    "type": "integer",
                    "minimum": 5,
                    "maximum": 100,
                    "default": 50,
                    "description": "Short-term moving average period"
                },
                "long_window": {
                    "type": "integer", 
                    "minimum": 50,
                    "maximum": 500,
                    "default": 200,
                    "description": "Long-term moving average period"
                },
                "position_size": {
                    "type": "number",
                    "minimum": 0.01,
                    "maximum": 1.0,
                    "default": 0.2,
                    "description": "Position size as fraction of balance (0.2 = 20%)"
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