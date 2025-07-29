"""
Bot Base Classes Loader
Loads base classes from bot_sdk folder for dynamic bot execution
"""

import os
import sys
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

def load_base_classes_from_sdk():
    """
    Load base classes from bot_sdk folder
    
    Returns:
        str: Combined base classes code
    """
    try:
        # Get the path to bot_sdk folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        bot_sdk_path = os.path.join(parent_dir, 'bots', 'bot_sdk')
        
        base_classes_code = []
        
        # Read Action.py
        action_file = os.path.join(bot_sdk_path, 'Action.py')
        if os.path.exists(action_file):
            with open(action_file, 'r', encoding='utf-8') as f:
                action_code = f.read()
                base_classes_code.append(f"# Action class from bot_sdk\n{action_code}")
                logger.info("Loaded Action class from bot_sdk")
        
        # Read CustomBot.py (only the base class, not the full implementation)
        custombot_file = os.path.join(bot_sdk_path, 'CustomBot.py')
        if os.path.exists(custombot_file):
            with open(custombot_file, 'r', encoding='utf-8') as f:
                custombot_code = f.read()
                
                # Extract only the base class definition and essential methods
                # This is a simplified version for dynamic loading
                simplified_custombot = """
# Simplified CustomBot base class from bot_sdk
import pandas as pd
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CustomBot:
    \"\"\"Base bot class for dynamic loading\"\"\"
    def __init__(self, config: Dict[str, Any] = None, api_keys: Dict[str, str] = None):
        self.config = config or {}
        self.api_keys = api_keys or {}
        self.bot_name = "Base Bot"
        self.version = "1.0.0"
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        return Action("HOLD", 0.0, "Base implementation")
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        return {}
    
    def crawl_market_data(self, timeframe: str) -> pd.DataFrame:
        \"\"\"Crawl market data - to be implemented by specific bots\"\"\"
        return pd.DataFrame()
    
    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        \"\"\"Preprocess data - to be implemented by specific bots\"\"\"
        return data
    
    def post_process_action(self, action: Action, data: pd.DataFrame) -> Action:
        \"\"\"Post-process action - to be implemented by specific bots\"\"\"
        return action
    
    def execute_full_cycle(self, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        \"\"\"Execute full cycle - to be implemented by specific bots\"\"\"
        return Action("HOLD", 0.0, "Base implementation")
"""
                base_classes_code.append(simplified_custombot)
                logger.info("Loaded CustomBot base class from bot_sdk")
        
        # Add necessary imports
        imports = """
# Required imports for base classes
import pandas as pd
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)
"""
        
        # Combine all code
        full_code = imports + "\n\n".join(base_classes_code)
        
        logger.info(f"Successfully loaded base classes from bot_sdk")
        return full_code
        
    except Exception as e:
        logger.error(f"Failed to load base classes from bot_sdk: {e}")
        
        # Return fallback base classes
        return """
# Fallback base classes
import pandas as pd
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Action:
    \"\"\"Trading action class\"\"\"
    def __init__(self, action: str, value: float, reason: str = "", type: str = "PERCENTAGE"):
        self.action = action.upper()  # BUY, SELL, HOLD
        self.value = value
        self.reason = reason
        self.type = type  # PERCENTAGE, USDT_AMOUNT, QUANTITY
    
    @classmethod
    def buy(cls, type: str, value: float, reason: str = ""):
        return cls("BUY", value, reason, type)
    
    @classmethod  
    def sell(cls, type: str, value: float, reason: str = ""):
        return cls("SELL", value, reason, type)
    
    @classmethod
    def hold(cls, reason: str = ""):
        return cls("HOLD", 0.0, reason)
    
    def __str__(self):
        return f"Action(action={self.action}, value={self.value}, reason={self.reason})"

class CustomBot:
    \"\"\"Base bot class\"\"\"
    def __init__(self, config: Dict[str, Any] = None, api_keys: Dict[str, str] = None):
        self.config = config or {}
        self.api_keys = api_keys or {}
        self.bot_name = "Base Bot"
        self.version = "1.0.0"
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        return Action.hold("Base implementation")
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        return {}
    
    def execute_full_cycle(self, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        return Action.hold("Base implementation")
"""

def get_base_classes():
    """
    Get base classes for bot execution
    
    Returns:
        str: Base classes code
    """
    return load_base_classes_from_sdk() 