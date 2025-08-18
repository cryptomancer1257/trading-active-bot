"""
Simple SMA Trading Bot
A basic trading bot using Simple Moving Average strategy
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List

from bots.bot_sdk import CustomBot, Action

logger = logging.getLogger(__name__)

class SimpleSMABot(CustomBot):
    """Simple SMA Trading Bot with basic technical analysis"""
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str] = None):
        """Initialize Simple SMA Bot"""
        super().__init__(config, api_keys)
        
        # Bot configuration
        self.trading_pair = config.get('trading_pair', 'BTCUSDT')
        self.short_period = config.get('short_period', 10)  # Short SMA period
        self.long_period = config.get('long_period', 20)    # Long SMA period
        self.min_data_points = config.get('min_data_points', 50)
        
        logger.info(f"Initialized SimpleSMABot for {self.trading_pair}")
        logger.info(f"SMA Configuration: Short={self.short_period}, Long={self.long_period}")
    
    def prepare_data(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> pd.DataFrame:
        """Prepare data for SMA analysis"""
        try:
            logger.info(f"Preparing data for {len(data)} data points")
            
            if len(data) < self.min_data_points:
                logger.warning(f"Insufficient data: {len(data)} < {self.min_data_points}")
                return data
            
            # Ensure required columns exist
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in data.columns:
                    logger.warning(f"Missing column {col}, using default values")
                    data[col] = 0.0
            
            # Convert to numeric types
            for col in required_columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
            
            # Fill any NaN values
            data = data.fillna(method='ffill').fillna(method='bfill')
            
            # Add SMA indicators
            data = self._add_sma_indicators(data)
            
            logger.info(f"Data preparation completed: {len(data)} rows")
            return data
            
        except Exception as e:
            logger.error(f"Error preparing data: {e}")
            return data
    
    def predict(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """Predict trading action based on SMA analysis"""
        try:
            logger.info(f"Making SMA prediction for {len(data)} data points")
            
            if len(data) < self.min_data_points:
                return Action(action="HOLD", value=0.0, reason="Insufficient data for SMA analysis")
            
            # Get latest SMA values
            current_price = float(data['close'].iloc[-1])
            short_sma = data[f'sma_{self.short_period}'].iloc[-1]
            long_sma = data[f'sma_{self.long_period}'].iloc[-1]
            
            # Check if we have valid SMA values
            if pd.isna(short_sma) or pd.isna(long_sma):
                return Action(action="HOLD", value=0.0, reason="Invalid SMA values")
            
            # Calculate signal strength
            signal_strength = 0
            reasons = []
            
            # SMA crossover logic
            if short_sma > long_sma:
                # Bullish signal
                signal_strength = 1
                reasons.append(f"Bullish SMA crossover (Short: {short_sma:.2f} > Long: {long_sma:.2f})")
                
                # Calculate confidence based on price position relative to SMAs
                if current_price > short_sma:
                    signal_strength += 0.5
                    reasons.append("Price above short SMA")
                
            elif short_sma < long_sma:
                # Bearish signal
                signal_strength = -1
                reasons.append(f"Bearish SMA crossover (Short: {short_sma:.2f} < Long: {long_sma:.2f})")
                
                # Calculate confidence based on price position relative to SMAs
                if current_price < short_sma:
                    signal_strength -= 0.5
                    reasons.append("Price below short SMA")
            
            # Calculate confidence (0-1 range)
            confidence = min(abs(signal_strength) * 0.6, 1.0)
            reason_text = ", ".join(reasons)
            
            # Generate action based on signal strength
            if signal_strength > 0.5:
                return Action(action="BUY", value=confidence, reason=reason_text)
            elif signal_strength < -0.5:
                return Action(action="SELL", value=confidence, reason=reason_text)
            else:
                return Action(action="HOLD", value=confidence, reason=reason_text)
                
        except Exception as e:
            logger.error(f"Error in SMA prediction: {e}")
            return Action(action="HOLD", value=0.0, reason=f"Prediction error: {e}")
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """Execute SMA trading algorithm (alias for predict for compatibility)"""
        return self.predict(data, timeframe, subscription_config)
    
    def _add_sma_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add SMA indicators to the data"""
        try:
            # Calculate short SMA
            data[f'sma_{self.short_period}'] = data['close'].rolling(window=self.short_period).mean()
            
            # Calculate long SMA
            data[f'sma_{self.long_period}'] = data['close'].rolling(window=self.long_period).mean()
            
            # Calculate SMA difference for additional analysis
            data['sma_diff'] = data[f'sma_{self.short_period}'] - data[f'sma_{self.long_period}']
            
            return data
            
        except Exception as e:
            logger.error(f"Error adding SMA indicators: {e}")
            return data
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Get bot configuration schema"""
        return {
            "trading_pair": {
                "type": "string",
                "default": "BTCUSDT",
                "description": "Trading pair symbol"
            },
            "short_period": {
                "type": "integer",
                "default": 10,
                "minimum": 5,
                "maximum": 50,
                "description": "Short SMA period"
            },
            "long_period": {
                "type": "integer", 
                "default": 20,
                "minimum": 10,
                "maximum": 100,
                "description": "Long SMA period"
            },
            "min_data_points": {
                "type": "integer",
                "default": 50,
                "minimum": 20,
                "description": "Minimum data points required for analysis"
            }
        }
    
    def get_bot_info(self) -> Dict[str, Any]:
        """Get bot information"""
        return {
            "name": "Simple SMA Bot",
            "description": "A simple trading bot using Simple Moving Average crossover strategy",
            "version": "1.0.0",
            "author": "AI Trading System",
            "strategy": "SMA Crossover",
            "timeframes": ["1h", "4h", "1d"],
            "pairs": ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        }

# Factory function for creating bot instances
def create_simple_sma_bot(config: Dict[str, Any] = None) -> SimpleSMABot:
    """
    Factory function to create SimpleSMABot instance
    
    Args:
        config: Bot configuration (optional)
        
    Returns:
        Configured SimpleSMABot instance
    """
    default_config = {
        'trading_pair': 'BTCUSDT',
        'short_period': 10,
        'long_period': 20,
        'min_data_points': 50
    }
    
    if config:
        default_config.update(config)
    
    return SimpleSMABot(default_config)

if __name__ == "__main__":
    # Test the bot
    print("🧪 Testing Simple SMA Bot...")
    
    # Create test data
    import numpy as np
    from datetime import datetime, timedelta
    
    # Generate sample OHLCV data
    dates = pd.date_range(start=datetime.now() - timedelta(days=100), periods=100, freq='1H')
    base_price = 50000
    
    test_data = []
    for i, date in enumerate(dates):
        # Simulate price movement
        change = np.random.normal(0, 0.02)  # 2% volatility
        base_price *= (1 + change)
        
        # Generate OHLCV
        open_price = base_price
        high_price = open_price * (1 + abs(np.random.normal(0, 0.01)))
        low_price = open_price * (1 - abs(np.random.normal(0, 0.01)))
        close_price = np.random.uniform(low_price, high_price)
        volume = np.random.uniform(100, 1000)
        
        test_data.append({
            'timestamp': date,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
    
    df = pd.DataFrame(test_data)
    df.set_index('timestamp', inplace=True)
    
    # Create and test bot
    bot = create_simple_sma_bot({
        'trading_pair': 'BTCUSDT',
        'short_period': 10,
        'long_period': 20
    })
    
    # Prepare data
    prepared_data = bot.prepare_data(df, '1h')
    
    # Make prediction
    action = bot.predict(prepared_data, '1h')
    
    print(f"📊 Test Results:")
    print(f"   Data points: {len(prepared_data)}")
    print(f"   Current price: ${prepared_data['close'].iloc[-1]:.2f}")
    print(f"   Short SMA: ${prepared_data['sma_10'].iloc[-1]:.2f}")
    print(f"   Long SMA: ${prepared_data['sma_20'].iloc[-1]:.2f}")
    print(f"   Action: {action.action}")
    print(f"   Confidence: {action.value:.2f}")
    print(f"   Reason: {action.reason}")
    
    print("✅ Simple SMA Bot test completed!")