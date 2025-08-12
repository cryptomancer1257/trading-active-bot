"""
LLM Trading Bot
Advanced trading bot using OpenAI, Claude, or Gemini for market analysis with Fibonacci
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging
import asyncio
from datetime import datetime

from bots.bot_sdk.CustomBot import CustomBot
from bots.bot_sdk.Action import Action
from services.llm_integration import create_llm_service

logger = logging.getLogger(__name__)

class LLMTradingBot(CustomBot):
    """
    LLM Trading Bot using OpenAI, Claude, or Gemini
    Advanced AI-powered trading with Fibonacci analysis
    """
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str]):
        super().__init__(config, api_keys)
        
        # Bot metadata
        self.bot_name = "LLM Trading Bot"
        self.description = "Advanced AI-powered trading bot with Fibonacci analysis"
        self.version = "1.0.0"
        self.bot_type = "LLM"
        
        # LLM Configuration
        self.llm_model = config.get('llm_model', 'openai')  # openai, claude, gemini
        self.analysis_timeframes = config.get('analysis_timeframes', ['1h', '4h', '1d'])
        self.confidence_threshold = config.get('confidence_threshold', 70)  # Minimum confidence %
        self.data_points = config.get('data_points', 100)  # How much historical data to use
        
        # Risk management
        self.max_position_size = config.get('max_position_size', 0.1)  # 10% max
        self.stop_loss_pct = config.get('stop_loss_pct', 0.02)  # 2% default
        self.take_profit_pct = config.get('take_profit_pct', 0.04)  # 4% default
        
        # Initialize LLM service
        llm_config = {
            'openai_api_key': api_keys.get('openai_api_key', os.getenv('OPENAI_API_KEY')),
            'claude_api_key': api_keys.get('claude_api_key', os.getenv('CLAUDE_API_KEY')),
            'gemini_api_key': api_keys.get('gemini_api_key', os.getenv('GEMINI_API_KEY'))
        }
        
        self.llm_service = create_llm_service(llm_config)
        
        # Check if chosen model is available
        if self.llm_model == 'openai' and not self.llm_service.openai_client:
            logger.warning("OpenAI not available, falling back to available model")
            self._select_fallback_model()
        elif self.llm_model == 'claude' and not self.llm_service.claude_client:
            logger.warning("Claude not available, falling back to available model")
            self._select_fallback_model()
        elif self.llm_model == 'gemini' and not self.llm_service.gemini_client:
            logger.warning("Gemini not available, falling back to available model")
            self._select_fallback_model()
        
        logger.info(f"Initialized LLM Trading Bot with {self.llm_model} model")
    
    def _select_fallback_model(self):
        """Select available LLM model as fallback"""
        if self.llm_service.openai_client:
            self.llm_model = 'openai'
        elif self.llm_service.claude_client:
            self.llm_model = 'claude'
        elif self.llm_service.gemini_client:
            self.llm_model = 'gemini'
        else:
            logger.error("No LLM models available!")
            self.llm_model = None
    
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
                interval='1h',  # Use 1h as base interval
                limit=self.data_points
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
    
    def preprocess_data(self, raw_data: pd.DataFrame) -> Dict[str, List[Dict]]:
        """
        Preprocess raw data into timeframe format for LLM analysis
        """
        try:
            if raw_data.empty:
                return {}
            
            timeframes_data = {}
            
            # Convert to different timeframes
            for timeframe in self.analysis_timeframes:
                if timeframe == '1h':
                    # Use original data (already 1h)
                    tf_data = raw_data.copy()
                elif timeframe == '4h':
                    # Resample to 4h
                    tf_data = raw_data.resample('4H').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).dropna()
                elif timeframe == '1d':
                    # Resample to 1d
                    tf_data = raw_data.resample('1D').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).dropna()
                else:
                    continue
                
                # Convert to LLM format
                ohlcv_list = []
                for idx, row in tf_data.iterrows():
                    ohlcv_list.append({
                        'timestamp': int(idx.timestamp() * 1000),
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': float(row['volume'])
                    })
                
                timeframes_data[timeframe] = ohlcv_list
            
            logger.info(f"Preprocessed data for timeframes: {list(timeframes_data.keys())}")
            return timeframes_data
            
        except Exception as e:
            logger.error(f"Error preprocessing data: {e}")
            return {}
    
    def run_algorithm(self, processed_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Run LLM algorithm to generate trading signals
        """
        try:
            if not processed_data or not self.llm_model:
                return {
                    'signal': 'HOLD',
                    'confidence': 0.0,
                    'reason': 'No data or LLM model available'
                }
            
            # Run LLM analysis asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                analysis = loop.run_until_complete(
                    self.llm_service.analyze_market(
                        symbol=self.trading_pair,
                        timeframes_data=processed_data,
                        model=self.llm_model
                    )
                )
            finally:
                loop.close()
            
            # Process LLM analysis
            if "error" in analysis:
                return {
                    'signal': 'HOLD',
                    'confidence': 0.0,
                    'reason': f'LLM error: {analysis["error"]}'
                }
            
            if not analysis.get("parsed", False):
                return {
                    'signal': 'HOLD',
                    'confidence': 0.0,
                    'reason': 'Failed to parse LLM response'
                }
            
            # Extract recommendation
            recommendation = analysis.get("recommendation", {})
            action = recommendation.get("action", "HOLD")
            # Handle confidence - remove % if present
            confidence_str = str(recommendation.get("confidence", 0)).replace('%', '')
            confidence = float(confidence_str)
            entry_price = recommendation.get("entry_price")
            take_profit = recommendation.get("take_profit")
            stop_loss = recommendation.get("stop_loss")
            strategy = recommendation.get("strategy", "LLM Analysis")
            reasoning = recommendation.get("reasoning", "AI-generated signal")
            
            # Validate confidence threshold
            if confidence < self.confidence_threshold:
                return {
                    'signal': 'HOLD',
                    'confidence': confidence,
                    'reason': f'Low confidence ({confidence}%) below threshold ({self.confidence_threshold}%)'
                }
            
            result = {
                'signal': action,
                'confidence': confidence,
                'entry_price': entry_price,
                'take_profit': take_profit,
                'stop_loss': stop_loss,
                'strategy': strategy,
                'reasoning': reasoning,
                'llm_model': self.llm_model,
                'analysis': analysis.get("analysis", {}),
                'reason': f'{self.llm_model.upper()} {action} signal: {reasoning}'
            }
            
            logger.info(f"LLM Algorithm result: {action} (confidence: {confidence}%)")
            return result
            
        except Exception as e:
            logger.error(f"Error in LLM algorithm: {e}")
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
            
            # Risk management - adjust position size based on confidence
            base_position = self.max_position_size * 100  # Convert to percentage
            confidence_factor = confidence / 100.0
            adjusted_position = base_position * confidence_factor
            
            if signal == 'BUY':
                return Action.buy(
                    type="PERCENTAGE",
                    value=adjusted_position,
                    reason=f"LLM BUY signal: {reason}"
                )
            elif signal == 'SELL':
                # Sell based on confidence
                sell_percentage = min(75.0 * confidence_factor, 90.0)
                return Action.sell(
                    type="PERCENTAGE",
                    value=sell_percentage,
                    reason=f"LLM SELL signal: {reason}"
                )
            elif signal == 'CLOSE':
                return Action.sell(
                    type="PERCENTAGE",
                    value=100.0,
                    reason=f"LLM CLOSE signal: {reason}"
                )
            else:
                return Action.hold(f"LLM HOLD signal: {reason}")
                
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return Action.hold(f"Prediction error: {str(e)}")
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """
        Main execution method - implements the complete trading pipeline
        """
        try:
            logger.info(f"Executing LLM algorithm for {self.trading_pair} with {self.llm_model}")
            
            # Step 1: Crawl data (if data not provided or insufficient)
            if data.empty or len(data) < 50:
                data = self.crawl_data()
            
            # Step 2: Preprocess data into timeframes
            processed_data = self.preprocess_data(data)
            
            # Step 3: Run LLM algorithm
            algorithm_result = self.run_algorithm(processed_data)
            
            # Step 4: Make prediction
            action = self.make_prediction(algorithm_result)
            
            logger.info(f"LLM Bot action: {action}")
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
            'llm_model': self.llm_model,
            'features': [
                'OpenAI/Claude/Gemini Integration',
                'Fibonacci Retracement Analysis',
                'Multi-timeframe Analysis',
                'Confidence-based Position Sizing',
                'Risk Management',
                'AI-powered Market Analysis'
            ],
            'parameters': {
                'llm_model': self.llm_model,
                'analysis_timeframes': self.analysis_timeframes,
                'confidence_threshold': self.confidence_threshold,
                'max_position_size': self.max_position_size,
                'data_points': self.data_points
            }
        }

# Test function
def test_bot():
    """Test the LLM bot with sample configuration"""
    config = {
        'exchange_type': 'BINANCE',
        'trading_pair': 'BTC/USDT',
        'llm_model': 'openai',  # or 'claude', 'gemini'
        'analysis_timeframes': ['1h', '4h', '1d'],
        'confidence_threshold': 70,
        'max_position_size': 0.1
    }
    
    api_keys = {
        'api_key': 'test_key',
        'api_secret': 'test_secret',
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'claude_api_key': os.getenv('CLAUDE_API_KEY'),
        'gemini_api_key': os.getenv('GEMINI_API_KEY')
    }
    
    bot = LLMTradingBot(config, api_keys)
    print("✅ LLM Trading Bot created successfully!")
    print(f"Bot Info: {bot.get_bot_info()}")
    
    return bot

if __name__ == "__main__":
    test_bot()