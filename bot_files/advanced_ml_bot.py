"""
Advanced ML Trading Bot
Sử dụng Machine Learning để dự đoán giá và đưa ra quyết định trading
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import json

from bots.bot_sdk.CustomBot import CustomBot
from bots.bot_sdk.Action import Action

logger = logging.getLogger(__name__)

class AdvancedMLBot(CustomBot):
    """
    Advanced Machine Learning Trading Bot
    Sử dụng multiple indicators và ML models để trading
    """
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str]):
        super().__init__(config, api_keys)
        
        # Bot metadata
        self.bot_name = "Advanced ML Trading Bot"
        self.description = "Advanced ML bot using multiple indicators and neural networks"
        self.version = "2.0.0"
        self.bot_type = "ML"
        
        # ML Configuration
        self.lookback_period = config.get('lookback_period', 50)
        self.prediction_threshold = config.get('prediction_threshold', 0.6)
        self.risk_tolerance = config.get('risk_tolerance', 0.02)  # 2% risk per trade
        
        # Technical indicators config
        self.sma_short = config.get('sma_short', 10)
        self.sma_long = config.get('sma_long', 30)
        self.rsi_period = config.get('rsi_period', 14)
        self.bb_period = config.get('bb_period', 20)
        self.bb_std = config.get('bb_std', 2)
        
        # ML Model parameters
        self.model_features = [
            'sma_ratio', 'rsi', 'bb_position', 'volume_ratio', 
            'price_change', 'volatility', 'momentum'
        ]
        
        logger.info(f"Initialized {self.bot_name} v{self.version}")
    
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
                limit=self.lookback_period + 50  # Extra data for indicators
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
        Preprocess raw data and calculate technical indicators
        """
        try:
            if raw_data.empty:
                return pd.DataFrame()
            
            df = raw_data.copy()
            
            # Calculate technical indicators
            # 1. Simple Moving Averages
            df['sma_short'] = df['close'].rolling(window=self.sma_short).mean()
            df['sma_long'] = df['close'].rolling(window=self.sma_long).mean()
            df['sma_ratio'] = df['sma_short'] / df['sma_long']
            
            # 2. RSI (Relative Strength Index)
            df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)
            
            # 3. Bollinger Bands
            bb_sma = df['close'].rolling(window=self.bb_period).mean()
            bb_std = df['close'].rolling(window=self.bb_period).std()
            df['bb_upper'] = bb_sma + (bb_std * self.bb_std)
            df['bb_lower'] = bb_sma - (bb_std * self.bb_std)
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # 4. Volume indicators
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            
            # 5. Price change and momentum
            df['price_change'] = df['close'].pct_change()
            df['volatility'] = df['price_change'].rolling(window=10).std()
            df['momentum'] = df['close'] / df['close'].shift(10) - 1
            
            # 6. Future price for training (shifted target)
            df['future_return'] = df['close'].shift(-1) / df['close'] - 1
            
            # Drop NaN values
            df.dropna(inplace=True)
            
            logger.info(f"Preprocessed data with {len(df)} valid rows")
            return df
            
        except Exception as e:
            logger.error(f"Error preprocessing data: {e}")
            return pd.DataFrame()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def run_algorithm(self, processed_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Run ML algorithm to generate trading signals
        """
        try:
            if processed_data.empty or len(processed_data) < self.lookback_period:
                return {
                    'signal': 'HOLD',
                    'confidence': 0.0,
                    'reason': 'Insufficient data for ML prediction'
                }
            
            # Get latest data point
            latest = processed_data.iloc[-1]
            
            # Feature engineering
            features = {
                'sma_ratio': latest['sma_ratio'],
                'rsi': latest['rsi'],
                'bb_position': latest['bb_position'],
                'volume_ratio': latest['volume_ratio'],
                'price_change': latest['price_change'],
                'volatility': latest['volatility'],
                'momentum': latest['momentum']
            }
            
            # Simple ML-like scoring system (in production, use real ML models)
            score = self._calculate_ml_score(features)
            
            # Generate signal based on score
            if score > self.prediction_threshold:
                signal = 'BUY'
                confidence = min(score, 0.95)
            elif score < -self.prediction_threshold:
                signal = 'SELL'
                confidence = min(abs(score), 0.95)
            else:
                signal = 'HOLD'
                confidence = 1 - abs(score)
            
            # Market condition analysis
            market_condition = self._analyze_market_condition(processed_data.tail(20))
            
            result = {
                'signal': signal,
                'confidence': confidence,
                'ml_score': score,
                'features': features,
                'market_condition': market_condition,
                'reason': f"ML Score: {score:.3f}, Market: {market_condition}"
            }
            
            logger.info(f"ML Algorithm result: {signal} (confidence: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error in ML algorithm: {e}")
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'reason': f'Algorithm error: {str(e)}'
            }
    
    def _calculate_ml_score(self, features: Dict[str, float]) -> float:
        """
        Calculate ML-like score (simplified version)
        In production, this would use trained neural networks
        """
        score = 0.0
        
        # SMA trend signal
        if features['sma_ratio'] > 1.02:
            score += 0.3
        elif features['sma_ratio'] < 0.98:
            score -= 0.3
        
        # RSI signals
        if features['rsi'] < 30:  # Oversold
            score += 0.4
        elif features['rsi'] > 70:  # Overbought
            score -= 0.4
        
        # Bollinger Bands position
        if features['bb_position'] < 0.2:  # Near lower band
            score += 0.2
        elif features['bb_position'] > 0.8:  # Near upper band
            score -= 0.2
        
        # Volume confirmation
        if features['volume_ratio'] > 1.5:  # High volume
            score *= 1.2
        
        # Momentum factor
        if features['momentum'] > 0.05:
            score += 0.1
        elif features['momentum'] < -0.05:
            score -= 0.1
        
        # Volatility adjustment
        if features['volatility'] > 0.05:  # High volatility
            score *= 0.8  # Reduce confidence
        
        return np.clip(score, -1.0, 1.0)
    
    def _analyze_market_condition(self, recent_data: pd.DataFrame) -> str:
        """Analyze current market condition"""
        if recent_data.empty:
            return "UNKNOWN"
        
        price_trend = recent_data['close'].iloc[-1] / recent_data['close'].iloc[0] - 1
        volatility = recent_data['price_change'].std()
        
        if price_trend > 0.05 and volatility < 0.03:
            return "BULLISH_STABLE"
        elif price_trend > 0.02:
            return "BULLISH"
        elif price_trend < -0.05 and volatility < 0.03:
            return "BEARISH_STABLE"
        elif price_trend < -0.02:
            return "BEARISH"
        elif volatility > 0.05:
            return "VOLATILE"
        else:
            return "SIDEWAYS"
    
    def make_prediction(self, algorithm_result: Dict[str, Any]) -> Action:
        """
        Convert algorithm result to trading action
        """
        try:
            signal = algorithm_result.get('signal', 'HOLD')
            confidence = algorithm_result.get('confidence', 0.0)
            reason = algorithm_result.get('reason', 'No reason provided')
            
            # Risk management
            if confidence < 0.5:
                return Action.hold(f"Low confidence ({confidence:.2f}): {reason}")
            
            # Position sizing based on confidence and risk tolerance
            position_size = min(confidence * self.risk_tolerance * 2, self.risk_tolerance)
            
            if signal == 'BUY':
                return Action.buy(
                    type="PERCENTAGE",
                    value=position_size * 100,  # Convert to percentage
                    reason=f"ML BUY signal (conf: {confidence:.2f}): {reason}"
                )
            elif signal == 'SELL':
                return Action.sell(
                    type="PERCENTAGE", 
                    value=50.0,  # Sell 50% of position
                    reason=f"ML SELL signal (conf: {confidence:.2f}): {reason}"
                )
            else:
                return Action.hold(f"ML HOLD signal: {reason}")
                
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return Action.hold(f"Prediction error: {str(e)}")
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """
        Main execution method - implements the complete trading pipeline
        """
        try:
            logger.info(f"Executing ML algorithm for {self.trading_pair} on {timeframe}")
            
            # Step 1: Crawl data (if data not provided)
            if data.empty:
                data = self.crawl_data()
            
            # Step 2: Preprocess data
            processed_data = self.preprocess_data(data)
            
            # Step 3: Run algorithm
            algorithm_result = self.run_algorithm(processed_data)
            
            # Step 4: Make prediction
            action = self.make_prediction(algorithm_result)
            
            logger.info(f"ML Bot action: {action}")
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
            'features': [
                'Machine Learning Predictions',
                'Multiple Technical Indicators',
                'Risk Management',
                'Market Condition Analysis',
                'Confidence-based Position Sizing'
            ],
            'parameters': {
                'lookback_period': self.lookback_period,
                'prediction_threshold': self.prediction_threshold,
                'risk_tolerance': self.risk_tolerance,
                'sma_short': self.sma_short,
                'sma_long': self.sma_long,
                'rsi_period': self.rsi_period
            }
        }

# Test function
def test_bot():
    """Test the ML bot with sample configuration"""
    config = {
        'exchange_type': 'BINANCE',
        'trading_pair': 'BTC/USDT',
        'lookback_period': 50,
        'prediction_threshold': 0.6,
        'risk_tolerance': 0.02
    }
    
    api_keys = {
        'api_key': 'test_key',
        'api_secret': 'test_secret'
    }
    
    bot = AdvancedMLBot(config, api_keys)
    print("✅ Advanced ML Bot created successfully!")
    print(f"Bot Info: {bot.get_bot_info()}")
    
    return bot

if __name__ == "__main__":
    test_bot()