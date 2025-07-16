"""
RSI Trading Bot Example

This bot demonstrates how to create a trading bot using the RSI indicator.
It generates buy signals when RSI is oversold and sell signals when RSI is overbought.
"""

import pandas as pd
import pandas_ta as ta
from bots.bot_sdk import CustomBot, Action

class RSIBot(CustomBot):
    bot_name = "RSI Trading Bot"
    bot_description = "Trades based on RSI overbought/oversold signals with customizable parameters"
    
    def __init__(self, bot_config: dict, user_api_keys: dict):
        super().__init__(bot_config, user_api_keys)
        
        # RSI parameters
        self.rsi_period = int(bot_config.get('rsi_period', 14))
        self.oversold_threshold = float(bot_config.get('oversold_threshold', 30))
        self.overbought_threshold = float(bot_config.get('overbought_threshold', 70))
        
        # Risk management
        self.stop_loss_percent = float(bot_config.get('stop_loss_percent', 5.0))
        self.take_profit_percent = float(bot_config.get('take_profit_percent', 10.0))
        
        # Position sizing
        self.position_size_percent = float(bot_config.get('position_size_percent', 25.0))
        
        print(f"RSI Bot initialized with period={self.rsi_period}, "
              f"oversold={self.oversold_threshold}, overbought={self.overbought_threshold}")
    
    def prepare_data(self, candles_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare market data by adding RSI indicator
        
        Args:
            candles_df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with RSI indicator added
        """
        try:
            # Ensure we have enough data
            if len(candles_df) < self.rsi_period + 1:
                return candles_df
            
            # Calculate RSI
            candles_df['rsi'] = ta.rsi(candles_df['close'], length=self.rsi_period)
            
            # Add additional indicators for confirmation
            candles_df['sma_20'] = ta.sma(candles_df['close'], length=20)
            candles_df['volume_sma'] = ta.sma(candles_df['volume'], length=20)
            
            # Calculate price momentum
            candles_df['price_change'] = candles_df['close'].pct_change()
            candles_df['price_momentum'] = candles_df['price_change'].rolling(window=3).mean()
            
            return candles_df
            
        except Exception as e:
            print(f"Error in prepare_data: {e}")
            return candles_df
    
    def predict(self, prepared_df: pd.DataFrame) -> Action:
        """
        Generate trading signals based on RSI
        
        Args:
            prepared_df: DataFrame with RSI indicator
            
        Returns:
            Action object with trading decision
        """
        try:
            # Need at least 2 rows for comparison
            if len(prepared_df) < 2:
                return Action.hold()
            
            # Get current and previous values
            current = prepared_df.iloc[-1]
            previous = prepared_df.iloc[-2]
            
            # Check if RSI is available
            if pd.isna(current['rsi']) or pd.isna(previous['rsi']):
                return Action.hold()
            
            current_rsi = current['rsi']
            previous_rsi = previous['rsi']
            current_price = current['close']
            
            # RSI oversold signal (potential buy)
            if (previous_rsi <= self.oversold_threshold and 
                current_rsi > self.oversold_threshold and
                current_rsi < 50):  # Still in bearish territory but recovering
                
                # Additional confirmation: check if price is above SMA
                if not pd.isna(current['sma_20']) and current_price > current['sma_20']:
                    return Action.buy(type="PERCENTAGE", value=self.position_size_percent)
                
                # Even without SMA confirmation, buy if RSI is very oversold
                if current_rsi < 25:
                    return Action.buy(type="PERCENTAGE", value=self.position_size_percent * 0.5)
            
            # RSI overbought signal (potential sell)
            elif (previous_rsi >= self.overbought_threshold and 
                  current_rsi < self.overbought_threshold and
                  current_rsi > 50):  # Still in bullish territory but weakening
                
                # Additional confirmation: check volume
                if (not pd.isna(current['volume_sma']) and 
                    current['volume'] > current['volume_sma'] * 1.2):
                    return Action.sell(type="PERCENTAGE", value=100)
                
                # Sell if RSI is very overbought
                if current_rsi > 75:
                    return Action.sell(type="PERCENTAGE", value=100)
            
            # Extreme RSI conditions
            elif current_rsi < 20:  # Extremely oversold
                return Action.buy(type="PERCENTAGE", value=self.position_size_percent * 0.75)
            
            elif current_rsi > 80:  # Extremely overbought
                return Action.sell(type="PERCENTAGE", value=100)
            
            # Momentum-based signals
            elif (current_rsi > 50 and 
                  not pd.isna(current['price_momentum']) and
                  current['price_momentum'] > 0.02):  # Strong upward momentum
                return Action.buy(type="PERCENTAGE", value=self.position_size_percent * 0.3)
            
            elif (current_rsi < 50 and 
                  not pd.isna(current['price_momentum']) and
                  current['price_momentum'] < -0.02):  # Strong downward momentum
                return Action.sell(type="PERCENTAGE", value=50)
            
            # Default: hold position
            return Action.hold()
            
        except Exception as e:
            print(f"Error in predict: {e}")
            return Action.hold()
    
    def get_signal_strength(self, prepared_df: pd.DataFrame) -> float:
        """
        Calculate signal strength (0-1)
        
        Args:
            prepared_df: DataFrame with indicators
            
        Returns:
            Signal strength between 0 and 1
        """
        try:
            if len(prepared_df) < 1:
                return 0.0
                
            current = prepared_df.iloc[-1]
            
            if pd.isna(current['rsi']):
                return 0.0
            
            rsi = current['rsi']
            
            # Calculate distance from neutral RSI (50)
            distance_from_neutral = abs(rsi - 50) / 50
            
            # Higher strength for extreme values
            if rsi < 30 or rsi > 70:
                return min(distance_from_neutral * 1.5, 1.0)
            else:
                return distance_from_neutral * 0.5
                
        except Exception as e:
            print(f"Error calculating signal strength: {e}")
            return 0.0
    
    def get_risk_metrics(self, prepared_df: pd.DataFrame) -> dict:
        """
        Calculate risk metrics for current market conditions
        
        Args:
            prepared_df: DataFrame with indicators
            
        Returns:
            Dictionary with risk metrics
        """
        try:
            if len(prepared_df) < 20:
                return {"volatility": 0.0, "trend_strength": 0.0}
            
            # Calculate volatility (standard deviation of returns)
            returns = prepared_df['close'].pct_change().dropna()
            volatility = returns.std() * 100  # Convert to percentage
            
            # Calculate trend strength using SMA
            current_price = prepared_df['close'].iloc[-1]
            sma_20 = prepared_df['sma_20'].iloc[-1]
            
            if not pd.isna(sma_20) and sma_20 > 0:
                trend_strength = abs((current_price - sma_20) / sma_20) * 100
            else:
                trend_strength = 0.0
            
            return {
                "volatility": round(volatility, 2),
                "trend_strength": round(trend_strength, 2),
                "rsi_current": round(prepared_df['rsi'].iloc[-1], 2) if not pd.isna(prepared_df['rsi'].iloc[-1]) else 0.0
            }
            
        except Exception as e:
            print(f"Error calculating risk metrics: {e}")
            return {"volatility": 0.0, "trend_strength": 0.0}

# Configuration schema for the bot
RSI_BOT_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "rsi_period": {
            "type": "integer",
            "minimum": 5,
            "maximum": 50,
            "default": 14,
            "description": "Period for RSI calculation"
        },
        "oversold_threshold": {
            "type": "number",
            "minimum": 10,
            "maximum": 40,
            "default": 30,
            "description": "RSI level considered oversold"
        },
        "overbought_threshold": {
            "type": "number",
            "minimum": 60,
            "maximum": 90,
            "default": 70,
            "description": "RSI level considered overbought"
        },
        "position_size_percent": {
            "type": "number",
            "minimum": 1,
            "maximum": 100,
            "default": 25,
            "description": "Position size as percentage of portfolio"
        },
        "stop_loss_percent": {
            "type": "number",
            "minimum": 1,
            "maximum": 20,
            "default": 5,
            "description": "Stop loss percentage"
        },
        "take_profit_percent": {
            "type": "number",
            "minimum": 1,
            "maximum": 50,
            "default": 10,
            "description": "Take profit percentage"
        }
    },
    "required": ["rsi_period", "oversold_threshold", "overbought_threshold"]
}

# Default configuration
RSI_BOT_DEFAULT_CONFIG = {
    "rsi_period": 14,
    "oversold_threshold": 30,
    "overbought_threshold": 70,
    "position_size_percent": 25.0,
    "stop_loss_percent": 5.0,
    "take_profit_percent": 10.0
} 