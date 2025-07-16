"""
Enhanced CustomBot SDK
Provides complete trading bot framework with exchange integration and data processing
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import logging
from abc import ABC, abstractmethod

from bots.bot_sdk.Action import Action
from exchange_factory import ExchangeFactory, BaseExchange

logger = logging.getLogger(__name__)

class CustomBot(ABC):
    """
    Enhanced base class for all trading bots
    Provides complete flow: data crawling -> preprocessing -> algorithm -> prediction -> action
    """
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str]):
        """
        Initialize bot with configuration and API keys
        
        Args:
            config: Bot configuration including strategy parameters and models
            api_keys: User's exchange API credentials
        """
        self.config = config
        self.api_keys = api_keys
        
        # Bot metadata
        self.bot_name = "CustomBot"
        self.description = "Base trading bot"
        self.version = "1.0.0"
        self.bot_type = "TECHNICAL"
        
        # Exchange client
        self.exchange_client: Optional[BaseExchange] = None
        self.exchange_type = config.get('exchange_type', 'BINANCE')
        self.trading_pair = config.get('trading_pair', 'BTC/USDT')
        
        # Data configuration
        self.max_data_points = config.get('max_data_points', 1000)  # Maximum historical data points
        self.required_warmup_periods = config.get('required_warmup_periods', 50)  # Minimum periods for analysis
        
        # Model storage
        self.models = {}
        self.scalers = {}
        self.is_models_loaded = False
        
        # Performance tracking
        self.last_analysis_time = None
        self.analysis_count = 0
        
        # Initialize exchange client
        self._initialize_exchange_client()
        
        # Load models if available
        if 'models' in config:
            self.load_models(config['models'])
    
    def _initialize_exchange_client(self):
        """Initialize exchange client for data access"""
        try:
            if self.api_keys.get('key') and self.api_keys.get('secret'):
                self.exchange_client = ExchangeFactory.create_exchange(
                    exchange_name=self.exchange_type,
                    api_key=self.api_keys['key'],
                    api_secret=self.api_keys['secret'],
                    testnet=self.config.get('testnet', True)
                )
                logger.info(f"Exchange client initialized for {self.exchange_type}")
            else:
                logger.warning("No API keys provided - exchange client not initialized")
        except Exception as e:
            logger.error(f"Failed to initialize exchange client: {e}")
            self.exchange_client = None
    
    def load_models(self, models_dict: Dict[str, Any]):
        """Load ML models and scalers from config"""
        try:
            self.models = models_dict.get('models', {})
            self.scalers = models_dict.get('scalers', {})
            self.is_models_loaded = len(self.models) > 0
            logger.info(f"Loaded {len(self.models)} models and {len(self.scalers)} scalers")
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            self.is_models_loaded = False
    
    def execute_full_cycle(self, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """
        Main execution function - complete cycle from data to action
        
        Args:
            timeframe: Trading timeframe (1m, 5m, 1h, 1d)
            subscription_config: Additional subscription configuration
            
        Returns:
            Action: Trading action (BUY/SELL/HOLD)
        """
        try:
            self.last_analysis_time = datetime.utcnow()
            self.analysis_count += 1
            
            logger.info(f"Starting full cycle analysis for {self.trading_pair} on {timeframe}")
            
            # Step 1: Crawl market data
            raw_data = self.crawl_market_data(timeframe)
            if raw_data is None or raw_data.empty:
                return Action("HOLD", 0.0, "No market data available")
            
            # Step 2: Preprocess data
            processed_data = self.preprocess_data(raw_data)
            if processed_data is None or processed_data.empty:
                return Action("HOLD", 0.0, "Data preprocessing failed")
            
            # Step 3: Execute algorithm and get prediction
            action = self.execute_algorithm(processed_data, timeframe, subscription_config)
            
            # Step 4: Post-process action (risk management, validation)
            final_action = self.post_process_action(action, processed_data)
            
            logger.info(f"Full cycle completed: {final_action.action} at {final_action.value}")
            return final_action
            
        except Exception as e:
            logger.error(f"Error in full cycle execution: {e}")
            return Action("HOLD", 0.0, f"Execution error: {str(e)}")
    
    def crawl_market_data(self, timeframe: str) -> pd.DataFrame:
        """
        Crawl market data from exchange
        
        Args:
            timeframe: Trading timeframe
            
        Returns:
            DataFrame: Raw market data with OHLCV
        """
        try:
            if not self.exchange_client:
                logger.error("Exchange client not available")
                return pd.DataFrame()
            
            # Get symbol in exchange format
            symbol = self.trading_pair.replace('/', '')
            
            # Get historical data
            data = self.exchange_client.get_klines(
                symbol=symbol,
                interval=timeframe,
                limit=self.max_data_points
            )
            
            if data.empty:
                logger.warning(f"No data received for {symbol}")
                return pd.DataFrame()
            
            # Ensure we have enough data
            if len(data) < self.required_warmup_periods:
                logger.warning(f"Insufficient data: {len(data)} < {self.required_warmup_periods}")
                return pd.DataFrame()
            
            # Add additional market information
            data = self.enrich_market_data(data)
            
            logger.info(f"Crawled {len(data)} data points for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error crawling market data: {e}")
            return pd.DataFrame()
    
    def enrich_market_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich market data with additional information
        
        Args:
            data: Basic OHLCV data
            
        Returns:
            DataFrame: Enriched data
        """
        try:
            # Add basic calculations
            data['price_change'] = data['close'].pct_change()
            data['price_change_abs'] = data['close'].diff()
            data['volume_change'] = data['volume'].pct_change()
            data['volatility'] = data['close'].rolling(window=20).std()
            
            # Add time-based features
            data['hour'] = data['timestamp'].dt.hour
            data['day_of_week'] = data['timestamp'].dt.dayofweek
            data['is_weekend'] = data['day_of_week'].isin([5, 6])
            
            # Add market session info (if needed)
            data = self.add_market_session_info(data)
            
            return data
            
        except Exception as e:
            logger.error(f"Error enriching market data: {e}")
            return data
    
    def add_market_session_info(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add market session information (Asian, European, US sessions)"""
        try:
            # Simple session classification based on UTC hours
            def get_session(hour):
                if 0 <= hour < 8:
                    return "ASIAN"
                elif 8 <= hour < 16:
                    return "EUROPEAN"
                else:
                    return "US"
            
            data['market_session'] = data['hour'].apply(get_session)
            return data
            
        except Exception as e:
            logger.error(f"Error adding market session info: {e}")
            return data
    
    def preprocess_data(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess raw market data for analysis
        
        Args:
            raw_data: Raw market data
            
        Returns:
            DataFrame: Preprocessed data
        """
        try:
            data = raw_data.copy()
            
            # Handle missing values
            data = self.handle_missing_values(data)
            
            # Add technical indicators
            data = self.add_technical_indicators(data)
            
            # Add custom features
            data = self.add_custom_features(data)
            
            # Normalize/scale features if needed
            if self.scalers:
                data = self.apply_scaling(data)
            
            # Remove any remaining NaN values
            data = data.dropna()
            
            logger.info(f"Preprocessed data shape: {data.shape}")
            return data
            
        except Exception as e:
            logger.error(f"Error preprocessing data: {e}")
            return raw_data
    
    def handle_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in data"""
        try:
            # Forward fill first, then backward fill
            data = data.fillna(method='ffill').fillna(method='bfill')
            
            # Fill remaining NaN with appropriate values
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            data[numeric_columns] = data[numeric_columns].fillna(0)
            
            return data
            
        except Exception as e:
            logger.error(f"Error handling missing values: {e}")
            return data
    
    def add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to data"""
        try:
            # Simple Moving Averages
            data['sma_10'] = data['close'].rolling(window=10).mean()
            data['sma_20'] = data['close'].rolling(window=20).mean()
            data['sma_50'] = data['close'].rolling(window=50).mean()
            
            # Exponential Moving Averages
            data['ema_12'] = data['close'].ewm(span=12).mean()
            data['ema_26'] = data['close'].ewm(span=26).mean()
            
            # RSI
            data['rsi'] = self.calculate_rsi(data['close'].values, 14)
            
            # MACD
            data['macd'] = data['ema_12'] - data['ema_26']
            data['macd_signal'] = data['macd'].ewm(span=9).mean()
            data['macd_histogram'] = data['macd'] - data['macd_signal']
            
            # Bollinger Bands
            data['bb_middle'] = data['close'].rolling(window=20).mean()
            bb_std = data['close'].rolling(window=20).std()
            data['bb_upper'] = data['bb_middle'] + (bb_std * 2)
            data['bb_lower'] = data['bb_middle'] - (bb_std * 2)
            data['bb_width'] = data['bb_upper'] - data['bb_lower']
            data['bb_position'] = (data['close'] - data['bb_lower']) / data['bb_width']
            
            # Volume indicators
            data['volume_sma'] = data['volume'].rolling(window=20).mean()
            data['volume_ratio'] = data['volume'] / data['volume_sma']
            
            return data
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {e}")
            return data
    
    def add_custom_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add custom features specific to the bot strategy"""
        try:
            # Price momentum
            data['momentum_5'] = data['close'].pct_change(5)
            data['momentum_10'] = data['close'].pct_change(10)
            
            # Volatility measures
            data['volatility_5'] = data['close'].rolling(window=5).std()
            data['volatility_20'] = data['close'].rolling(window=20).std()
            data['volatility_ratio'] = data['volatility_5'] / data['volatility_20']
            
            # Support/Resistance levels
            data['support'] = data['low'].rolling(window=20).min()
            data['resistance'] = data['high'].rolling(window=20).max()
            data['support_distance'] = (data['close'] - data['support']) / data['close']
            data['resistance_distance'] = (data['resistance'] - data['close']) / data['close']
            
            return data
            
        except Exception as e:
            logger.error(f"Error adding custom features: {e}")
            return data
    
    def apply_scaling(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply scaling to features if scalers are available"""
        try:
            if not self.scalers:
                return data
            
            # Apply scaling to numeric columns
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            
            for scaler_name, scaler in self.scalers.items():
                if hasattr(scaler, 'transform'):
                    scaled_data = scaler.transform(data[numeric_columns])
                    data[numeric_columns] = scaled_data
                    logger.info(f"Applied {scaler_name} scaling")
                    break  # Use first available scaler
            
            return data
            
        except Exception as e:
            logger.error(f"Error applying scaling: {e}")
            return data
    
    @abstractmethod
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """
        Execute trading algorithm - must be implemented by subclasses
        
        Args:
            data: Preprocessed market data
            timeframe: Trading timeframe
            subscription_config: Additional configuration
            
        Returns:
            Action: Trading action
        """
        pass
    
    def post_process_action(self, action: Action, data: pd.DataFrame) -> Action:
        """
        Post-process action with risk management and validation
        
        Args:
            action: Original action from algorithm
            data: Market data for context
            
        Returns:
            Action: Final processed action
        """
        try:
            # Risk management checks
            if self.should_skip_action(action, data):
                return Action("HOLD", action.value, "Action skipped due to risk management")
            
            # Adjust action based on market conditions
            adjusted_action = self.adjust_action_for_market_conditions(action, data)
            
            # Validate action
            if not self.validate_action(adjusted_action, data):
                return Action("HOLD", action.value, "Action validation failed")
            
            return adjusted_action
            
        except Exception as e:
            logger.error(f"Error in post-processing action: {e}")
            return Action("HOLD", action.value, f"Post-processing error: {str(e)}")
    
    def should_skip_action(self, action: Action, data: pd.DataFrame) -> bool:
        """Check if action should be skipped due to risk management"""
        try:
            # Skip during high volatility periods
            if 'volatility' in data.columns:
                current_volatility = data['volatility'].iloc[-1]
                avg_volatility = data['volatility'].mean()
                
                if current_volatility > avg_volatility * 2:
                    logger.warning("Skipping action due to high volatility")
                    return True
            
            # Skip during low volume periods
            if 'volume_ratio' in data.columns:
                current_volume_ratio = data['volume_ratio'].iloc[-1]
                if current_volume_ratio < 0.5:
                    logger.warning("Skipping action due to low volume")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if action should be skipped: {e}")
            return False
    
    def adjust_action_for_market_conditions(self, action: Action, data: pd.DataFrame) -> Action:
        """Adjust action based on current market conditions"""
        try:
            # Reduce signal strength in uncertain market conditions
            if 'bb_position' in data.columns:
                bb_position = data['bb_position'].iloc[-1]
                
                # Reduce strength if price is at extremes
                if bb_position > 0.8 or bb_position < 0.2:
                    action.value *= 0.8  # Reduce signal strength
                    action.reason += " (adjusted for extreme BB position)"
            
            return action
            
        except Exception as e:
            logger.error(f"Error adjusting action for market conditions: {e}")
            return action
    
    def validate_action(self, action: Action, data: pd.DataFrame) -> bool:
        """Validate action before execution"""
        try:
            # Check if action is valid
            if action.action not in ["BUY", "SELL", "HOLD"]:
                logger.error(f"Invalid action: {action.action}")
                return False
            
            # Check if value is reasonable
            if action.value <= 0:
                logger.error(f"Invalid action value: {action.value}")
                return False
            
            # Additional validation can be added here
            return True
            
        except Exception as e:
            logger.error(f"Error validating action: {e}")
            return False
    
    # Utility methods
    def calculate_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate RSI indicator"""
        try:
            deltas = np.diff(prices)
            seed = deltas[:period+1]
            up = seed[seed >= 0].sum() / period
            down = -seed[seed < 0].sum() / period
            rs = up / down if down != 0 else 0
            rsi = np.zeros_like(prices)
            rsi[:period] = 100.0 - 100.0 / (1.0 + rs)
            
            for i in range(period, len(prices)):
                delta = deltas[i-1]
                if delta > 0:
                    upval = delta
                    downval = 0.0
                else:
                    upval = 0.0
                    downval = -delta
                
                up = (up * (period - 1) + upval) / period
                down = (down * (period - 1) + downval) / period
                rs = up / down if down != 0 else 0
                rsi[i] = 100.0 - 100.0 / (1.0 + rs)
            
            return rsi
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return np.zeros_like(prices)
    
    def calculate_sma(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average"""
        try:
            return pd.Series(prices).rolling(window=period).mean().values
        except Exception as e:
            logger.error(f"Error calculating SMA: {e}")
            return np.zeros_like(prices)
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information from exchange"""
        try:
            if not self.exchange_client:
                return {}
            
            account_info = self.exchange_client.get_account_info()
            return account_info
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}
    
    def get_balance(self, asset: str = "USDT") -> Dict[str, Any]:
        """Get balance for specific asset"""
        try:
            if not self.exchange_client:
                return {"free": "0", "locked": "0"}
            
            balance = self.exchange_client.get_balance(asset)
            return {
                "asset": balance.asset,
                "free": balance.free,
                "locked": balance.locked
            }
            
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return {"free": "0", "locked": "0"}
    
    def get_current_price(self, symbol: str = None) -> float:
        """Get current price for symbol"""
        try:
            if not self.exchange_client:
                return 0.0
            
            symbol = symbol or self.trading_pair.replace('/', '')
            return self.exchange_client.get_current_price(symbol)
            
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return 0.0
    
    def get_bot_info(self) -> Dict[str, Any]:
        """Get bot information"""
        return {
            "name": self.bot_name,
            "description": self.description,
            "version": self.version,
            "bot_type": self.bot_type,
            "exchange_type": self.exchange_type,
            "trading_pair": self.trading_pair,
            "models_loaded": self.is_models_loaded,
            "analysis_count": self.analysis_count,
            "last_analysis": self.last_analysis_time.isoformat() if self.last_analysis_time else None
        }
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this bot - to be overridden by subclasses"""
        return {
            "type": "object",
            "properties": {
                "max_data_points": {
                    "type": "integer",
                    "minimum": 100,
                    "maximum": 5000,
                    "default": 1000,
                    "description": "Maximum number of historical data points to use"
                },
                "required_warmup_periods": {
                    "type": "integer",
                    "minimum": 20,
                    "maximum": 200,
                    "default": 50,
                    "description": "Minimum number of periods required for analysis"
                }
            },
            "required": ["max_data_points", "required_warmup_periods"],
            "additionalProperties": True
        }
    
    # Backward compatibility methods
    def analyze_market(self, market_data: pd.DataFrame) -> Action:
        """Backward compatibility method - delegates to execute_algorithm"""
        return self.execute_algorithm(market_data, "1h")
    
    def analyze_market_simple(self, market_info: Dict[str, Any]) -> Action:
        """
        Simplified market analysis method that accepts basic market info
        and performs full cycle analysis
        
        Args:
            market_info: Dictionary containing basic market information
                        Keys: symbol, current_price, timestamp
                        
        Returns:
            Action: Trading action based on full analysis
        """
        try:
            # Extract timeframe from config or use default
            timeframe = self.config.get('timeframe', '1h')
            
            # Use full cycle analysis which includes data crawling
            return self.execute_full_cycle(timeframe)
            
        except Exception as e:
            logger.error(f"Error in simplified market analysis: {e}")
            return Action("HOLD", 0.0, f"Analysis error: {str(e)}") 