"""
Alternating Trading Bot - Version 1.0.0
Simple strategy that alternates between BUY and SELL every timeframe with 5% allocation.
Perfect for testing and demonstrating consistent trading activity.
"""

from bots.bot_sdk.CustomBot import CustomBot
from bots.bot_sdk.Action import Action
import pandas as pd
from typing import Dict, Any
import logging
import os
import json

logger = logging.getLogger(__name__)

class AlternatingBot(CustomBot):
    """
    Alternating Strategy Bot
    - Alternates between BUY and SELL every execution
    - Uses 5% of balance for BUY orders
    - Uses 5% of current position for SELL orders
    - Maintains state to track last action
    """
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str]):
        super().__init__(config, api_keys)
        
        # Bot metadata
        self.bot_name = "Alternating Trading Bot"
        self.description = "Simple strategy that alternates between BUY and SELL with 5% allocation"
        self.version = "1.0.0"
        self.bot_type = "BASIC"
        
        # Strategy parameters
        self.allocation_percentage = config.get('allocation_percentage', 5.0)  # 5%
        self.enable_alternating = config.get('enable_alternating', True)
        self.start_with_buy = config.get('start_with_buy', True)
        
        # State management
        self.state_file = f"alternating_bot_state_{self.trading_pair.replace('/', '_')}.json"
        self.last_action = self.load_state()
        
        logger.info(f"AlternatingBot v{self.version} initialized: allocation={self.allocation_percentage}%, last_action={self.last_action}")
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """
        Alternating Strategy Implementation
        
        Args:
            data: Preprocessed market data (not used in this simple strategy)
            timeframe: Trading timeframe 
            subscription_config: Additional configuration from subscription
            
        Returns:
            Action: Alternating BUY/SELL action with 5% allocation
        """
        try:
            current_price = float(data['close'].iloc[-1])
            
            # Determine next action based on last action
            if self.last_action is None:
                # First time running - use start_with_buy preference
                next_action = "BUY" if self.start_with_buy else "SELL"
            elif self.last_action == "BUY":
                next_action = "SELL"
            elif self.last_action == "SELL":
                next_action = "BUY"
            else:
                # Last action was HOLD, default to BUY
                next_action = "BUY"
            
            # Create action with 5% allocation
            if next_action == "BUY":
                action = Action.buy(
                    type="PERCENTAGE", 
                    value=self.allocation_percentage, 
                    reason=f"Alternating strategy: BUY {self.allocation_percentage}% (previous: {self.last_action})"
                )
            else:  # SELL
                action = Action.sell(
                    type="PERCENTAGE", 
                    value=self.allocation_percentage, 
                    reason=f"Alternating strategy: SELL {self.allocation_percentage}% (previous: {self.last_action})"
                )
            
            # Save state for next execution
            self.save_state(next_action)
            self.last_action = next_action
            
            logger.info(f"Alternating Bot: {next_action} {self.allocation_percentage}% at {current_price:.2f}")
            return action
                
        except Exception as e:
            logger.error(f"Error in Alternating algorithm: {e}")
            return Action("HOLD", 0.0, f"Algorithm error: {str(e)}")
    
    def load_state(self) -> str:
        """Load last action from state file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    return state.get('last_action', None)
            return None
        except Exception as e:
            logger.warning(f"Could not load state: {e}")
            return None
    
    def save_state(self, action: str):
        """Save current action to state file"""
        try:
            state = {
                'last_action': action,
                'timestamp': pd.Timestamp.now().isoformat(),
                'trading_pair': self.trading_pair
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save state: {e}")
    
    def reset_state(self):
        """Reset bot state (useful for testing)"""
        try:
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
            self.last_action = None
            logger.info("Alternating bot state reset")
        except Exception as e:
            logger.warning(f"Could not reset state: {e}")
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this bot"""
        return {
            "type": "object",
            "properties": {
                "allocation_percentage": {
                    "type": "number",
                    "minimum": 1.0,
                    "maximum": 50.0,
                    "default": 5.0,
                    "description": "Percentage of balance/position to trade each time (default: 5%)"
                },
                "enable_alternating": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable alternating behavior (if false, always BUY)"
                },
                "start_with_buy": {
                    "type": "boolean",
                    "default": True,
                    "description": "Start with BUY order (true) or SELL order (false)"
                },
                "timeframe": {
                    "type": "string",
                    "enum": ["1m", "5m", "15m", "1h", "4h", "1d"],
                    "default": "1m",
                    "description": "Trading timeframe"
                }
            },
            "required": ["allocation_percentage"],
            "additionalProperties": True
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get detailed strategy information"""
        return {
            "name": self.bot_name,
            "version": self.version,
            "description": self.description,
            "strategy_type": "Basic/Testing",
            "indicators_used": ["None (price-agnostic)"],
            "suitable_for": ["Testing", "Demo", "High-frequency pairs"],
            "risk_level": "Low to Medium",
            "recommended_timeframes": ["1m", "5m", "15m"],
            "features": [
                "Alternates between BUY and SELL every execution",
                "Fixed 5% allocation per trade",
                "State persistence across restarts",
                "No technical analysis required",
                "Guaranteed trading activity"
            ],
            "warnings": [
                "This is a basic strategy for testing purposes",
                "Does not consider market conditions",
                "May not be profitable in trending markets",
                "Suitable for sideways/ranging markets"
            ]
        }
    
    def add_custom_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add custom features (not needed for this simple strategy)"""
        return data 