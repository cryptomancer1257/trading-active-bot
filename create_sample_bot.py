#!/usr/bin/env python3
"""
Create sample bot for testing
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment
load_dotenv('.env')

from database import SessionLocal
import models
import schemas

def create_bot_directory_structure(bot_id, version="1.0.0"):
    """Create bot directory structure"""
    bot_dir = Path(f"bots/{bot_id}/code/{version}")
    bot_dir.mkdir(parents=True, exist_ok=True)
    return bot_dir

def create_golden_cross_bot_file(bot_dir):
    """Create a simple Golden Cross bot file"""
    bot_content = '''#!/usr/bin/env python3
"""
Golden Cross Trading Bot - Simple Version for Testing
"""

import pandas as pd
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class Action:
    def __init__(self, action_type: str, amount: float, reason: str = ""):
        self.action_type = action_type  # BUY, SELL, HOLD
        self.amount = amount
        self.reason = reason
    
    def __str__(self):
        return f"Action({self.action_type}, {self.amount}, {self.reason})"

class GoldenCrossBot:
    """
    Simple Golden Cross Trading Bot for Testing
    Uses 50-day and 200-day moving averages
    """
    
    def __init__(self):
        self.name = "Golden Cross Bot"
        self.version = "1.0.0"
        self.short_window = 50
        self.long_window = 200
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """
        Execute Golden Cross algorithm
        """
        try:
            logger.info(f"Golden Cross Bot executing with {len(data)} data points")
            
            # Get configuration
            config = subscription_config or {}
            short_window = config.get('short_window', self.short_window)
            long_window = config.get('long_window', self.long_window)
            position_size = config.get('position_size', 0.2)
            
            # Check if we have enough data
            if len(data) < max(short_window, long_window):
                return Action("HOLD", 0.0, f"Insufficient data: need {max(short_window, long_window)}, got {len(data)}")
            
            # Calculate moving averages
            data['SMA_short'] = data['close'].rolling(window=short_window).mean()
            data['SMA_long'] = data['close'].rolling(window=long_window).mean()
            
            # Get latest values
            latest = data.iloc[-1]
            previous = data.iloc[-2] if len(data) >= 2 else data.iloc[-1]
            
            sma_short_current = latest['SMA_short']
            sma_long_current = latest['SMA_long']
            sma_short_previous = previous['SMA_short']
            sma_long_previous = previous['SMA_long']
            
            # Check for golden cross (short MA crosses above long MA)
            if (sma_short_previous <= sma_long_previous and 
                sma_short_current > sma_long_current and
                not pd.isna(sma_short_current) and not pd.isna(sma_long_current)):
                
                return Action("BUY", position_size, 
                    f"Golden Cross detected: SMA{short_window}({sma_short_current:.2f}) > SMA{long_window}({sma_long_current:.2f})")
            
            # Check for death cross (short MA crosses below long MA)  
            elif (sma_short_previous >= sma_long_previous and
                  sma_short_current < sma_long_current and
                  not pd.isna(sma_short_current) and not pd.isna(sma_long_current)):
                
                return Action("SELL", position_size,
                    f"Death Cross detected: SMA{short_window}({sma_short_current:.2f}) < SMA{long_window}({sma_long_current:.2f})")
            
            # Hold position
            return Action("HOLD", 0.0, 
                f"No signal: SMA{short_window}({sma_short_current:.2f}), SMA{long_window}({sma_long_current:.2f})")
            
        except Exception as e:
            logger.error(f"Error in Golden Cross algorithm: {e}")
            return Action("HOLD", 0.0, f"Algorithm error: {str(e)}")
    
    def get_configuration_schema(self):
        """Get configuration schema"""
        return {
            "short_window": {"type": "integer", "default": 50, "min": 5, "max": 100},
            "long_window": {"type": "integer", "default": 200, "min": 50, "max": 500},
            "position_size": {"type": "float", "default": 0.2, "min": 0.01, "max": 1.0}
        }
'''
    
    bot_file = bot_dir / "golden_cross_bot.py"
    with open(bot_file, 'w') as f:
        f.write(bot_content)
    
    return bot_file

def create_bot_in_database():
    """Create bot entry in database"""
    db = SessionLocal()
    try:
        # Check if bot already exists
        existing_bot = db.query(models.Bot).filter(models.Bot.id == 7).first()
        if existing_bot:
            print(f"✅ Bot with ID 7 already exists: {existing_bot.name}")
            return existing_bot
        
        # Create bot directory and file
        bot_dir = create_bot_directory_structure(7)
        bot_file = create_golden_cross_bot_file(bot_dir)
        
        # Create bot entry
        bot = models.Bot(
            id=7,
            name="Golden Cross Bot",
            description="Simple Golden Cross trading strategy using moving averages",
            developer_id=1,  # Assume admin user exists
            status=models.BotStatus.APPROVED,
            code_path=str(bot_file),
            version="1.0.0",
            bot_type="TECHNICAL",
            is_free=True,
            price_per_month=0.0,
            config_schema={
                "type": "object",
                "properties": {
                    "short_window": {"type": "integer", "default": 50},
                    "long_window": {"type": "integer", "default": 200},
                    "position_size": {"type": "number", "default": 0.2}
                }
            },
            default_config={
                "short_window": 50,
                "long_window": 200,
                "position_size": 0.2
            }
        )
        
        db.add(bot)
        db.commit()
        db.refresh(bot)
        
        print(f"✅ Created bot: {bot.name} (ID: {bot.id})")
        print(f"   File: {bot.code_path}")
        return bot
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating bot: {e}")
        return None
    finally:
        db.close()

def create_test_user():
    """Create test user if not exists"""
    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(models.User).filter(models.User.id == 1).first()
        if user:
            print(f"✅ User already exists: {user.email}")
            return user
        
        # Create admin user
        from security import get_password_hash
        
        user = models.User(
            id=1,
            email="admin@test.com",
            hashed_password=get_password_hash("admin123"),
            role=models.UserRole.ADMIN,
            is_active=True,
            developer_name="Test Admin",
            developer_bio="Test admin user for bot marketplace"
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"✅ Created admin user: {user.email}")
        return user
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating user: {e}")
        return None
    finally:
        db.close()

def main():
    """Main function"""
    print("🤖 Creating Sample Bot for Testing")
    print("=" * 40)
    
    # Create test user first
    user = create_test_user()
    if not user:
        print("❌ Failed to create test user")
        return
    
    # Create bot
    bot = create_bot_in_database()
    if not bot:
        print("❌ Failed to create bot")
        return
    
    print("\n🎉 Sample bot created successfully!")
    print(f"Bot ID: {bot.id}")
    print(f"Bot File: {bot.code_path}")
    print("\nYou can now:")
    print("1. Restart Celery worker")
    print("2. Create subscriptions using this bot")
    print("3. Test bot execution")

if __name__ == "__main__":
    main() 