"""
Simple Moving Average Trading Bot
Bot đơn giản sử dụng SMA crossover strategy
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

from bots.bot_sdk.CustomBot import CustomBot
from bots.bot_sdk.Action import Action

logger = logging.getLogger(__name__)

class SimpleSMABot(CustomBot):
    """
    Simple Moving Average Trading Bot
    Sử dụng SMA crossover strategy để trading
    """
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str]):
        super().__init__(config, api_keys)
        
        # Bot metadata
        self.bot_name = "Simple Moving Average Bot"
        self.description = "Simple bot using SMA crossover strategy for trading signals"
        self.version = "1.0.0"
        self.bot_type = "TECHNICAL"
        
        # SMA Configuration
        self.ma_short_period = config.get('ma_short_period', 10)
        self.ma_long_period = config.get('ma_long_period', 20)
        self.min_data_points = max(self.ma_long_period + 10, 50)
        
        # Trading configuration
        self.position_size = config.get('position_size', 0.1)  # 10% of portfolio
        self.stop_loss_pct = config.get('stop_loss_pct', 0.02)  # 2% stop loss
        self.take_profit_pct = config.get('take_profit_pct', 0.04)  # 4% take profit
        
        logger.info(f"Initialized {self.bot_name} with MA({self.ma_short_period}, {self.ma_long_period})")
    
    def crawl_data(self) -> pd.DataFrame:
        """
        Crawl historical price data from exchange
        """
        try:
            if not self.exchange_client:
                logger.error("Exchange client not initialized")
                return pd.DataFrame()
            
            # Get historical klines data
            klines = self.exchange_client.get_historical_klines(
                symbol=self.trading_pair,
                interval='1h',  # 1 hour intervals
                limit=self.min_data_points + 20  # Extra buffer
            )
            
            if not klines:
                logger.warning("No klines data received")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert numeric columns
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"Crawled {len(df)} data points for {self.trading_pair}")
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Error crawling data: {e}")
            return pd.DataFrame()
    
    def preprocess_data(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess raw data and calculate moving averages
        """
        try:
            if raw_data.empty:
                return pd.DataFrame()
            
            df = raw_data.copy()
            
            # Calculate Simple Moving Averages
            df['sma_short'] = df['close'].rolling(window=self.ma_short_period).mean()
            df['sma_long'] = df['close'].rolling(window=self.ma_long_period).mean()
            
            # Calculate additional indicators
            df['sma_diff'] = df['sma_short'] - df['sma_long']
            df['sma_diff_pct'] = (df['sma_short'] / df['sma_long'] - 1) * 100
            
            # Signal indicators
            df['bullish_cross'] = (
                (df['sma_short'] > df['sma_long']) & 
                (df['sma_short'].shift(1) <= df['sma_long'].shift(1))
            )
            df['bearish_cross'] = (
                (df['sma_short'] < df['sma_long']) & 
                (df['sma_short'].shift(1) >= df['sma_long'].shift(1))
            )
            
            # Volume analysis
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            
            # Price momentum
            df['price_change'] = df['close'].pct_change()
            df['momentum'] = df['close'].rolling(window=5).mean() / df['close'].rolling(window=10).mean() - 1
            
            # Drop NaN values
            df.dropna(inplace=True)
            
            logger.info(f"Preprocessed data with {len(df)} valid rows")
            return df
            
        except Exception as e:
            logger.error(f"Error preprocessing data: {e}")
            return pd.DataFrame()
    
    def run_algorithm(self, processed_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Run SMA crossover algorithm
        """
        try:
            if processed_data.empty or len(processed_data) < self.min_data_points:
                return {
                    'signal': 'HOLD',
                    'confidence': 0.0,
                    'reason': 'Insufficient data for SMA analysis'
                }
            
            # Get latest data points
            latest = processed_data.iloc[-1]
            previous = processed_data.iloc[-2] if len(processed_data) > 1 else latest
            
            # Current SMA values
            sma_short = latest['sma_short']
            sma_long = latest['sma_long']
            sma_diff_pct = latest['sma_diff_pct']
            
            # Check for crossover signals
            bullish_cross = latest['bullish_cross']
            bearish_cross = latest['bearish_cross']
            
            # Volume confirmation
            volume_ratio = latest['volume_ratio']
            volume_confirmed = volume_ratio > 1.2  # Above average volume
            
            # Momentum check
            momentum = latest['momentum']
            
            # Generate signal
            signal = 'HOLD'
            confidence = 0.5
            reason_parts = []
            
            if bullish_cross:
                signal = 'BUY'
                confidence = 0.7
                reason_parts.append("Bullish SMA crossover")
                
                # Increase confidence with confirmations
                if volume_confirmed:
                    confidence += 0.1
                    reason_parts.append("high volume")
                if momentum > 0.01:
                    confidence += 0.1
                    reason_parts.append("positive momentum")
                    
            elif bearish_cross:
                signal = 'SELL'
                confidence = 0.7
                reason_parts.append("Bearish SMA crossover")
                
                # Increase confidence with confirmations
                if volume_confirmed:
                    confidence += 0.1
                    reason_parts.append("high volume")
                if momentum < -0.01:
                    confidence += 0.1
                    reason_parts.append("negative momentum")
            
            else:
                # No crossover, check trend strength
                if abs(sma_diff_pct) > 2.0:  # Strong trend
                    if sma_short > sma_long:
                        signal = 'BUY' if momentum > 0 else 'HOLD'
                        confidence = 0.6
                        reason_parts.append("Strong uptrend")
                    else:
                        signal = 'SELL' if momentum < 0 else 'HOLD'
                        confidence = 0.6
                        reason_parts.append("Strong downtrend")
                else:
                    reason_parts.append("No clear trend")
            
            # Cap confidence
            confidence = min(confidence, 0.95)
            
            result = {
                'signal': signal,
                'confidence': confidence,
                'sma_short': sma_short,
                'sma_long': sma_long,
                'sma_diff_pct': sma_diff_pct,
                'bullish_cross': bullish_cross,
                'bearish_cross': bearish_cross,
                'volume_ratio': volume_ratio,
                'momentum': momentum,
                'reason': ' + '.join(reason_parts) if reason_parts else 'No clear signal'
            }
            
            logger.info(f"SMA Algorithm result: {signal} (confidence: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error in SMA algorithm: {e}")
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'reason': f'Algorithm error: {str(e)}'
            }
    
    def make_prediction(self, algorithm_result: Dict[str, Any]) -> Action:
        """
        Convert algorithm result to trading action
        """
        try:
            signal = algorithm_result.get('signal', 'HOLD')
            confidence = algorithm_result.get('confidence', 0.0)
            reason = algorithm_result.get('reason', 'No reason provided')
            
            # Minimum confidence threshold
            if confidence < 0.6:
                return Action.hold(f"Low confidence ({confidence:.2f}): {reason}")
            
            # Calculate position size based on confidence
            base_position = self.position_size * 100  # Convert to percentage
            adjusted_position = base_position * confidence
            
            if signal == 'BUY':
                return Action.buy(
                    type="PERCENTAGE",
                    value=adjusted_position,
                    reason=f"SMA BUY signal (conf: {confidence:.2f}): {reason}"
                )
            elif signal == 'SELL':
                # Sell partial position based on confidence
                sell_percentage = min(50.0 * confidence, 75.0)
                return Action.sell(
                    type="PERCENTAGE",
                    value=sell_percentage,
                    reason=f"SMA SELL signal (conf: {confidence:.2f}): {reason}"
                )
            else:
                return Action.hold(f"SMA HOLD signal: {reason}")
                
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return Action.hold(f"Prediction error: {str(e)}")
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """
        Main execution method - implements the complete trading pipeline
        """
        try:
            logger.info(f"Executing SMA algorithm for {self.trading_pair} on {timeframe}")
            
            # Step 1: Crawl data (if data not provided)
            if data.empty:
                data = self.crawl_data()
            
            # Step 2: Preprocess data
            processed_data = self.preprocess_data(data)
            
            # Step 3: Run algorithm
            algorithm_result = self.run_algorithm(processed_data)
            
            # Step 4: Make prediction
            action = self.make_prediction(algorithm_result)
            
            logger.info(f"SMA Bot action: {action}")
            return action
            
        except Exception as e:
            logger.error(f"Error in execute_algorithm: {e}")
            return Action.hold(f"Execution error: {str(e)}")
    
    def get_bot_info(self) -> Dict[str, Any]:
        """Return bot information"""
        return {
            'name': self.bot_name,
            'description': self.description,
            'version': self.version,
            'type': self.bot_type,
            'strategy': 'SMA Crossover',
            'features': [
                'Simple Moving Average Crossover',
                'Volume Confirmation',
                'Momentum Analysis',
                'Risk Management',
                'Confidence-based Position Sizing'
            ],
            'parameters': {
                'ma_short_period': self.ma_short_period,
                'ma_long_period': self.ma_long_period,
                'position_size': self.position_size,
                'stop_loss_pct': self.stop_loss_pct,
                'take_profit_pct': self.take_profit_pct
            }
        }

# Test function
def test_bot():
    """Test the SMA bot with sample configuration"""
    config = {
        'exchange_type': 'BINANCE',
        'trading_pair': 'BTC/USDT',
        'ma_short_period': 10,
        'ma_long_period': 20,
        'position_size': 0.1,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.04
    }
    
    api_keys = {
        'api_key': 'test_key',
        'api_secret': 'test_secret'
    }
    
    bot = SimpleSMABot(config, api_keys)
    print("✅ Simple SMA Bot created successfully!")
    print(f"Bot Info: {bot.get_bot_info()}")
    
    return bot

if __name__ == "__main__":
    test_bot()