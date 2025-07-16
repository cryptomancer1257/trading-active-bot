"""
Machine Learning LSTM Trading Bot
Demonstrates ML bot capabilities with LSTM price prediction
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from bot_sdk import CustomBot, Action

logger = logging.getLogger(__name__)

class MLLSTMBot(CustomBot):
    """
    ML Trading Bot using LSTM for price prediction
    Demonstrates how to integrate ML models with trading logic
    """
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str]):
        super().__init__(config, api_keys)
        self.bot_name = "ML LSTM Price Predictor"
        self.description = "Uses LSTM neural network to predict price movements"
        self.version = "1.0.0"
        
        # ML specific configuration
        self.sequence_length = config.get('sequence_length', 60)  # 60 time steps
        self.prediction_threshold = config.get('prediction_threshold', 0.02)  # 2%
        self.confidence_threshold = config.get('confidence_threshold', 0.7)
        self.lookback_periods = config.get('lookback_periods', 100)
        
        # Model configuration
        self.model = None
        self.scaler = None
        self.feature_columns = ['open', 'high', 'low', 'close', 'volume']
        self.is_model_loaded = False
        
        # Load models if available
        if 'models' in config:
            self.load_models_from_config(config['models'])
    
    def load_models_from_config(self, models_dict: Dict[str, Any]):
        """Load ML models from config"""
        try:
            if 'MODEL' in models_dict:
                self.model = models_dict['MODEL']
                logger.info("LSTM model loaded successfully")
            
            if 'SCALER' in models_dict:
                self.scaler = models_dict['SCALER']
                logger.info("Data scaler loaded successfully")
            
            self.is_model_loaded = (self.model is not None and self.scaler is not None)
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            self.is_model_loaded = False
    
    def prepare_features(self, market_data: pd.DataFrame) -> np.ndarray:
        """Prepare features for ML model"""
        try:
            # Select feature columns
            features = market_data[self.feature_columns].values
            
            # Calculate technical indicators
            close_prices = market_data['close'].values
            
            # RSI
            rsi = self.calculate_rsi(close_prices, 14)
            
            # Moving averages
            ma_short = self.calculate_sma(close_prices, 10)
            ma_long = self.calculate_sma(close_prices, 30)
            ma_ratio = ma_short / ma_long
            
            # Price change percentage
            price_change = np.diff(close_prices, prepend=close_prices[0]) / close_prices * 100
            
            # Volatility (rolling std)
            volatility = pd.Series(close_prices).rolling(window=10).std().fillna(0).values
            
            # Volume change
            volume_change = np.diff(market_data['volume'].values, prepend=market_data['volume'].values[0])
            
            # Combine all features
            additional_features = np.column_stack([
                rsi, ma_ratio, price_change, volatility, volume_change
            ])
            
            all_features = np.column_stack([features, additional_features])
            
            # Fill NaN values
            all_features = np.nan_to_num(all_features, nan=0.0)
            
            return all_features
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return features  # Return basic features if advanced calculation fails
    
    def create_sequences(self, data: np.ndarray) -> np.ndarray:
        """Create sequences for LSTM model"""
        try:
            if len(data) < self.sequence_length:
                # Pad with zeros if not enough data
                padding = np.zeros((self.sequence_length - len(data), data.shape[1]))
                data = np.vstack([padding, data])
            
            # Take the last sequence_length points
            sequence = data[-self.sequence_length:]
            
            # Reshape for LSTM (batch_size=1, timesteps, features)
            return sequence.reshape(1, self.sequence_length, -1)
            
        except Exception as e:
            logger.error(f"Error creating sequences: {e}")
            return None
    
    def predict_with_model(self, features: np.ndarray) -> Dict[str, Any]:
        """Make prediction using LSTM model"""
        try:
            if not self.is_model_loaded:
                return {"prediction": 0.0, "confidence": 0.0, "direction": "HOLD"}
            
            # Scale features
            scaled_features = self.scaler.transform(features.reshape(-1, features.shape[-1]))
            scaled_features = scaled_features.reshape(features.shape)
            
            # Make prediction
            prediction = self.model.predict(scaled_features, verbose=0)
            
            # Convert prediction to price direction and confidence
            predicted_change = float(prediction[0][0])  # Assuming single output
            confidence = min(abs(predicted_change) * 10, 1.0)  # Scale to 0-1
            
            direction = "HOLD"
            if predicted_change > self.prediction_threshold:
                direction = "BUY"
            elif predicted_change < -self.prediction_threshold:
                direction = "SELL"
            
            return {
                "prediction": predicted_change,
                "confidence": confidence,
                "direction": direction,
                "threshold": self.prediction_threshold
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return {"prediction": 0.0, "confidence": 0.0, "direction": "HOLD"}
    
    def analyze_market(self, market_data: pd.DataFrame) -> Action:
        """Analyze market using ML model and technical indicators"""
        try:
            if len(market_data) < self.lookback_periods:
                logger.warning("Insufficient market data for analysis")
                return Action("HOLD", 0.0, "Insufficient data")
            
            # Prepare features
            features = self.prepare_features(market_data)
            
            # Create sequences for LSTM
            sequences = self.create_sequences(features)
            if sequences is None:
                return Action("HOLD", 0.0, "Failed to create sequences")
            
            # Make ML prediction
            ml_prediction = self.predict_with_model(sequences)
            
            # Combine with traditional technical analysis
            current_price = float(market_data['close'].iloc[-1])
            
            # Calculate additional indicators
            rsi = self.calculate_rsi(market_data['close'].values, 14)[-1]
            sma_20 = self.calculate_sma(market_data['close'].values, 20)[-1]
            volume_ratio = self.calculate_volume_ratio(market_data)
            
            # Decision logic combining ML and traditional indicators
            ml_direction = ml_prediction["direction"]
            ml_confidence = ml_prediction["confidence"]
            
            # Only take action if ML confidence is high enough
            if ml_confidence < self.confidence_threshold:
                return Action("HOLD", current_price, f"Low ML confidence: {ml_confidence:.2f}")
            
            # Additional confirmation from technical indicators
            signal_strength = ml_confidence
            action_reason = f"ML prediction: {ml_direction} (confidence: {ml_confidence:.2f})"
            
            if ml_direction == "BUY":
                # Confirm with technical indicators
                if rsi < 70 and current_price > sma_20 and volume_ratio > 1.2:
                    signal_strength += 0.2
                    action_reason += ", Technical confirmation: RSI<70, Price>SMA20, High volume"
                    return Action("BUY", current_price, action_reason, "ML_BUY", signal_strength)
                elif rsi < 50:  # Less strict confirmation
                    return Action("BUY", current_price, action_reason + ", Partial technical confirmation", "ML_BUY", signal_strength * 0.8)
            
            elif ml_direction == "SELL":
                # Confirm with technical indicators
                if rsi > 30 and current_price < sma_20 and volume_ratio > 1.2:
                    signal_strength += 0.2
                    action_reason += ", Technical confirmation: RSI>30, Price<SMA20, High volume"
                    return Action("SELL", current_price, action_reason, "ML_SELL", signal_strength)
                elif rsi > 50:  # Less strict confirmation
                    return Action("SELL", current_price, action_reason + ", Partial technical confirmation", "ML_SELL", signal_strength * 0.8)
            
            # Default to HOLD if no strong signal
            return Action("HOLD", current_price, f"ML suggests {ml_direction} but lacks technical confirmation", "ML_HOLD", ml_confidence)
            
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            return Action("HOLD", 0.0, f"Analysis error: {str(e)}")
    
    def calculate_volume_ratio(self, market_data: pd.DataFrame) -> float:
        """Calculate current volume ratio vs average"""
        try:
            current_volume = float(market_data['volume'].iloc[-1])
            avg_volume = float(market_data['volume'].tail(20).mean())
            return current_volume / avg_volume if avg_volume > 0 else 1.0
        except:
            return 1.0
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        return {
            "model_loaded": self.is_model_loaded,
            "model_type": "LSTM" if self.model else None,
            "sequence_length": self.sequence_length,
            "feature_count": len(self.feature_columns) + 5,  # +5 for additional features
            "prediction_threshold": self.prediction_threshold,
            "confidence_threshold": self.confidence_threshold,
            "scaler_loaded": self.scaler is not None
        }
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Return configuration schema for this bot"""
        return {
            "type": "object",
            "properties": {
                "sequence_length": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 200,
                    "default": 60,
                    "description": "Number of time steps for LSTM input"
                },
                "prediction_threshold": {
                    "type": "number",
                    "minimum": 0.001,
                    "maximum": 0.1,
                    "default": 0.02,
                    "description": "Minimum price change percentage to trigger action"
                },
                "confidence_threshold": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 1.0,
                    "default": 0.7,
                    "description": "Minimum confidence level to take action"
                },
                "lookback_periods": {
                    "type": "integer",
                    "minimum": 50,
                    "maximum": 500,
                    "default": 100,
                    "description": "Number of historical periods to analyze"
                }
            },
            "required": ["sequence_length", "prediction_threshold", "confidence_threshold"],
            "additionalProperties": False
        }
    
    def get_required_models(self) -> List[Dict[str, Any]]:
        """Return information about required ML models"""
        return [
            {
                "type": "MODEL",
                "framework": "tensorflow",
                "model_type": "LSTM",
                "description": "LSTM model for price prediction",
                "input_shape": [self.sequence_length, len(self.feature_columns) + 5],
                "output_shape": [1],
                "required": True
            },
            {
                "type": "SCALER",
                "framework": "sklearn",
                "model_type": "preprocessing",
                "description": "Feature scaler (StandardScaler or MinMaxScaler)",
                "required": True
            }
        ]
    
    def validate_models(self) -> Dict[str, Any]:
        """Validate that all required models are loaded and working"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if not self.is_model_loaded:
            validation_result["valid"] = False
            validation_result["errors"].append("Required models not loaded")
        
        if self.model is None:
            validation_result["errors"].append("LSTM model not loaded")
        
        if self.scaler is None:
            validation_result["errors"].append("Feature scaler not loaded")
        
        # Test model with dummy data
        if self.is_model_loaded:
            try:
                dummy_data = np.random.random((1, self.sequence_length, len(self.feature_columns) + 5))
                scaled_data = self.scaler.transform(dummy_data.reshape(-1, dummy_data.shape[-1]))
                prediction = self.model.predict(scaled_data.reshape(dummy_data.shape), verbose=0)
                if prediction.shape != (1, 1):
                    validation_result["warnings"].append(f"Unexpected prediction shape: {prediction.shape}")
            except Exception as e:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Model validation failed: {str(e)}")
        
        return validation_result 